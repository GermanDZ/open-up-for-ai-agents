# Exploration: `openup-agent` reference driver — first live-run feedback

**Started:** 2026-07-13
**Question:** What did the first real (non-Anthropic, local-model) run of the
reference driver (`openup-agent run`, T-072) surface that should shape the next
iterations — the live-model acceptance of T-072, the T-074 human-in-the-loop
work, and the T-073 service?
**Follow-on to:** [2026-07-12-harness-agnostic-openup.md](2026-07-12-harness-agnostic-openup.md)

## Context

A session set out to exercise the T-072 reference driver end-to-end by building a
throwaway example project ("todo task list") on a **local LM Studio endpoint**
(`qwen/qwen3.6-35b-a3b`, OpenAI-compatible), operator playing the customer. The
goal was explicitly feedback-gathering, not delivery. The run reached the driver's
first model call, then the LM Studio host dropped off the network (100% packet
loss), so the loop did not complete. Everything up to the first inference call
validated; several concrete findings emerged, plus one unplanned process finding.

This is **evidence for the T-072 "live-model acceptance" success measure** (still
`done`, not yet `verified`) — it is a *partial* run: setup + transport proven, the
agentic loop itself unproven on a local model. A clean end-to-end still owes a
`verified` read-back.

## What validated (before the endpoint died)

- **Auth reality on LM Studio.** The server had auth **enabled**; a real generated
  token was required. Dummy strings (`lm-studio`) are rejected with
  `Malformed LM Studio API token` — the doc's "any non-empty string for local
  servers" is only true when the operator has *not* turned on "Require API key".
- **Model tool-calling.** `qwen/qwen3.6-35b-a3b` emits native OpenAI `tool_calls`
  (~3.7s warm, with reasoning tokens) — a viable driver model. `google/gemma-4-31b-qat`
  also served but not exercised.
- **Scaffolding.** `scripts/bootstrap-project.sh todo-task-list` produced a runnable
  project: procedure pack + 21 OpenUP CLIs + `git init` + clean initial commit.
  `docs/` starts empty (only `.gitkeep`).
- **Deterministic layer.** Customer-seeded `docs/roadmap.md` (one pending task) →
  `openup-roadmap.py next` → T-001 → `openup-board.py resolve` →
  `{path: promote, next_action: "author spec + start"}`. Byte-clean, no model needed.
- **Driver launch.** `openup-agent run --dir <proj> --procedure next` started,
  resolved the tier/model/endpoint, reached iteration 1.

## Findings → proposed action

### F1. No retry/backoff on transport errors *(highest value)*
Iteration 1 hit `[Errno 60] Operation timed out` and the whole run died
(`FATAL: endpoint error on iteration 1`). A single transient network blip kills a
long local-model run with no recovery.
- **Action:** wrap the chat call in a bounded retry (e.g. 3 tries, exponential
  backoff) for transport-class errors (timeout, connection refused, 5xx). Keep
  config errors (2) and auth/4xx (3) fatal. Small, well-scoped driver task.

### F2. First-call timeout too tight for cold local loads
`llm.py` uses a flat `timeout=120`. A cold 35B load + the large first prompt
(full procedure text + 6 tool definitions) can exceed that on a local box; the very
first call is the worst case.
- **Action:** longer first-call timeout (or a cheap warm-up ping / `GET /models`
  probe before the loop), then a shorter steady-state timeout. Document that cold
  loads are slow and suggest pre-loading the model.

### F3. Non-interactive by design blocks the "customer answers questions" flow
The driver auto-proceeds the plan gate (T-072 assumption); there is no channel for
a blocking question to reach a human. So "assume the customer role and answer
questions" cannot happen *through the driver* — customer intent must be seeded up
front as Ring-1 artifacts (as done here: hand-written `project-status.md` +
`roadmap.md`).
- **Action:** this is exactly **T-074** (human-in-the-loop input handling), which
  was delivered concurrently during this very session. The live re-run should
  re-test whether a procedure that asks a blocking question now pauses for operator
  input instead of auto-proceeding. T-074 is the unblock; verify it against a real
  question, not just unit tests.

### F4. Fresh project has empty `docs/` — `next` no-ops with nothing to promote
A bootstrapped project cannot be driven until someone authors a roadmap with a
pending task. There is no "seed the first task" on-ramp; the operator hand-wrote the
table (and had to match the `openup-roadmap.py` header-column parser exactly).
- **Action:** a small `--seed` / init helper (or an `openup-inception` run wired for
  the driver) that writes a valid `project-status.md` + `roadmap.md` skeleton, so a
  brand-new project is drivable without reverse-engineering the table format.

### F5. Two agent sessions in one working tree deadlock the stop hook *(process, not driver)*
Mid-session, a **concurrent T-074 delivery session** (a separate window/loop)
checked out `feat/T-074-human-in-the-loop-input` in the **same working tree**,
switching the branch under this session. This session's `on-stop.py` then looped
indefinitely, blocking on the *other* lane's uncommitted files
(`scripts/openup-agent.py`, `openup_agent/loop.py`, `tools.py`, tests,
`docs/changes/T-074/`). The correct behaviour was to **refuse to commit or stash
another lane's live work**; the loop only cleared once the T-074 session committed
and ran `sync-status.py` itself.
- **Impact:** a shared-tree, multi-session setup can wedge a bystander session's
  stop gate on work it must not touch. The write-fence protects *content* lanes but
  the *branch + working tree* are still a single shared resource.
- **Action:** lane isolation via **git worktrees** (one working tree per active
  lane) would prevent branch-switching under a live session. Short of that, the
  stop hook could scope its uncommitted-changes check to files inside the *current
  session's* declared lane/touches, so a bystander is not blocked by another lease's
  work. Recommend a follow-on task.

## Suggested next-iteration ordering

1. **T-072 live-model acceptance (finish the `verified` read-back).** Re-run
   `--procedure next` on the local model to a clean sentinel + fence/`check-docs`
   green, now that F1/F2 are understood. Record model, sentinel, gate friction in
   `docs/changes/archive/T-072/design.md`.
2. **Driver hardening (F1 + F2).** Retry/backoff + first-call timeout. Small,
   independent, unblocks every future local run.
3. **T-074 live verification (F3).** Confirm a blocking question actually pauses for
   operator input on the driver, end-to-end (not only unit-tested).
4. **First-run on-ramp (F4).** Seed helper for a drivable empty project.
5. **Lane/working-tree isolation (F5).** Worktree-per-lane or lane-scoped stop-hook
   check, to stop concurrent sessions wedging each other.

## Reproduction

Project + customer seed are committed in a **separate** scratch git repo
(`todo-task-list/`), so the run is repeatable. When the endpoint is back:

```
export LLM_API_URL='http://<host>:1234/v1'
export LLM_API_KEY='<lm-studio-token>'
export OPENUP_MODEL_MAIN='qwen/qwen3.6-35b-a3b'   # + _MID / _SMALL to the same id
python3 scripts/openup-agent.py run --dir <proj>/todo-task-list --procedure next --max-iterations 60
```

---
id: T-089
title: Cycle engine core — deterministic pick/resume + Operations-step executor
status: ready   # proposed → ready → in-progress → done → verified
priority: high   # critical | high | medium | low
estimate: 1-2 sessions
plan: docs/explorations/2026-07-13-deterministic-cycle-engine.md
depends-on: [T-072, T-080]
blocks: [T-090, T-091]
touches:
  - scripts/openup-agent.py
  - scripts/openup_agent/
  - scripts/openup-agent-bench.py
  - scripts/bench-scenarios/cycle-quick-doc/
  - scripts/tests/test_openup_agent.py
  - scripts/tests/test_openup_agent_cycle.py
  - scripts/tests/test_openup_agent_bench.py
  - scripts/process-manifest.txt
  - docs-eng-process/reference-driver.md
  - docs-eng-process/script-cli-reference.md
last-synced: ""
---

# T-089 — Cycle engine core: deterministic pick/resume + Operations-step executor

## Story

> **As** the owner of the harness-optional program running OpenUP on a weak local
> model through the reference driver
> **I want** a new `openup-agent.py cycle` mode that runs one delivery cycle as a
> deterministic state machine over the existing scripts — resolve → session begin
> → per-Operations-box executor (scripts as code, judgment as fresh bounded
> sub-runs) → gates → deterministic completion
> **So that** the model only ever authors one step at a time while code does the
> ceremony — collapsing the measured ~20–30× LLM-orchestration token tax and
> making the loop crash-safe (all inter-step state already lives in the repo).

INVEST — ✅ Independent (composes delivered T-072 driver + T-065/T-063 scripts; `run` untouched) · ✅ Negotiable (unsupported decision paths defer to T-090/T-091) · ✅ Valuable (order-of-magnitude token cut, measured by T-080) · ✅ Estimable · ✅ Small (one new module + additive CLI/bench wiring) · ✅ Testable (hermetic seam tests + bench scenario)

## Analysis Context

- **Domain.** The T-072 reference driver (`scripts/openup-agent.py` +
  `scripts/openup_agent/`) and the T-080 benchmark harness. The engine is a
  *conductor* over already-built scripts (`openup-board.py resolve`,
  `openup-session.py begin|end`, `openup-fence.py`, `check-docs.py`,
  `sync-status.py`) — it re-implements none of them.
- **Scope boundaries.** Only the **pick/resume** decision paths run end-to-end.
  `plan-iteration` (T-090) and `assess-iteration` / `milestone-review` (T-091)
  exit cleanly as "unsupported here". No procedure-pack prose changes (the
  ceremony/judgment split of the pack is T-091). The Claude Code harness path
  (`/openup-next` skill) is untouched. The `run` subcommand's behavior is
  byte-for-byte unchanged.
- **Definition of done.** On a bootstrapped fixture with one READY lane,
  `openup-agent.py cycle --dir <fixture>` claims the lane, executes its
  Operations boxes (script-steps with zero LLM calls; judgment-steps as fresh
  bounded `loop.run()` sub-runs), ticks boxes, runs gates, completes the lane
  deterministically, and prints the `/openup-next`-parity sentinel — all proven
  hermetically; a `cycle-quick-doc` bench scenario exists so the ≥5× token
  claim is measurable on a live model.

Non-blocking defaults chosen (exploration §7 open questions):

> **Assumption:** Step classification is **text-pattern + explicit marker
> override**: a box whose text contains `scripts/<name>.py` or starts with a
> `git `/`python3 ` command is executed as code; a `(judgment)` marker forces a
> sub-run, an `(auto)` marker forces exec. Everything else is a judgment
> sub-run. *(Vetoable at review.)*

> **Assumption:** The judgment sub-run instruction loads: the box text, the role
> hat, the change folder path (`plan.md` + `design.md` if present), and Ring-1
> *paths* (not bodies) — the documented briefing rule. Budget tuning is a
> benchmark follow-up, not this task. *(Vetoable at review.)*

> **Assumption:** The sub-run's step contract (system prompt) lives **in the
> engine** (`cycle.py` constant) via an additive `loop.run()` override — not as
> a new pack procedure — until T-091 moves ceremony authority pack-side.
> Keeps this lane off the pack/skills-mirror surface. *(Vetoable at review.)*

> **Assumption:** `openup-loop.sh` keeps pointing at the `next` procedure;
> `cycle` is invoked explicitly until T-091 reaches sentinel parity across all
> paths. *(Vetoable at review.)*

> **Assumption:** Judgment outputs are **files in the repo** (the measured 3/3
> pattern), never parsed prose. *(Vetoable at review.)*

> **Assumption:** `cycle` acquires the lane with an **in-place task branch**
> (`git checkout -b`) in `--dir`, not a worktree — the driver targets a
> dedicated project checkout (the bench fixture shape); worktree-per-lane stays
> the Claude Code harness default. *(Vetoable at review.)*

## Requirements

1. **Deterministic decision + acquire.** `openup-agent.py cycle --dir <project>`
   resolves the board decision and acquires the lane in code — `openup-board.py
   resolve` then `openup-session.py begin` — with **zero LLM calls** before the
   first judgment step.
   - **Given** a fixture project with one READY change-folder lane and a
     recording LLM seam **When** `cycle` runs **Then** the lane's lease exists
     (session begun) and the seam recorded no completion request during
     resolve/claim.

2. **Script-step dispatch.** An unchecked Operations box classified as a
   script-step (per the classification assumption) is executed as a subprocess
   under `--dir`, with no LLM call.
   - **Given** a claimed lane whose next box is `- [ ] Run python3
     scripts/sync-status.py` **When** the executor processes it **Then** the
     command runs as a subprocess (exit code captured) and the seam recorded no
     completion request for that step.

3. **Judgment-step dispatch (the sub-run contract).** A judgment box runs as a
   **fresh, bounded** `loop.run()` sub-run: new messages, small
   `--max-iterations` (default 10), instruction built from the box text + role
   hat + change-folder context per the briefing assumption.
   - **Given** a claimed lane whose next box is `- [ ] (developer) Append the
     line \`bench ok\` to docs/bench-scratch/note.md …` **When** the executor
     processes it **Then** exactly one sub-run starts with fresh messages, its
     instruction contains the box text and the `developer` hat, and its
     iteration cap is ≤ 10.

4. **Tick + gates per step, resumable on failure.** After a step succeeds the
   engine runs the deterministic gates (fence + check-docs, reusing the
   driver's `run_gates` semantics incl. inapplicable-skip), and **only then**
   ticks the box `- [ ]` → `- [x]` in `plan.md`. A gate failure exits with a
   typed non-zero code, the box left unticked.
   - **Given** a step whose gates pass **When** the engine advances **Then** the
     box reads `[x]` on disk before the next box is considered.
   - **Given** a step after which `check-docs.py` exits non-zero **When** the
     engine runs gates **Then** `cycle` exits with the documented gate-failure
     code, stderr carries the gate report, and the box still reads `[ ]`.

5. **Deterministic completion + sentinel parity.** When every box is ticked the
   engine completes the lane in code — plan `status:` → `done`, status-note
   shard for the lane, `sync-status.py`, archive the change folder, commit,
   `openup-session.py end` (release) — then prints `OPENUP-NEXT: ADVANCED —
   <task-id>` as the only stdout line and exits 0. (Track-aware: the sequence
   mirrors `/openup-complete-task`'s per-track ceremony — e.g. a `quick` lane
   skips the ceremony that track never required.)
   - **Given** a lane whose last box just ticked **When** completion runs
     **Then** the folder lives under `docs/changes/archive/`, the lease is
     released, the work is committed, and stdout's last line is `OPENUP-NEXT:
     ADVANCED — <task-id>` with exit 0.

6. **Crash-safe resume.** A killed cycle loses nothing: all inter-step state is
   the repo (boxes, state.json, lease), so re-running `cycle` resumes at the
   first unchecked box without redoing ticked steps.
   - **Given** a lane with its first box ticked and a live lease (a simulated
     kill) **When** `cycle` runs again **Then** resolve returns the resume path
     and execution starts at the second box (the seam shows no work for box 1).

7. **Unsupported paths degrade cleanly.** Decision paths beyond pick/resume are
   out of scope here and must not half-run.
   - **Given** a project whose board resolves `plan-iteration` (or
     `assess-iteration` / `milestone-review`) **When** `cycle` runs **Then** it
     exits with a distinct documented code, stderr names the unsupported path
     and the covering task (T-090/T-091), and no session was begun.
   - **Given** a project whose board resolves `noop` **When** `cycle` runs
     **Then** it prints `OPENUP-NEXT: DONE — <reason>` and exits 0 (parity with
     `/openup-next`).

8. **Benchmarkable + regression-free.** A `cycle-quick-doc` bench scenario
   drives `cycle` through the T-080 harness, and the existing `run` path is
   unchanged.
   - **Given** the bench harness, the `cycle-quick-doc` scenario, and a mock
     endpoint **When** one benchmark run executes **Then** `results.jsonl`
     records the run with outcome derived from `cycle`'s typed exit code and the
     deliverable check passes.
   - **Given** the pre-existing driver + bench test suites **When** they run
     unmodified (except additive cases) **Then** they pass — the `run`
     subcommand's behavior is unchanged.

9. **Shipped.** The new module is in `scripts/process-manifest.txt` so every
   install path ships it.
   - **Given** `install_process_clis` into a fresh temp dir **When** it runs
     **Then** `openup_agent/cycle.py` lands beside its package and `import
     openup_agent.cycle` succeeds.

## Behavior Delta

n/a — all Added (the `cycle` subcommand is new driver behavior; no Ring-1
product artifact describes existing behavior it modifies or removes; the `run`
subcommand and the `/openup-next` Claude Code path are explicitly unchanged).

**Added**
- `openup-agent.py cycle --dir <project>` — one deterministic delivery cycle
  (pick/resume), LLM only at judgment steps.
- Bench scenario `cycle-quick-doc` + harness support for driving `cycle`.

## Entities

- **cycle engine** (new) — `scripts/openup_agent/cycle.py`
- **CLI entry** (modified) — `scripts/openup-agent.py` (new `cycle` subparser)
- **agent loop** (modified, additive only) — `scripts/openup_agent/loop.py`
  (optional system-prompt/label override for step-scoped sub-runs; default path
  byte-unchanged)
- **bench harness** (modified) — `scripts/openup-agent-bench.py` (scenario can
  declare the `cycle` command)
- **bench scenario** (new) — `scripts/bench-scenarios/cycle-quick-doc/`
- **board / session / gates / views scripts** (read-only — composed via
  subprocess) — `scripts/openup-board.py`, `scripts/openup-session.py`,
  `scripts/openup-fence.py`, `scripts/check-docs.py`, `scripts/sync-status.py`
- **manifest** (modified) — `scripts/process-manifest.txt`

## Approach

Invert the driver's control for ceremony (exploration §3): a new `cycle.py`
state machine mirrors `/openup-next`'s contract — resolve → begin → per-box
executor → gates → completion — calling the *existing* scripts as subprocesses
(never reimplementing them) and dropping to the LLM only per judgment box, each
as an independent bounded `loop.run()` sub-run with a step-scoped instruction
(the shape that measured 3/3 clean at ~59k tokens). Progress state is the repo
itself (boxes, lease, state.json), so resume is free. `run` stays the
procedure-direct mode; `cycle` is additive and explicitly invoked.

## Structure

**Add:**
- `scripts/openup_agent/cycle.py`
- `scripts/bench-scenarios/cycle-quick-doc/` (scenario.json + overlay)
- `scripts/tests/test_openup_agent_cycle.py`

**Modify:**
- `scripts/openup-agent.py` — `cycle` subparser → `cycle.run_cycle()`
- `scripts/openup_agent/loop.py` — additive optional params for step-scoped
  sub-runs (system-prompt override); no default-path behavior change
- `scripts/openup-agent-bench.py` — scenario-declared command (`run` | `cycle`)
- `scripts/tests/test_openup_agent_bench.py` — cycle-scenario case
- `scripts/process-manifest.txt` — add `openup_agent/cycle.py`
- `docs-eng-process/reference-driver.md` — document `cycle`
- `docs-eng-process/script-cli-reference.md` — `cycle` signature + exit codes

**Do not touch:**
- `docs-eng-process/procedures/openup-next.md` (and all pack ceremony prose) —
  the ceremony/judgment split is T-091; touching it now creates drift mid-program
- `scripts/openup-board.py`, `scripts/openup-session.py`, `scripts/sync-status.py`,
  `scripts/openup-fence.py`, `scripts/check-docs.py` — the engine composes them;
  any gap found there is its own task
- `.claude-templates/skills/`, `.claude/skills/` — no skill changes; the Claude
  Code path is deliberately untouched
- `scripts/openup-loop.sh` — keeps driving the `next` procedure until T-091 parity

## Operations

- [x] Implement `cycle.py` decision + acquire wiring: `resolve` → typed
      dispatch (pick/resume proceed; noop → DONE sentinel; other paths → typed
      unsupported exit) → in-place branch + `openup-session.py begin`; hermetic
      tests for all five dispatch outcomes (Req 1, 7)
- [x] Implement the Operations-step executor: box parser + classifier
      (pattern + marker override), script-step subprocess exec, judgment-step
      bounded `loop.run()` sub-run with instruction builder (box + hat + change
      folder), gates-then-tick ordering with typed gate-failure exit; hermetic
      tests incl. resume-at-second-box (Req 2, 3, 4, 6)
- [x] Implement deterministic completion: status flip → status-note shard →
      `sync-status.py` → archive → commit → `session end` → `OPENUP-NEXT:
      ADVANCED` sentinel on stdout, exit 0; hermetic end-to-end fixture test
      (Req 5)
- [x] Wire the `cycle` subparser into `scripts/openup-agent.py`, add
      `openup_agent/cycle.py` to `scripts/process-manifest.txt`, and verify a
      fresh `install_process_clis` lands + imports it (Req 9)
- [x] Add `scripts/bench-scenarios/cycle-quick-doc/` and bench support for
      scenario-declared `cycle` command; hermetic mock-endpoint bench test
      records a scored run (Req 8)
- [x] (analyst) Document `cycle` in `reference-driver.md` +
      `script-cli-reference.md` (signature, exit codes, sub-run contract,
      loop.sh non-change)
- [ ] (tester) Run the full driver+bench suites plus `openup-spec-scenarios.py
      check`, `check-docs.py`, and `openup-fence.py check --base
      harness-optional`; record results + any deviations in
      `docs/changes/T-089/design.md`

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.)
- `docs-eng-process/model-tiers.md` — tier resolution stays in
  `openup_agent/tiers.py`; the engine never hardcodes a model
- `docs-eng-process/parallel-lanes.md` — lane surface / write-fence rules the
  completion step must respect

## Safeguards

- **`run` invariance.** The `run` subcommand and default `loop.run()` path are
  byte-for-byte behavior-unchanged — existing driver tests pass unmodified.
- **Compose, never reimplement.** The engine calls board/session/gates/views
  scripts as subprocesses; re-deriving any of their logic in `cycle.py` is a
  no-go zone (that duplication is the drift the program exists to kill).
- **Stdlib-only.** The driver stays dependency-free (T-072 invariant).
- **Reversibility.** `cycle` is additive and opt-in; backing out = not invoking
  it (no config, flag, or pack change to unwind).
- **Sub-run bound.** Judgment sub-runs default to ≤ 10 iterations — a runaway
  step must fail typed, not silently burn the budget the engine exists to save.
- **Token budget (lane).** Solo standard-track lane; checkpoint to `design.md`
  and hand off rather than exceeding one session's budget mid-executor.

## Success Measures

We expect **total tokens for one clean quick-doc delivery cycle on the same
local model** to drop by **≥5× vs the `next`-procedure baseline** (T-080
measured baseline: 1–2M tokens, 37–50 iterations) with **pass rate ≥
baseline's**, within **the owner's next live benchmark batch after merge**.
Instrumentation: `OPENUP_AGENT_USAGE_LOG` per-call usage records aggregated by
`openup-agent-bench.py` into `summary.json` (`cycle-quick-doc` vs `quick-doc`
batches). Read-back: recorded in `docs/changes/T-089/design.md` (and the
roadmap program block) when that batch runs — live runs are owner-side, this
sandbox cannot reach a local endpoint (T-080/T-086 precedent).

## Rollout

Not flagged — **n/a (reason):** internal developer tooling, not user-facing
product behavior; the new code path is reachable only via the new explicit
`cycle` subcommand, which *is* the toggle (nothing existing routes to it —
`openup-loop.sh` and the pack keep using `next` until T-091). Kill-switch =
stop invoking `cycle`; no in-flight data to consider beyond a resumable lane,
which `run`/manual completion can finish.

## Verification

- `python3 -m pytest scripts/tests/test_openup_agent_cycle.py
  scripts/tests/test_openup_agent.py scripts/tests/test_openup_agent_bench.py
  scripts/tests/test_openup_agent_tools.py` — all green
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-089/plan.md` — exit 0
- `python3 scripts/check-docs.py` — exit 0
- `python3 scripts/openup-fence.py check --base harness-optional` — exit 0
- Fresh-dir manifest install lands `openup_agent/cycle.py` (Req 9 scenario)
- Grade the final artifact against `.claude/rubrics/task-spec-rubric.md` —
  every criterion must be ✅ or have a clear gap call-out.

# Exploration: deterministic cycle engine — stop paying the LLM to orchestrate

**Started:** 2026-07-13
**Question:** Why does `next` depend so much on the LLM? The repo state (phases,
iterations, tasks, Operations boxes) plus the process map should be enough for a
**deterministic** flow that selects the next activity+role itself — and drops to
the LLM only to author artifacts — until the defined goal is reached. What has to
change in the reference driver (and possibly the procedure pack) to get there?
**Inputs:** T-080 benchmark data (`.openup/bench/`), the T-072 driver
(`scripts/openup_agent/`), the phase-aware program (T-075…T-079), the live
ShareShed run (owner, 2026-07-13).
**Follow-on to:** [2026-07-12-harness-agnostic-openup.md](2026-07-12-harness-agnostic-openup.md),
[2026-07-13-phase-aware-loop-redesign.md](2026-07-13-phase-aware-loop-redesign.md)

## 1. The problem, measured

The driver hands the **entire procedure text** to the model as its system prompt
and says "execute it." The model then does two jobs in one ever-growing
conversation:

1. **Orchestration** — interpret the ceremony prose, decide which script to call
   next, tick boxes, run session begin/end, sync views (~90% of turns).
2. **Judgment** — author the vision / spec / code (~10% of turns).

Job 1 is deterministic and *already implemented as scripts*; delegating it as
prose makes the model re-derive what code already knows, while the conversation
re-sends its whole history every turn. The T-080 benchmark quantifies the tax
(same model, `qwen/qwen3.6-35b-a3b`, same framework):

| | `--procedure next` (LLM orchestrates) | `--procedure openup-create-vision` (LLM only authors) |
|---|---|---|
| Iterations | 37–50 | ~8 |
| Tokens/run | 1–2M | ~59k |
| Outcome | inconsistent (1 pass / 5 tries at 50 iters) | **3/3 clean** |

**~20–30× token cost and unreliability, purely from LLM-interpreted ceremony.**
This also explains why small local models "can do the work but can't finish the
loop" (they deliver the artifact, then drown in ceremony).

## 2. What already exists (the engine's parts are all built)

Every deterministic step of a cycle is already a script — built across
T-017/T-063/T-065/T-075…T-079:

| Step | Existing code |
|---|---|
| "What next?" (resume/pick/assess/milestone/plan-iteration) | `openup-board.py resolve` — pure, derived from repo state |
| Phase / milestone criteria | `openup-lifecycle.py status` |
| Phase → activity → role → skill | `process-map.yaml` + `openup-process-map.py activities-for` |
| Iteration id, work-item ids | `mint-iteration-id`, `openup-claims.py reserve-id --prefix` |
| Cluster partitioning (parallel iterations) | `openup-board.py partition` (T-079) |
| Session lifecycle (claim+state+log) | `openup-session.py begin|end` |
| Gates | `openup-fence.py check`, `check-docs.py` |
| Views | `sync-status.py` |
| Progress state | Operations checkboxes in `plan.md` |
| Human pause | `openup-input.py` + suspend sentinel (T-074) |

What is **missing** is only the conductor: a deterministic state machine that
chains these in code and calls the LLM at genuine judgment points. Today the
conductor is `openup-next.md` prose, because the pack was designed for harness
LLMs (Claude Code) where the model *is* the harness. The reference driver
inherited that shape; it shouldn't have — **the driver is the harness, so the
driver should do the deterministic steps** (the framework's own rule).

## 3. Design: invert the control

New driver mode — `openup-agent.py cycle --dir <project>` (the `run` command
stays as-is for procedure-direct/authoring runs). One `cycle` invocation = one
delivery cycle, same contract and sentinels as `/openup-next`:

```
decision = board.resolve()                              # code
match decision.path:
  resume | pick:
      openup-session.py begin                           # code
      for each unchecked Operations box in plan.md:
          if step names a script → exec it              # code
          else → LLM sub-run: author THIS step          # judgment (fresh, small)
          tick the box                                  # code
          gates (fence + check-docs)                    # code
      completion: status flip, sync, archive, release   # code
  plan-iteration:
      phase (lifecycle), mint id, activities-for(phase) # code
      LLM: choose 1–5 objectives                        # judgment (one small call)
      partition into clusters (T-079)                   # code
      per lane: LLM authors its spec (create-task-spec) # judgment (small call each)
      roadmap rows + iteration-plan skeleton, commit    # code
  assess-iteration:
      done-ness of committed items                      # code
      LLM: grade the non-derivable criteria, demo notes # judgment
      feed-back rows, ## Assessment append              # code
  milestone-review:
      evidence prep + input-request pause               # code (zero LLM)
```

**The sub-run contract** (the key mechanism): each judgment point is an
independent, *bounded* `loop.run()` — a tiny step-scoped prompt + `--instruction`
carrying exactly the needed context (the box text, the role hat, the change
folder, Ring-1 refs) with fresh messages and a small `--max-iterations` (~10).
That is precisely the shape that scored 3/3 at ~59k tokens. Outputs are files in
the repo (the pattern that works), never parsed prose.

Properties this buys:

- **Token cost** collapses from one O(n²) conversation to Σ(small independent
  calls) — an order of magnitude, per the benchmark.
- **Reliability**: the model can no longer "forget the ceremony"; a weak model
  only has to author one step at a time.
- **Crash-safety / resumability for free**: all inter-step state is already in
  the repo (boxes, state.json, lease) — a killed cycle resumes at the next box.
- **Observability**: per-step usage/latency in the T-080 usage log.
- **Model tiering per step** becomes real: authoring steps → `MID`, grading →
  `MAIN`, mechanical fills → `SMALL` (today one model per whole procedure).
- **Human gates unchanged**: ask_user/input-request still suspend (exit 5).

## 4. What stays LLM (irreducible judgment)

Choosing objectives; authoring artifacts (vision, use cases, specs, code,
tests); grading non-derivable evaluation criteria; content of answers to human
questions. Everything else is dispatch — and dispatch is code.

## 5. Pushback / risks (challenge pass)

- **Prose–code drift.** The engine hard-codes the ceremony that `openup-next.md`
  describes → two sources of truth. *Mitigation:* the procedures slim toward
  judgment-prompt content (what "good" looks like per artifact), and the ceremony
  authority moves to the engine + scripts; the pack's ceremony sections become
  the human-readable description of what the engine does. Claude Code skills are
  unaffected (they keep orchestrating in-context — that harness's model is its
  engine; parity is at the artifact level, not the mechanism level).
- **Step classification.** "Does this Operations box need judgment or a script?"
  must be decidable. *Convention:* a box whose text names `scripts/…` or a bare
  git command is executed; everything else is a judgment sub-run. An optional
  per-box marker (e.g. `(auto)`) can force the choice. Open question §7.
- **Context starvation.** A too-small sub-run context may under-inform authoring.
  *Mitigation:* the instruction builder loads Ring 1 + the change folder (the
  documented briefing rule); measure with the benchmark, tune.
- **Scope creep.** This is the biggest driver change since T-072. *Mitigation:*
  three slices, each independently valuable (§6), each benchmarked before the
  next.

## 6. Proposed deliverables (ids reserved)

- **T-089 — cycle engine core: pick/resume path.** `openup-agent.py cycle`:
  resolve → session begin → Operations-step executor (script-vs-judgment
  dispatch, box ticking, gates) → deterministic completion. Bench scenario
  `cycle-quick-doc` proving ≥5× token reduction vs the `next` baseline on the
  same model. *(The heart; immediately useful alone.)*
- **T-090 — plan-iteration path.** Objectives sub-run + per-lane spec authoring
  sub-runs + deterministic lane/iteration-plan generation (reuses T-077/T-079
  machinery). Inception on a bootstrapped project (the ShareShed flow) runs
  end-to-end through `cycle`.
- **T-091 — assess + milestone paths, and the pack's ceremony/judgment split.**
  Assess-Results grading sub-run, milestone pause (code-only), DONE-sentinel
  parity with `/openup-next`; slim the affected procedures to judgment content
  with the engine as ceremony authority. Program acceptance runs here.

**Program acceptance (falsifiable):** on the same local model and scenario, a
`cycle`-driven delivery of the ShareShed Inception iteration completes with
**≥80% clean-pass rate and ≤1/10th the tokens** of the `next`-procedure baseline,
measured by the T-080 benchmark; all gates green; Claude Code path untouched.

## 7. Open questions (resolve at promote)

1. Step-classification convention: text-pattern only, or an explicit per-box
   marker in `## Operations`? (Leaning: pattern + optional marker override.)
2. How much Ring-1 context does each authoring sub-run load by default — and is
   that budget per-tier?
3. Does `openup-loop.sh` point at `cycle` by default once T-089 lands, or only
   behind a flag until T-091 parity?
4. Structured judgment outputs (objectives list): file-in-repo convention or a
   forced tool-call schema?

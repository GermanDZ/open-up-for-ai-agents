---
id: T-124
title: "Make the Inception use-case/architecture task-defs converge on the weak model (T-107 gate blocker)"
status: ready
priority: high
estimate: 1 session
plan: docs/roadmap.md
depends-on: []
blocks: [T-107]
last-synced: ""
touches:
  - scripts/openup_agent/plan_iteration.py
  - scripts/openup_agent/cycle.py
  - scripts/tests/test_openup_agent_plan_iteration.py
  - scripts/tests/test_openup_agent_cycle.py
  - docs-eng-process/reference-driver.md
---

# T-124 — Task-def convergence on the weak model

## Story

> **As** a maintainer running the Inception cycle on a weak local model (the
> T-107 promotion gate)
> **I want** every `execution: direct` authoring sub-run to converge — read its
> inputs once, write the one artifact, and stop
> **So that** the full Inception cycle finishes instead of a sub-run flailing in
> a re-read loop until it times out (the observed T-107-gate failure)

INVEST — ✅ Independent · ✅ Negotiable · ✅ Valuable · ✅ Estimable · ✅ Small · ✅ Testable

## Analysis Context

- **Domain.** Live-model diagnosis (2026-07-16, qwen3.6-27b via LM Studio) of the
  T-107 promotion-gate acceptance run
  (`.openup/bench/t107-smoke`, scenario `inception-taskdef`, `command: cycle`).
  The initiate-project task-defs — `develop-technical-vision` (4 turns) and
  `author-initial-roadmap` (3 turns) — **converge cleanly** (≤6 iters, the gate's
  target). But the cycle plans the **full** Inception (T-119 made every activity
  `execution: direct`), and the later sub-runs flail: `envision-the-architecture`
  runs 9 turns, and `identify-and-outline-requirements` (the use-case) **ran away
  to 28+ turns and hit the 40-min wall** without ever emitting its terminal
  sentinel.
- **Root cause — two compounding, both in the task-def/briefing layer.**
  1. **Inputs don't resolve to real context.** The use-case def declares
     `inputs: [Technical Specification]` (extracted verbatim from its KB source).
     The T-120 name→path map (`_input_path_map`, keyed by a def's `artifact` slug
     / output stem) has **no producer** for "Technical Specification", so it does
     not resolve → nothing is inlined → the model reads the generic KB slot doc,
     finds it useless, and **re-reads vision/brief/architecture 5× each** hunting
     for context (debug trace: iters 1–22 are read/glob loops). `Vision` and
     `Architecture Notebook` *do* resolve — which is why the vision/roadmap defs
     converge.
  2. **No convergence after the write.** `_task_system_prompt` says only "when
     the file is saved, emit `OPENUP-TASK: DONE` and stop." The weak model wrote a
     16 KB `UC-001.md` at iter 23 but then **re-read its own output 4× to verify**
     (iters 24–27) instead of emitting the sentinel, and timed out.
- **Scope boundaries.** Task-def input resolution + the direct-sub-run
  convergence contract only. No execution-seam change (the T-106 `run_task`
  mechanism is unchanged), no compiler/`task-library.yaml` edit (it is compiled
  from the KB — `build-task-library.py --check` must stay green), no `next`-loop
  work, no `main` merge. This **unblocks** but does not start T-107.
- **Definition of done.** On a live re-run of `inception-taskdef` (`command:
  cycle`), the `identify-and-outline-requirements` sub-run converges — reads its
  inputs, writes `UC-001.md` once, emits `OPENUP-TASK: DONE`, in ≤6 iterations,
  with no post-write re-read — and the full Inception cycle reaches a clean
  terminal state (no timeout). Hermetic tests lock the resolver + prompt.

## Requirements

1. **Non-resolving KB input display-names resolve to the real upstream
   artifacts.** A task-def whose declared `inputs` name a KB workproduct with no
   producer in the loaded library (e.g. "Technical Specification") still gets real
   project context inlined, via an alias to the artifacts that realize it in the
   driver's flow.
   - **Given** the loaded library and a def with `inputs: [Technical Specification]`
     **When** its instruction is rendered **Then** the "Provided inputs (already
     loaded …)" block includes the resolved **Vision** and **Architecture
     Notebook** content (not the display name alone), so the model needs no hunt.
   - **Given** a def whose inputs already resolve directly (e.g. `[Vision]`)
     **When** rendered **Then** behavior is unchanged (the alias only fires for
     names the direct map misses).
   - **Given** an alias target artifact that does not exist on disk yet **When**
     rendered **Then** it degrades cleanly (no phantom block, no crash).

2. **The direct-sub-run convergence contract stops the re-read loops.**
   `_task_system_prompt` instructs the model to write the one artifact with a
   single `write_file`, to **not** read it back to verify, to **not** re-read
   inputs already provided/read, and to emit `OPENUP-TASK: DONE` **immediately**
   after the write with no further tool calls.
   - **Given** the task system prompt **When** built **Then** it contains the
     single-write, no-verify-reread, no-input-reread, and emit-DONE-immediately
     clauses (asserted on the string).

3. **Live acceptance (falsifiable).** Re-running the `inception-taskdef` bench
   (`command: cycle`) on the configured weak model, the use-case sub-run converges
   (writes `UC-001.md`, emits `OPENUP-TASK: DONE`, ≤6 iterations, no post-write
   re-read) and the full Inception cycle reaches a clean terminal state within the
   run budget — vs the pre-fix 28+-turn timeout.
   - **Given** the fix **When** the bench smoke re-runs **Then** the use-case
     sub-run's iteration count drops from 28+ (timeout) to ≤6 and it emits its
     terminal sentinel.

## Behavior Delta

**Added** — `plan_iteration._INPUT_ALIASES` (KB display-name → real produced-artifact
keys) + alias resolution in `render_task_instruction`'s input-inlining loop.

**Modified** — `cycle._task_system_prompt`: the convergence contract (single
write, no verify-reread, no input re-read, emit DONE immediately). A note in
`reference-driver.md §task-def authoring` on both.

**Removed** — n/a.

## Entities

- **Input resolver** (modified) — `scripts/openup_agent/plan_iteration.py`:
  `_INPUT_ALIASES`, `render_task_instruction`.
- **Task-def shell** (modified) — `scripts/openup_agent/cycle.py`:
  `_task_system_prompt`.

## Approach

- **F1** `plan_iteration.py`: add `_INPUT_ALIASES = {"technicalspecification":
  ["vision", "architecturenotebook"]}` (normalized keys, matching `_norm`). In
  `render_task_instruction`'s resolution loop, when `pmap.get(_norm(name))` misses,
  look up the alias, resolve each aliased key through `pmap`, and inline the
  existing ones (same `inline_file` + de-dup path as T-120). Degrades to nothing
  when a target is absent.
- **F2** `cycle.py` `_task_system_prompt`: extend the shell — "Write the artifact
  with a SINGLE write_file call; the tool result confirms success, so do NOT read
  it back to check it. Do NOT re-read any input you were given or have already
  read. The moment the artifact is written, your next reply MUST be
  `OPENUP-TASK: DONE` with no tool calls." Keep the body-only / no-procedures
  framing.
- **Verify** by re-running `openup-agent-bench.py --scenario
  scripts/bench-scenarios/inception-taskdef --command cycle` on the live endpoint
  and reading the use-case sub-run's turn count + sentinel from the driver log.

## Structure

**Modify:**
- `scripts/openup_agent/plan_iteration.py` — `_INPUT_ALIASES` + alias resolution.
- `scripts/openup_agent/cycle.py` — `_task_system_prompt` convergence clauses.
- `scripts/tests/test_openup_agent_plan_iteration.py` — alias resolves+inlines;
  direct-resolve unchanged; absent target degrades.
- `scripts/tests/test_openup_agent_cycle.py` — prompt carries the convergence clauses.
- `docs-eng-process/reference-driver.md` — convergence-contract + input-alias note.

**Do not touch:** the T-106 execution seam (`run_task`), `build-task-library.py`
/ `task-library.yaml` (compiled — no hand edit), the gates, `main`.

## Operations

- [ ] F1 — `plan_iteration._INPUT_ALIASES` + alias resolution in `render_task_instruction` (non-resolving KB input names → real upstream artifacts, inlined; direct-resolve unchanged; absent-target degrades).
- [ ] F2 — `cycle._task_system_prompt` convergence contract: single write, no verify-reread, no input re-read, emit `OPENUP-TASK: DONE` immediately.
- [ ] (tester) Hermetic tests: alias resolves+inlines Vision+Architecture; direct-resolve path unchanged; absent alias target degrades; prompt carries the four convergence clauses.
- [ ] Docs: reference-driver note on the convergence contract + input aliasing.
- [ ] Live acceptance: re-run `inception-taskdef` (`command: cycle`) on the endpoint; use-case sub-run converges (≤6 iters, `OPENUP-TASK: DONE`, no post-write re-read, no timeout). Record the before/after in `design.md`.
- [ ] Full suite green; fence `--base harness-optional` + check-docs clean.

## Norms

Inherits from:
- `docs-eng-process/conventions.md`
- T-106 task-def consumption + T-118/T-120 input inlining (the mechanism this extends)
- T-119 direct-execution Inception defs (the defs this makes converge)

## Safeguards

- **No compiler/library edit.** `task-library.yaml` stays compiler-generated; the
  fix is render-time (alias) + prompt — `build-task-library.py --check` stays green.
- **Additive resolution.** The alias only fires when the direct name→path map
  misses; defs whose inputs already resolve are byte-unchanged.
- **No execution-seam change.** `run_task` and the sub-run mechanism are untouched;
  only the instruction/system-prompt content changes.
- **Convergence contract is model-agnostic.** The single-write / emit-DONE clauses
  are correct behavior for any model; they only *bind* the weak one that would
  otherwise loop.

## Verification

- `python3 -m pytest scripts/tests/test_openup_agent_plan_iteration.py scripts/tests/test_openup_agent_cycle.py -q` passes.
- Live: `inception-taskdef` cycle re-run — use-case sub-run ≤6 iters + `OPENUP-TASK: DONE`, no timeout (recorded in `design.md`).
- Full suite green; fence `--base harness-optional` + `build-task-library.py --check` + check-docs clean.

## Success Measures

Falsifiable, read from the live bench driver log / `OPENUP_AGENT_DEBUG_LOG`: the
`identify-and-outline-requirements` sub-run's iteration count drops from **28+
(timeout)** to **≤6**, it emits `OPENUP-TASK: DONE`, and it makes **no** read_file
call against its own `output_path` after the write. Before = `.openup/bench/t107-smoke`;
after = the post-fix re-run recorded in `design.md`.

## Rollout

n/a — internal driver briefing/prompt fix on harness-optional; no flag, no
user-facing runtime surface.

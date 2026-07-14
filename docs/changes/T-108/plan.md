---
id: T-108
title: Engine commits every artifact it produces — direct artifacts + per-cycle run-log sweep
status: ready
priority: high   # critical | high | medium | low
estimate: 1 session
plan: docs/roadmap.md#planned-driver-delivery-trail--console-narration-t-108-t-109
depends-on: []
blocks: []
touches:
  - scripts/openup_agent/plan_iteration.py
  - scripts/openup_agent/cycle.py
  - scripts/tests/test_openup_agent_plan_iteration.py
  - scripts/tests/test_openup_agent_cycle.py
  - docs-eng-process/reference-driver.md
last-synced: ""
---

# T-108 — Engine commits every artifact it produces

## Story

> **As** a practitioner running `./scripts/next-cycle` on a real project,
> **I want** every artifact the engine produces to land in a git commit — the
>   `execution: direct` outputs (vision, roadmap) and each cycle's run-log
>   trail —
> **So that** a crash or abandoned session never loses authored work, the board
>   and other machines can see it, and every cycle is durably registered
>   (observed live on my-product, 2026-07-14: `docs/vision.md`,
>   `docs/roadmap.md`, and `docs/agent-logs/` all left untracked).

INVEST — ✅ Independent (engine-side only) · ✅ Negotiable (commit granularity) ·
✅ Valuable (live data-loss gap) · ✅ Estimable · ✅ Small · ✅ Testable
(hermetic: tree clean after each path)

## Analysis Context

- **Domain.** The driver's commit discipline. Today `run_plan_iteration`'s
  `execution: direct` branch runs the procedure (T-101), the engine stamps the
  artifact (T-104), then `continue`s — **no gate, no commit** — while the
  spec-then-execute lanes and the iteration-plan instance are gated + committed.
  Separately, `run_cycle` writes `docs/agent-logs/` shards (session begin/end,
  auto-log) that only the lane-completion ceremony commits — a cycle that fails
  or suspends strands them untracked.
- **Scope boundaries.** No change to the lane executor's own completion
  ceremony; no change to what the model is asked to do; console output is
  T-109. The framework repo's on-stop sweep hook is untouched (this is the
  driver-side equivalent).
- **Definition of done.** After any cycle exit (ADVANCED, DONE, SUSPEND, typed
  failure), `git status` in the project shows no untracked/modified files under
  `docs/` produced by the engine: direct artifacts are gated + committed at the
  point they are produced; run-log shards are swept into a log-only commit at
  cycle end.

> **Assumption:** the direct-path commit stages `docs/` (the sub-run's
> whole docs delta: the stamped artifact + companion outputs like the initial
> roadmap), not just the `PROCEDURE_ARTIFACTS` path — the activity may
> legitimately produce more than one file. *(Vetoable at review.)*

> **Assumption:** the cycle-end sweep commits with the `[openup-skip]` marker
> (mirroring the framework's own run-log sweeps) so intake hooks ignore it.
> *(Vetoable at review.)*

## Requirements

1. **A successful direct activity is gated and committed.**
   - **Given** a fresh-Inception `plan-iteration` whose `initiate-project`
     direct run succeeds and is stamped **When** the branch continues **Then**
     the engine runs the gates and commits the produced `docs/` changes
     (message naming the iteration + activity + skill), and `git status` shows
     neither `docs/vision.md` nor `docs/roadmap.md` as untracked.

2. **Gate failure after a direct run aborts with nothing committed.**
   - **Given** the gates fail after a direct run **When** the branch evaluates
     the result **Then** it aborts with the typed step exit and no commit is
     made (consistent with the lane-spec flow).

3. **Every cycle exit sweeps run-log shards.**
   - **Given** a cycle that wrote `docs/agent-logs/` files and exits on ANY
     path (advanced, done, suspend, typed failure) **When** `run_cycle`
     returns **Then** the untracked/modified `docs/agent-logs/` files are
     committed as a log-only `[openup-skip]` commit on the current branch.

4. **The sweep is a no-op when clean.**
   - **Given** a cycle that produced no new log shards **When** it exits
     **Then** no empty commit is created.

5. **Commit failures never mask the cycle's own exit code.**
   - **Given** the sweep's `git commit` fails (e.g. no git identity) **When**
     the cycle exits **Then** the failure is logged and the cycle's original
     exit code is preserved.

## Behavior Delta

Ring-1 truth for the driver lives in `docs-eng-process/`.

**Added:**
- Direct-path gate + commit; per-cycle run-log sweep —
  `docs-eng-process/reference-driver.md` §direct execution / §cycle engine.

**Modified:**
- The `execution: direct` flow: produce → stamp (T-104) → **gate → commit** —
  `docs-eng-process/reference-driver.md` §engine-owned authoring ceremony.

**Removed:** none.

## Entities

- **plan_iteration** (modified) — direct branch gains gate + `git_commit` after
  `run_procedure` success (both callables already injected).
- **cycle** (modified) — `run_cycle` exit paths sweep `docs/agent-logs/`.
- **git_commit / run_gates** (read-only) — existing injected seams; no new
  driver coupling.

## Approach

Reuse the injected seams — no new git plumbing. In `run_plan_iteration`'s
direct branch, after `run_procedure` returns 0: `run_gates()` → on failure the
typed abort used by the lane flow; on success `git_commit(["docs/"], ...)` with
an iteration-tagged message. In `cycle.py`, wrap the cycle's exit in a sweep
helper (`_sweep_run_logs(root)`) that stages `docs/agent-logs/` when dirty and
commits `[openup-skip]`, swallowing (but logging) git errors so the cycle's
exit code always wins. Applied on every return path via a single wrapper point.

## Structure

**Add:** (none — two existing modules)

**Modify:**
- `scripts/openup_agent/plan_iteration.py` — direct branch: gates + commit.
- `scripts/openup_agent/cycle.py` — `_sweep_run_logs` + exit-path wiring.
- `scripts/tests/test_openup_agent_plan_iteration.py` — commit/gate-abort cases.
- `scripts/tests/test_openup_agent_cycle.py` — sweep cases (dirty, clean, failure).
- `docs-eng-process/reference-driver.md` — document both behaviors.

**Do not touch:**
- The lane executor's completion ceremony (already commits its lane work).
- `.claude/scripts/hooks/on-stop.py` — the framework-repo sweep; different tier.
- `stamping.py` — T-104 behavior unchanged (stamp still precedes gate+commit).

## Operations

- [x] `plan_iteration.py`: after a successful direct run, run gates (typed
  abort on failure, nothing committed) and `git_commit(["docs/"], ...)` with an
  iteration-tagged message.
- [x] (tester) Plan-iteration tests: direct success → commit recorded with
  `docs/` staged; gate failure → typed abort, zero commits.
- [x] `cycle.py`: add `_sweep_run_logs(root)` and invoke it on every
  `run_cycle` exit path; log-only `[openup-skip]` message; git errors logged,
  exit code preserved.
- [x] (tester) Cycle tests: dirty agent-logs → swept on advanced AND on a
  failing exit; clean tree → no commit; commit error → original exit code.
- [x] Update `reference-driver.md` (direct commit + sweep).
- [ ] (tester) Full driver suite green; spec-scenarios, check-docs, fence
  (`--base harness-optional`) green.

## Norms

Inherits from:
- `docs-eng-process/conventions.md`
- `docs-eng-process/reference-driver.md` — the driver contract

## Safeguards

- **Stdlib-only; injected seams only** — no new subprocess git calls in
  `plan_iteration.py` (use the `git_commit`/`run_gates` callables).
- **No behavior change for the model** — instructions untouched (T-104's
  contract is stable).
- **The sweep never raises** — a failed log commit must not convert a
  successful cycle into a failure.
- **Reversibility.** Additive engine behavior; git-revertible.

## Success Measures

We expect **zero engine-produced untracked files** after any cycle exit on a
fresh-project run — verified by the T-106 behavioral-acceptance batch on the
qwen fixture (`git status --porcelain` empty of `docs/` entries after each
`next-cycle` invocation). Instrumentation: the acceptance run script + git.
Read-back: at the T-106 gate.

## Rollout

`n/a — not user-facing`: reference-driver internals, no flag; backout is a
version pin.

## Verification

- Hermetic: direct-path test asserts a commit with `docs/` staged and the
  iteration-tagged message; gate-failure test asserts zero commits.
- Hermetic: cycle test asserts the sweep commit exists after both a successful
  and a failing cycle, absent on a clean tree, and that a sweep error preserves
  the exit code.
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-108/plan.md` → 0;
  `check-docs.py` → 0; fence `--base harness-optional` → clean.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

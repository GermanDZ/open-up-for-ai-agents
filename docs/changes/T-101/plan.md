---
id: T-101
title: Fresh-project deterministic navigation — resolve trigger + map-driven inputs + execution direct (delivers T-101 + T-102)
status: ready   # proposed → ready → in-progress → done → verified
priority: high   # critical | high | medium | low
estimate: 1–2 sessions
plan: docs/iteration-plans/2026-07-14-deterministic-process-map-navigation.md
depends-on: [T-100]
blocks: [T-103]
touches:
  - scripts/openup-board.py
  - scripts/openup_agent/plan_iteration.py
  - scripts/openup_agent/cycle.py
  - scripts/tests/test_openup_board_resolve.py
  - scripts/tests/test_openup_agent_plan_iteration.py
  - docs-eng-process/reference-driver.md
last-synced: ""
---

# T-101 — Fresh-project deterministic navigation (delivers T-101 + T-102)

## Story

> **As** the deterministic navigation layer (P1),
> **I want** a fresh authoring-phase project to reach its work products by walking
>   the **process map** — `resolve` fires `plan-iteration` with no roadmap, each
>   activity's declared `requires_input` is scaffolded + gated deterministically,
>   and an `execution: direct` authoring activity runs its procedure directly,
> **So that** Inception converges **without the per-cycle LLM navigator or the
>   hardcoded bootstrap** — the coherent replacement T-103 then lets us delete.

*(Folds the plan's T-101 + T-102 into one lane — they are coupled: firing
`plan-iteration` on a fresh project bypasses the navigator's brief-scaffold, so
the map-driven scaffold must land together to avoid a regression window. T-102's
roadmap row is delivered here.)*

INVEST — ✅ Independent (consumes T-100 data; navigator untouched until T-103) · ✅ Negotiable (input-gate placement) · ✅ Valuable (deterministic fresh flow) · ✅ Estimable · ✅ Small-ish (resolve branch + plan_iteration input/exec handling) · ✅ Testable (resolve + plan_iteration seams)

## Analysis Context

- **Domain.** `openup-board.py resolve_decision` (§1c/§1d/noop) + the T-090 Plan
  Iteration (`plan_iteration.py`), consuming the T-100 schema
  (`requires_input`, `execution`).
- **Resolve today.** `plan-iteration` fires only when `_promote_next` returns a
  roadmap `entry` (§1d); a fresh project → `noop` → the navigator/bootstrap. A
  fresh **inception** has unmet **machine** criteria (`vision_defined`,
  `requirements_outlined`, `risk_list_present` — all `unmet`), so
  `_phase_exit_ready` is False and §1c-milestone does **not** fire — the exact
  signal for "this authoring phase has undone work."
- **Plan Iteration today (T-090).** Mints an iteration, one objectives sub-run,
  one lane per skilled activity, a spec-authoring sub-run per lane, an
  iteration-plan instance. Every activity is spec-then-execute; no input gating.
- **The coupling.** The instant `resolve` returns `plan-iteration` on a fresh
  project, the navigator (noop-only) is bypassed — but the brief scaffold that
  made the fresh flow converge lives in the navigator until T-103. So the
  map-driven scaffold (T-102) must land **with** the resolve trigger (T-101).
- **Definition of done.** A fresh authoring-phase project resolves to
  `plan-iteration`; Plan Iteration scaffolds the first missing declared
  `requires_input` (marker-guarded) and suspends; once provided, an
  `execution: direct` authoring activity runs its procedure directly (no
  spec-authoring sub-run, no redundant lane); spec-then-execute activities keep
  the T-090 lane flow. The navigator/bootstrap are untouched (deleted in T-103).

> **Assumption:** the fresh-phase trigger is gated to **authoring phases**
> (inception/elaboration) — the same `AUTHORING_PHASES` T-090 uses; construction/
> transition's drained-roadmap case stays `noop`→T-094. *(Vetoable.)*
> **Assumption:** `requires_input` is gated **before** minting — the first missing
> input scaffolds + suspends, so no half-planned iteration exists without its
> inputs. *(Vetoable.)*
> **Assumption:** a `direct` activity produces a **Ring-1 artifact** (vision,
> architecture) directly and is recorded in the iteration-plan instance body, not
> as a change-folder lane; spec-then-execute lanes remain the `traces-from`
> committed work items for assess (T-091). *(Vetoable — open question 2.)*

## Requirements

1. **`resolve` fires `plan-iteration` on a fresh authoring phase (no roadmap).**
   - **Given** an authoring phase (inception) with unmet machine criteria, no
     active iteration, no promotable roadmap entry, and non-empty
     `activities-for(phase)`, **When** `resolve` runs, **Then** it returns
     `plan-iteration` carrying the phase (no roadmap `lane.task` required), not
     `noop`.
   - **Given** `construction` with a drained roadmap (nothing promotable) and
     unmet criteria, **When** `resolve` runs, **Then** it does **not** fire the
     fresh trigger (stays `noop` → T-094), preserving today's behavior.

2. **Plan Iteration scaffolds the first missing declared input and suspends.**
   - **Given** the phase's first activity declares `requires_input` whose file is
     absent (or still a template marker), **When** Plan Iteration runs, **Then**
     it scaffolds a marker-guarded template at that path, suspends (exit 5) with
     guidance, mints **no** iteration, and authors nothing.
   - **Given** the declared input file exists (no marker), **When** Plan Iteration
     runs, **Then** it proceeds (no scaffold, no suspend).

3. **An `execution: direct` activity runs its procedure directly.**
   - **Given** `initiate-project` (`execution: direct`, skill `openup-create-vision`)
     with its brief present, **When** Plan Iteration reaches it, **Then** it runs
     `openup-create-vision` via the procedure runner (no spec-authoring sub-run,
     no `docs/changes/<lane>/` for it), and its `ADVANCED` outcome is reported.

4. **`spec-then-execute` activities keep the T-090 lane flow.**
   - **Given** an activity with default `execution`, **When** Plan Iteration
     reaches it, **Then** it reserves an iteration-prefixed lane, authors its spec
     via the sub-run, gates + commits it, and it is `traces-from` the iteration-
     plan instance (byte-equivalent to T-090 for that activity).

5. **The navigator/bootstrap are untouched (deleted in T-103).**
   - **Given** this lane, **When** the diff is read, **Then** `navigator.py`'s
     `_bootstrap_step`/decision path are unchanged; the fresh-project path now
     reaches Plan Iteration via `resolve`, and the navigator is dead code on that
     path (removed in T-103), not modified here.

## Behavior Delta

Ring-1 truth for the driver/process lives in `docs-eng-process/`.

**Added:**
- `resolve` fresh-authoring-phase `plan-iteration` trigger (no roadmap needed).
- Map-driven `requires_input` scaffold + suspend, and `execution: direct` procedure
  run, in Plan Iteration.

**Modified:**
- Fresh-project navigation — `docs-eng-process/reference-driver.md`: a fresh
  authoring phase is planned deterministically from the map; declared inputs are
  scaffolded; direct activities run their procedure directly.

**Removed:** nothing here (the navigator/bootstrap removal is T-103).

## Entities

- **resolve** (modified) — `scripts/openup-board.py` (`resolve_decision`)
- **Plan Iteration** (modified) — `scripts/openup_agent/plan_iteration.py`
  (`run_plan_iteration`: input gate + per-activity execution mode; a marker-guarded
  scaffold helper), `cycle.py` (`_run_plan_iteration` passes the procedure runner)
- **process map** (read-only consumer) — T-100 `requires_input`/`execution`
- **tests** — `test_openup_board_resolve.py`, `test_openup_agent_plan_iteration.py`

## Approach

`resolve_decision`: add a branch (after §1c-milestone, before §1d) — for an
authoring phase with unmet machine criteria, no active iteration, nothing
promotable, and non-empty activities — return `plan-iteration` (phase-driven,
`lane=None`). `run_plan_iteration`: (1) before minting, walk `activities_for(phase)`
and scaffold+suspend the first activity whose declared `requires_input.path` is
missing/templated (a marker-guarded generic template, generalizing T-097); (2) per
activity, branch on `execution`: `direct` → `run_procedure(skill, instruction)`
(no spec sub-run, no lane); else → the existing reserve-id + spec sub-run + gate +
commit + trace. `cycle._run_plan_iteration` already has a procedure runner
(`run_procedure` from `_run_navigator`); thread one into the plan-iteration wiring.

## Structure

**Modify:**
- `scripts/openup-board.py` — `resolve_decision` fresh-authoring-phase branch
  (reads `activities_for` via the process-map sibling; `AUTHORING_PHASES` set).
- `scripts/openup_agent/plan_iteration.py` — input gate + scaffold helper +
  per-activity execution branch; `run_plan_iteration` gains a `run_procedure`
  injected callable.
- `scripts/openup_agent/cycle.py` — `_run_plan_iteration` provides `run_procedure`
  (mirrors the navigator wiring).
- `scripts/tests/test_openup_board_resolve.py` — fresh-inception → plan-iteration;
  construction drained → noop.
- `scripts/tests/test_openup_agent_plan_iteration.py` — input scaffold+suspend;
  direct runs procedure (no lane); spec-then-execute unchanged.
- `docs-eng-process/reference-driver.md` — the deterministic fresh-project path.

**Do not touch:**
- `navigator.py` — untouched here; the navigator/bootstrap are deleted in T-103.
- `openup-process-map.py` — T-100 already exposes the fields; read-only here.
- assess/milestone paths (T-091).

## Operations

- [ ] `resolve_decision`: add the fresh-authoring-phase `plan-iteration` branch
  (unmet machine criteria + nothing promotable + activities present; authoring
  phases only), returning a phase-driven decision.
- [ ] `plan_iteration.run_plan_iteration`: add the pre-mint `requires_input` gate
  (scaffold marker-guarded template + suspend on the first missing input) using a
  new scaffold helper.
- [ ] `plan_iteration.run_plan_iteration`: per-activity `execution` branch —
  `direct` runs the procedure via an injected `run_procedure` (no spec sub-run, no
  lane); `spec-then-execute` keeps the T-090 flow; wire `run_procedure` from
  `cycle._run_plan_iteration`.
- [ ] (tester) resolve tests (fresh-inception→plan-iteration; construction→noop)
  + plan_iteration tests (input scaffold+suspend; direct-runs-procedure;
  spec-then-execute unchanged; a fresh e2e reaching create-vision).
- [ ] Update `docs-eng-process/reference-driver.md` (deterministic fresh path).
- [ ] (tester) Full driver+board suite green; `check-docs`, `spec-scenarios`,
  `process-map validate`, fence (`--base harness-optional`) green.

## Norms

Inherits from:
- `docs-eng-process/conventions.md`
- `docs-eng-process/reference-driver.md` — driver/decision contract
- `docs/iteration-plans/2026-07-14-deterministic-process-map-navigation.md`
- `docs/changes/archive/T-090/plan.md` (Plan Iteration), `T-097` (scaffold)

## Safeguards

- **No regression window.** The map-driven scaffold lands **with** the resolve
  trigger, so the fresh flow converges throughout; the navigator stays as
  now-unused code until T-103.
- **Authoring-phase gate.** The fresh trigger fires only for inception/elaboration;
  construction/transition are unchanged (Req 1).
- **Input gate before minting.** No half-planned iteration without its inputs.
- **Stdlib-only.**

## Success Measures

n/a — internal navigation. Falsifiable acceptance = the resolve + plan_iteration
tests (Req 1–5), incl. a scripted fresh-inception run that scaffolds the brief,
suspends, then (brief present) runs create-vision directly — **no navigator LLM
call**. The program measure (zero per-cycle navigator calls + navigator deleted)
is read back at T-103.

## Rollout

`n/a — not user-facing`: reference-driver navigation; no flag. Backout is a
version pin.

## Verification

- `python3 -m pytest scripts/tests/test_openup_board_resolve.py
  scripts/tests/test_openup_agent_plan_iteration.py -q` — green.
- Scripted fresh inception: no brief → scaffold + exit 5; brief present →
  `create-vision` runs directly (no `docs/changes/` lane for it); construction
  drained → noop.
- `openup-spec-scenarios.py check docs/changes/T-101/plan.md` → 0; `check-docs.py`
  → 0; `openup-process-map.py validate` → 0; `openup-fence.py check
  --base harness-optional` → clean.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

---
id: T-090
title: Cycle engine — plan-iteration path (phase-appropriate Plan Iteration)
status: done
priority: high   # critical | high | medium | low
estimate: 1–2 sessions
plan: docs/explorations/2026-07-13-deterministic-cycle-engine.md
depends-on: [T-089]
blocks: [T-091]
touches:
  - scripts/openup_agent/plan_iteration.py
  - scripts/openup_agent/cycle.py
  - scripts/check-docs.py
  - scripts/process-manifest.txt
  - scripts/tests/test_openup_agent_plan_iteration.py
  - scripts/tests/test_openup_agent_cycle.py
  - scripts/tests/test_check_docs.py
  - docs-eng-process/reference-driver.md
  - docs-eng-process/script-cli-reference.md
last-synced: ""
---

# T-090 — Cycle engine: the plan-iteration path

## Story

> **As an** operator driving OpenUP with the reference-driver `cycle` engine,
> **I want** `cycle` to **plan a phase-appropriate iteration** deterministically —
>   mint the iteration, pick objectives, generate the phase's work-item lanes,
>   author each spec, and write the iteration-plan instance — with the LLM used
>   only for the two genuine judgment points,
> **So that** a fresh project's Inception (the ShareShed flow) runs end-to-end
>   through `cycle` at a fraction of the tokens, and a real named iteration with
>   evaluation criteria exists for the assess/milestone paths (T-091) to read.

INVEST — ✅ Independent (composes existing scripts; single-row promote untouched) · ✅ Negotiable (lane-generation source, phase gating) · ✅ Valuable (unblocks Inception-through-cycle + T-091) · ✅ Estimable · ✅ Small-ish (one handler module + wiring; reuses mint/reserve/partition/dispatch) · ✅ Testable (hermetic scripted-LLM sub-runs, the T-089 `_subrun`/`_completion` seams)

## Analysis Context

- **Domain.** The `cycle` engine (`scripts/openup_agent/cycle.py`, T-089). Its
  `resolve` → `plan-iteration` decision (`openup-board.py` §1d) currently reaches
  the engine only through **recovery** (T-092 `recover_missing_spec`): it authors
  the **single** named roadmap entry's spec and picks it. That is the *degenerate,
  single-work-item* case the board comment already calls out. What's missing is
  the genuine **Plan Iteration** (KB §3, start-iteration §0b): committing a *set*
  of phase-appropriate work items to a **named iteration** with an iteration-plan
  instance — the structure T-091's `assess-iteration` (`_active_iteration_plan`)
  and `milestone-review` paths depend on existing.
- **Design (owner decision 2026-07-13): §0b-faithful.** The iteration's lanes are
  generated from **`activities-for(phase)`** (the process map), not from feature
  roadmap rows — for Inception that is `initiate-project`→vision,
  `identify-refine-requirements`→use-cases, `agree-technical-approach`→
  architecture, etc. Lanes carry **iteration-prefixed ids** (`I1-001`, `C1-001`)
  so `_active_iteration_plan` (which matches `^[A-Z]\d+-\d+$`) recognizes the
  iteration. This mirrors `/openup-start-iteration` §0b exactly, in code.
- **Scope boundaries.** (1) The Plan Iteration fires for **authoring phases**
  (`inception`, `elaboration`) — the phases whose `activities-for` compose
  `create-*` work-product authoring. For `construction`/`transition`,
  plan-iteration keeps the **existing single-row promote** (`recover_missing_spec`)
  untouched, so feature-by-feature delivery is unaffected. (2) The engine plans +
  starts the **first lane**; remaining lanes are READY change folders the board
  picks next (cross-cluster parallelism stays opt-in-by-structure, T-079). (3)
  Only two LLM sub-runs: **choose objectives** (once) and **author each lane's
  spec** (once per lane). Everything else — mint, reserve, activities, partition,
  the iteration-plan instance — is code. (4) Does **not** implement
  `assess-iteration`/`milestone-review` (T-091); does **not** change
  `openup-board.py` resolve logic.
- **Definition of done.** On a `plan-iteration` decision in an authoring phase
  with no active iteration, `cycle` mints an iteration, runs one objectives
  sub-run, generates + partitions lanes from `activities-for`, authors each lane's
  spec (gated + committed), writes an iteration-plan instance (`traces-from` the
  lane ids + evaluation criteria) under `docs/phases/<phase>/`, commits, and
  re-resolves so the first lane executes. A scripted (hermetic) Inception plan
  produces ≥2 iteration-prefixed lanes + a recognizable iteration-plan instance.

> **Assumption:** the Plan Iteration is **phase-gated to `inception`/`elaboration`**;
> `construction`/`transition` plan-iteration decisions keep the T-092 single-row
> promote. *(Vetoable at review — the alternative is a per-activity heuristic.)*
> **Assumption:** the objectives sub-run and each spec sub-run write their output
> as **files in the repo** (objectives → `.openup/iteration-objectives.json`; specs
> → `docs/changes/<lane>/plan.md`), the T-072 pattern, read back deterministically.
> *(Vetoable at review.)*
> **Assumption:** one lane per phase activity (bounded by the objectives count,
> 1–5); the objectives sub-run may narrow which activities are in scope. A single
> resulting lane is the degenerate case (≡ today's promote). *(Vetoable.)*

## Requirements

1. **`cycle` handles `plan-iteration` in an authoring phase by planning a named
   iteration** — no longer exit 7 / single-row-only.
   - **Given** a bootstrapped Inception project (vision + roadmap present, no
     active iteration) whose `resolve` returns `plan-iteration` with `phase:
     inception`, **When** `cycle` runs (recover on), **Then** it mints an
     iteration id via `openup-process-map.py mint-iteration-id inception` and does
     not return `EXIT_UNSUPPORTED`.

2. **Objectives are chosen by exactly one bounded LLM sub-run**, its result read
   from a file.
   - **Given** the Plan Iteration is running, **When** the objectives step
     dispatches, **Then** exactly one sub-run is invoked (authoring tier, default
     cap) and the engine reads 1–5 objectives from
     `.openup/iteration-objectives.json`; a malformed/absent result fails the
     cycle typed (nothing committed).

3. **Lanes are generated deterministically from `activities-for(phase)`** with
   iteration-prefixed ids and partitioned via T-079 — zero LLM.
   - **Given** `activities-for(inception)` lists `initiate-project`,
     `identify-refine-requirements`, … , **When** lanes are generated, **Then**
     each in-scope activity yields one lane with a reserved id under the
     iteration prefix (`openup-claims.py reserve-id --prefix "I1-"`), the
     activity's `role` recorded as the lane hat and its `skills[0]` as the
     authoring skill, and `openup-board.py partition` groups them into clusters.

4. **Each lane's spec is authored by one bounded sub-run and gated** before the
   iteration is recorded.
   - **Given** a generated lane `I1-002` for activity `identify-refine-requirements`,
     **When** its spec sub-run runs, **Then** `docs/changes/I1-002/plan.md` is
     written with valid instance frontmatter + `## Operations`, passes
     `check-docs.py`, and is committed; a lane whose spec fails the gate aborts
     the Plan Iteration with a typed exit and no half-planned iteration is left
     picked.

5. **An iteration-plan instance is written deterministically** so
   `_active_iteration_plan` recognizes the iteration and it passes `check-docs`.
   - **Given** lanes `I1-001…I1-00n` authored, **When** the iteration is recorded,
     **Then** `docs/phases/inception/iteration-<iter>-plan.md` exists with
     `type: iteration-plan`, `traces-from` listing every iteration-prefixed lane
     id, an evaluation-criteria section, and no `## Assessment` yet — and
     `openup-board.py resolve` then returns `resume`/`pick` for the first lane
     (not `plan-iteration`).
   - **Given** the iteration-plan instance `traces-from` its change-folder lane
     ids (whose `plan.md` is a task-spec, not a typed instance), **When**
     `check-docs.py` runs, **Then** those refs resolve (change folders are
     registered as implicit `work-item`s) and there is no `dangling-ref` failure.

6. **The construction/transition single-row promote is unchanged.**
   - **Given** a `plan-iteration` decision with `phase: construction` naming a
     feature roadmap entry, **When** `cycle` runs, **Then** it takes the existing
     `recover_missing_spec` single-row path (no iteration minted, no
     `activities-for` lanes) — byte-equivalent to T-092 behavior.

7. **A hermetic end-to-end Inception plan works through the seams.**
   - **Given** the scripted `_subrun`/objectives seam, **When** an Inception
     `cycle` plans, **Then** the test observes ≥2 iteration-prefixed lanes, a
     recognizable iteration-plan instance, and a re-resolve that no longer says
     `plan-iteration` — with the objectives + per-lane specs the only sub-runs.

## Behavior Delta

Ring-1 truth for the driver lives in `docs-eng-process/`.

**Added:**
- A `cycle` plan-iteration handler that mints a named phase iteration, chooses
  objectives (1 sub-run), generates + partitions `activities-for` lanes, authors
  each spec (1 sub-run/lane), and writes the iteration-plan instance.

**Modified:**
- The `cycle` engine's `plan-iteration` handling —
  `docs-eng-process/reference-driver.md` (`cycle` section) +
  `docs-eng-process/script-cli-reference.md`: for authoring phases it now plans a
  full iteration instead of only recovering one named spec.

**Removed:** none — the single-row promote (T-092) is retained as the
construction/transition path and the degenerate case.

## Entities

- **plan-iteration handler** (new) — `scripts/openup_agent/plan_iteration.py`
- **`run_cycle` wiring** (modified) — `scripts/openup_agent/cycle.py`
- **process map** (read-only) — `openup-process-map.py mint-iteration-id`,
  `activities-for`; **id reservation** — `openup-claims.py reserve-id --prefix`;
  **partition** — `openup-board.py partition`
- **spec-authoring primitive** (reused) — `_dispatch_judgment` + a spec contract
- **iteration-plan instance** (new output) — `docs/phases/<phase>/iteration-<n>-plan.md`
- **assess reader** (read-only consumer, T-091) — `_active_iteration_plan`

## Approach

Port start-iteration §0b into the engine as a composition of existing scripts.
A new `plan_iteration.py` holds the deterministic steps + the two judgment
contracts; it takes injected callables (dispatch a sub-run, run a gate, git
commit) so it stays testable and imports nothing heavyweight from `cycle`.
`cycle.run_cycle` calls it on a `plan-iteration` decision when the phase is an
authoring phase and no iteration is active; otherwise the existing
`recover_missing_spec` path runs unchanged. Objectives and per-lane specs are the
only LLM sub-runs (reusing the T-089/T-092 bounded-sub-run machinery); mint,
reserve, activities, partition, and the iteration-plan instance are code. All
inter-step state is the repo (reserved ids, committed specs, the instance), so a
crashed plan resumes.

## Structure

**Add:**
- `scripts/openup_agent/plan_iteration.py` — `run_plan_iteration(...)` +
  helpers: `objectives_contract`, `read_objectives`, `generate_lanes`
  (activities-for → candidates), `partition_lanes`, `lane_spec_contract`,
  `write_iteration_plan_instance`. Stdlib-only; driver-coupled ops injected.
- `scripts/tests/test_openup_agent_plan_iteration.py` — hermetic unit + seam
  tests.

**Modify:**
- `scripts/openup_agent/cycle.py` — in the `plan-iteration` branch of
  `run_cycle`, dispatch to `plan_iteration.run_plan_iteration` for authoring
  phases (no active iteration); keep `recover_missing_spec` for the rest.
- `scripts/check-docs.py` — register each `docs/changes/<id>/` (and archived)
  change folder as an implicit `work-item` in the id index, so an iteration-plan
  tracing its change-folder lane ids resolves (change folders are the system's
  work-item instances; the trace model already allows iteration-plan → work-item).
- `scripts/process-manifest.txt` — ship `openup_agent/plan_iteration.py`.
- `scripts/tests/test_openup_agent_cycle.py` — wiring test (authoring-phase
  plan-iteration invokes the handler; construction does not).
- `scripts/tests/test_check_docs.py` — a change-folder ref resolves (no
  dangling); a real typed instance with the same id still wins.
- `docs-eng-process/reference-driver.md`, `script-cli-reference.md` — document
  the plan-iteration path.

**Do not touch:**
- `openup-board.py` resolve / `_active_iteration_plan` — the engine produces
  structure the existing reader already recognizes; no reader change.
- The T-092 `recover_missing_spec` single-row promote — kept as-is.
- T-091 paths (`assess-iteration`, `milestone-review`).

## Operations

- [x] Add `scripts/openup_agent/plan_iteration.py`: deterministic steps
  (mint-iteration-id, reserve-id `--prefix`, `activities-for`→candidate lanes,
  `partition`, `write_iteration_plan_instance`) + the two judgment contracts
  (`objectives_contract`, `lane_spec_contract`) + `read_objectives`.
- [x] Implement `run_plan_iteration(root, decision, …, dispatch, run_gates,
  git_commit)`: mint → objectives sub-run → generate+partition lanes → per-lane
  reserve-id + spec sub-run + gate + commit → write iteration-plan instance +
  commit → return so the re-resolve picks the first lane.
- [x] Wire into `cycle.py` `run_cycle`: on `plan-iteration` with an authoring
  phase and no active iteration, call the handler; else keep `recover_missing_spec`.
- [x] Add `openup_agent/plan_iteration.py` to `scripts/process-manifest.txt`.
- [x] (tester) Add `scripts/tests/test_openup_agent_plan_iteration.py` (unit:
  lane generation, partition, instance writing, objectives parse) + a cycle
  wiring test (authoring-phase plans; construction promotes) and a scripted
  end-to-end Inception plan (≥2 lanes, instance recognized, re-resolve ≠
  plan-iteration).
- [x] Update `reference-driver.md` + `script-cli-reference.md` for the
  plan-iteration path.
- [x] (tester) Full driver+cycle+plan-iteration suite green; `check-docs`,
  `openup-spec-scenarios`, `openup-fence.py check --base harness-optional` green.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, process conventions
- `docs-eng-process/reference-driver.md` — driver contract (stdlib-only,
  sentinel/exit codes, bounded sub-runs)
- `.claude/skills/openup-start-iteration/SKILL.md` §0b — the Plan Iteration model
  being ported
- `docs-eng-process/model-tiers.md` — authoring/MID tier for sub-runs

## Safeguards

- **Token / size budget.** Sub-runs = 1 (objectives) + 1 per lane, each bounded
  (default cap, authoring tier) — no unbounded loop. Zero LLM for mint / reserve /
  activities / partition / instance.
- **Reversibility.** Phase-gated + within the existing `recover` flag; a failed
  lane spec aborts with a typed exit before the iteration-plan instance is written
  (no half-planned iteration is left picked). Everything committed is git-revertible.
- **No-go zones.** No change to `resolve` or `_active_iteration_plan`; the
  construction/transition single-row promote must stay byte-equivalent to T-092.
- **Stdlib-only**; ships via process-manifest.

## Success Measures

n/a — internal process tooling. Falsifiable acceptance = the hermetic tests
(Req 1–7) plus the scripted Inception plan producing ≥2 iteration-prefixed lanes +
a recognized iteration-plan instance. Live-model token/reliability is the T-080
benchmark's job (measured under T-091's program acceptance; this sandbox reaches
no endpoint).

## Rollout

`n/a — not user-facing`: the reference driver is a developer tool. The path is
guarded by the existing code-level `recover` flag + phase gating, not a feature
flag; backout is a version pin or disabling recover. No flag-removal follow-up owed.

## Verification

- `python3 -m pytest scripts/tests/test_openup_agent_plan_iteration.py
  scripts/tests/test_openup_agent_cycle.py -q` — all green.
- Scripted Inception plan: ≥2 `I<n>-0xx` lanes authored, one
  `docs/phases/inception/iteration-*-plan.md` with `type: iteration-plan` +
  `traces-from` the lanes, and `openup-board.py resolve` afterwards ≠
  `plan-iteration`.
- Construction plan-iteration still single-row (no iteration minted).
- `openup-spec-scenarios.py check docs/changes/T-090/plan.md` → 0; `check-docs.py`
  → 0; `openup-fence.py check --base harness-optional` → clean.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

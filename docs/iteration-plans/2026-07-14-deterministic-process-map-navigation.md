# Plan: Deterministic process-map navigation (P1)

**Created:** 2026-07-14
**Phase:** construction
**Status:** planned
**Priority:** high
**Branch:** harness-optional
**Seeds from:** [explorations/2026-07-14-process-map-as-compiled-navigator.md](../explorations/2026-07-14-process-map-as-compiled-navigator.md)
**Tasks:** T-100 → {T-101, T-102} → T-103

## Goal

Make loop navigation a **deterministic walk of the shipped process map**, with
per-activity human inputs declared as **data**, and **delete** the per-cycle LLM
navigator (T-096) + the hardcoded Inception bootstrap (T-097/T-098). The LLM is
left with exactly two jobs — author artifacts, and (P2, deferred) compile a
customized process — and is **never** in the per-cycle navigation seat.

This is the **P1** slice from the exploration. **P2 (the LLM compile step that
generates a project-local map from a process description) is explicitly out of
scope here** and is deferred until a real custom-process need lands.

## Context / motivation

Four consecutive live bugs (T-096→T-099, on the `my-product` / qwen driver) came
from the same root: navigation was made an LLM job (T-096 writes a decision file
each cycle to pick the next procedure), which is flaky on a weak model, so
T-097/T-098 bolted a **hardcoded** bootstrap ("inception needs a brief →
create-vision") on top. The hardcoding is non-agnostic and duplicates what the
process map (T-077) + T-090 Plan Iteration already know — the redundant
`initiate-project` lane re-authoring the vision is the visible symptom.

The T-090 Plan Iteration **already** navigates deterministically from
`activities-for(phase)`; it is simply gated behind "a promotable roadmap entry
exists." P1 unlocks it for a fresh project and moves the two things the bootstrap
hardcoded — *which activity needs which human input* and *how an authoring
activity runs* — into the process-map **data** the deterministic layer already
reads.

## Current state (load-bearing code)

- **`docs-eng-process/process-map.yaml`** + **`scripts/openup-process-map.py`**
  (T-077): `phases:` → ordered activity names; `activities:` → `{role, skills}`;
  `phase_letters:`. `activities-for`, `mint-iteration-id`, `validate` verbs. **No**
  per-activity input declaration or execution mode today.
- **`scripts/openup-board.py` `resolve_decision`** (§1d ~line 867): emits
  `plan-iteration` **only when `_promote_next` returns a promotable roadmap
  `entry`**; a fresh project with no roadmap → `noop`.
- **`scripts/openup_agent/plan_iteration.py`** (T-090): mints iteration, one
  objectives sub-run, `generate_lanes(activities)` (one lane per skilled
  activity), per-lane spec authoring sub-run, iteration-plan instance. Every
  activity is spec-then-execute; no `execution: direct`.
- **`scripts/openup_agent/navigator.py`** (T-096/T-097/T-098): `run_navigator`
  (LLM decision file), `_bootstrap_step` (hardcoded inception brief→vision),
  `_scaffold_input`/`BRIEF_TEMPLATE`/`DEFAULT_INPUT_PATH` (brief-specific
  scaffold), `_run_procedure_reporting` (ADVANCED, keep). `cycle.py` wires the
  navigator on the `noop` path (`_run_navigator`).
- **`scripts/openup_agent/loop.py`**: `ask_user` → suspend (T-074) already lets a
  sub-run request a human answer; `OPENUP_AGENT_USAGE_LOG` (T-080) records
  per-call metadata (the falsifiable-measure read-back surface).

## Tasks

### T-100 — Process-map schema: per-activity `requires_input` + `execution` mode
Extend `process-map.yaml` + `openup-process-map.py`:
- `activities.<name>.requires_input: { path, describe }` (0..n) — a human-authored
  file the activity needs.
- `activities.<name>.execution: direct | spec-then-execute` (default
  `spec-then-execute`) — `direct` runs the activity's `procedure` without an
  intermediate lane spec (for authoring activities like create-vision).
- New reader verbs (e.g. `activity <name> --json` returning the enriched record).
- `validate` extended to hard-gate the new fields (well-formed `path`, known
  `execution` value, `direct` implies a single `procedure`).
- Populate the shipped inception/elaboration activities with real
  `requires_input` (e.g. `initiate-project.requires_input =
  docs/inputs/stakeholder-brief.md`) and `execution: direct` where apt.
**Foundation; no behavior change to the engine yet.** Depends on: —

### T-101 — Fire Plan Iteration on a fresh project (no roadmap)
`openup-board.py resolve_decision`: when there is no active iteration, no
promotable roadmap entry, **and the current phase has undone `activities-for`
work** (its work products don't yet exist), emit `plan-iteration` (carrying the
phase) instead of `noop` — so T-090 Plan Iteration runs from `activities-for`. A
genuinely finished/empty phase still resolves to `milestone-review`/`noop` as
today. Reuses T-090 machinery; no new engine path. Depends on: T-100 (so lanes
can carry input/execution data).

### T-102 — Map-driven input scaffold + `execution: direct`
In the cycle/Plan-Iteration path: before running an activity whose
`execution: direct`, run its `procedure` directly (no lane spec) — killing the
redundant `initiate-project`-re-authors-vision lane. Before running any activity,
check each declared `requires_input`: if the file is missing (marker-aware, from
T-097), **scaffold a generic template there + suspend (exit 5)** with guidance —
the T-097 affordance generalized to **any** declared input, driven by the map, not
hardcoded to "brief". `ask_user` remains the fallback for undeclared inputs.
Depends on: T-100.

### T-103 — Delete the hardcoded bootstrap + retire the per-cycle navigator
Remove `navigator._bootstrap_step`, the brief-specific
`BRIEF_TEMPLATE`/`DEFAULT_INPUT_PATH`/`_scaffold_input` specialization, and the
per-cycle LLM navigator decision path (`run_navigator` decision-file flow +
`.openup/navigator-decision.json`); rewire `cycle.py`'s `noop` path to the
map-driven Plan Iteration (T-101). Keep `_run_procedure_reporting` (ADVANCED,
T-099) and the generic template-scaffold helper (moved/kept for T-102). Update
docs (`reference-driver.md`, `script-cli-reference.md`) — navigation is
deterministic; the navigator LLM is gone from the per-cycle path. Depends on:
T-101, T-102.

## Acceptance criteria (program)

- [ ] A fresh project (no vision/roadmap) drives Inception through `cycle`
      **without any per-cycle navigator LLM call**: the deterministic layer fires
      Plan Iteration from `activities-for(inception)`; `initiate-project` runs
      create-vision **directly**; its declared `requires_input` (the brief), when
      missing, scaffolds a template + suspends.
- [ ] No redundant `initiate-project` lane that re-authors an existing vision.
- [ ] `navigator.py`'s `_bootstrap_step` and per-cycle decision-file path are
      **deleted**; `.openup/navigator-decision.json` is no longer produced.
- [ ] `process-map.yaml validate` hard-gates the new `requires_input`/`execution`
      fields; the shipped map declares them for inception/elaboration.
- [ ] Full driver suite green; `check-docs`, `spec-scenarios`, fence
      (`--base harness-optional`) green.

## Success Measure

We expect a fresh Inception-through-delivery run — on the T-080 benchmark and the
my-product fixture — to complete with **zero per-cycle navigator LLM calls** (down
from ≥1/cycle) and the `navigator.py` decision-file code **deleted**, **without
regressing** convergence (still reaches a promotable roadmap + first lane) or
total LLM-call count. Instrumentation: `OPENUP_AGENT_USAGE_LOG` call records + a
test asserting the navigator decision path is never entered on the fresh-project
scenario. Read-back: at P1 completion (T-103), via the T-080 batch.

## Dependencies

- T-100 (schema) → foundation for T-101 (lanes carry data) and T-102 (scaffold +
  execution).
- {T-101, T-102} → T-103 (the deterministic replacement must be in place before
  deleting the bootstrap/navigator).
- Program builds on T-077 (process map), T-090 (Plan Iteration), T-097 (scaffold),
  T-080 (usage log / benchmark).

## Out of scope

- **P2 — the LLM compile step** that generates a project-local process map from a
  process description (schema-strict + `validate`-gated + human-reviewed).
  Deferred until a real customized-process need appears; the T-100 schema is kept
  forward-compatible for it.
- Any change to the deterministic engine's other decision paths (pick/resume/
  assess/milestone) beyond the fresh-project `plan-iteration` trigger.
- Non-`harness-optional` branches; no `main` merge.

## Open Questions

1. **Phase-completeness signal for T-101** — "the phase has undone activities" is
   derived how? By checking each `activities-for(phase)` activity's expected work
   product exists (create-vision→docs/vision.md, etc.), or by a lifecycle
   criterion? *Assumed:* work-product existence per activity, reusing the Ring-1
   survey. *(Vetoable at task-spec review.)*
2. **`execution: direct` and the iteration-plan instance** — a direct authoring
   activity still needs to appear as a committed work item the assess path (T-091)
   recognizes. Does it get a minimal change-folder record, or is the iteration-plan
   instance's `traces-from` extended to cover direct activities? *Resolve at T-102
   spec.*
3. **Migration of in-flight my-product** — projects already bootstrapped by
   T-098 have a `.openup/navigator-decision.json` / brief scaffold; T-103 should
   no-op cleanly on them (no migration needed since the artifacts already exist).
4. **No-fallback risk (self-critique, load-bearing).** T-103 removes the per-cycle
   LLM navigator entirely — so a genuinely *unclassifiable* state (one the process
   map + Plan Iteration + assess/milestone don't cover) has no LLM to reason about
   it. *Assessment:* for standard OpenUP this niche is empty — `noop` becomes
   `plan-iteration` (T-101), an exhausted-but-incomplete phase goes to T-094
   replenish or T-091 milestone, and delivery is pick/resume. The navigator was
   only ever reached on `noop`. *Mitigation:* keep the retirement to the *decision*
   path only; if a real uncovered state ever appears it is a P2 (compile) or a new
   deterministic case, not a reason to keep the flaky per-cycle LLM. Confirm no
   uncovered `resolve` path remains before deleting (T-103 acceptance).

---

*Program plan; each task's REASONS-Canvas spec is authored on promote via
`/openup-create-task-spec`. Sequenced per the exploration's product-manager pass:
delete the flaky navigator (evidenced value now); the LLM compile step is P2.*

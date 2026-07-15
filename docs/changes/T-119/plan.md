---
id: T-119
title: "Full Inception cycle on the weak model: direct task-def authoring for all authoring activities + tool-arg guard"
status: ready
priority: high
estimate: 1 session
plan: docs/iteration-plans/2026-07-14-lean-authoring-tasks.md
depends-on: [T-106]
blocks: []
last-synced: ""
touches:
  - docs-eng-process/process-map.yaml
  - scripts/openup-process-map.py
  - scripts/openup_agent/tools.py
  - scripts/tests/test_openup_agent_tools.py
  - scripts/tests/test_task_map_wiring.py
  - scripts/tests/test_openup_process_map.py
  - docs-eng-process/reference-driver.md
---

# T-119 — Full Inception cycle on the weak model

## Story

> **As a** reference-driver running a fresh Inception cycle on a weak local model
> **I want** every authoring activity to use the proven lean task-def path (not the ceremony-heavy spec-lane authoring), and a bad tool arg to not crash the driver
> **So that** the whole Inception cycle completes reliably — the program's end-to-end measure, not just `initiate-project`

INVEST — ✅ Independent · ✅ Negotiable · ✅ Valuable · ✅ Estimable · ✅ Small · ✅ Testable

## Analysis Context

- **Domain.** Driven by the 2026-07-15 live qwen-27b batch: `initiate-project` (T-106 task-def path) authored vision+roadmap cleanly in 5/5 runs, but the **full Inception cycle failed 0/5** downstream in the **spec-then-execute lane-spec authoring** (`cycle.dispatch_spec` → the `cycle-step` procedure, which T-106 did NOT convert — still procedure-read). On the 27B it (a) ran out at 50 turns authoring the `I1-002` lane spec, and (b) made a malformed `glob ""` call that crashed the driver with `IndexError` (unguarded tool arg).
- **Scope boundaries.** Two targeted fixes: **(A)** guard the tool layer so a bad model arg returns an error to the model instead of crashing; **(B)** flip the Inception authoring activities (agree-technical-approach, identify-refine-requirements, plan-manage-iteration) to `execution: direct` so they use their **already-compiled T-105 task defs** via the proven task-def path — retiring their reliance on the ceremony-heavy spec-lane authoring. NOT in scope: converting construction/transition lanes; the `cycle-step` procedure itself; scaling the library (T-107).
- **Definition of done.** The three Inception authoring activities run `execution: direct`; the `direct requires exactly one skill` validation is relaxed to `direct requires ≥1 task` (T-106 direct is task-driven); the `glob` tool guards empty/invalid patterns; a re-run of the `inception-taskdef` bench completes the full cycle (owner endpoint).

> **Assumption:** authoring Inception documents directly (like the vision) is the right model — these are deliverables, not code work items; the iteration-plan instance already records direct activities and accepts empty `traces-from`. *(Vetoable at review.)*

## Requirements

1. The `glob` tool returns an error string for an empty/invalid pattern instead of raising (which crashes the driver).
   - **Given** the model calls `glob("")` **When** the tool runs **Then** it returns an `ERROR: …` string (no exception), and the sub-run continues.
2. `openup-process-map.py validate` requires an `execution: direct` activity to declare ≥1 `tasks:` entry (task-driven), replacing the obsolete "exactly one skill" rule.
   - **Given** a direct activity with `tasks: [a]` and 2 skills **When** `validate` runs **Then** no problem is reported; **Given** a direct activity with no `tasks:` **Then** it reports "direct requires ≥1 task".
3. The three Inception authoring activities are `execution: direct` and resolve their task defs; the map validates.
   - **Given** the shipped map + library **When** `openup-process-map.py validate` runs **Then** it exits 0 with the three activities direct.
4. No regression to the existing task-def direct path or the spec-then-execute path for non-flipped activities.
   - **Given** the full existing suite **When** it runs **Then** it passes (updating only the assertions the flip changes).

## Behavior Delta

**Modified** — the Inception authoring flow (`docs-eng-process/reference-driver.md §task-def authoring`): agree-technical-approach / identify-refine-requirements / plan-manage-iteration now author their artifacts **directly** via task defs instead of authoring spec-then-execute lanes. The `direct` validation rule (skill-count → task-count).

**Added** — tool-arg guard on `glob`.

**Removed** — the "direct requires exactly one skill" rule.

## Entities

- **Process map** (modified) — `docs-eng-process/process-map.yaml` (execution flags), `scripts/openup-process-map.py` (validate rule)
- **Tool layer** (modified) — `scripts/openup_agent/tools.py` (`glob` guard)
- **Task defs** (read-only, consumed) — `docs-eng-process/task-library.yaml`

## Approach

(A) In `tools.py` `glob`, reject an empty/whitespace pattern up front and wrap `root.glob` in a try/except returning `ERROR: …` (mirroring `grep`'s invalid-regex handling). (B) In `process-map.yaml`, set `execution: direct` on the three activities (they already carry `tasks:`). In `openup-process-map.py validate`, replace the `direct ⇒ exactly one skill` check with `direct ⇒ len(tasks) ≥ 1`. Update the map-wiring test + any spec-lane tests that assumed those activities were spec-then-execute.

## Structure

**Modify:**
- `docs-eng-process/process-map.yaml` — `execution: direct` on the 3 activities.
- `scripts/openup-process-map.py` — validate: direct requires ≥1 task.
- `scripts/openup_agent/tools.py` — `glob` empty/invalid guard.
- `scripts/tests/test_openup_agent_tools.py` — glob-guard test.
- `scripts/tests/test_task_map_wiring.py` — direct-requires-task validation test.
- `docs-eng-process/reference-driver.md` — note the Inception activities are direct.

**Do not touch:** the `run_task`/stamping seam; `task-library.yaml` content; construction/transition activities; the `cycle-step` procedure.

## Operations

- [x] Guard `tools.py` `glob` against empty/invalid patterns (return `ERROR: …`, never raise).
- [x] Relax `openup-process-map.py` validate: `execution: direct` requires ≥1 `tasks:` entry (drop the exactly-one-skill rule).
- [x] Set `execution: direct` on agree-technical-approach, identify-refine-requirements, plan-manage-iteration in `process-map.yaml`.
- [x] (tester) Tests: `glob("")` returns an error not a crash; direct-without-tasks fails validate, direct-with-tasks+2-skills passes; shipped map validates; update any spec-lane test assuming those activities are spec-then-execute.
- [x] Update `reference-driver.md` (Inception authoring activities are direct/task-def).
- [x] Full suite green; fence `--base harness-optional`; then re-run the `inception-taskdef` bench (owner endpoint) for the full-cycle read-back.

## Norms

Inherits from:
- `docs-eng-process/conventions.md`
- T-106 task-def authoring path (the mechanism this extends to more activities)

## Safeguards

- **No execution-seam change.** `run_task`/stamping/gates untouched — reusing the proven path, just for more activities.
- **Robustness.** No model tool-arg may crash the driver (the guard generalizes: empty glob is the observed case).
- **Reversibility.** Revert the map `execution` flags + the validate rule to restore spec-then-execute for those activities.
- **Gate honesty.** T-107 stays gated until the full `inception-taskdef` cycle passes ≥4/5 on the owner's endpoint.

## Verification

- `python3 scripts/openup-process-map.py validate` exits 0 (3 activities direct).
- `glob("")` returns `ERROR:` (unit test); driver no longer crashes on it.
- Full suite green; fence clean.
- Re-run `inception-taskdef --runs 5` (owner endpoint): full cycle completes ≥4/5.
- Grade against `.claude/rubrics/task-spec-rubric.md`.

## Success Measures

We expect the `inception-taskdef` full-cycle clean-pass rate to move from **0/5 → ≥4/5** on the qwen fixture (the spec-lane 50-turn timeout eliminated by the direct task-def path; the glob crash eliminated by the guard). Instrumentation: bench `results.jsonl` `outcome`/`clean_passes` + `OPENUP_AGENT_DEBUG_LOG`. Read-back: the next batch on the owner's endpoint.

## Rollout

n/a — internal driver behavior on harness-optional; no flag, no user-facing runtime. Claude Code path unchanged.

---
id: T-106
title: "Engine consumes the task library: generic authoring sub-run + tasks map wiring"
status: done
priority: high
estimate: 1-2 sessions
plan: docs/iteration-plans/2026-07-14-lean-authoring-tasks.md
depends-on: [T-104, T-105]
blocks: [T-107]
last-synced: ""
touches:
  - scripts/openup_agent/plan_iteration.py
  - scripts/openup_agent/cycle.py
  - scripts/openup_agent/stamping.py
  - docs-eng-process/process-map.yaml
  - scripts/openup-process-map.py
  - scripts/bench-scenarios/inception-taskdef/
  - scripts/tests/test_openup_agent_plan_iteration.py
  - scripts/tests/test_openup_agent_cycle.py
  - scripts/tests/test_task_map_wiring.py
  - docs-eng-process/reference-driver.md
---

# T-106 — The engine consumes the library: generic sub-run + map wiring

## Story

> **As a** reference-driver running authoring activities on a weak local model
> **I want** each authoring sub-run driven by a lean task def (no procedure file read)
> **So that** per-call context drops to the shape that measured reliable (T-080), ending the mid-run restarts caused by 650+-line procedure fan-out

INVEST — ✅ Independent · ✅ Negotiable · ✅ Valuable · ✅ Estimable · ✅ Small · ✅ Testable

## Analysis Context

- **Domain.** The reference-driver's authoring path (`execution: direct` activities). Today `cycle.py`'s `run_procedure` closure calls `loop.run(procedure=…)` with no `system_prompt`, so the full procedure FILE is read as the system prompt. T-106 switches this to a generic shell built from a T-105 task def — the file is never read.
- **Scope boundaries.** Only the **driver** authoring path. No Claude Code skill changes (parity at artifact level). No KB edits. The `next` procedure / `openup-loop.sh` untouched. Non-authoring judgment sub-runs (Operations boxes, assess, objectives) already lean — untouched. No `main` merge (harness-optional only). The **live behavioral measure** (qwen batch) is read by the owner post-merge; this task ships the bench scenario + the hermetic proof.
- **Definition of done.** `process-map.yaml` authoring activities carry `tasks: [ids]` resolving into the library; the direct path iterates a task's ordered defs, one bounded `loop.run(system_prompt=…, model=…)` sub-run each (no procedure read); T-104 stamping keys off the def's `artifact`/`output_path` (retiring `PROCEDURE_ARTIFACTS` + the `ROADMAP_FORMAT` interim constant); a bench scenario drives the task-def path; hermetic tests prove the flow.

> **Assumption:** the generic system-prompt shell is *"You are performing OpenUP task `<name>` (role `<role>`). Produce `<artifact>` at `<output_path>`. What good looks like: `<judgment>`. Read `<inputs>`. Save the file; emit the sentinel."* wrapped by the existing T-104 ceremony (config injection, stamping, gates). *(Vetoable at review.)*
> **Assumption:** the flagship split is `initiate-project: tasks: [develop-technical-vision, author-initial-roadmap]` (vision body, then the roadmap carrying the pinned format from its def). *(Vetoable.)*
> **Assumption:** the live behavioral acceptance is validated by the owner's qwen batch after merge; T-107 stays gated on it. This sandbox cannot reach an LLM endpoint. *(Vetoable.)*

## Requirements

1. `process-map.yaml` authoring activities gain an ordered `tasks: [ids]` field; `openup-process-map.py validate` requires every listed id to resolve in `task-library.yaml`.
   - **Given** an activity with `tasks: [nonexistent]` **When** `openup-process-map.py validate` runs **Then** it reports the unresolved task id and exits 2; **Given** the shipped map **Then** it exits 0.
2. The direct path iterates an activity's ordered `tasks`, running one bounded sub-run per def with a generic system prompt built from the def — the procedure file is never read.
   - **Given** `initiate-project` (tasks: vision, roadmap) **When** the direct path runs **Then** two sub-runs execute, each with a `system_prompt` (not a procedure file), and neither reads a `docs-eng-process/procedures/*.md` file.
3. Frontmatter stamping keys off the running task def's `artifact` + `output_path` (not the `PROCEDURE_ARTIFACTS` table).
   - **Given** the `develop-technical-vision` def (artifact vision, output docs/product/vision.md) **When** its sub-run completes **Then** `stamp_file` stamps `type: vision` at that path.
4. The pinned roadmap format is carried by the `author-initial-roadmap` def, retiring the `ROADMAP_FORMAT` interim constant from `plan_iteration.py`.
   - **Given** the `author-initial-roadmap` sub-run **When** its instruction is built **Then** it contains the pinned `| ID | Title | … |` format contract sourced from the def, and `plan_iteration.py` no longer defines `ROADMAP_FORMAT`.
5. A bench scenario drives the fresh-Inception flow through the task-def path, wired to `OPENUP_AGENT_USAGE_LOG` + `OPENUP_AGENT_DEBUG_LOG`.
   - **Given** the new `inception-taskdef` scenario **When** the bench builds its fixture **Then** it runs `command: cycle` on a fresh Inception project and checks the authored deliverable.

## Behavior Delta

**Added** — `tasks:` field on process-map activities; generic task-def-driven authoring sub-run; bench scenario `inception-taskdef`.

**Modified** — the driver's authoring execution path — `docs-eng-process/reference-driver.md §Plan Iteration` (the `execution: direct` procedure-read behavior becomes task-def-driven); frontmatter stamping source (`stamping.py` — from `PROCEDURE_ARTIFACTS` table to task-def `artifact`/`output_path`).

**Removed** — the `ROADMAP_FORMAT` interim constant + `PROCEDURE_ARTIFACTS` table (superseded by task defs) — `docs-eng-process/reference-driver.md §Engine-owned authoring ceremony (T-104)`.

## Entities

- **Direct authoring path** (modified) — `scripts/openup_agent/plan_iteration.py`, `scripts/openup_agent/cycle.py`
- **Stamping** (modified) — `scripts/openup_agent/stamping.py`
- **Process map** (modified) — `docs-eng-process/process-map.yaml`, `scripts/openup-process-map.py`
- **Task library** (read-only, consumed) — `docs-eng-process/task-library.yaml`
- **Bench scenario** (new) — `scripts/bench-scenarios/inception-taskdef/`

## Approach

Wire `tasks:` onto activities in the map + parser; `validate` joins them to `load_tasks`. In `plan_iteration.py`, the direct branch iterates `lane["tasks"]`, resolving each def (via an injected `task_defs` map) and building a per-task instruction (generic shell + CEREMONY_EXCLUSION + config injection; the roadmap def carries its own pinned format). A new injected `run_task(task_def, instruction)` replaces the single `run_procedure` call. In `cycle.py`, `run_task` builds the generic `system_prompt` from the def, calls `loop.run(system_prompt=…, model=resolved, instruction=…)` (file-skipping seam), and stamps via the def's `artifact`/`output_path`. `stamping.py` gains a `stamp_for_task(root, def)` keyed off the def; `PROCEDURE_ARTIFACTS` + `ROADMAP_FORMAT` are removed.

## Structure

**Add:**
- `scripts/bench-scenarios/inception-taskdef/scenario.json` (+ overlay) — task-def-path bench.
- `scripts/tests/test_task_map_wiring.py` — map `tasks:` parse + validate join.

**Modify:**
- `scripts/openup-process-map.py` — parse + validate `tasks:` on activities.
- `docs-eng-process/process-map.yaml` — `tasks:` on authoring activities (flagship split).
- `scripts/openup_agent/plan_iteration.py` — iterate ordered tasks; per-task instruction; drop `ROADMAP_FORMAT`.
- `scripts/openup_agent/cycle.py` — `run_task` closure (system_prompt + model + task stamping).
- `scripts/openup_agent/stamping.py` — `stamp_for_task`; retire `PROCEDURE_ARTIFACTS`.
- `scripts/tests/test_openup_agent_plan_iteration.py` — task-def direct-path tests.
- `docs-eng-process/reference-driver.md` — document the task-def authoring path.

**Do not touch:**
- Claude Code `openup-create-*` skills — parity at artifact level (T-107).
- KB files / `task-library.yaml` content (T-105) — read-only here.
- `next` procedure / `openup-loop.sh` — out of scope.

## Operations

- [x] Parse `tasks:` on activities in `openup-process-map.py` (`_activity_record` + `activities_for`); extend `validate` to require every listed id resolve in `load_tasks`.
- [x] Add `tasks:` to `process-map.yaml` authoring activities — flagship `initiate-project: [develop-technical-vision, author-initial-roadmap]` + the other authoring activities' defs.
- [x] Add `stamp_for_task(root, task_def)` to `stamping.py` (key off `artifact`/`output_path`); remove `PROCEDURE_ARTIFACTS`.
- [x] Rework `plan_iteration.py` direct branch to iterate ordered task defs, build the per-task generic instruction, call injected `run_task`; delete `ROADMAP_FORMAT` (now in the `author-initial-roadmap` def).
- [x] Rework `cycle.py`'s runner into `run_task`: build the generic `system_prompt` shell from the def, `loop.run(system_prompt=…, model=…)` (no procedure read), stamp via `stamp_for_task`.
- [x] Add the `inception-taskdef` bench scenario (`command: cycle`, deliverable + markers) wired to the usage/debug logs.
- [x] (tester) Hermetic tests: map `tasks:` parse+validate join; direct path runs N sub-runs with `system_prompt` (no procedure read); stamping keyed off the def; roadmap def carries the pinned format. Full suite green; fence `--base harness-optional`.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions
- `docs-eng-process/reference-driver.md` — the driver's authoring-path contract
- T-104 machinery — `CEREMONY_EXCLUSION`, `project_config_block`, `stamping.stamp_file`

## Safeguards

- **No-go zones.** Only the driver authoring path. No Claude Code skill / KB edits. `main` untouched (harness-optional only). Non-authoring sub-runs unchanged.
- **Behavioral gate.** T-107 stays gated on the live qwen-batch acceptance (zero mid-run restarts, ≤6 iters/sub-run, ≥80%/5 runs, ≤⅓ context) — read by the owner post-merge; not claimed satisfied by this task.
- **Reversibility.** The change is localized to the direct-run seam; reverting restores the procedure-file path. Task library stays inert if `tasks:` wiring is removed.
- **Regression guard.** The `spec-then-execute` (non-authoring) lane path must be byte-unchanged; full existing suite green.

## Verification

- `openup-process-map.py validate` exits 0 (map + task join); rejects an unresolved `tasks:` id.
- Hermetic: scripted `initiate-project` → two `system_prompt` sub-runs, no procedure-file read, engine-stamped, `check-docs` green, roadmap promotable.
- `python3 -m pytest scripts/tests/ -q` green; fence `--base harness-optional` clean.
- Grade against `.claude/rubrics/task-spec-rubric.md`.

## Success Measures

We expect the fresh-Inception authoring tasks on the qwen fixture to complete with **zero mid-run restarts, ≤6 iterations per sub-run, ≥80% clean-pass over 5 runs, and per-sub-run prompt context ≤⅓ of the 2026-07-14 baseline**. Instrumentation: `OPENUP_AGENT_USAGE_LOG` (prompt_tokens) + `OPENUP_AGENT_DEBUG_LOG` (restart = repeated opener), via the `inception-taskdef` bench scenario. Read-back: the owner's live batch post-merge (this sandbox has no endpoint) — the gate for promoting T-107.

## Rollout

n/a — internal reference-driver behavior on the `harness-optional` integration branch; no user-facing runtime, no feature flag. The Claude Code path is unchanged (artifact-level parity).

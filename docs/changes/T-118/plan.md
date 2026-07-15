---
id: T-118
title: "Task-def authoring instruction names the concrete input path (kills glob-thrash)"
status: ready
priority: medium
estimate: 0.5 session
plan: docs/iteration-plans/2026-07-14-lean-authoring-tasks.md
depends-on: [T-106]
blocks: []
last-synced: ""
touches:
  - scripts/openup_agent/plan_iteration.py
  - scripts/tests/test_openup_agent_plan_iteration.py
---

# T-118 — Task-def authoring instruction names the concrete input path

## Story

> **As a** weak local model running a task-def authoring sub-run
> **I want** the instruction to name the concrete file path of the provided input
> **So that** I read it directly instead of spending 4+ turns globbing to locate it — fewer turns, less context, lower restart risk

INVEST — ✅ Independent · ✅ Negotiable · ✅ Valuable · ✅ Estimable · ✅ Small · ✅ Testable

## Analysis Context

- **Domain.** The T-106 task-def authoring path. Evidence: a live qwen-27b run of `initiate-project` spent **5 `glob` calls across 4 turns** (`**/Vision*`, `*`, `inputs/*`, `docs/*`, `docs/inputs/*`, …) hunting for its input before reading `docs/inputs/stakeholder-brief.md`. Root cause: `render_task_instruction` tells the model `Inputs to read: Vision` — a KB workproduct **display-name**, not a resolvable path.
- **Scope boundaries.** Only the instruction text for the direct/task-def path. No change to the execution seam, stamping, the map, or the task-library data. The activity's human-provided input path is already known — it is the lane's `requires_input.path` (T-100). This task threads that concrete path into the instruction; it does NOT attempt full workproduct-name→path resolution for every input (that would be a T-105 data change).
- **Definition of done.** When the activity declares a `requires_input` path, the task instruction names that concrete file to read first; the workproduct-name `inputs` stay as secondary context. A hermetic test asserts the concrete path appears in the instruction.

## Requirements

1. When the direct activity declares a `requires_input` path, `render_task_instruction` names that concrete path as the file to read first.
   - **Given** `initiate-project` (requires_input `docs/inputs/stakeholder-brief.md`) **When** the vision task instruction is built **Then** it contains "docs/inputs/stakeholder-brief.md" as a file to read, not only the workproduct name "Vision".
2. When no `requires_input` path is declared, the instruction is unchanged (workproduct-name inputs only) — no regression.
   - **Given** an activity with no `requires_input` **When** its task instruction is built **Then** it still lists the def's workproduct `inputs` and names no phantom path.
3. The workproduct-name `inputs` remain in the instruction as secondary context (not removed).
   - **Given** a task with `inputs: [Vision]` and a provided input path **When** the instruction is built **Then** both the concrete path and "Vision" appear.

## Behavior Delta

**Modified** — the T-106 task-def authoring instruction (`plan_iteration.render_task_instruction`): now names the activity's concrete `requires_input` path when present. Ring-1 driver-behavior doc: `docs-eng-process/reference-driver.md §task-def authoring` (instruction content) — a one-line note, no structural change.

**Added / Removed** — n/a.

## Entities

- **Instruction builder** (modified) — `scripts/openup_agent/plan_iteration.py` `render_task_instruction` + the direct branch that calls it.

## Approach

Give `render_task_instruction` an optional `input_path`. When set, prepend an explicit "Read the provided input file at `<path>`." line; keep the workproduct-name `inputs` as "additional inputs to consider". In the direct branch, pass `lane["requires_input"]["path"]` when the activity declares one (it applies to the activity's tasks). Purely additive to the instruction string — no execution change.

## Structure

**Modify:**
- `scripts/openup_agent/plan_iteration.py` — `render_task_instruction(…, input_path=None)`; direct branch passes the lane's requires_input path.
- `scripts/tests/test_openup_agent_plan_iteration.py` — assert the concrete path appears; assert no-requires_input is unchanged.

**Do not touch:** the execution seam (`run_task`/`cycle.py`), stamping, the map, `task-library.yaml`.

## Operations

- [ ] Add `input_path=None` to `render_task_instruction`; when set, name the concrete file to read first and keep workproduct `inputs` as secondary.
- [ ] In the direct branch, pass the lane's `requires_input.path` (when declared) to `render_task_instruction`.
- [ ] (tester) Tests: concrete path present for `initiate-project`; unchanged when no `requires_input`; workproduct names still present.

## Norms

Inherits from:
- `docs-eng-process/conventions.md`
- T-106 `render_task_instruction` (the builder this refines)

## Safeguards

- **No execution change.** Only the instruction string changes; `run_task`/stamping/gates untouched.
- **No regression.** Activities without `requires_input` produce the same instruction as before.
- **Reversibility.** Revert restores the T-106 instruction verbatim.

## Verification

- `python3 -m pytest scripts/tests/test_openup_agent_plan_iteration.py -q` passes.
- Full suite green; fence `--base harness-optional` clean.
- Re-run `inception-taskdef` bench (owner endpoint) shows the vision sub-run reading the brief without the multi-glob hunt.

## Success Measures

We expect the vision authoring sub-run on the qwen fixture to reach its input in **≤1 tool call** (a direct `read_file` of the named path) instead of the 5-glob/4-turn hunt observed 2026-07-15. Instrumentation: `OPENUP_AGENT_DEBUG_LOG` tool-call trace of the `inception-taskdef` bench. Read-back: the next batch on the owner's endpoint.

## Rollout

n/a — internal driver instruction text on harness-optional; no flag, no user-facing runtime.

---
id: T-083
title: Benchmark harness — realistic "stakeholder brief → Vision doc" scenario
status: done
priority: high
plan: docs/changes/archive/T-080/plan.md
depends-on: [T-080, T-072]
touches:
  - scripts/openup-agent.py
  - scripts/openup_agent/loop.py
  - scripts/openup-agent-bench.py
  - scripts/bench-scenarios/
  - scripts/tests/test_openup_agent_bench.py
  - docs-eng-process/reference-driver.md
  - docs-eng-process/reference-driver-benchmark.md
  - docs/changes/
last-synced: ""
---

# T-083 — Benchmark the real flow: stakeholder brief → Vision document

## Story

> **As** the owner benchmarking the reference driver on a local model
> **I want** a scenario that seeds a **fresh project + a minimal stakeholder brief**
> and drives the driver to **produce the project Vision document** (via
> `openup-create-vision`), scored on whether a valid `docs/vision.md` results
> **So that** the benchmark measures the framework's *actual first-iteration
> value* — turning a stakeholder brief into a vision — instead of the `quick-doc`
> toy edit.

## Context & decisions

- **Owner decision (2026-07-13):** drive **`openup-create-vision` directly** (not
  the full `next` loop or Plan-Iteration) — the tightest, cheapest, most
  deterministic measurement of "can this model turn a brief into a valid vision."
- **The vision flow (from the pack):** `openup-create-vision` (Inception
  `initiate-project` activity, role analyst) copies
  `docs-eng-process/templates/vision.md` → **`docs/vision.md`**, filling
  project name / problem statement / stakeholders / key features / success
  criteria. Its inputs are `project_name` + `problem_statement` **arguments**.
- **The gap this task closes:** the driver's initial user message is hardcoded
  ("Execute the procedure now.") — there is **no way to hand it the brief or the
  arguments**. And the harness scenario format assumes a change-folder lane picked
  by `resolve` + a single deliverable marker — neither fits a vision run.

## Requirements

1. **Driver accepts an optional instruction.** `openup-agent.py run` gains
   `--instruction TEXT`; `loop.run(instruction=…)` appends it to the initial user
   message. Absent ⇒ today's behavior verbatim.
   - **Given** `--instruction "read X, produce Y"` **When** the loop starts **Then**
     the first user message contains that text (asserted via the loop seam).
2. **Scenarios are self-describing.** `scenario.json` may set `procedure` (the
   default procedure to drive), `instruction` (passed to the driver), make
   `expect_pick` **optional** (skip the resolve==pick sanity check when absent),
   and declare success as `deliverable_file` + `required_markers` (a list — all
   substrings must be present), superseding the single `deliverable_marker`
   (still honored for back-compat).
   - **Given** a scenario with `procedure` set and no `--procedure` flag **When**
     the batch runs **Then** the scenario's procedure is driven.
   - **Given** `required_markers` **When** the deliverable contains all of them
     **Then** `deliverable_produced` is true; missing any ⇒ false.
3. **New `inception-vision` scenario.** Seeds a fresh project + a minimal
   **stakeholder brief** (`docs/inputs/stakeholder-brief.md`, invented content),
   drives `openup-create-vision` with an instruction to read the brief and produce
   `docs/vision.md`, and scores on a valid vision (required sections present). No
   `expect_pick` (there is no change-folder lane).
   - **Given** the scenario **When** the driver writes a `docs/vision.md` with the
     required sections **Then** the run scores `deliverable_produced=true`.
4. **Hermetic coverage.** The mock-endpoint test drives the `inception-vision`
   scenario end-to-end (scripted model reads the brief, writes a sectioned
   `docs/vision.md`) and asserts the success check + that `--instruction` reached
   the driver. Existing tests stay green.
   - **Given** the mock-endpoint vision test **When** the suite runs **Then** the
     scenario scores a clean pass and the quick-doc pipeline test still passes.

## Operations

- [x] Driver: add `--instruction` to `openup-agent.py`; thread `instruction` into
  `loop.run` (append to the initial user message). Test the seam.
- [x] Harness: scenario.json `procedure`/`instruction`/`required_markers` +
  optional `expect_pick`; `--procedure` default becomes "scenario's, else next";
  `resolves_to` sanity check skipped when no `expect_pick`; `work_delta` success
  honors `required_markers`. Pass `--instruction` through `run_driver`.
- [x] Author `scripts/bench-scenarios/inception-vision/` — `scenario.json` +
  `overlay/docs/inputs/stakeholder-brief.md` (invented, benign product) +
  instruction pointing at the brief; success = `docs/vision.md` + required section
  markers.
- [x] Extend `scripts/tests/test_openup_agent_bench.py` — scripted vision run +
  `--instruction` assertion; keep the quick-doc pipeline test green.
- [x] Docs: `--instruction` in `reference-driver.md`; scenario-format +
  `inception-vision` in `reference-driver-benchmark.md`.
- [x] (tester) driver + bench suites + `openup-fence.py check --base harness-optional`.

## Verification

- `openup-agent-bench.py --repo . --scenario scripts/bench-scenarios/inception-vision`
  drives `openup-create-vision`; a run that writes a sectioned `docs/vision.md`
  scores `deliverable_produced=true`.
- `--instruction` text reaches the driver's first user message.
- quick-doc scenario still works (change-folder lane path unchanged).
- driver + bench tests green; fence (`--base harness-optional`) green.

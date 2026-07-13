---
id: T-084
title: Benchmark harness archives each run's deliverable for inspection
status: done
priority: medium
plan: docs/changes/archive/T-080/plan.md
depends-on: [T-080, T-083]
touches:
  - scripts/openup-agent-bench.py
  - scripts/tests/test_openup_agent_bench.py
  - docs-eng-process/reference-driver-benchmark.md
  - docs/changes/
last-synced: ""
---

# T-084 — Archive each run's deliverable into the results dir

## Story

> **As** someone benchmarking the driver (e.g. across models)
> **I want** each run's produced deliverable (the `docs/vision.md` a run wrote) copied
> into the results dir as `run-NN.<basename>`
> **So that** I can read and compare the actual artifacts a batch scored **without
> `--keep`** — the whole point of a vision benchmark is *did it produce a good
> vision*, and today that file dies with the torn-down fixture.

## Context

The harness scores `deliverable_produced` (markers present) but discards the file.
The 20260713-154218 vision batch was 5/5 clean, yet the actual visions were
unreadable (fixtures removed). Copying the deliverable into `<out>/` per run closes
that — cheap, additive, no behavior change to scoring.

## Requirements

1. **Each run archives its deliverable.** When the scenario declares a
   `deliverable_file` and it exists in the fixture after the run, copy it to
   `<out>/run-NN.<basename>` (e.g. `run-01.vision.md`) before teardown; record the
   archived path in the run record (`deliverable_archived`).
   - **Given** a run that writes `docs/vision.md` **When** the batch finishes **Then**
     `<out>/run-01.vision.md` exists with that content and the record points at it.
   - **Given** a run that produced no deliverable **When** the batch finishes **Then**
     no archive file is written for it and `deliverable_archived` is null.

## Operations

- [x] In `openup-agent-bench.py`, after `measure_run` and before fixture teardown,
  copy `scenario['deliverable_file']` (if present in the fixture) to
  `<out>/run-NN.<basename>`; set `record['deliverable_archived']`. Extend the
  hermetic vision test to assert the archived vision exists. Note it in
  `reference-driver-benchmark.md`. Run driver+bench suites + fence.

## Verification

- After the vision test batch, `<out>/run-01.vision.md` exists and matches the
  produced vision; a no-deliverable run archives nothing.
- driver + bench tests green; `openup-fence.py check --base harness-optional` green.

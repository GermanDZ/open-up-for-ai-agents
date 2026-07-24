---
id: T-081
title: Benchmark harness surfaces the driver's failure reason (stderr capture)
status: done
priority: high
plan: docs/changes/archive/T-080/plan.md
depends-on: [T-080]
blocks: []
touches:
  - scripts/openup-agent-bench.py
  - scripts/tests/test_openup_agent_bench.py
  - docs/changes/
last-synced: ""
---

# T-081 — Benchmark harness surfaces the driver's failure reason

## Story

> **As** someone running the T-080 benchmark harness
> **I want** each non-`pass` run to record and surface the driver's failure reason
> (its `FATAL:` line + a stderr tail, and a full per-run driver log on disk)
> **So that** an endpoint/config error explains itself in `summary.md` /
> `results.jsonl` instead of forcing a manual side-run of the driver to see why —
> the gap hit on the first live batch (all runs `endpoint-error`, reason hidden).

## Context

The first live batch returned `endpoint-error` on every run, but the harness had
**captured the driver's stderr and thrown it away** — the reason (a transient
endpoint-not-ready) was invisible in the results. This closes that observability
gap: the harness already has `raw["stderr"]`; it just needs to keep a tail in the
record, pull out the `FATAL:` line, write the full driver log per run, and print
the reason on a non-pass outcome. Quick track — one script + its test, additive,
no behavior change to a passing run.

## Operations

- [x] Add `fatal` (the driver's FATAL line) + `stderr_tail` + `stdout_tail` to each
  run record in `measure_run`; write the full driver stdout/stderr to
  `<out>/run-NN.driver.log`; in `run_batch`, `_log` the `fatal`/stderr tail on any
  non-`pass` outcome. Extend the hermetic test to assert the fields on a forced
  endpoint-error (bad `LLM_API_URL`). Run the driver+bench suites + fence.

## Verification

- A run against an unreachable `LLM_API_URL` records `outcome=endpoint-error` with a
  non-empty `fatal`/`stderr_tail`, writes `run-01.driver.log`, and the reason is
  printed to the bench stderr.
- Existing bench + driver tests stay green; `openup-fence.py check --base
  harness-optional` green.

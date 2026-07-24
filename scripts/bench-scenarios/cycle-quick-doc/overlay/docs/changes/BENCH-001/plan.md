---
id: BENCH-001
title: "Bench scenario — append a line to the scratch note"
status: ready
priority: high
track: quick
touches:
  - docs/bench-scratch/
last-synced: ""
---

# BENCH-001 — reference-driver benchmark micro-task

A deterministic, single-step micro-task used by the reference-driver benchmark
harness (`scripts/openup-agent-bench.py`). It is intentionally trivial so that a
clean cycle is fence-clean by construction and cheap in tokens — the benchmark
measures whether the driver can *drive the process*, not solve a hard problem.

**The task:** append the exact line `bench ok` to `docs/bench-scratch/note.md`
(create the file and its directory if absent), then tick the Operations box below
and complete the lane on the `quick` track.

The only file this lane may change is under `docs/bench-scratch/` (its declared
`touches`), plus its own change folder and the lane-owned audit trails.

## Operations

- [ ] (developer) Append the line `bench ok` to `docs/bench-scratch/note.md`, creating the file and `docs/bench-scratch/` if they do not exist.

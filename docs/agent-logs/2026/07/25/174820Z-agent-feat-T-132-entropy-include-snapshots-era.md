---
type: agent-run-log
task: T-132
branch: feat/T-132-entropy-include-snapshots-era
phase: construction
started: 2026-07-25T17:48:20Z
ended: 2026-07-25T18:24:34Z
duration_seconds: 2174
---

# T-132 Construction Run — 2026-07-25T17:48:20Z

## Run Metadata

| Field | Value |
|-------|-------|
| **Task** | T-132 (entropy-include-snapshots-era) |
| **Branch** | feat/T-132-entropy-include-snapshots-era |
| **Phase** | construction |
| **Started** | 2026-07-25T17:48:20Z |
| **Ended** | 2026-07-25T18:24:34Z |
| **Duration** | 36 min 14 sec |

## Commits

- 96d9245
- 0a10a97
- 4e4977e
- f18c679

## Files Changed

- scripts/openup-entropy.py
- scripts/tests/test_openup_entropy.py
- scripts/process-manifest.txt
- docs-eng-process/script-cli-reference.md
- docs/changes/T-132/plan.md
- docs/changes/T-132/design.md
- docs/iteration-plans/t-132-entropy-include-snapshots-era-manifest.md
- docs/roadmap.md

## Key Decisions

### (1) Era Slicing: N Equal-Commit-Count Eras

The `--by-era N` option slices commit history into N equal-commit-count eras, matching the reference implementation's coupling_trend.py `--eras` parameter. This avoids explicit FROM:TO date ranges and aligns with Project B's baseline for trend reproducibility.

### (2) --snapshots Co-Located in openup-entropy.py

The `--snapshots` feature was implemented directly within openup-entropy.py rather than as a separate sibling script. Per the exploration disposition's directive, the three entropy measures are folded into a single analyzer, reducing surface area and improving maintainability.

### (3) F1 Acceptance Criterion: Formula-Parity Verification

The F1 criterion—reproduce Project B's p90 trend 382 → 315—is verified via formula-parity comparison against recorded values in docs/explorations/2026-07-25-agent-built-repo-decay.md. Live re-run was deferred because neither Project A nor Project B is reachable from this environment.

## Summary

Construction phase complete. All decision rationales documented in the change folder's design.md. Ready for completion workflow.

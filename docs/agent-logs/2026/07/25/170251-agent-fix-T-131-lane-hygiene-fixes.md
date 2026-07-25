# T-131: Lane-hygiene fixes — Agent Run Log

**Task ID:** T-131  
**Branch:** fix/T-131-lane-hygiene-fixes  
**Phase:** construction  
**Track:** standard  
**Status:** completed  

**Timing:**
- Start: 2026-07-25T16:49:07Z
- End: 2026-07-25T17:02:51Z
- Duration: 13m 44s

## Commits (chronological)

| Hash | Message |
|---|---|
| 1ff7ec5 | docs(T-131): promote lane — author spec, board-visible [T-131] |
| 460269e | docs(T-131): add missing touches: frontmatter to the task spec [T-131] |
| af57bf2 | chore(process): sweep run-log shards [T-131] [openup-skip] |
| 34be0c7 | fix(claims): scan lane-owned audit trees for used task ids (F2) [T-131] |
| 993035d | fix(fence): stamp base_sha at begin, fence prefers it over origin/main (F3) [T-131] |
| d3d08d6 | docs(T-131): fix touches: to include openup-state.schema.json + tick final box [T-131] |
| 976f1f2 | docs(T-131): implementation-vs-spec verification [T-131] |
| 51be98f | chore(process): sweep run-log shard [T-131] [openup-skip] |
| 1fb8336 | docs(T-131): status note + sync roadmap/project-status [T-131] |

## Files Changed

### Scripts (implementation & tests)
- `scripts/openup-claims.py`
- `scripts/openup-fence.py`
- `scripts/openup-session.py`
- `scripts/openup-state.py`
- `scripts/openup-state.schema.json`
- `scripts/tests/test_openup_claims.py`
- `scripts/tests/test_openup_fence.py`
- `scripts/tests/test_openup_session.py`

### Documentation & Process
- `docs-eng-process/script-cli-reference.md`
- `docs/changes/T-131/plan.md`
- `docs/changes/T-131/design.md`
- `docs/iteration-plans/t-131-lane-hygiene-id-scan-fence-base-sha.md`
- `docs/roadmap.md`
- `docs/project-status.md`
- `docs/status-notes/2026-07-25-T-131.md`

## Decisions

### F2: Audit-Tree Scan for Used Task IDs

**Decision:** Extend `used_seqs_in_repo()` with two additional scan sources rather than changing the reservation/locking protocol.

**Rationale:** The id-allocator's collision detection now scans:
1. Task IDs in `docs/agent-logs/runs/*.jsonl` (run-log shards)
2. Task IDs in filenames of `docs/status-notes/*.md` (completion notes)

This preserves backward compatibility and avoids introducing a reservation lock mechanism.

### F3: Base SHA Stamping in Fence

**Decision:** `openup-session.py begin` computes and stamps `base_sha` at call time; `openup-fence.py resolve_base` consults it as a primary fallback.

**Rationale:** The moment of `git rev-parse HEAD` at `begin` is authoritative because the branch/worktree is always created before `begin` runs. The stamp ensures the fence base is stable across the lane lifecycle. Resolution order in `resolve_base`:
1. Explicit `--base` argument (pre-existing contract)
2. Stamped `base_sha` from claim file / `.openup/state.json`
3. `origin/main` (remote default)
4. `main` (fallback)

## Summary

Lane-hygiene fixes resolved two critical collision-detection and fence-stability gaps:

- **F2** adds audit-tree scanning to catch task IDs already allocated in completion notes and run logs, preventing silent collisions during rapid iteration.
- **F3** establishes base-SHA stability by stamping it at branch creation time, eliminating fence drift from changing remote state.

Both fixes maintain backward compatibility and existing protocol contracts while closing detection and consistency gaps in the lane-management layer.

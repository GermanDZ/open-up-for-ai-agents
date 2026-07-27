# Agent Run — T-157

- **Branch**: `feat/T-157-sync-status-views-only`
- **Task**: T-157 — `sync-status.py --views-only`: regenerate the shared views without a live lane
- **Phase**: construction · **Iteration**: 108 · **Track**: standard (solo, no team)
- **Start**: 2026-07-27T17:47:51Z · **End**: 2026-07-27T18:03:07Z
- **Source**: iteration-103 retrospective action item **B1** (high)

## Commits

| SHA | Message |
|---|---|
| `5726680` | docs(T-157): promote lane — author spec, board-visible |
| `91793d8` | docs(T-157): add roadmap entry — B1 promoted to a lane |
| `cc7fbcf` | feat(sync-status): add state-free `--views-only` view recovery |
| `f0435dd` | docs(T-157): record completion verification — 9/9 requirements graded |

## Files Changed

- `scripts/sync-status.py` — `run_views_only()` + `--views-only` flag; early return before `read_state()`
- `scripts/tests/test_sync_status_notes.py` — `ViewsOnlyTests` (11 cases)
- `docs-eng-process/parallel-lanes.md` — conflict-recovery recipe split lane-live / completed
- `docs-eng-process/script-cli-reference.md` — `--views-only` signature + semantics
- `docs-eng-process/.claude-templates/CLAUDE.md` — the "If a PR conflicts in the views" rule
- `docs/changes/T-157/{plan,design}.md`, `docs/roadmap.md`, `docs/status-notes/2026-07-27-T-157.md`

## Decisions

1. **Scope drawn at "committed and lane-independent."** Regenerate `## Notes` (from the
   shards) and `## T-NNN:` section statuses (from archived folders); leave the header
   fields and roadmap table-row cells alone, because both need a live lane.
2. **Rejected `--state-dir docs/changes/T-NNN`** (DD1) — the folder is archived shortly
   after, and the run would write `gates.roadmap_synced` into an archived artifact.
3. **`Last Updated` / `Updated By` kept inside the no-go zone** (DD3) — arguable either
   way; chosen so requirement 4's invariant stays absolute rather than "nothing except
   these two".
4. **Scope grew by one file mid-lane** (DD5) — the agent-facing `CLAUDE.md` rule still
   named the broken command; spec updated *before* the edit (fix-spec-first).
5. **Historical records deliberately not swept** — several state the old recipe verbatim,
   but they are audit records of what was true when written.

## Verification

- Step 1a: **9/9 requirements ✅** graded against the diff (table in `design.md`).
- Step 1b: instrumentation ✅ — retrospective Measure Read-Back tables pre-exist in the
  named read-back environment (this repo). Read-back: second retrospective after landing,
  backstop 2026-09-30.
- Bite check: **9 of 11** new tests fail against `HEAD`'s script; the 2 that pass both
  ways are recorded with their reasons rather than counted as evidence.
- Full suite: **884 passed, 1 skipped, 20 subtests** (873 baseline + 11 new).
- Live check: 113/113 note shards restored, header `diff` empty.
- Fence ✅ (9 files in lane) · check-docs ✅ · check-docs --coverage ✅

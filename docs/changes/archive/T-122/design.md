# T-122 — design & completion notes

## Implementation-vs-spec grade (complete-task step 1a) — 2026-07-16

Graded against the actual diff (`git diff harness-optional...HEAD`) + working tree.

**Req 1 — B8: `docs/INDEX.md` is fenced as a derived view.**
- ✅ Given fresh-base INDEX.md regeneration → fence passes, not OUT OF LANE —
  `VIEW_PATHS` now includes `docs/INDEX.md` (`scripts/openup-fence.py:69`);
  `test_index_view_with_fresh_base_passes` green.
- ✅ Given a stale base → STALE VIEW (not OUT OF LANE); `--allow-views` overrides —
  `test_index_view_with_stale_base_is_stale_view_not_out_of_lane` +
  `test_index_view_allow_views_overrides_stale_base` green (the existing view
  branch covers INDEX with zero new branching).
- ✅ `openup-fence.py allowed` lists INDEX among `views` —
  `test_allowed_prints_resolved_allowlist` asserts `docs/INDEX.md` in `views`.

**Req 2 — B9: `roadmap_status()` reads prose `## T-NNN:` sections.**
- ✅ prose section → `"completed"` — `test_prose_section_status_resolved` (and
  `_pending_` variant) green; verified live against this repo's own prose roadmap
  (T-063/T-059/T-073 resolved).
- ✅ table row still resolved — `test_table_row_status_still_resolved` green
  (delegates to `openup-roadmap.py parse_roadmap`).
- ✅ missing id → `None` — `test_missing_id_returns_none` + `test_no_roadmap_returns_none`.
- ✅ archived dep vouched by a **prose** roadmap → satisfied (the T-009 path) —
  `test_archived_stale_but_PROSE_roadmap_completed_is_satisfied` green (preflight
  READY).
- ✅ bonus: exact-id match (no `T-1`↔`T-12` substring false-match) —
  `test_exact_id_match_not_substring`.

No ❌. All requirements satisfied by the diff and by green hermetic tests.

## Success-measure instrumentation (step 1b)

`## Success Measures` = **n/a (argued)** — internal process-gate correctness sweep;
the falsifiable check is the hermetic regression tests (each reproduces the pre-fix
failure and asserts the fix). No runtime metric/flag to instrument. Recorded per
step 1b.

## Notes

- Fixture correction: `_roadmap` test helper used a non-canonical `| Task | …`
  header; changed to the canonical `| ID | …` the shared `parse_roadmap` (and every
  real roadmap) requires. A "Task"-header table is not a valid roadmap for the
  canonical parser either, so this aligns the fixture with reality — not a
  workaround.
- No import cycle: `openup-roadmap.py` imports `openup-claims.py` at module load;
  `openup-claims.py` loads roadmap.py **lazily at call time** (cached), so both
  top-levels have run before either reaches across.

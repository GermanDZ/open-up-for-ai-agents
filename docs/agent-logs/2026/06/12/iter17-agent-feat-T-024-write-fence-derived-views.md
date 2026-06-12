# Agent Run — T-024 Write-fence + derived shared views

- **Task**: T-024 — Write-fence + derived shared views (parallel-PR conflicts in roadmap/status)
- **Branch**: claude/intelligent-curie-j3uce2
- **Phase**: construction · **Track**: standard · **Iteration**: 17
- **Date**: 2026-06-12
- **Seeded by**: docs/explorations/2026-06-12-multi-worktree-coordination.md

## What landed

- `scripts/openup-fence.py` — deterministic write-fence: a lane's committed diff
  must stay inside its claim `touches` (live claim first, T-009 D7) + change
  folder + lane-owned audit trees; the shared views pass only against a fresh
  trunk (`origin/main` ancestor of HEAD) or `--allow-views`. Imports
  `openup-claims.py` for parsing/path-match (agreement-by-construction).
  Exit 8 prints `OUT OF LANE:` / `STALE VIEW:` per file with remediation.
- `.githooks/pre-push` — same fence for humans; fires only when
  `.openup/state.json` exists; `SKIP_OPENUP_FENCE=1` escape hatch.
- `scripts/sync-status.py` — roadmap `completed` cells stamped
  `completed (YYYY-MM-DD)` idempotently; ID cells in link form
  (`[T-NNN](...)`) now match; `## Notes` of project-status assembled
  newest-first from sharded `docs/status-notes/*.md` (absent dir = untouched).
- `docs/status-notes/` — prior Notes entries migrated byte-exact, one file per
  entry; completions now write one lane-owned note file instead of prepending
  to the shared section.
- `/openup-complete-task` steps 3–4 — scribe hand-edits of the two views
  replaced by BLOCKING rebase + fence + one deterministic `sync-status.py` run.
- `CLAUDE.md` stay-in-your-lane critical rule; full model in
  `docs-eng-process/parallel-lanes.md`.

## Tests

- `scripts/tests/test_openup_fence.py` (15) + `test_sync_status_notes.py` (7)
  new, hermetic; `test_t006_hooks.py` SyncStatusTests updated (notes-dir
  isolation, dated-stamp regex). Touched-module suite green (58 tests).

## Decisions

- Views stay committed (browsable on GitHub) rather than gitignored like
  `board.json`; conflicts become mechanically resolvable (rebase + re-run)
  instead of impossible.
- Full "derive the roadmap tables from frontmatter" (exploration Option A)
  deliberately deferred; only the Status-cell write and Notes section became
  script-owned.

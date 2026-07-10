# T-067 — design & verification trail

## Root cause (why the rot happened)

`sync-status.py:update_roadmap()` matched only markdown **table rows**
(`row_re = ^\s*\|`). Roadmap entries authored by `/openup-plan-feature` are
free-form `## T-NNN:` sections whose status lives in a `**Status**:` line — never
a table cell. So section entries were updated only by hand. `git blame` confirms:
T-065's `completed` came from a manual commit (`7ae9b716`, "…+ section status");
T-063/T-064/T-066 were never hand-fixed and rotted (`pending`/`pending`/`ready`)
despite being merged + archived.

## Design decisions

- **DD1 — fallback, not replace.** `update_roadmap` returns in-loop on a table-row
  match (table path byte-identical); the section stamp is reached only when no row
  matched. Keeps the authoritative table path untouched (req 2).
- **DD2 — reconcile is state-free + derives from ground truth.** `--reconcile`
  sweeps `docs/changes/archive/<id>/` and stamps any non-completed matching
  section. Ground truth = archived folder, so it self-heals regardless of when the
  rot happened. Idempotent (writes only on change).
- **DD3 — archival date, not today.** Completion date = last git commit touching
  `docs/changes/archive/<id>` (`git log -1 --format=%cs`), fallback today. Keeps
  backfilled dates accurate (T-063 → 2026-07-06).
- **DD4 — doctor detects, sync-status fixes.** `openup-doctor` is read-only by
  contract; it invokes `sync-status.py --reconcile --dry-run` and turns each
  `DRIFT <id>` line into a `warning`, pointing at the fix. No logic duplicated;
  single source of truth for the drift set is `section_status_drift()`.

## 1a. Requirement grades (vs diff + live run)

- ✅ **R1** section fallback — `sync-status.py stamp_section_status()` + fallback in
  `update_roadmap`; test `test_section_fallback_stamps_status_line`.
- ✅ **R2** table path unchanged — in-loop `return`; test
  `test_table_row_path_unchanged_no_section_touched`.
- ✅ **R3** `--reconcile` idempotent — `reconcile_sections()` + CLI; test
  `test_reconcile_cli_writes_and_reports`; live: 2nd run `reconciled 0 section(s)`.
- ✅ **R4** doctor warning, no write — `check_section_status_drift()`; test
  `test_warning_finding_and_no_write`; live: 3 warnings before, 0 after, exit 0.
- ✅ **R5** live backfill dates — reconcile output: `T-063 (2026-07-06),
  T-064 (2026-07-10), T-066 (2026-07-10)`.

## 1b. Success-measure instrumentation

`n/a — internal tooling` (argued in spec `## Success Measures`). Falsifiable
proxy verified: doctor drift 0 after reconcile; suite green; reconcile idempotent.

## Test result

`scripts/tests/test_sync_status_sections.py` — 9/9 pass. Full `scripts/tests/`
suite: 340/341; the one failure (`test_docs_index … test_write_creates_index_file`)
is a pre-existing macOS `/var`↔`/private/var` realpath mismatch, unrelated to
T-067 (fails identically on clean `main`).

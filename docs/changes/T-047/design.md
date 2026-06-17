# T-047 — Design / Completion grade

## DD1 — migration logic extracted to a sourceable lib

`migrate_untrack_agent_runs` lives in `scripts/lib/migrate-data.sh` (sourced by
the sync, like `lib/install-process-clis.sh`) rather than inline in
`sync-from-framework.sh`, so it is unit-testable in isolation —
`test_sync_migration.py` sources just the function. The sync's call site keeps
the user-facing logging; the lib stays pure (no `log_*` dependency) so the test
needs no harness.

## DD2 — stage, never commit

The migration `git rm --cached`'s + appends to `.gitignore` but does not commit,
matching how the rest of the sync modifies files and leaves committing to the
user. Guarded on `git ls-files --error-unmatch`, so it is a silent no-op once
applied and on projects that never tracked the file.

## Completion grade (step 1a) — requirements vs diff

- ✅ **R1** idempotent untrack — `migrate_untrack_agent_runs` guards on
  `git ls-files`, appends to `.gitignore` (grep-guarded), `git rm --cached`'s;
  `test_tracked_file_is_untracked_and_ignored` (untracked + on disk + ignored
  once) and `test_already_untracked_is_clean_noop` (no change, rc 0) cover both
  scenarios.
- ✅ **R2** `--dry-run` — `dry=true` prints `[DRY RUN]` and returns before any
  mutation; `test_dry_run_changes_nothing` asserts the file stays tracked.
- ✅ **R3** no `.gitignore` dup — `grep -qxF` guard;
  `test_gitignore_not_duplicated` asserts a single entry.

No ❌. Full suite 254 tests; the lone failure
(`test_docs_index…test_write_creates_index_file`) is the pre-existing macOS
`/private/var` path assertion, unrelated (docs-index.py untouched).

## Success-Measure grade (step 1b)

`n/a` — internal tooling. R1's scenario is the mechanical, test-enforced check:
a formerly-tracking project no longer tracks `agent-runs.jsonl` after a sync.

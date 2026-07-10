# T-068 — design & verification trail

## Root cause

`auto-log-commit.py` derived the logged sha (`git rev-parse HEAD`) and the shard
path (`shard_path(cwd, …)`) from `payload.cwd`. OpenUP skills run `cd <worktree>
&& git commit`, but the harness cwd stays pinned to the **main** checkout, so a
worktree commit made the hook read **main's** HEAD and append a bogus `commit`
record into **main's** run shard. Evidence from the wild: the stray record read
`"branch":"main","sha":"d882a85"` (main's HEAD) while the real commit was on a
feature branch in the worktree. That uncommitted shard on main then blocked the
next `git pull` ("local changes would be overwritten"). Fires on every
worktree-based task → "pulls break all the time".

## Design decisions

- **DD1 — route by newest HEAD, not cwd.** `resolve_commit_root(cwd)` enumerates
  `git worktree list --porcelain` and returns the `(path, sha)` of the worktree
  whose HEAD has the max committer timestamp (`git show -s --format=%ct`). A
  freshly-made commit is always the newest, so this identifies the tree that just
  committed with **no command parsing** and **no cross-invocation state** — the
  approach chosen over `cd`-parsing (fragile) and symptom-only on-stop hardening.
- **DD2 — strict superset / fallback.** With ≤1 worktree (the plain repo) or any
  enumeration failure, it returns `(cwd, HEAD-of-cwd)` — byte-identical to today's
  behavior. In-place commits and non-worktree repos are unchanged.
- **DD3 — preserve every contract.** Record shape, idempotency guard, logs-only
  self-reference guard, and the exit-0/fail-open contract are untouched; only the
  cwd→root substitution changed. Shards stay **tracked** (no gitignore — T-046).
- **DD4 — sync, don't hand-edit `.claude/`.** Edited the canonical template and
  ran `sync-templates-to-claude.sh`; `.claude/` is byte-identical (check-claude-sync
  green).

## 1a. Requirement grades (vs diff + tests)

- ✅ **R1** commit root by newest HEAD ts — `resolve_commit_root` +
  `_worktree_heads`/`_committer_ts`; test `test_worktree_commit_logs_to_worktree_not_main`
  asserts `rec["sha"] == worktree HEAD` (not main's).
- ✅ **R2** main stays clean — same test asserts `shard_files(main) == []` and
  `git status` on main shows no `docs/agent-logs/runs` entry.
- ✅ **R3** no-worktree path unchanged — existing `test_appends_once_and_sets_gate`
  (single worktree → logs to cwd) still passes; fallback branch returns
  `(cwd, HEAD)`.
- ✅ **R4** idempotency + fail-open preserved — `test_idempotent_same_sha` passes;
  guard/try-except untouched.

## 1b. Success-measure instrumentation

`n/a — internal hook` (argued in spec). Falsifiable proxy verified in the new
test: worktree commit → worktree shard gains exactly one record; main checkout
run-shard set is empty.

## Test result

`test_t006_hooks.py::AutoLogCommitTests` — 10/10 pass (incl. new routing test and
the pre-existing commit-in-main worktree test, both green). Full `scripts/tests/`
suite: 341/342; the one failure (`test_docs_index…test_write_creates_index_file`)
is a pre-existing macOS `/var`↔`/private/var` realpath mismatch, unrelated to
T-068 (fails identically on clean `main`).

## Note on this session

The buggy hook (main's `.claude/`) is still the one firing during T-068's own
delivery, so this session's worktree commits keep polluting main's shards; the
fix takes effect for future sessions once merged and `.claude/` re-synced. Main's
stray shards are swept by on-stop / cleaned at end.

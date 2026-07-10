# T-069 — design & verification trail

## Root cause

`on-stop.py`, when only the exempt run-log shards are dirty, swept them into a
`chore(process): sweep run-log shards [openup-skip]` commit **on whatever branch
was checked out**. On a feature branch that's fine (the commit rides the PR or
dies with the branch). On **trunk** it created a local-only commit; once a PR
merged into `origin/main`, local `main` had diverged (1 local sweep commit vs
origin's merge) and `git pull` failed with "divergent branches". Observed this
session: `0d255c0 chore(process): sweep run-log shards [openup-skip]` on `main`
after PR #68 merged. Sibling of T-068.

## Design decisions

- **DD1 — guard the sweep on trunk only.** Resolve `get_trunk(cwd)` + current
  branch; when on `main`/`master`/detected default, skip the `git commit` and
  print a note. Feature-branch path is byte-identical. Trunk never gains a
  local-only commit over log noise → no divergence.
- **DD2 — leaving shards uncommitted on trunk is safe.** The shards are already
  in `EXEMPT_DIRTY_PREFIXES`, so the stop-blocker (section 1) doesn't block on
  them — stop proceeds with the shard left dirty. They can be `git clean`ed at
  will and never cause divergence.
- **DD3 — nothing else changes.** Dirty-block, exempt list, gate-block sections
  (2/3), `auto-log-commit.py`, and the T-046 tracked-shard model are untouched.
  `.claude/` synced from the template (check-claude-sync green).

## 1a. Requirement grades (vs diff + tests)

- ✅ **R1** trunk skips sweep-commit — guard in the sweep `else`; test
  `test_trunk_does_not_sweep_commit` asserts HEAD unchanged, exit 0, "On trunk"
  note, shard still dirty.
- ✅ **R2** feature-branch sweep preserved — test `test_feature_branch_still_sweeps`
  asserts HEAD advances + message `sweep run-log shards`; existing
  `test_exempt_log_dirty_does_not_block` (feature branch) still green.
- ✅ **R3** non-exempt dirty still blocks on trunk — existing
  `test_blocks_dirty_worktree` runs on `main` with a dirty non-exempt file →
  exit 2 (unchanged); the guard sits only in the exempt-only `else`.

## 1b. Success-measure instrumentation

`n/a — internal hook` (argued in spec). Falsifiable proxy verified: on `main`
with only a dirty shard, on-stop leaves HEAD unchanged (no sweep commit); on a
feature branch it still creates the sweep commit.

## Test result

`test_t006_hooks.py::OnStopTests` — 8/8 pass (2 new + 6 existing). Full
`scripts/tests/` suite: 343/344; the one failure
(`test_docs_index…test_write_creates_index_file`) is a pre-existing macOS
`/var`↔`/private/var` realpath mismatch, unrelated to T-069.

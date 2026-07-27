# T-140 — In-flight design decisions

## DD1. Why the roadmap's "stage-then-commit" direction was not built as written

The roadmap offered two directions: (1) stage-then-commit — write the shard
pre-commit so it lands in the triggering commit; (2) batch at session end.

**Direction 1 is not implementable.** The record contains the commit's SHA; the
SHA is a hash of the tree that would contain the record. A commit can therefore
never contain its own log record, and `--amend` invalidates the very SHA the
record just wrote. This is an information-theoretic constraint, not an
engineering difficulty.

What *is* implementable is staging the records of all **prior** commits. That
removes the dirty tree completely and leaves a steady-state lag of exactly one
record — the trailing record describing a lane's final commit.

## DD2. Queue + pre-commit drain, rather than flush-at-session-end

Chosen shape: `auto-log-commit.py` (PostToolUse) appends to an untracked queue;
`stage-run-log.py` (PreToolUse) drains it into the lane shard and `git add`s it
immediately before the next commit runs.

Rejected alternatives:
- **Flush at `openup-session.py end`** — still leaves a dirty tree at teardown,
  merely moving the sweep commit to the end of the lane.
- **Flush from `/openup-complete-task`** — a skill step can be skipped or
  reordered by a model; a hook cannot. The defect being fixed *was* a documented
  manual step that agents kept having to remember.

## DD3. Queue lives in the MAIN checkout, not the lane worktree

`<main-repo-root>/.openup/run-log-pending.jsonl`, resolved via
`git rev-parse --path-format=absolute --git-common-dir`. Two reasons: `/.openup/`
is already gitignored (so the queue can never dirty any tree), and
`/openup-complete-task` removes the lane worktree — a queue inside it would take
the trailing record with it.

## DD4. Pathspec-limited commits do not drain

`git commit -- <paths>` ignores everything else in the index, so staging a shard
for such a commit would leave it staged-but-uncommitted — precisely the dirty
tree this task removes. `commit_has_pathspec()` detects the case (handling
clustered short options like `-am`, `--opt=value`, and `--` separators) and the
drain no-ops; the records simply wait for the next unrestricted commit. Parsing
failures return `True` (skip), which is the safe direction.

## DD5. The fix goes live only after the merge + a sync on main

Verified live during this lane: `CLAUDE_PROJECT_DIR` resolves to the **main**
checkout, and hooks execute from its gitignored `.claude/scripts/hooks/`. The
worktree's own synced `.claude/` is not what the harness runs. So while this
branch is in flight the *old* hook is still firing — which is why this lane
contains one final legacy sweep commit (`chore(process): fold the final legacy
run-log sweep`).

Consequence for whoever merges: run `scripts/sync-templates-to-claude.sh` on
main after the merge, otherwise the new `stage-run-log.py` is never registered
and `auto-log-commit.py` keeps writing shards directly. This is normal for any
hook change in this repo (hooks live in the gitignored `.claude/`, synced from
the pack) and is why verification below drives the hooks with real payloads
rather than relying on harness registration.

## DD6. Verification approach

Because of DD5, end-to-end verification pipes realistic hook payloads straight
into the two hook scripts and asserts on the queue, the shard, and the git
index. `scripts/tests/test_openup_runlog.py` (26 tests) covers the drain logic
itself against real temporary git repos.

## Completion verification (step 1a) — graded against the diff

All eight requirements ✅. Evidence is a passing test or a line of the diff, not intent.

| # | Requirement | Verdict | Evidence |
|---|---|---|---|
| 1 | Successful commit never leaves `docs/agent-logs/` dirty | ✅ | `test_run_log_hooks.py::test_post_commit_hook_queues_without_dirtying_the_tree` asserts `dirty_logs(repo) == ""`; also asserted after the second commit in `test_pre_commit_hook_drains_stages_and_lands_inside_the_commit` |
| 2 | Record queued to untracked file, not the tracked shard | ✅ | same test: `queue_shas == [head]` and `shard_records == []`. Hook change at `auto-log-commit.py` `main()` — `queue_record(root, record)` replaced the `log_path.open("a")` write |
| 3 | Pending records drained into their own lane shard and staged before the next commit | ✅ | `test_pre_commit_hook_drains_stages_and_lands_inside_the_commit` asserts the shard record, `git diff --cached` containing it, and `docs/agent-logs/runs/` present in `git show --name-only HEAD` |
| 4 | Draining is idempotent, never duplicates | ✅ | `test_openup_runlog.py::test_flush_dedupes_a_sha_already_in_the_shard`, `::test_flush_dedupes_within_one_batch`, `test_run_log_hooks.py::test_sha_already_in_a_shard_is_not_requeued` |
| 5 | `log_written` gate keeps its meaning and timing | ✅ | `test_t006_hooks.py::test_appends_once_and_sets_gate` still asserts `gates.log_written == true` after the hook fires; the `set_gate` call site is unchanged in the diff |
| 6 | Every hook path fails open, never blocks a commit | ✅ | `test_run_log_hooks.py::test_hooks_fail_open_on_a_corrupt_queue` (parametrized over both hooks), `test_openup_runlog.py::test_every_subcommand_exits_zero_even_outside_a_git_repo`, `::test_flush_exits_zero_when_the_queue_is_unreadable` |
| 7 | Pathspec-limited commit leaves the queue untouched | ✅ | `test_run_log_hooks.py::test_pathspec_limited_commit_does_not_drain`; parser covered by 11 parametrized cases in `test_openup_runlog.py` |
| 8 | The three documents no longer prescribe the manual sweep | ✅ | `grep -rn "fold in any\|check for this delta and fold it in" docs-eng-process/ .claude/skills/` returns nothing; `conventions.md` §Pre-Commit Housekeeping rewritten, `openup-complete-task.md` step 2 rewritten, hook docstring rewritten |

Full suite after the change: **918 passed, 1 skipped, 0 failed**.

## Completion verification (step 1b) — Success-Measure instrumentation

✅ **instrumentation pre-exists; no emitter needed.** The measure is "commits per
lane whose entire diff is a `docs/agent-logs/` shard delta → 0", read via
`git log --oneline --name-only` (count commits whose file list is entirely under
`docs/agent-logs/`) and the direct post-commit check
`git status --porcelain -- docs/agent-logs/`. Both are plain git queries over
committed history — the instrument is the repository itself, so there is nothing
to add to the diff and nothing that can silently stop emitting.

**Read-back date: after the third lane completes post-merge** (expected within
days of this merge, given current lane cadence). The expectation is falsifiable:
if any lane after this one still produces a logs-only commit, the measure fails.

**Caveat recorded for the read-back (DD5):** the count only drops once
`scripts/sync-templates-to-claude.sh` has run on main after this merge, because
hooks execute from the main checkout's gitignored `.claude/`. A read-back taken
before that sync will show no change and must not be read as a failed measure.

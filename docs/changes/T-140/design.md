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

---
id: T-140
title: "auto-log-commit.py fires post-commit, forcing a follow-up sweep commit on every lane"
status: ready
priority: medium
estimate: 1 session
plan: ""
depends-on: []
blocks: []
last-synced: ""
touches:
  - scripts/openup-runlog.py
  - scripts/tests/test_openup_runlog.py
  - scripts/tests/test_run_log_hooks.py
  - docs-eng-process/.claude-templates/scripts/hooks/auto-log-commit.py
  - docs-eng-process/.claude-templates/scripts/hooks/stage-run-log.py
  - docs-eng-process/.claude-templates/settings.json.example
  - docs-eng-process/.claude-templates/skills/openup-complete-task/SKILL.md
  - docs-eng-process/procedures/openup-complete-task.md
  - docs-eng-process/conventions.md
  - .claude/settings.json
  - docs/roadmap.md
---

# T-140 — `auto-log-commit.py` fires post-commit, forcing a follow-up sweep commit on every lane

## Story

> **As an** agent or human reviewing a lane's history
> **I want** the run-log record for a commit to arrive without dirtying the working tree
> **So that** `git log` describes product change instead of bookkeeping, and no lane
> pays an extra commit whose entire content is "the log line about the previous commit".

INVEST check:
✅ Independent (no deps) · ✅ Negotiable (mechanism is a choice, outcome is not) ·
✅ Valuable (removes a per-lane commit + a documented manual workaround in three files) ·
✅ Estimable (two hooks + one script + tests) · ✅ Small (one session) ·
✅ Testable (post-commit `git status --porcelain -- docs/agent-logs/` must be empty).

## Analysis Context

- **Domain.** The run-log audit trail: the `PostToolUse`/Bash hook
  `auto-log-commit.py`, the lane-owned shards under `docs/agent-logs/runs/`, and the
  three places that document the resulting manual sweep
  (`docs-eng-process/conventions.md` §Pre-Commit Housekeeping,
  `openup-complete-task` step 2, and the hook's own docstring).
- **Scope boundaries.** Does NOT change the JSONL record schema, the shard naming
  (`<UTC-date>-<lane-key>.jsonl`), the `log_written` gate semantics, the
  `agent-runs.jsonl` derived-view consolidation (T-046), or the fence allowlist
  (that is T-147). Does NOT touch `on-stop.py` or the `roadmap_synced` gate.
- **Definition of done.** After any `git commit` made through the harness,
  `git status --porcelain -- docs/agent-logs/` is empty, and the record for every
  earlier commit in the lane is present, committed, in that lane's shard. The three
  documents that instruct a human/agent to sweep the delta no longer do.

**The load-bearing constraint (why the roadmap's direction 1 cannot be built as
written).** The record for a commit contains that commit's SHA. The SHA is a hash of
the tree containing the record. A commit therefore *can never* contain its own log
record — no amount of pre-staging fixes this, and `--amend` invalidates the SHA the
record just wrote. Literal "stage-then-commit" is not implementable. What *is*
implementable is staging the records of all **prior** commits, which removes the dirty
tree entirely and leaves a steady-state lag of exactly one record.

> **Assumption:** the fix is direction 2 (batch), refined — the hook appends to an
> **untracked pending file** and a new `PreToolUse`/Bash hook drains it into the
> tracked shards and `git add`s them immediately before each commit runs. Chosen over
> "flush only at `openup-session.py end`" because end-of-session flushing still leaves
> a dirty tree at teardown, and over "flush from `/openup-complete-task`" because a
> skill step can be skipped whereas a hook cannot. *(Vetoable at review.)*

> **Assumption:** the pending file lives at `<main-repo-root>/.openup/run-log-pending.jsonl`
> — `/.openup/` is already gitignored (so it can never dirty a tree), and the *main*
> root (not the task worktree's) is used so records survive worktree teardown at
> `/openup-complete-task`. Resolved via `git rev-parse --git-common-dir`. *(Vetoable at review.)*

> **Assumption:** a **pathspec-limited** commit (`git commit -- <paths>`, or `git commit <paths>`)
> does not drain — staging a shard into an index that the commit will then ignore would
> leave it staged-but-uncommitted, i.e. exactly the dirty tree this task removes. The
> pre-commit hook detects a pathspec and leaves the queue untouched for the next
> unrestricted commit. *(Vetoable at review.)*

> **Assumption:** the clean-tree invariant is scoped to a **successful** commit. If a
> commit fails after the drain has staged a shard (e.g. a validation hook rejects it),
> the shard stays modified until the next commit attempt drains and stages it again —
> a window in which the tree was already dirty from the failed commit's own content.
> No compensating rollback is built. *(Vetoable at review.)*

> **Assumption:** the trailing record — the one describing a lane's final commit — stays
> pending and is drained by the next commit made anywhere in the repo, landing in a later
> lane's shard (routed by the record's own `task_id`, so it lands in the *correct* shard,
> just in a later commit). The audit trail is complete but eventually-consistent by one
> record. Accepted rather than paying a sweep commit to close it. *(Vetoable at review.)*

## Requirements

1. A successful `git commit` never leaves `docs/agent-logs/` dirty.
   - **Given** an active lane with a committed spec, **When** the agent runs any
     successful `git commit` through the harness, **Then**
     `git status --porcelain -- docs/agent-logs/` prints nothing.

2. The record for a commit is appended to an untracked pending file, not to the
   tracked shard.
   - **Given** a successful non-logs-only commit at SHA `X`, **When**
     `auto-log-commit.py` runs, **Then** `<main>/.openup/run-log-pending.jsonl` gains
     exactly one line whose `sha` is `X`, and no file under `docs/agent-logs/runs/`
     is modified.

3. Pending records are drained into their own lane's shard and staged, immediately
   before the next commit is created.
   - **Given** `run-log-pending.jsonl` holds a record for task `T-A`, **When** a
     `git commit` command is about to run, **Then** the pre-commit hook appends that
     record to `docs/agent-logs/runs/<date>-T-A.jsonl`, `git add`s that path, empties
     the pending file, and the resulting commit contains the record.

4. Draining is idempotent and never duplicates a record already in the shard.
   - **Given** a shard whose last commit-event line already records SHA `X`, **When**
     a pending record for SHA `X` is drained, **Then** the shard is unchanged and the
     record is dropped from pending.

5. The `log_written` gate keeps its current meaning and timing.
   - **Given** an active lane with `log_written` false, **When** a non-logs-only
     commit is auto-logged, **Then** `gates.log_written` is `true` — as today, so
     `on-stop.py` and completion behave unchanged.

6. Every hook path stays fail-open and never blocks a commit.
   - **Given** a corrupt or unreadable pending file (bad JSON, no write permission),
     **When** a `git commit` runs, **Then** both hooks exit 0, the commit proceeds,
     and no exception surfaces to the user.

7. A pathspec-limited commit leaves the queue untouched rather than staging a shard the
   commit would ignore.
   - **Given** a non-empty pending queue, **When** the command about to run is
     `git commit -m "x" -- scripts/foo.py`, **Then** the pre-commit hook drains nothing,
     the pending file is unchanged, and no shard is staged.

8. The three documents prescribing the manual sweep no longer do.
   - **Given** the repo after this task, **When** a reader greps
     `docs-eng-process/conventions.md`, `docs-eng-process/procedures/openup-complete-task.md`,
     and the hook docstring for the sweep instruction, **Then** it is gone (or replaced
     by a one-line statement that the tree stays clean automatically).

## Behavior Delta

**Added** — behavior that did not exist before:
- A `PreToolUse`/Bash hook (`stage-run-log.py`) that drains + stages pending run-log
  records ahead of any `git commit`.
- `scripts/openup-runlog.py` — the drain mechanism, callable and unit-testable
  independently of the hook.

**Modified** — behavior that changes:
- Run-log append target — `docs-eng-process/.claude-templates/scripts/hooks/auto-log-commit.py`
  §main (writes to the untracked pending file instead of the tracked shard; the
  self-reference guard for logs-only commits becomes redundant but is kept as a
  cheap belt-and-braces).
- Pre-commit housekeeping instruction — `docs-eng-process/conventions.md`
  §"Pre-Commit Housekeeping: Sweep Hook-Appended Log Deltas".
- Completion step 2 — `docs-eng-process/procedures/openup-complete-task.md` §step 2
  (drops "fold in any `docs/agent-logs/` delta … it can only fire post-commit").

**Removed** — behavior that no longer holds:
- The per-lane sweep commit whose only content is a run-log shard delta — no Ring-1
  product artifact describes it; it was documented process behavior only (the two
  §sections cited above).

## Entities

- **auto-log-commit hook** (modified) — `docs-eng-process/.claude-templates/scripts/hooks/auto-log-commit.py`
- **stage-run-log hook** (new) — `docs-eng-process/.claude-templates/scripts/hooks/stage-run-log.py`
- **Run-log drain** (new) — `scripts/openup-runlog.py`
- **Pending file** (new, untracked) — `<main-repo-root>/.openup/run-log-pending.jsonl`
- **Lane shard** (read/write) — `docs/agent-logs/runs/<UTC-date>-<lane-key>.jsonl`
- **Shard key** (read-only) — `shard_key()` in the hook, mirroring `_shard_key` in `scripts/openup-state.py`
- **Hook wiring** (modified) — `.claude/settings.json` + `docs-eng-process/.claude-templates/settings.json.example`

## Approach

Split the write in two: *observing* a commit (post) and *persisting* the observation
(pre-next-commit). The `PostToolUse` hook keeps doing exactly what it does — resolve
the commit's worktree, SHA, task, branch — but appends the record to an untracked
pending queue in the main repo's gitignored `.openup/`, so a successful commit can
never dirty the tree. A new `PreToolUse`/Bash hook fires just before the *next*
`git commit`, drains the queue into each record's own lane shard (routing by the
record's `task_id`, deduping by SHA), and `git add`s the touched shards so the drained
records land inside that commit. The drain logic lives in `scripts/openup-runlog.py`
so it is unit-testable without a hook harness and reusable if a skill ever needs an
explicit flush. Both hooks stay fail-open.

## Structure

**Add:**
- `scripts/openup-runlog.py` — `append` (queue one record) + `flush` (drain → shards,
  dedupe by SHA, print staged paths); `--repo-root` / `--worktree` args, exit 0 always.
- `scripts/tests/test_openup_runlog.py` — pytest covering flush, dedupe, corrupt-line
  tolerance, multi-lane routing, empty/missing pending.
- `scripts/tests/test_run_log_hooks.py` — end-to-end pytest driving BOTH real hook
  scripts with realistic payloads against a throwaway git repo (added during
  implementation: the hooks themselves were otherwise untested).
- `docs-eng-process/.claude-templates/scripts/hooks/stage-run-log.py` — `PreToolUse`/Bash;
  matches the same `COMMIT_RE`, calls flush against the target worktree, `git add`s
  the shards, exits 0 unconditionally.

**Modify:**
- `docs-eng-process/.claude-templates/scripts/hooks/auto-log-commit.py` — append to the
  pending queue instead of the shard; resolve `<main-root>/.openup/` via
  `git rev-parse --git-common-dir`; update the docstring's tail-chase paragraph.
- `.claude/settings.json` + `docs-eng-process/.claude-templates/settings.json.example` —
  register `stage-run-log.py` under `PreToolUse`/Bash.
- `docs-eng-process/conventions.md` — replace §Pre-Commit Housekeeping with a one-liner
  stating the tree stays clean automatically.
- `docs-eng-process/procedures/openup-complete-task.md` — step 2 drops the fold-in
  instruction; re-render the mirror.
- `docs/roadmap.md` — status row for T-140.

**Do not touch:**
- `scripts/openup-fence.py` allowlist — that is T-147, a separate lane.
- `scripts/openup-state.py` `_shard_key` — the naming contract stays; only the writer moves.
- `.claude/scripts/hooks/*` — generated by `sync-templates-to-claude.sh`; edit the pack.
- `docs/agent-logs/agent-runs.jsonl` — a gitignored derived view (T-046), unaffected.

## Operations

- [x] Add `scripts/openup-runlog.py` with `append` + `flush`, resolving the pending
      path from `git rev-parse --git-common-dir` and routing each record to its own
      lane shard, deduping by SHA, and skipping entirely on a pathspec-limited commit.
- [x] Add `scripts/tests/test_openup_runlog.py` covering flush, SHA dedupe, corrupt
      lines, multi-lane routing, pathspec-limited skip, and missing/empty pending; run it green.
- [x] Rewrite `auto-log-commit.py` (pack copy) to append via the pending queue and
      update its docstring.
- [x] Add `stage-run-log.py` (pack copy) and register it under `PreToolUse`/Bash in
      both `.claude/settings.json` and `settings.json.example`.
- [x] Run `scripts/sync-templates-to-claude.sh` so the live `.claude/scripts/hooks/`
      copies match the pack.
- [x] Drop the sweep instruction from `docs-eng-process/conventions.md` and
      `docs-eng-process/procedures/openup-complete-task.md`, then re-render the mirror
      (`render-skills-mirror.py --write` + sync-templates).
- [x] (tester) Verify end to end in this lane: make a real commit, confirm
      `git status --porcelain -- docs/agent-logs/` is empty and the previous commit's
      record is inside the new commit.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, pre-commit housekeeping
- `docs-eng-process/parallel-lanes.md` — lane-owned audit trees + write-fence surfaces
- `.claude/CLAUDE.openup.md` — token-efficiency protocol, legal exits
- `docs-eng-process/state-file.md` — gate semantics (`log_written`)

## Safeguards

- **Fail-open, always.** Neither hook may block or slow a commit; every failure path
  exits 0 silently. A logging bug must never break a session.
- **No tracked-file write from a `PostToolUse` hook.** That is the defect; the fix is
  void if any post-commit path can touch `docs/agent-logs/`.
- **Schema frozen.** The JSONL record keys and shard filename convention are unchanged
  — `analyze-authoring-reliability.py` and the consolidation view read them.
- **Reversibility.** Revert the two hook files, un-register `stage-run-log.py`, and
  restore the two doc sections; any records left in the pending queue are plain JSONL
  and can be appended to their shards by hand.
- **Token / size budget.** `openup-runlog.py` ≤ ~150 lines; `stage-run-log.py` ≤ ~80.
- **No-go zones.** Fence allowlist (T-147), `_shard_key` contract, `on-stop.py` gates.

## Success Measures

We expect **the number of commits per lane whose entire diff is a `docs/agent-logs/`
shard delta** to move **from ≥1 per lane to 0** within **the next 3 lanes** after
release. Instrumentation: `git log --oneline --name-only` over the lanes following
this one, counting commits whose file list is entirely under `docs/agent-logs/`;
plus the direct check `git status --porcelain -- docs/agent-logs/` immediately after
each commit. Read-back: after the third lane completes post-merge.

## Rollout

**Flagged? No.** These are `settings.json`-registered hooks read fresh at each
invocation — the kill switch is removing the `PreToolUse` entry, which is already
cheaper and faster than any flag read, and the change is invisible to end users
(internal tooling, no user-facing surface). Backout is the revert described under
Safeguards. Not user-facing: `n/a` for environment defaults and in-flight-user
behavior — no user state exists to strand.

## Verification

- `python3 -m pytest scripts/tests/test_openup_runlog.py -q` passes.
- `python3 scripts/check-docs.py` passes (spec frontmatter + trace web).
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-140/plan.md` exits 0.
- Live check in this lane: after a commit, `git status --porcelain -- docs/agent-logs/`
  is empty and `git show --name-only HEAD` lists the shard carrying the *previous*
  commit's record.
- `grep -rn "fold in any" docs-eng-process/` returns nothing.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

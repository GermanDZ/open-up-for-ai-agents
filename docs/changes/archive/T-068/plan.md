---
id: T-068
title: auto-log-commit logs to the worktree that received the commit (not the pinned harness cwd)
status: done
priority: high   # critical | high | medium | low
estimate: 1 session
plan: ""
depends-on: []
blocks: []
touches:
  - docs-eng-process/.claude-templates/scripts/hooks/
  - .claude/scripts/hooks/
  - scripts/tests/
  - docs/changes/
  - docs/roadmap.md
last-synced: ""
---

# T-068 — auto-log-commit follows the commit to its worktree

## Story

> **As a** developer running OpenUP's worktree-per-task flow
> **I want** the `auto-log-commit` hook to append its run-log record into the
> worktree where the commit actually landed — not the harness cwd
> **So that** worktree commits stop dirtying the **main** checkout's run-log
> shards, which silently blocks the next `git pull` / merge on main.

INVEST — ✅ Independent · ✅ Negotiable · ✅ Valuable · ✅ Estimable · ✅ Small · ✅ Testable

## Analysis Context

- **Domain.** The `PostToolUse` hook `auto-log-commit.py` (canonical source
  `docs-eng-process/.claude-templates/scripts/hooks/`, synced to
  `.claude/scripts/hooks/`). It fires after every `git commit` Bash call and
  appends one `commit` JSONL record to the lane-owned run shard.
- **Root cause.** The hook derives everything from the **harness cwd**
  (`payload.cwd`): `git rev-parse HEAD` (line ~211) and `shard_path(cwd, …)`
  (line ~242). But OpenUP skills run `cd <worktree> && git commit`, and the
  harness cwd stays pinned to the **main repo**. So a worktree commit makes the
  hook read **main's** HEAD and append a bogus `commit` record into **main's**
  `docs/agent-logs/runs/*.jsonl`. Observed in the wild: the stray record read
  `"branch": "main", "sha": "d882a85"` (main's HEAD) while the real commit was on
  a feature branch in the worktree. That uncommitted shard on main then blocks
  the next `git pull` ("local changes would be overwritten").
- **Why now.** This fires on *every* worktree-based task (the default flow), so
  the main checkout accumulates stray shards continuously and pulls break "all
  the time". `on-stop.py` sweeps the tail only when the agent stops, so any
  pull/merge mid-session hits the dirt first.
- **Scope boundaries.** Does NOT change the record shape, the idempotency guard,
  the logs-only self-reference guard, the fail-open contract, or `on-stop.py`.
  Does NOT gitignore the shards (T-046 keeps them tracked as the audit source).
  Does NOT parse the Bash command string (chosen approach avoids `cd`-parsing).
- **Definition of done.** A commit made in a linked worktree is logged into that
  worktree's shard; the main checkout's tree stays clean. In-place commits (no
  linked worktree, or a real commit on main) behave exactly as before.

> **Assumption:** the worktree that just received the commit is the one whose
> HEAD has the **newest committer timestamp** (`%ct`) across all linked
> worktrees — a freshly-made commit is always the newest. This needs no command
> parsing and no cross-invocation state. *(Vetoable at review.)*

> **Assumption:** when `git worktree list` shows a single worktree (the common
> non-worktree repo) or enumeration fails, the hook falls back to today's
> behavior (cwd + its HEAD), so the change is a strict superset. *(Vetoable.)*

## Requirements

1. `auto-log-commit` resolves the **commit root** as the linked worktree whose
   HEAD has the newest committer timestamp, and reads the logged sha from that
   same worktree — not from `payload.cwd`.
   - **Given** a repo whose harness cwd is the main checkout and a commit just
     made in a linked worktree `W`, **When** the hook fires, **Then** the sha it
     logs equals `W`'s HEAD (not main's HEAD).
2. The `commit` record is written into the commit root's shard, leaving the main
   checkout's working tree clean.
   - **Given** the scenario in R1, **When** the hook completes, **Then** a new
     shard line exists under `W/docs/agent-logs/runs/` and
     `git status --porcelain` in the **main** checkout reports no run-shard
     change.
3. The no-worktree / in-place path is unchanged: a repo with a single worktree
   logs the commit to `cwd`'s shard exactly as before.
   - **Given** a plain repo (no linked worktrees) with a fresh commit, **When**
     the hook fires, **Then** the record lands in `cwd`'s shard with `cwd`'s HEAD
     sha.
4. Idempotency, the logs-only self-reference guard, and fail-open are preserved.
   - **Given** the hook fires twice for the same commit, **When** it runs the
     second time, **Then** no duplicate record is appended (idempotent), and any
     internal error still exits 0 (fail-open).

## Behavior Delta

Internal process-tooling / hook change; no Ring-1 (`docs/product/`) product
behavior is touched.

**Added** — none (no new surface).

**Modified**
- `auto-log-commit.py` — commit-root resolution now follows the commit to its
  worktree instead of trusting the pinned harness cwd. Hook internal; not a
  Ring-1 artifact.

**Removed** — n/a.

## Entities

- **`resolve_commit_root`** (new helper) — `…/hooks/auto-log-commit.py`
- **`main()` cwd usage** (modified) — same file
- **run shard** (write target) — `docs/agent-logs/runs/<date>-<lane>.jsonl`
- **hook test** (modified) — `scripts/tests/test_t006_hooks.py`

## Approach

Add a `resolve_commit_root(cwd)` helper that enumerates `git worktree list
--porcelain` (path + HEAD per worktree), and returns the `(root, sha)` of the
worktree whose HEAD has the max committer timestamp (`git show -s --format=%ct`).
With ≤1 worktree or on any enumeration failure it returns `(cwd, HEAD-of-cwd)` —
the current behavior. `main()` then uses that `root`/`sha` for the logs-only
guard, branch, state resolution, shard path, and gate flip. Everything else
(record shape, idempotency, fail-open) is untouched. Mirror the template edit
into `.claude/scripts/hooks/` via `sync-templates-to-claude.sh` so the
check-claude-sync guard stays green.

## Structure

**Modify:**
- `docs-eng-process/.claude-templates/scripts/hooks/auto-log-commit.py` —
  canonical source: add `resolve_commit_root`, rewire `main()`.
- `.claude/scripts/hooks/auto-log-commit.py` — synced copy (via the sync script,
  not hand-edited).
- `scripts/tests/test_t006_hooks.py` — worktree-routing test(s).
- `docs/roadmap.md` — status via generator.

**Do not touch:**
- `on-stop.py` — its exempt-and-sweep behavior is correct and complementary.
- Record schema / idempotency / self-reference / fail-open logic.
- The T-046 tracked-shard design (no gitignore).

## Operations

- [x] Add `resolve_commit_root(cwd)` + `_worktree_heads` / `_committer_ts`
      helpers to the template `auto-log-commit.py`; return `(cwd, HEAD)` on ≤1
      worktree or failure.
- [x] Rewire `main()` to use `(root, sha)` from the helper for the logs-only
      guard, branch, `resolve_state_root`, `shard_path`, and gate flip.
- [x] Run `scripts/sync-templates-to-claude.sh` so `.claude/` matches the
      template (check-claude-sync green).
- [x] (tester) Extend `scripts/tests/test_t006_hooks.py`: a linked-worktree
      commit logs to the worktree shard and leaves main clean (R1/R2); the
      no-worktree path still logs to cwd (R3); idempotency preserved (R4). Run
      the full `scripts/tests/` suite.
- [x] Backfill sanity: confirm `git status` in the main checkout stays clean
      across a simulated worktree commit in the test.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, process conventions.
- Existing `auto-log-commit.py` / `on-stop.py` idioms (`run`,
  `resolve_state_root`, shard helpers).
- `scripts/tests/test_t006_hooks.py` `TempRepo` harness.

## Safeguards

- **Token / size budget.** ~1 helper + a rewire in `main()`; no schema change.
- **Reversibility.** Pure hook-internal change; revert the commit to restore.
  Fail-open contract means a bug degrades to "no log", never a broken session.
- **No-go zones.** Record shape, idempotency guard, logs-only self-reference
  guard, and the exit-0-always / fail-open contract must all be preserved. The
  shards stay **tracked** (no gitignore). `.claude/` must equal the template
  (sync, don't hand-edit the live copy).
- **Determinism.** No cross-invocation state, no wall-clock branching in
  selection logic beyond reading commit timestamps that git already stamped.

## Success Measures

`n/a — internal hook tooling with no runtime user metric.` Falsifiable proxy: in
the new test, a worktree commit leaves the main checkout's `git status
--porcelain` empty of run-shard entries (was non-empty before the fix), and the
worktree shard gains exactly one record with the worktree's HEAD sha. Read-back:
next multi-worktree session — `git pull` on main after a merge should not be
blocked by stray shards.

## Rollout

`n/a — not user-facing.` Internal `PostToolUse` hook; ships by syncing
`.claude/` from the template. No flag — additive behavior, strict superset of the
current path (fallback preserves today's behavior), so a flag would add no
safety. Backout: revert the commit and re-sync `.claude/`.

## Verification

- `python3 scripts/tests/test_t006_hooks.py` (and the full `scripts/tests/`
  suite) pass, including the new worktree-routing cases.
- `diff .claude/scripts/hooks/auto-log-commit.py
  docs-eng-process/.claude-templates/scripts/hooks/auto-log-commit.py` is empty
  (sync green).
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-068/plan.md`
  exits 0.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

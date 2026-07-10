---
id: T-069
title: on-stop.py skips the run-log sweep-commit when HEAD is trunk (no divergence)
status: ready   # proposed → ready → in-progress → done → verified
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

# T-069 — on-stop must not sweep-commit run-log shards on trunk

## Story

> **As a** developer ending a Claude Code session on `main`
> **I want** `on-stop.py` to NOT create a run-log sweep-commit while HEAD is
> trunk
> **So that** local `main` never gains a commit that origin lacks — which
> diverges the branch and breaks the next `git pull` after a PR merges.

INVEST — ✅ Independent · ✅ Negotiable · ✅ Valuable · ✅ Estimable · ✅ Small · ✅ Testable

## Analysis Context

- **Domain.** The `Stop` hook `on-stop.py` (canonical source
  `docs-eng-process/.claude-templates/scripts/hooks/`, synced to
  `.claude/scripts/hooks/`).
- **Root cause.** When only the hook-managed run-log shards
  (`docs/agent-logs/runs/*.jsonl`, exempt from the dirty-block) are dirty,
  on-stop "sweeps" them into a `chore(process): sweep run-log shards
  [openup-skip]` commit so the tree ends clean. It does this on **whatever
  branch is checked out**. On a feature branch that's fine (the commit rides the
  PR or dies with the branch). On **trunk** it creates a local-only commit; the
  moment a PR merges into `origin/main`, local `main` has diverged (1 local
  sweep commit vs origin's merge) and `git pull` fails with "divergent
  branches". Observed this session: `0d255c0 chore(process): sweep run-log
  shards [openup-skip]` on `main` blocked the pull after PR #68 merged.
- **Why now.** Sibling of T-068 (worktree commits dirtying main). Shards get
  orphaned onto `main` easily — e.g. a quick-task in-place branch commit appends
  a shard, then `git checkout main` carries the untracked shard over, and on-stop
  sweeps it onto `main`. Every such session risks a divergence.
- **Scope boundaries.** Does NOT change the sweep behavior on **feature
  branches** (still sweeps → clean tree). Does NOT change the dirty-block, the
  exempt-prefix list, the gate checks, or the auto-log-commit hook. Does NOT
  delete or gitignore shards (T-046 keeps them tracked). Leaving shards
  uncommitted on trunk is acceptable — they are already exempt from the
  stop-blocker, so stop still proceeds.
- **Definition of done.** On trunk (`main`/`master`/origin default), on-stop
  does not run the sweep `git commit`; on a feature branch it still does. No
  divergence path remains through the sweep.

> **Assumption:** trunk is detected the same way on-stop already detects it —
> `get_trunk(cwd)` (origin HEAD symbolic-ref, falling back to a `main`/`master`
> local branch), plus the literal `main`/`master` names as a belt-and-suspenders.
> *(Vetoable at review.)*

## Requirements

1. When on-stop's only-exempt-shards-dirty branch is reached AND HEAD is trunk,
   it does NOT create the sweep commit; HEAD is unchanged and stop still exits 0.
   - **Given** a repo on `main` whose only dirty path is a
     `docs/agent-logs/runs/*.jsonl` shard, **When** on-stop runs, **Then** no new
     commit is created (HEAD unchanged) and the hook exits 0.
2. On a non-trunk feature branch, the existing sweep-commit behavior is
   preserved.
   - **Given** a repo on `feature/x` with only a dirty run-log shard, **When**
     on-stop runs, **Then** it creates the `chore(process): sweep run-log shards
     [openup-skip]` commit exactly as before.
3. The dirty-block for real (non-exempt) work is unchanged on every branch,
   including trunk.
   - **Given** a repo on `main` with a dirty non-exempt file (e.g. `src/x`),
     **When** on-stop runs, **Then** it still blocks stop (exit 2) naming that
     file.

## Behavior Delta

Internal Stop-hook change; no Ring-1 (`docs/product/`) product behavior is
touched.

**Added** — none.

**Modified**
- `on-stop.py` — the exempt-shard sweep now no-ops on trunk (guards the `git
  commit`). Hook internal; not a Ring-1 artifact.

**Removed** — n/a.

## Entities

- **on-stop sweep branch** (modified) — `…/hooks/on-stop.py`
- **`get_trunk`** (read-only reuse) — same file
- **run shard** (read-only input) — `docs/agent-logs/runs/*.jsonl`
- **hook test** (modified) — `scripts/tests/test_t006_hooks.py`

## Approach

In the `else` branch that currently runs the sweep `git commit`, first resolve
trunk (`get_trunk(cwd)`) and the current branch (`git rev-parse --abbrev-ref
HEAD`). If the current branch is trunk (`main`/`master`/detected default), skip
the commit and print a one-line note; otherwise run the existing sweep commit
unchanged. Mirror the template edit into `.claude/scripts/hooks/` via
`sync-templates-to-claude.sh`.

## Structure

**Modify:**
- `docs-eng-process/.claude-templates/scripts/hooks/on-stop.py` — trunk guard in
  the sweep branch.
- `.claude/scripts/hooks/on-stop.py` — synced copy (via the sync script).
- `scripts/tests/test_t006_hooks.py` — trunk-skip + feature-branch-still-sweeps
  tests.
- `docs/roadmap.md` — status via generator.

**Do not touch:**
- The dirty-block / exempt-prefix logic.
- The gate-block sections (2 and 3) of on-stop.
- `auto-log-commit.py` and the T-046 tracked-shard design.

## Operations

- [x] Add a trunk guard in on-stop's exempt-shard sweep branch: resolve
      `get_trunk` + current branch; skip the `git commit` (print a note) when on
      trunk, else sweep as before.
- [x] Run `scripts/sync-templates-to-claude.sh` so `.claude/` matches the
      template (check-claude-sync green).
- [x] (tester) Extend `scripts/tests/test_t006_hooks.py`: on `main` with only a
      dirty shard → no commit, HEAD unchanged, exit 0 (R1); on `feature/x` →
      sweep commit still created (R2); non-exempt dirty on `main` → still blocks
      (R3). Run the full `scripts/tests/` suite.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, process conventions.
- Existing `on-stop.py` idioms (`run`, `get_trunk`, exempt-prefix handling).
- `scripts/tests/test_t006_hooks.py` `TempRepo` harness.

## Safeguards

- **Token / size budget.** ~6-line guard + tests; no refactor.
- **Reversibility.** Pure hook-internal guard; revert the commit to restore.
  Fail-open contract of on-stop is preserved (guard only skips a commit).
- **No-go zones.** Feature-branch sweep behavior must be byte-identical. The
  dirty-block for real work must not weaken on any branch. Shards stay tracked
  (no gitignore). `.claude/` must equal the template (sync, don't hand-edit).
- **Residue.** Leaving shards uncommitted on trunk is intentional and safe
  (they are exempt from the stop-blocker); they never cause divergence and can be
  `git clean`ed at will.

## Success Measures

`n/a — internal hook tooling with no runtime user metric.` Falsifiable proxy: in
the new test, running on-stop on `main` with only a dirty run-log shard leaves
HEAD unchanged (no sweep commit), whereas on a feature branch it still creates
the sweep commit. Read-back: next session ending on `main` — a subsequent `git
pull` after a PR merge is not blocked by a divergent local sweep commit.

## Rollout

`n/a — not user-facing.` Internal `Stop` hook; ships by syncing `.claude/` from
the template. No flag — additive guard, strict superset (feature-branch path
unchanged). Backout: revert the commit and re-sync `.claude/`.

## Verification

- `python3 scripts/tests/test_t006_hooks.py` (and the full `scripts/tests/`
  suite) pass, including the new trunk-skip cases.
- `diff .claude/scripts/hooks/on-stop.py
  docs-eng-process/.claude-templates/scripts/hooks/on-stop.py` is empty.
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-069/plan.md`
  exits 0.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

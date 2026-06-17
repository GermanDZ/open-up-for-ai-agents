---
id: T-048
title: "Audit fixes: archived-plan status bump (false dep-block) + worktree-promote board-blindness"
status: ready   # proposed → ready → in-progress → done → verified
priority: high   # critical | high | medium | low
estimate: 1 session   # two related fixes + one-shot migration, single PR
plan: docs/roadmap.md#maintenance-standalone-fixes
depends-on: []
blocks: []
last-synced: ""
touches:
  - scripts/openup-claims.py
  - .claude/skills/openup-complete-task/
  - .claude/skills/openup-start-iteration/
  - docs/changes/T-048/
---

# T-048 — Audit fixes: false dep-block + worktree-promote board-blindness

Two framework defects surfaced while auditing the continue-loop sessions of a
downstream adopting project. Bundled into one PR-able maintenance lane.

## Story

> **As an** agent or human driving the OpenUP continue-loop across iterations
> **I want** a completed dependency to read as satisfied, and a freshly-promoted
>   lane to be visible repo-wide the moment it's started
> **So that** the board doesn't falsely block ready work and a promote can't leave
>   a lane stranded as uncommitted worktree files (forcing a recovery session).

INVEST check:
✅ Independent · ✅ Negotiable · ✅ Valuable · ✅ Estimable · ✅ Small (two scoped fixes) · ✅ Testable

## Analysis Context

- **Domain.** Dependency resolution (`scripts/openup-claims.py` `dep_satisfied`) and
  lane promotion/visibility (`/openup-start-iteration` + `scripts/openup-board.py`).
- **Bug A — false dep-block from stale archived status.** `dep_satisfied`
  (`scripts/openup-claims.py:233`) resolves a dependency via `find_task_plan`, which
  matches archived plans too. If a plan is found it **trusts that plan's `status:`**
  and only falls back to the roadmap (line 241) when *no* plan is found. A task
  completed via `/openup-complete-task` is `git mv`'d to `docs/changes/archive/` but
  its plan `status:` is **never bumped** off `in-progress` — so the archived plan
  reads `in-progress` forever and falsely blocks every downstream dependent even
  though the roadmap says `completed`. Observed in a downstream project: a completed
  dependency false-blocked its dependent's preflight, and a second already-completed
  task carried the same latent staleness.
- **Bug B — worktree-promote board-blindness.** A lane was promoted with its spec
  authored inside a git worktree but left **uncommitted**. `openup-board.py`
  `active_plans` reads the working tree, so the lane was invisible from trunk and from
  any other worktree/machine — a "botched promote" that cost a full recovery session
  (consolidate to trunk, retire worktree/branch/lease, double `--no-ff` merge). A
  freshly-promoted standard/full lane must never exist only as uncommitted worktree
  files.
- **Scope boundaries.** Does NOT redesign the claims/lease model, the worktree
  workflow, or the board schema. No change to what "satisfied" means (still
  done/verified).
- **Definition of done.** (A) Completing a task leaves its archived plan at a
  satisfied status, a one-shot migration repairs already-archived stale plans, and
  `dep_satisfied` no longer false-blocks on an archived dep the roadmap calls done.
  (B) `/openup-start-iteration` commits the spec + state at promote time so the lane
  is board-visible from a clean trunk checkout immediately.

> **Assumption:** the satisfied status written on archive is `verified` for a
> rubric-graded complete-task and `done` for a quick-track completion. *(Vetoable at review.)*
> **Assumption:** Bug B is fixed primarily in the promote/start path (commit-on-promote),
> not by teaching the board to read uncommitted worktrees. *(Vetoable at review.)*

## Requirements

1. `/openup-complete-task` sets the archived plan's `status:` to a satisfied enum
   value (`verified` rubric-graded, else `done`) as part of the archive step.
   - **Given** a task with `status: in-progress` whose change folder is being archived
     **When** `/openup-complete-task` runs its archive step
     **Then** the file at `docs/changes/archive/T-NNN/plan.md` has a satisfied
     `status:` (`done`/`verified`), committed with the completion commits.

2. `dep_satisfied` does not false-block when an archived dependency's plan is stale
   but the roadmap marks it satisfied (defense-in-depth for data already in repos).
   - **Given** an archived dep whose `plan.md` reads `in-progress` while the roadmap
     row reads `completed` **When** a downstream lane's preflight calls `dep_satisfied`
     **Then** it returns `(True, …)` (roadmap-satisfied / archive-folder presence wins
     for an archived plan) rather than `(False, "is in-progress")`.

3. A one-shot migration/validator repairs already-archived plans carrying a stale
   non-satisfied `status:`.
   - **Given** a repo where one or more `docs/changes/archive/T-NNN/plan.md` files
     read `in-progress` while their roadmap rows read completed **When** the migration
     runs **Then** each such archived plan is rewritten to a satisfied `status:` and
     the command reports which files it changed (idempotent: a second run changes zero).

4. `/openup-start-iteration` commits the authored spec + persisted state at promote
   time, so the lane is visible to `openup-board.py` from a clean trunk checkout and
   from other worktrees — never left only as uncommitted worktree files.
   - **Given** a pending roadmap task promoted via `/openup-start-iteration`
     **When** the start completes **Then** `git status` shows the spec + state
     committed (not dangling), and `openup-board.py` run from a fresh checkout of that
     branch lists the lane.

## Behavior Delta

Process/tooling change to OpenUP scripts + skills; no Ring-1 product (`docs/product/`)
behavior in this framework repo's own product sense.

**Added** — behavior that did not exist before:
- One-shot archived-plan status migration/validator (Req 3).
- Commit-on-promote step in `/openup-start-iteration` (Req 4).

**Modified** — behavior that changes (framework process artifacts, not Ring-1 use cases):
- `/openup-complete-task` archive step — now bumps archived plan `status:`
  (`.claude/skills/openup-complete-task/SKILL.md` §archive, ~line 330).
- `dep_satisfied` resolution order for archived plans
  (`scripts/openup-claims.py:233-246`).

**Removed** — n/a.

## Entities

- **`dep_satisfied`** (modified) — `scripts/openup-claims.py:233`
- **complete-task archive step** (modified) — `.claude/skills/openup-complete-task/SKILL.md` (~330)
- **start-iteration promote** (modified) — `.claude/skills/openup-start-iteration/SKILL.md`
- **archived-status migration** (new) — a `scripts/openup-*.py` subcommand or small script
- **archived plans** (read-only data, repaired by migration) — `docs/changes/archive/T-*/plan.md`

## Approach

Two independent fixes plus a backfill, in one lane. Fix Bug A at both ends: write a
satisfied status on archive (the source) and harden `dep_satisfied` to prefer the
roadmap / archive-folder signal over a stale archived plan body (defense for data
already out there), then a one-shot migration to repair existing stale archived plans.
Fix Bug B by making promotion durable: `/openup-start-iteration` commits the spec +
state once authored, so the lane's existence survives in git and is board-visible rather
than living only in an uncommitted worktree.

## Structure

**Add:**
- A migration command (prefer a subcommand on an existing `scripts/openup-*.py`, e.g.
  `openup-state.py migrate-archived-status`, or a dedicated tiny script) — Req 3.

**Modify:**
- `scripts/openup-claims.py` — `dep_satisfied`: for an archived-folder plan, let
  roadmap-satisfied / archive presence win over a stale plan-body status (Req 2).
- `.claude/skills/openup-complete-task/SKILL.md` — archive step bumps plan `status:` (Req 1).
- `.claude/skills/openup-start-iteration/SKILL.md` — commit spec + state on promote (Req 4).
- Mirror any skill edits into `docs-eng-process/.claude-templates/` if that is the
  shipped source (verify which tree is canonical before editing — sync-templates lineage).

**Do not touch:**
- `scripts/openup-board.py` lane classification — the board is correct; the inputs are wrong.
- Lease/claims reservation model — out of scope.
- `openup-knowledge-base/**`, `docs-eng-process/templates/**` (OpenUP read-only guardrail).

## Operations

- [ ] Bump archived plan `status:` to satisfied (`verified`/`done`) in the
      `/openup-complete-task` archive step; verify the bumped file is in the completion commit.
- [ ] Harden `dep_satisfied` (`scripts/openup-claims.py`) so an archived dep that is
      roadmap-satisfied is not false-blocked by a stale plan-body status; add a unit/CLI check.
- [ ] Add the one-shot migration command and run it to repair any stale archived
      plans; confirm idempotent (second run = zero changes).
- [ ] Add commit-on-promote to `/openup-start-iteration` so the spec + state land in a
      commit at promote time (lane board-visible from a clean checkout).
- [ ] Sync edited skills into `docs-eng-process/.claude-templates/` if that is the
      canonical shipped tree; run the template→.claude sync check.
- [ ] (tester) Reproduce both bugs against pre-fix state and confirm the fixes:
      archived-dep no longer false-blocks; a promoted lane shows in `openup-board.py`
      from a fresh checkout.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, process conventions.
- `.claude/CLAUDE.openup.md` — fix-spec-first, edit-artifacts-through-skill, legal exits.
- `docs-eng-process/parallel-lanes.md` — write-fence + derived-view rules.

## Safeguards

- **Token / size budget.** Two focused script/skill edits + one small migration;
  keep the migration ≤ ~80 lines.
- **Reversibility.** Migration is idempotent and reports changed files; revert is a git
  revert of the lane commit. The `dep_satisfied` change is additive (only flips
  false→true for genuinely-satisfied archived deps).
- **No-go zones.** Do not change what "satisfied" means (still done/verified). Do not
  edit OpenUP read-only trees. Do not weaken collision/lease safety.
- **Reference, don't restate** the template→.claude canonical-tree rule and the
  write-fence model (`parallel-lanes.md`).

## Verification

- Req 1: complete a scratch task; assert `docs/changes/archive/<id>/plan.md` `status:`
  is satisfied and committed.
- Req 2: unit/CLI check feeding a stale-archived-plan + completed-roadmap pair to
  `dep_satisfied` → `(True, …)`.
- Req 3: run migration on a repo with a stale archived plan → bumped; re-run → no changes.
- Req 4: promote a task via `/openup-start-iteration`; `git status` clean for the spec,
  `openup-board.py` lists the lane from a fresh checkout.
- Grade against `.claude/rubrics/task-spec-rubric.md` — all criteria ✅ or explicit gap.

## Success Measures

n/a — internal process/tooling fix. The honest success check is binary and covered by
Verification: zero false dep-blocks from archived plans, and zero "promoted lane invisible
to the board" recovery sessions. No metric instrumentation is warranted for a two-fix
maintenance lane; re-occurrence of either failure mode in a future session audit is the
read-back signal.

## Rollout

n/a — not user-facing. Changes are to OpenUP process scripts/skills, delivered to projects
through the existing template/manifest sync (no flag: the fixes are corrective and safe-on,
a flag would add no safety). The `dep_satisfied` change and the archive-status bump are
both backward-compatible (they only stop false-blocks); the one-shot migration is idempotent
and self-reporting, so no staged rollout or kill-switch is needed.

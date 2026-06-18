---
id: T-049
title: "Board surfaces 'elsewhere' lanes: committed-but-unmerged worktree lanes visible from trunk"
status: done
priority: high   # critical | high | medium | low
estimate: 1 session   # board change + skill skip-rule + tests, single PR
plan: docs/roadmap.md#maintenance-standalone-fixes
depends-on: []
blocks: []
last-synced: ""
touches:
  - scripts/openup-board.py
  - scripts/tests/test_openup_board.py
  - .claude/skills/openup-next/
  - docs-eng-process/.claude-templates/skills/openup-next/
  - docs/changes/T-049/
---

# T-049 — Board surfaces 'elsewhere' lanes (committed-but-unmerged worktree lanes)

Follow-on to T-048. T-048 fixed the *uncommitted* dangling-promote (Bug B); this
fixes the residual it leaves behind: a lane whose spec is committed on an
**unmerged branch** is invisible to `openup-board.py` run from the trunk, even
though its live lease is readable repo-wide.

## Story

> **As an** agent or human driving the OpenUP continue-loop from a trunk checkout
> **I want** a task that is being worked in another worktree (its spec committed
>   on an unmerged branch) to show up on the board as in-flight-elsewhere
> **So that** the board doesn't read "no lanes" and the loop doesn't waste a cycle
>   re-promoting a task that is already in progress, only "self-correcting" by
>   colliding in pre-flight.

INVEST check:
✅ Independent · ✅ Negotiable · ✅ Valuable · ✅ Estimable · ✅ Small (one script + one skill rule) · ✅ Testable

## Analysis Context

- **Domain.** Board lane derivation (`scripts/openup-board.py`) and the
  continue-loop's promote step (`/openup-next` §1c).
- **The defect.** `active_plans()` (`scripts/openup-board.py:73`) globs
  `docs/changes/*/plan.md` in the **current working tree** only; `build_board()`
  (`:249`) builds one lane per plan found there. A lane whose `plan.md` is
  committed on an **unmerged branch** is not on the trunk's tree, so from trunk
  it yields **zero lanes** — even though its lease lives at
  `<git-common-dir>/openup/claims/T-NNN.json`, which is shared across every
  worktree of the clone and is therefore readable from trunk. Verified live: with
  T-048's completion unmerged (PR #41), `openup-board.py top` run from trunk picks
  T-048 as a fresh `ready` lane because the trunk tree still carries its
  pre-completion folder; the symmetric case (a *new* lane authored only on a
  branch) yields "no active lanes" from trunk.
- **Two symptoms.** (1) *Board-blindness* — in-flight work is hidden from a trunk
  board. (2) *Re-promote trap* — `/openup-next` §1c then promotes the next pending
  roadmap task; if that is the same task already being worked elsewhere (its
  folder absent from trunk), the cycle authors a spec and only discovers the clash
  when `openup-claims.py preflight` collides on the live lease — a wasted cycle.
- **Why the lease is the right signal.** The lease is already "registered
  somewhere the trunk can see" (shared `--git-common-dir`); `collider_for()`
  (`:152`) already reads it for collision parity. The board simply never treats a
  lease as a *lane source*, only as decoration on a plan-derived lane.
- **Scope boundaries.** Does NOT teach the board to read uncommitted worktree
  trees (T-048 mandates commit-on-promote), does NOT add a cross-machine mechanism
  (T-044's `remote-check` owns the `origin` axis), does NOT change what
  pickable / satisfied mean, and does NOT touch the lease/claims model.
- **Definition of done.** A live lease with no local plan renders as a
  non-pickable `elsewhere` lane (carrying its branch + worktree); the loop's
  promote step skips a pending roadmap task that already holds a live lease; and
  promotion of genuinely independent pending work is unaffected.

> **Assumption:** the synthesized lane's state name is `elsewhere` (distinct from
> `in-progress`, which denotes a lane whose plan *is* local and leased). *(Vetoable at review.)*
> **Assumption:** an orphan lease whose `_corrupt` flag is set is NOT rendered as
> an `elsewhere` lane (it is already surfaced fail-closed as a collider); only
> well-formed orphan leases become lanes. *(Vetoable at review.)*

## Requirements

1. `openup-board.py` renders every live lease that has **no** plan-derived lane as
   a synthesized non-pickable lane with `state: "elsewhere"`, carrying the lease's
   `branch` and `worktree`.
   - **Given** a live claim `T-900.json` whose task has no `docs/changes/T-900/plan.md`
     in the current tree **When** `openup-board.py refresh` runs **Then** `lanes[]`
     contains a lane `{task: "T-900", state: "elsewhere", lease: {branch, worktree…}}`
     and that lane is not pickable (`top` never selects it).

2. An `elsewhere` lane preserves collision parity: a local ready lane whose
   `touches` overlap an orphan lease's `touches` still reads `colliding`, exactly
   as today (the orphan-lane addition must not change existing collision output).
   - **Given** a local ready lane `T-901` and an orphan lease `T-900` whose
     `touches` overlap `T-901`'s **When** the board is built **Then** `T-901.state`
     is `colliding` with `collides_with: "T-900"` (unchanged from pre-T-049 behavior).

3. `none_pickable_reason()` routes the loop's promote step correctly: when there
   are **no local plan-derived lanes** (only `elsewhere` lanes, or none), it
   returns a promote-eligible reason; when a local non-pickable lane exists, it
   returns the existing "no pickable lane (…)" stop reason.
   - **Given** a board whose only lanes are `elsewhere` **When** `top` finds
     nothing pickable **Then** the stderr reason marks promote-eligibility (no
     *local* lanes), so `/openup-next` §1c proceeds to consider pending roadmap work
     rather than stopping.
   - **Given** a board with one local `blocked` lane and zero `elsewhere` lanes
     **When** `top` finds nothing pickable **Then** the reason is the existing
     "no pickable lane (1 blocked)" stop message.

4. `/openup-next` §1c promote-selection skips a pending roadmap task that holds a
   live lease (surfaced as an `elsewhere`/`in-progress` lane), so the loop never
   re-promotes work already in flight; independent pending work is still promoted.
   The rule is mirrored into the canonical `docs-eng-process/.claude-templates/`
   copy.
   - **Given** task `T-900` in flight elsewhere (live lease, no local folder) and
     an independent pending roadmap task `T-902` **When** `/openup-next` reaches §1c
     **Then** it skips `T-900` (leased) and promotes `T-902`; with no independent
     pending task it stops cleanly instead of re-promoting `T-900`.

## Behavior Delta

Process/tooling change to OpenUP scripts + skills; no Ring-1 product
(`docs/product/`) behavior in this framework repo's own product sense.

**Added** — behavior that did not exist before (no prior Ring-1 artifact):
- Orphan-lease lanes (`state: "elsewhere"`) in `openup-board.py` output (Req 1).
- `/openup-next` §1c skip-leased-task rule (Req 4).

**Modified** — behavior that changes (framework process tooling, not Ring-1 use cases):
- `none_pickable_reason()` now distinguishes local vs elsewhere-only lanes
  (`scripts/openup-board.py:269`) — Req 3.

**Removed** — n/a.

## Entities

- **`build_board` / `active_plans`** (modified) — `scripts/openup-board.py:249,73`
- **`classify` / `STATE_RANK`** (modified) — `scripts/openup-board.py:212,~60` (add `elsewhere`)
- **`none_pickable_reason`** (modified) — `scripts/openup-board.py:269`
- **orphan-lease lane** (new, synthesized) — built from `claims.live_claims()` dicts
- **`/openup-next` §1c** (modified) — `.claude/skills/openup-next/SKILL.md` + template mirror

## Approach

Add a second lane source to `build_board`: after the plan-derived lanes, sweep the
live claims and synthesize a non-pickable `elsewhere` lane for any well-formed
lease whose task has no lane yet, reusing the lease's `branch`/`worktree`/`touches`
so collision parity (`collider_for`) is untouched. Make `none_pickable_reason`
count *local* plan-derived lanes separately so an elsewhere-only board still routes
the loop into its promote step. Close the re-promote trap in the consumer: teach
`/openup-next` §1c to skip a pending task that already holds a live lease.

## Structure

**Add:**
- Orphan-lease lane synthesis inside `build_board` (small helper, e.g.
  `orphan_lease_lanes(live, claimed_task_ids)`).

**Modify:**
- `scripts/openup-board.py` — `elsewhere` state in `classify`/`STATE_RANK`,
  orphan-lease lanes in `build_board`, local-vs-elsewhere split in
  `none_pickable_reason`.
- `scripts/tests/test_openup_board.py` — orphan-lease cases (Reqs 1–3).
- `.claude/skills/openup-next/SKILL.md` — §1c skip-leased-task rule (Req 4).
- `docs-eng-process/.claude-templates/skills/openup-next/SKILL.md` — same edit
  (canonical shipped tree; verify lineage before editing).

**Do not touch:**
- `is_pickable()` — already gates on `state == "ready"`, so `elsewhere` is
  non-pickable for free; no edit needed (tempting but redundant).
- `scripts/openup-claims.py` lease/collision model — the board reads it; the
  inputs are not wrong here.
- `docs-eng-process/templates/**`, `openup-knowledge-base/**` — OpenUP read-only.

## Operations

- [x] Add the `elsewhere` state to `STATE_RANK` and synthesize orphan-lease lanes
      in `build_board` (well-formed leases with no plan-derived lane; carry
      branch/worktree via the lease; non-pickable). Verified `top` never picks one.
      (`classify` untouched — orphan lanes set state directly; `is_pickable`
      already gates on `state == "ready"`.)
- [x] Split `none_pickable_reason` to count local plan-derived lanes vs
      elsewhere lanes; promote-eligible reason when no local lanes exist, the
      existing stop reason otherwise (empty-board message unchanged).
- [x] Added the §1c skip-leased-task rule + the `elsewhere` reason form to the
      canonical `docs-eng-process/.claude-templates/skills/openup-next/SKILL.md`
      (`.claude/` is gitignored — synced from the template tree).
- [x] (tester) Extended `scripts/tests/test_openup_board.py` with `OrphanLeaseTests`:
      elsewhere lane synthesized + non-pickable (Req 1), collision parity preserved
      (Req 2), reason routing both ways + empty-board unchanged + corrupt-lease
      skipped (Req 3). Full board suite green (23 tests); claims suite green (36).

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, process conventions.
- `.claude/CLAUDE.openup.md` — fix-spec-first, edit-artifacts-through-skill, legal exits.
- `docs-eng-process/parallel-lanes.md` — write-fence + derived-view rules.

## Safeguards

- **Token / size budget.** One focused script change (~30 LOC) + one skill rule +
  tests; keep the board helper ≤ ~25 lines.
- **Reversibility.** Purely additive to board output (a new lane class the loop
  never picks) + an additive skip-rule; revert is a git revert of the lane commit.
- **No-go zones.** Do not change `is_pickable`/`dep_satisfied`/collision semantics;
  do not read uncommitted worktree trees; do not weaken collision/lease safety.
- **Reference, don't restate** the canonical template→.claude rule and the
  board/preflight parity invariant (`parallel-lanes.md`).

## Verification

- Req 1: unit — synth a claims dir with a lease for `T-900` and no folder →
  `refresh` lists `state: "elsewhere"` with that branch/worktree; `top` exits 3.
- Req 2: unit — orphan lease whose touches overlap a local ready lane → that lane
  reads `colliding` (parity unchanged).
- Req 3: unit — elsewhere-only board → promote-eligible reason; local blocked lane
  → existing stop reason.
- Req 4: read the §1c diff (skill + template mirror agree); the skip-leased rule is
  stated as a mechanical selection filter, not prose scope.
- Grade against `.claude/rubrics/task-spec-rubric.md` — all criteria ✅ or explicit gap.

## Success Measures

n/a — internal process/tooling fix. The honest success check is binary and covered
by Verification: a trunk board run shows in-flight-elsewhere lanes instead of "no
lanes", and the loop stops re-promoting leased tasks. No metric instrumentation is
warranted for a one-script maintenance lane; re-occurrence of either failure mode
(board-blindness or re-promote collision) in a future session audit is the
read-back signal.

## Rollout

n/a — not user-facing. Delivered to projects through the existing template/manifest
sync (no flag: the change is corrective and safe-on — the new lane class is never
auto-picked, and the skip-rule only prevents a known-wasteful re-promote, so a flag
would add no safety). Backward-compatible: existing plan-derived lanes and the
collision output are unchanged; the only new output is a lane class the loop reads
but never claims.

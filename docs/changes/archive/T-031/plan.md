---
id: T-031
title: Task-ID allocation race in parallel lanes — reserve IDs through the claims mechanism
status: done   # proposed → ready → in-progress → done → verified
completed: 2026-06-12
priority: medium
estimate: 1 session
plan: ""   # standalone fix; roadmap Maintenance row, surfaced by the T-024→T-025…T-030 renumber
depends-on: []
blocks: []
touches:
  - scripts/openup-claims.py                                                  # reserve-id / next-id / release-id / list-ids
  - scripts/tests/test_openup_claims.py                                       # IdReservationTests (14 cases incl. the race)
  - docs-eng-process/.claude-templates/skills/openup-create-task-spec/SKILL.md  # step 1: reserve, don't scan
  - docs-eng-process/.claude-templates/skills/openup-plan-feature/SKILL.md      # step 2: reserve with --prefix
  - docs-eng-process/parallel-lanes.md                                        # the reservation model
  - docs/roadmap.md                                                           # T-031 row
claimed-by: null
claimed-at: null
worktree: null
last-synced: ""
---

# T-031 — Task-ID reservation through the claims mechanism

## Story

> **As a** maintainer running parallel planning lanes (agent sessions and humans)
> **I want** task IDs allocated atomically through the shared claims machinery instead of
> each lane scanning its own checkout for the highest ID
> **So that** two lanes planning concurrently — or one lane on a stale checkout — can never
> both allocate `T-{n+1}`, eliminating renumber-at-merge churn like the practice pack's
> T-024→T-025…T-030 shift.

INVEST check:
✅ Independent (extends `openup-claims.py`, changes no claim/fence/board behavior) ·
✅ Negotiable · ✅ Valuable (closes the one parallel-lane collision surface T-024 left) ·
✅ Estimable (1 script extension + 2 skill steps + docs) · ✅ Small · ✅ Testable
(hermetic CLI tests incl. a real concurrent-allocation race)

## Context

IDs are allocated at *planning* time, before any claim or fence runs. The T-024 write-fence
and T-009 surface claims police what a lane *writes*, but `create-task-spec` step 1 and
`plan-feature` step 2 both said "scan local files for the highest ID and add 1" — racy
against parallel lanes (both see the same max) and against stale checkouts (the max is
missing recently-merged IDs). Roadmap row T-031 named two candidate fixes; owner decision
2026-06-12: the claims mechanism (the fetch-fresh-trunk hard rule alone still loses the
simultaneous-allocation race).

## Behavior Delta

- **Added** — `openup-claims.py` subcommands `reserve-id`, `next-id`, `release-id`,
  `list-ids`: one reservation file per ID under `<claims-dir>/ids/`, created atomically
  (exclusive hard-link), candidate = `max(used ∪ reserved) + 1` where *used* unions
  change-folder frontmatter ids, `docs/roadmap.md` text, and `origin/main:docs/roadmap.md`
  when the ref exists. `--prefix`/`--pad` cover phase-iteration schemes (`C3-001`).
- **Modified** — `/openup-create-task-spec` step 1 (vs "scan for highest, allocate
  `T-{n+1}`"): reserve via the script; explicit `task_id` is pinned with
  `reserve-id --task-id` (refused if taken); abandoned planning releases the ID.
- **Modified** — `/openup-plan-feature` step 2 (vs "auto-detect by scanning roadmap"):
  reserve via the script with the phase-iteration `--prefix`.
- **Removed** — the scan-and-increment allocation rule from both skills (the scan
  survives *inside* the allocator, where it is unioned with reservations and trunk).

## Requirements

1. Concurrent reservations always yield distinct IDs.
   - **Given** N processes racing `reserve-id` from the same starting scan **When** they
     all complete **Then** every process exits 0 and the N printed IDs are pairwise
     distinct.
2. Allocation counts IDs that exist only in roadmap text or only on trunk.
   - **Given** a repo whose roadmap mentions T-007 with no change folder and whose highest
     frontmatter id is T-005 **When** `next-id` runs **Then** it prints `T-008`.
3. Reservations occupy their ID without expiring, and release is idempotent.
   - **Given** a live reservation for T-008 **When** another lane runs `reserve-id`
     **Then** it gets T-009; **Given** `release-id --task-id T-008` runs twice **When**
     a lane reserves again **Then** both releases exit 0 and the lane gets T-008.
4. An explicitly requested ID is refused when taken.
   - **Given** an ID already used in the repo or reserved by a different session **When**
     `reserve-id --task-id <id>` runs **Then** it exits 6 with the owner/usage named;
     **Given** the same session re-requests its own reservation **When** the command runs
     **Then** it exits 0 (idempotent).
5. ID reservations are invisible to the surface-claim machinery.
   - **Given** live ID reservations and no surface claims **When** `list` runs **Then**
     it prints an empty array (reservations live under `ids/`, outside the claim glob).

## Scope boundaries

- Does NOT change surface claims, pre-flight, the fence, or the board.
- Does NOT add cross-clone coordination: reservations share the git common dir, so they
  span worktrees of one clone — separate clones are covered only by the `origin/main`
  roadmap scan (same coverage the claims machinery itself has).
- Does NOT auto-release reservations at `/openup-complete-task`: a reservation whose ID
  landed on trunk is redundant by construction (the allocator's repo scan counts it), so
  no lifecycle hook is needed.

## Rollout

n/a — deterministic local tooling + skill-text change; no user-facing runtime surface,
nothing to flag. Backout is reverting the commit (old scan-and-increment text returns).

## Success Measures

We expect **zero task-ID collisions between parallel lanes** (renumber-at-merge events
like the T-024→T-025…T-030 shift) **from this change forward**. Instrumentation: roadmap
renumber callouts / merge commits mentioning ID renumbering. Read-back: next
retrospective after two or more lanes have planned concurrently.

## Operations

- [x] (developer) `reserve-id` / `next-id` / `release-id` / `list-ids` in
      `scripts/openup-claims.py` (atomic exclusive-create, union scan, prefix/pad)
- [x] (developer) `IdReservationTests` in `scripts/tests/test_openup_claims.py`,
      including the concurrent-race case
- [x] (analyst) `/openup-create-task-spec` step 1 rewritten to reserve-don't-scan
- [x] (analyst) `/openup-plan-feature` step 2 rewritten to reserve with `--prefix`
- [x] (analyst) reservation model documented in `docs-eng-process/parallel-lanes.md`
- [x] (tester) claims + fence + board + state suites green

## Verification

- `python3 -m unittest scripts.tests.test_openup_claims` — 31 tests green (17 existing
  claim tests untouched + 14 reservation tests).
- `python3 -m unittest scripts.tests.test_openup_fence scripts.tests.test_openup_board
  scripts.tests.test_openup_state` — 45 tests green (fence imports the modified module).
- `python3 scripts/openup-spec-scenarios.py check docs/changes/archive/T-031/plan.md` — exit 0.
- Live smoke against this repo: `next-id` printed `T-032` (sees roadmap-only T-031),
  `reserve-id --task-id T-024` refused with exit 6.

## Norms

- `docs-eng-process/parallel-lanes.md` — file classes, claims, fence
- `docs-eng-process/conventions.md`

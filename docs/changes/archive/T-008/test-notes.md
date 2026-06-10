# T-008 — Test Notes

## Self-verify: manual trace of `/openup-readiness` against live state (2026-06-11)

Traced the skill's rules (steps 1–5 in `readiness/SKILL.md`) by hand against the live
change folders + `docs/roadmap.md`.

### Step 1 — authoritative records parsed from `docs/changes/**/plan.md`

| id | status | depends-on | blocks | touches |
|---|---|---|---|---|
| T-001 (archive) | done | [] | [T-002] | — |
| T-002 (active) | deferred | [T-001] | [] | .claude/skills/openup-workflow/, docs-eng-process/templates/ |
| T-003 (archive) | done | [] | [] | — |
| T-007 (archive) | done | [] | [T-008] | — |
| T-008 (active) | in-progress | [T-007] | [T-009] | docs/changes/, .claude/skills/openup-workflow/, docs-eng-process/ |

Roadmap-only (rows with no change folder): T-009 (depends T-005, T-008), T-010 (depends
T-005, T-006), T-011 (depends T-005). T-004/T-005/T-006 are `completed` in the roadmap.

### Step 2/3 — classification

- T-001, T-003, T-007 → **DONE/VERIFIED** (status done).
- T-002 → **DEFERRED** (status deferred; never READY/BLOCKED).
- T-008 → **IN-PROGRESS** (status in-progress; dep T-007 is done, but in-progress tasks
  are bucketed by status, not re-evaluated for READY).
- No authoritative task is in `{proposed, ready, blocked}`, so READY and BLOCKED are both
  empty among authoritative tasks.

### Step 4 — collisions

Collision set = READY ∪ IN-PROGRESS = {T-008} (singleton). No pair to compare → no
overlap collision. T-002's `touches` overlaps T-008's, but T-002 is `deferred` and thus
NOT in the collision set, so it is correctly excluded. No non-null `claimed-by` anywhere.
→ no active collisions.

### Step 5 — generated report

```
# Readiness Report — 2026-06-11
Source of truth: docs/changes/**/plan.md frontmatter (authoritative).
Roadmap rows without a change folder are listed separately (human view, not authoritative).

## READY
(none)

## BLOCKED
(none)

## IN-PROGRESS
- T-008 — Coordination frontmatter + /openup-readiness DAG

## DONE / VERIFIED
3 task(s): T-001, T-003, T-007

## DEFERRED
- T-002 — /openup-sync-spec (defer-until: drift observed in practice after T-001 lands)

## ⚠ COLLISIONS
(none) — only T-008 is in the collision set; T-002 shares touches prefixes but is
deferred and therefore excluded.

## Roadmap-only (no change folder yet)
Human view from docs/roadmap.md — NOT authoritative frontmatter.
- T-009 — Worktree-per-task + lease claims        status=planned, depends-on=[T-005, T-008]  → BLOCKED on T-008 (in-progress, not done; T-005 ✅)
- T-010 — Graded tracks (quick/standard/full)      status=planned, depends-on=[T-005, T-006]  → READY (T-005 ✅, T-006 ✅)
- T-011 — Retro cadence trigger + create-handoff   status=planned, depends-on=[T-005]          → READY (T-005 ✅)
```

## Acceptance check (from spec / program plan)

> `/openup-readiness` lists READY/BLOCKED with dependency reasons.

| Spec expectation | Result | Match |
|---|---|---|
| T-008 reports as actionable in-progress task | IN-PROGRESS: T-008 | ✅ |
| T-009 BLOCKED on T-008 | Roadmap-only: T-009 BLOCKED on T-008 (in-progress) | ✅ |
| T-011 READY via T-005 ✅ | Roadmap-only: T-011 READY (T-005 ✅) | ✅ |
| T-002 deferred | DEFERRED: T-002 | ✅ |
| T-010 READY via T-005 ✅, T-006 ✅ | Roadmap-only: T-010 READY | ✅ |

All acceptance points match.

## Discrepancies / notes for the tester

1. **T-009/T-010/T-011 surface under "Roadmap-only", not READY/BLOCKED.** They have no
   change folder yet, so their status is sourced from the roadmap (non-authoritative) per
   the documented source-of-truth rule. This is by design — once they get a `plan.md`
   they move into the authoritative READY/BLOCKED buckets. The spec's acceptance text
   says "T-009 BLOCKED", "T-011 READY"; the dependency *reasoning* matches, it is just
   reported in the human-view section because the frontmatter doesn't exist yet.
2. **Collision exclusion of deferred tasks.** T-002 and T-008 both touch
   `.claude/skills/openup-workflow/`. They are NOT flagged because the collision set is
   READY ∪ IN-PROGRESS only; `deferred` is excluded. Tester should confirm this is the
   intended scope (it matches Design Decision #5 in plan.md — collisions are among READY
   and in-progress tasks).
3. Skill is read-only — no files were written by the trace; this report was produced by
   hand-execution of the documented rules.

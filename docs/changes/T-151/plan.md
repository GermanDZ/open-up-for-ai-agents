---
id: T-151
title: "One completion increments the retro-cadence counter twice; correct the false split-store finding"
status: ready
priority: high
estimate: 0.5 session
plan: ""
depends-on: []
blocks: []
last-synced: ""
touches:
  - docs-eng-process/procedures/openup-complete-task.md
  - docs-eng-process/.claude-templates/skills/openup-complete-task/SKILL.md
  - docs-eng-process/state-file.md
  - scripts/tests/test_t011_retro.py
  - docs/iteration-retrospectives/iteration-98-retrospective.md
  - docs/project-status.md
  - docs/roadmap.md
---

# T-151 — One completion increments the retro-cadence counter twice

## Story

> **As** the cadence gate that decides when a retrospective is due
> **I want** each completed task to advance the counter by exactly one
> **So that** "iterations since retro" means what it says, and the two long-open
> decisions about the gate's semantics can finally be answered against a number that
> is not inflated.

INVEST check:
✅ Independent · ✅ Negotiable · ✅ Valuable (the counter governs a real gate) ·
✅ Estimable (delete a skill step, add a test, record two decisions) · ✅ Small ·
✅ Testable (archive-then-complete moves the count by 1).

## Analysis Context

- **Domain.** The durable retro-cadence counter: `cmd_archive` in `scripts/openup-state.py`,
  `/openup-complete-task` step 7a, and the two carried decisions 9.1 and 77.2.
- **Scope boundaries.** Does NOT move the counter's storage location, change
  `read_retro_count`'s migration branch, alter the threshold (5), or change which tracks
  `/openup-start-iteration` hard-blocks. Does NOT touch `/openup-quick-task`.
- **Definition of done.** One completed task advances the counter by exactly 1 on every
  completion path; decisions 9.1 and 77.2 are recorded as citable choices; the false
  split-store finding published in the iteration-98 retrospective is corrected in place.

**Measured behaviour (isolated fixture, 2026-07-27).** Three questions, answered with
evidence rather than inference:

| # | Question | Result |
|---|---|---|
| Q1 | Does one completion increment once or twice? | **Twice.** `openup-state.py archive` prints `Retro cadence: 1` (0→1); `/openup-complete-task` step 7a then runs `retro increment` → 2 |
| Q2 | Does `reset` reach the store `get` reads? | **Yes.** After `reset`, authoritative store and `get` both read 0 |
| Q3 | Can a stale legacy `.openup/retro.json` override the authoritative file? | **No.** Legacy seeds only when the authoritative file is absent; once it exists the legacy value is ignored (verified: legacy rewritten to 4, `get` still returned 100) |

**The double-increment is a leftover, not a design conflict.** T-142 deliberately moved the
increment *into* `archive`, with the rationale recorded in the code: "Keeping the increment
here rather than in skill prose is what makes it universal — every completion path
(`/openup-complete-task` via `openup-session.py end`, and `/openup-quick-task`) already runs
archive, and a completion path added later inherits it." Step 7a of the skill was simply
never removed. **The fix is to delete the skill step, not to change the script** — the
script's placement is the correct design.

> **Assumption:** decision **9.1** (gate boundary) resolves as *keep `count >= threshold`*.
> The counter counts completions since the last retrospective, so reaching 5 means five
> tasks have completed and the sixth start is gated — which is the plain reading of
> "a retrospective every 5 tasks". No code change; the semantics get written down in
> `state-file.md` so the question stops recurring. *(Vetoable at review.)*

> **Assumption:** decision **77.2** (should `retro_due` apply outside `full`) resolves as
> *keep the hard block on `full` only*. This session is the evidence both ways: a long
> solo `standard` streak did outrun the cadence, but hard-blocking `standard` would have
> stopped ordinary delivery on a bookkeeping gate. The recorded decision is to keep the
> gate where it is and rely on the existing non-blocking reminder; revisit only if the
> cadence is outrun again *after* the counter is trustworthy. Recording "we chose the
> status quo, here is why" is what closes a 21-iteration-old item — leaving it unanswered
> is what kept it open. *(Vetoable at review.)*

> **Assumption:** the iteration-98 retrospective's action item A3 ("stores disagree,
> `reset` reaches only one") is **factually wrong** and is corrected in place rather than
> silently dropped — struck through with the measurement that disproves it, per the T-141
> disposition rules. The hand-zeroing of `.openup/retro.json` performed while closing that
> retrospective was unnecessary but harmless. *(Vetoable at review.)*

## Requirements

1. One completed task advances the durable counter by exactly one.
   - **Given** a counter at *n* and an active lane, **When** the lane completes through
     `/openup-complete-task`, **Then** the counter reads *n+1*, not *n+2*.

2. `/openup-complete-task` no longer issues its own `retro increment`.
   - **Given** the completion procedure, **When** step 7a is read, **Then** it documents
     that `archive` (inside `openup-session.py end`) owns the increment and issues no
     `retro increment` of its own.

3. `archive` remains the single increment site, so every completion path inherits it.
   - **Given** a lane completed via `/openup-quick-task` (which calls `archive` but never
     ran step 7a), **When** it finishes, **Then** the counter still advances by exactly one.

4. The gate-boundary semantics (9.1) are recorded.
   - **Given** `docs-eng-process/state-file.md`, **When** the retro-cadence section is
     read, **Then** it states that the counter counts completions since the last
     retrospective and the gate fires at `count >= 5`, with the boundary worked through.

5. The track-scope decision (77.2) is recorded.
   - **Given** the same section, **When** it is read, **Then** it states that the hard
     block applies to `full` starts only, why, and what would justify revisiting.

6. The false split-store finding is corrected where it was published.
   - **Given** the iteration-98 retrospective, `docs/project-status.md`, and the T-151
     roadmap entry, **When** each is read, **Then** the split-store claim is struck through
     or rewritten with the measurement that disproves it, and no document still asserts it.

## Behavior Delta

**Added** — behavior that did not exist before:
- Written-down semantics for the cadence boundary and its track scope.

**Modified** — behavior that changes:
- Completion increments once, not twice — `docs-eng-process/procedures/openup-complete-task.md`
  §"7a. Increment the Retro-Cadence Counter".
- Retro-cadence documentation — `docs-eng-process/state-file.md` §retro cadence.
- Published findings — `docs/iteration-retrospectives/iteration-98-retrospective.md`
  §"Action Items" (A3) and §"What to Improve", `docs/project-status.md` §Open Action Items,
  and the T-150..T-154 block of `docs/roadmap.md` (T-151's own entry).

**Removed** — behavior that no longer holds:
- The skill-issued `retro increment` at completion. No Ring-1 product artifact describes
  it; it is process prose superseded by T-142's script-side increment.

## Entities

- **Increment site** (read-only, must stay the only one) — `cmd_archive` in `scripts/openup-state.py`
- **Duplicate increment** (removed) — `/openup-complete-task` step 7a
- **Counter store** (read-only) — `<git-common-dir>/openup/retro.json`; legacy `.openup/retro.json` read only when absent
- **Cadence docs** (modified) — `docs-eng-process/state-file.md`
- **Retro tests** (modified) — `scripts/tests/test_t011_retro.py`
- **Published findings** (corrected) — iteration-98 retrospective, `project-status.md`, `roadmap.md`

## Approach

Delete the duplicate rather than reconcile it: T-142 already chose `archive` as the single
increment site precisely so no skill has to remember, and step 7a is a leftover from before
that choice. Removing it makes the counter correct on every path at once, including
`/openup-quick-task`, which never ran step 7a and has therefore been counting correctly all
along. Then close the two decisions the inflated counter was blocking by writing them down —
including the one whose answer is "keep the status quo", because an unrecorded decision is
indistinguishable from an unmade one, which is exactly why both sat open for 21 and 89
iterations. Finally, correct the split-store finding at each place it was published.

## Structure

**Modify:**
- `docs-eng-process/procedures/openup-complete-task.md` — step 7a stops issuing
  `retro increment`; states that `archive` owns it.
- `docs-eng-process/.claude-templates/skills/openup-complete-task/SKILL.md` — regenerated mirror.
- `docs-eng-process/state-file.md` — record decisions 9.1 and 77.2.
- `scripts/tests/test_t011_retro.py` — add the exactly-once regression.
- `docs/iteration-retrospectives/iteration-98-retrospective.md` — strike/correct A3.
- `docs/project-status.md` — correct the A3 line.
- `docs/roadmap.md` — rewrite T-151's entry to the measured diagnosis.

**Do not touch:**
- `scripts/openup-state.py` — `archive`'s increment is the correct design (T-142); the
  defect is the duplicate caller.
- The counter's storage location and migration branch — T-143, measured correct here.
- `/openup-start-iteration`'s hard-gate track scope — 77.2 resolves as no change.

## Operations

- [ ] Remove the `retro increment` call from step 7a of
      `docs-eng-process/procedures/openup-complete-task.md`, replacing it with a note that
      `archive` (via `openup-session.py end`) owns the increment; re-render the mirror.
- [ ] Add the exactly-once regression to `scripts/tests/test_t011_retro.py`: archive
      advances by 1, and a second archive-free completion path does not double-count.
- [ ] Record decisions 9.1 (boundary) and 77.2 (track scope) in
      `docs-eng-process/state-file.md`, each with its rationale and revisit condition.
- [ ] Correct the false split-store finding in the iteration-98 retrospective (strike A3
      with the disproving measurement), in `docs/project-status.md`, and in T-151's own
      roadmap entry.
- [ ] (tester) Verify end to end: run a completion in a throwaway fixture and confirm the
      counter advances by exactly 1; confirm `/openup-quick-task`'s path is unchanged.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, hook conventions
- `docs-eng-process/state-file.md` — gate + counter semantics
- `.claude/CLAUDE.openup.md` — legal exits, token-efficiency protocol
- `.claude/rubrics/` — T-141's disposition rules govern how a wrong finding is retired

## Safeguards

- **Exactly one increment site.** After this task `archive` must be the only place the
  durable counter advances; a second caller is the defect returning.
- **Never delete a published finding.** A3 was wrong; it is struck through with the
  measurement that disproves it, never removed — the struck row is what makes the error
  auditable (T-141 rule).
- **Over-counting was the safe direction, under-counting is not.** The existing code
  comment says so; the fix must not make a failed archive skip the increment.
- **Reversibility.** Restoring step 7a's command restores prior behaviour exactly.
- **No-go zones.** `scripts/openup-state.py`'s increment placement, the storage location,
  the threshold value.
- **Token / size budget.** Test additions ≤ ~60 lines.

## Success Measures

We expect **the drift between "tasks completed since the last retrospective" and the
counter's value** to move **from +1 per completion (100% over-count) to 0** within **the
next 3 completions**. Instrumentation: the new exactly-once regression in
`scripts/tests/test_t011_retro.py` (fails the suite if any completion path double-counts),
plus a direct read — `python3 scripts/openup-state.py retro get` compared against the count
of tasks archived since the last `retro reset`. Read-back: at the next retrospective, which
is itself the consumer of this number. Instrumentation lives in this repo, which is where
the read-back happens.

## Rollout

**Flagged? No.** The change is the removal of one command from a procedure document plus
documentation; there is no runtime path to toggle, and a flag would be more machinery than
the change itself. Backout is restoring the removed command. Not user-facing (internal
process tooling), so `n/a` for environment defaults and in-flight users.

## Verification

- `python3 -m pytest scripts/tests/test_t011_retro.py -q` passes, including the new
  exactly-once regression.
- `grep -n "retro increment" docs-eng-process/procedures/openup-complete-task.md` returns
  nothing.
- Fixture check: one completion advances `retro get` by exactly 1.
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-151/plan.md` exits 0.
- `python3 scripts/check-docs.py` exits 0; full suite green.
- No document still asserts the split-store claim:
  `grep -rn "stores disagree\|reaches only one" docs/` returns only struck-through text.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

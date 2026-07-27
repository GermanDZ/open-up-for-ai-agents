---
id: T-151
title: "Retro-cadence: record the two open gate decisions and correct two false findings"
status: ready
priority: high
estimate: 0.5 session
plan: ""
depends-on: []
blocks: []
last-synced: ""
touches:
  - docs-eng-process/state-file.md
  - docs/iteration-retrospectives/iteration-98-retrospective.md
  - docs/project-status.md
  - docs/roadmap.md
---

# T-151 — Retro-cadence: record the two open gate decisions, and correct two false findings

## Story

> **As** a reader of the iteration-98 retrospective and the roadmap
> **I want** the retro-cadence record to say what is actually true
> **So that** nobody builds a fix for a defect that is already fixed, and the two
> gate-semantics questions open since iterations 9 and 77 finally have citable answers.

INVEST check:
✅ Independent · ✅ Negotiable · ✅ Valuable (stops rework on a phantom defect; closes two
89-/21-iteration-old items) · ✅ Estimable (documentation + corrections) · ✅ Small ·
✅ Testable (grep for the retracted claims; the decisions exist or they do not).

## Analysis Context

- **Domain.** The durable retro-cadence counter's *record* — `docs-eng-process/state-file.md`,
  the iteration-98 retrospective, `docs/project-status.md`, and T-151's roadmap entry.
- **Scope boundaries.** Writes **no code**. Does not change the counter, its storage, the
  threshold, or which tracks `/openup-start-iteration` blocks — all three were measured
  correct. Does not touch `/openup-complete-task` or `/openup-quick-task`.
- **Definition of done.** Decisions 9.1 and 77.2 are written down with rationale and a
  revisit condition; the two false findings are struck through in place with the evidence
  that disproves them; no document still asserts either.

**This task was specified on two wrong premises. Both are retracted here.**

| Claim (iteration-98 retrospective) | Measured reality | Verdict |
|---|---|---|
| **A2** — "`openup-session.py end` increments *and* `/openup-complete-task` step 7a increments again" | **Already fixed** by T-142 (commit `177ee42`, merged mid-session as PR #93). The pack's step 7a now reads *"Do **not** issue a separate `retro increment` here — that would double-count this lane."* Every occurrence of `retro increment` in the pack is a prohibition | **obsolete** |
| **A3** — "stores disagree; `reset` reaches only the shared one; `get` reads the other" | **Never true.** Measured in an isolated fixture: after `reset`, the authoritative store *and* `get` both read 0. The legacy `.openup/retro.json` is a deliberate one-time migration seed, read only when the authoritative file is absent — rewriting it to 4 left `get` reporting 100 | **wrong** |

**How the false observation arose — worth recording, because it will recur.** The
double-increment was real *in this session*: `/openup-complete-task` was invoked from a
`.claude/skills/` mirror rendered before PR #93 merged, and that stale copy still said
"run `retro increment`". The observation was accurate; the *diagnosis* ("the framework
double-counts") was not — the framework had already been fixed, and the lane was executing
a stale mirror. **A hook or skill change is only live after `sync-templates-to-claude.sh`
runs, so a mid-session merge leaves the running agent on the old copy** — the same class of
trap as T-140's DD5 and T-150's root cause.

T-142's test coverage already asserts everything T-151 originally proposed to add:
`test_archive_advances_cadence`, `test_failed_archive_does_not_advance_cadence`,
`test_archive_no_retro_suppresses_increment`, `test_default_location_is_git_common_dir`,
`test_two_worktrees_share_one_count`, `test_legacy_count_is_carried_forward_once`. Adding
more would be duplication, so this lane adds none.

> **Assumption:** decision **9.1** (gate boundary) resolves as *keep `count >= threshold`*.
> The counter counts completions since the last retrospective, so reaching 5 means five
> tasks completed and the sixth start is gated — the plain reading of "a retrospective
> every 5 tasks". No code change; the semantics are written down so the question stops
> recurring. *(Vetoable at review.)*

> **Assumption:** decision **77.2** (should `retro_due` block outside `full`) resolves as
> *keep the hard block on `full` only*. This session is evidence both ways: a long solo
> `standard` streak did outrun the cadence, but hard-blocking `standard` would halt
> ordinary delivery on a bookkeeping gate. Recorded as a decision with a revisit condition
> — revisit if the cadence is outrun again now that the counter is known-trustworthy.
> Recording "we chose the status quo, and why" is what closes the item; leaving it
> unanswered is what kept it open for 21 iterations. *(Vetoable at review.)*

## Requirements

1. Decision 9.1 (gate boundary) is recorded with its rationale.
   - **Given** `docs-eng-process/state-file.md`, **When** its retro-cadence section is read,
     **Then** it states that the counter counts completions since the last retrospective and
     the gate fires at `count >= 5`, with the boundary worked through explicitly.

2. Decision 77.2 (track scope) is recorded with a revisit condition.
   - **Given** the same section, **When** it is read, **Then** it states that the hard block
     applies to `full` starts only, why, and what would justify revisiting it.

3. The obsolete double-increment finding (A2) is retracted where it was published.
   - **Given** the iteration-98 retrospective, **When** action item A2 is read, **Then** it
     is struck through as obsolete, citing T-142 / commit `177ee42` as the fix that
     preceded it.

4. The false split-store finding (A3) is retracted where it was published.
   - **Given** the same retrospective, **When** action item A3 is read, **Then** it is
     struck through as **wrong** (not merely done), citing the measurement that disproves it.

5. No live document still asserts either retracted claim.
   - **Given** `docs/project-status.md` and `docs/roadmap.md`, **When** each is read,
     **Then** neither presents A2 or A3 as an open finding, and T-151's roadmap entry
     describes the corrected scope.

6. The stale-mirror trap that produced the false observation is recorded once, reusably.
   - **Given** `docs-eng-process/state-file.md` (or the conventions it links), **When** the
     retro-cadence section is read, **Then** it warns that a mid-session merge leaves the
     agent on a pre-sync skill mirror, so an observed "framework bug" may be a stale copy.

## Behavior Delta

**Added** — behavior that did not exist before:
- Written-down cadence-boundary and track-scope decisions, each with a revisit condition.
- A recorded warning about diagnosing from a pre-sync skill mirror.

**Modified** — behavior that changes:
- Cadence documentation — `docs-eng-process/state-file.md` §retro cadence.
- Published findings — `docs/iteration-retrospectives/iteration-98-retrospective.md`
  §"Action Items" (A2, A3) and §"What to Improve"; `docs/project-status.md` §Open Action
  Items; T-151's entry in `docs/roadmap.md`.

**Removed** — behavior that no longer holds:
- Nothing. This lane writes no code; the counter behaves exactly as it did before.

## Entities

- **Cadence docs** (modified) — `docs-eng-process/state-file.md`
- **Retrospective** (corrected) — `docs/iteration-retrospectives/iteration-98-retrospective.md`
- **Live action-item list** (corrected) — `docs/project-status.md`
- **Roadmap entry** (rewritten) — `docs/roadmap.md` §T-151
- **Counter + increment site** (read-only, unchanged) — `scripts/openup-state.py` `cmd_archive`
- **Existing coverage** (read-only, unchanged) — `scripts/tests/test_t011_retro.py`

## Approach

Write nothing that already works. Measurement showed the counter, its store, its migration
branch, and its single increment site are all correct, and T-142 already carries the tests
— so the code is untouched and the lane becomes a correction of record plus two decisions.
The two false findings are struck through *in the retrospective that published them*, with
the disproving evidence inline, per the T-141 rule that a wrong finding must stay auditable
rather than vanish. The decisions are written where the gate is documented, so the next
person to ask "should this fire at 4 or 5, and on which tracks?" finds an answer instead of
an open item.

## Structure

**Modify:**
- `docs-eng-process/state-file.md` — record decisions 9.1 and 77.2, and the stale-mirror warning.
- `docs/iteration-retrospectives/iteration-98-retrospective.md` — strike A2 (obsolete) and A3 (wrong).
- `docs/project-status.md` — drop A2/A3 from the live list, noting where they were retracted.
- `docs/roadmap.md` — rewrite T-151's entry to the corrected scope.

**Do not touch:**
- `scripts/openup-state.py` — measured correct; `archive` is rightly the single increment site.
- `scripts/tests/test_t011_retro.py` — T-142's coverage already asserts every property; more would duplicate.
- `docs-eng-process/procedures/openup-complete-task.md` — already carries the prohibition.
- `/openup-start-iteration`'s track scope — 77.2 resolves as no change.

## Operations

- [x] Record decisions 9.1 (boundary) and 77.2 (track scope) in `docs-eng-process/state-file.md`,
      each with rationale and an explicit revisit condition.
- [x] Record the stale-mirror diagnostic warning in the same section.
- [x] Strike A2 through as **obsolete** in the iteration-98 retrospective, citing T-142 /
      commit `177ee42`; strike A3 through as **wrong**, citing the fixture measurement.
- [x] Correct `docs/project-status.md` and T-151's `docs/roadmap.md` entry so neither
      presents a retracted claim as open.
- [x] (tester) Verify: `retro get` before/after a fixture completion moves by exactly 1;
      full retro suite green; no live document asserts a retracted claim.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, hook conventions
- `docs-eng-process/state-file.md` — gate + counter semantics
- `.claude/CLAUDE.openup.md` — legal exits, token-efficiency protocol
- `.claude/rubrics/` — T-141's disposition rules govern how a wrong finding is retired

## Safeguards

- **Never delete a published finding.** A2 and A3 are struck through with the evidence that
  retires them, never removed — the struck row is what makes the original error auditable
  (T-141 rule). A3 in particular must read **wrong**, not "done".
- **Write no code.** Every behaviour this task once proposed to change was measured correct;
  a code edit here would be change without cause.
- **Do not weaken the gate.** Recording "keep the status quo" must not become "remove the gate".
- **Reversibility.** Documentation-only; `git revert` restores the prior text exactly.
- **No-go zones.** The counter, its store, the threshold, T-142's tests, the completion procedures.
- **Token / size budget.** `state-file.md` additions ≤ ~40 lines.

## Success Measures



We expect **the number of open action items whose premise is false or already-fixed** to
move **from 2 to 0** within **this lane**, and **the number of carried "decide X" items about
cadence semantics** to move **from 2 to 0**. Instrumentation:
`grep -rn "stores disagree\|reaches only one\|double-increment" docs/` returns only
struck-through text, and `docs-eng-process/state-file.md` contains both decisions with
revisit conditions. Read-back: at the next retrospective, whose disposition pass consumes
exactly these rows. Instrumentation lives in this repo, which is where the read-back happens.

## Rollout

**Flagged? No.** The change is the removal of one command from a procedure document plus
documentation; there is no runtime path to toggle, and a flag would be more machinery than
the change itself. Backout is restoring the removed command. Not user-facing (internal
process tooling), so `n/a` for environment defaults and in-flight users.

## Verification

- `python3 -m pytest scripts/tests/test_t011_retro.py -q` passes (unchanged by this lane).
- Fixture check: one completion advances `retro get` by exactly **1**.
- `grep -rn "stores disagree\|reaches only one" docs/` returns only struck-through text.
- `docs-eng-process/state-file.md` states both decisions with revisit conditions.
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-151/plan.md` exits 0.
- `python3 scripts/check-docs.py` exits 0; full suite green.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

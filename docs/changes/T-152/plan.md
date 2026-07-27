---
id: T-152
title: "A success measure may name instrumentation that does not exist where it will be read back"
status: ready
priority: medium
estimate: 0.5 session
plan: ""
depends-on: []
blocks: []
last-synced: ""
touches:
  - .claude/rubrics/task-spec-rubric.md
  - docs-eng-process/.claude-templates/rubrics/task-spec-rubric.md
  - docs-eng-process/procedures/openup-create-task-spec.md
  - docs-eng-process/procedures/openup-complete-task.md
  - docs-eng-process/.claude-templates/skills/openup-create-task-spec/SKILL.md
  - docs-eng-process/.claude-templates/skills/openup-complete-task/SKILL.md
  - docs/roadmap.md
---

# T-152 — A success measure may name instrumentation that does not exist where it will be read back

## Story

> **As** the retrospective that has to read a success measure back
> **I want** every measure to name the environment it will be read in, and to have proven
> the instrument exists *there* at completion time
> **So that** a read-back returns a number instead of the discovery that nobody can produce one.

INVEST check:
✅ Independent · ✅ Negotiable · ✅ Valuable (one measure already died this way) ·
✅ Estimable (one rubric criterion + two procedure steps) · ✅ Small ·
✅ Testable (a spec naming no read-back environment is a rubric gap).

## Analysis Context

- **Domain.** The success-measure contract: rubric criterion 12, the authoring step in
  `/openup-create-task-spec`, and the verification gate at `/openup-complete-task` step 1b.
- **Scope boundaries.** Does NOT change what a measure must contain otherwise (direction,
  magnitude, window, read-back date), the `n/a` escape, the `quick`-track exemption, or
  rubric criterion 13. Writes no script — the gate is a graded judgment step, and inventing
  a parser for prose measures would be more machinery than the rule it enforces.
- **Definition of done.** A `standard`/`full` spec must name where its measure will be read
  back; step 1b must verify the instrument exists *in that environment*; and both the
  authoring skill and the rubric say so.

**The failure this comes from, verified.** T-052's success measure named
`.claude/memory/bypass-log.md` in two downstream repos. At read-back (due 2026-07-18,
checked 2026-07-27, nine days late) **neither repo has that file at all** — so `grep -c` → 0
cannot be distinguished from "not logging", and the measure is unanswerable. It had sat as a
carried action item for 88 iterations. The measure was not vague; it named a concrete
instrument. It simply named one that does not exist where the number had to come from.

**Why today's gate misses it.** Step 1b asks that the instrumentation "exists — in the diff
or demonstrably pre-existing", and criterion 12 calls it a gap only when "nothing in the
Structure/Operations actually creates or already provides" it. Both are evaluated **in the
framework repo**, which is where the completing agent is standing. A measure about
*downstream* behaviour passes that check while being unreadable at read-back time.

> **Assumption:** the fix is to make the **read-back environment** an explicit, named part
> of the measure, and to scope step 1b's existence check to that environment. Chosen over
> "forbid measures about downstream behaviour" (that would ban exactly the measures worth
> making for a distributed framework) and over "ship instrumentation downstream as part of
> every such task" (correct in principle, far beyond this task, and often impossible —
> the consumer decides what it tracks). *(Vetoable at review.)*

> **Assumption:** no validator script. Criterion 12 is graded prose; a parser for "does this
> sentence name an environment" would be brittle and would still need the human judgment it
> replaced. Enforcement stays the rubric + the blocking step 1b, consistent with how every
> other criterion works. *(Vetoable at review.)*

> **Assumption:** where the read-back environment is simply "this repo" — the common case —
> naming it is one short clause, not ceremony. The rule is *state it*, not *justify it*.
> *(Vetoable at review.)*

## Requirements

1. A success measure names the environment its read-back will happen in.
   - **Given** a `standard`/`full` spec whose `## Success Measures` names an instrument but
     no read-back environment, **When** it is graded against criterion 12, **Then** that
     criterion is ❌ with the missing environment named as the gap.

2. Criterion 12 treats an instrument absent from the read-back environment as a gap.
   - **Given** a measure whose instrument exists only in the framework repo while the
     expectation is about a downstream repo, **When** criterion 12 is applied, **Then** it
     is ❌ — "instrumentation that exists somewhere other than where the number must be read".

3. Completion verifies existence in the named environment, not merely somewhere.
   - **Given** step 1b and a measure naming a downstream read-back environment, **When** the
     instrument is demonstrable only in the framework repo, **Then** step 1b grades ❌ and
     blocks completion.

4. The authoring skill instructs the analyst to name the environment.
   - **Given** `/openup-create-task-spec`'s Success Measures guidance, **When** it is read,
     **Then** it requires the read-back environment alongside the instrumentation and
     read-back date, with the "this repo" case shown as a one-clause example.

5. The rubric's live copy and its template copy stay identical.
   - **Given** `.claude/rubrics/task-spec-rubric.md` and
     `docs-eng-process/.claude-templates/rubrics/task-spec-rubric.md`, **When** both are
     read after the change, **Then** they are byte-identical and `check-claude-sync.sh` passes.

6. The rule is illustrated by the case that produced it.
   - **Given** the updated criterion or step, **When** read, **Then** T-052's failure is
     cited concretely enough that a reader understands the gap without reconstructing it.

## Behavior Delta

**Added** — behavior that did not exist before:
- A named **read-back environment** as a required element of a success measure.

**Modified** — behavior that changes:
- Success-measure grading — `.claude/rubrics/task-spec-rubric.md` §"12. Success Measure
  Falsifiability" (and its template copy).
- Measure authoring — `docs-eng-process/procedures/openup-create-task-spec.md`
  §"For **Success Measures**".
- Completion gate — `docs-eng-process/procedures/openup-complete-task.md`
  §"1b. Verify Success-Measure Instrumentation".

**Removed** — behavior that no longer holds:
- Instrumentation passing the gate purely because it exists in the framework repo, when the
  expectation is about another environment. No Ring-1 product artifact describes it; it is
  process behavior defined by the rubric and step 1b.

## Entities

- **Rubric criterion 12** (modified) — `.claude/rubrics/task-spec-rubric.md` + template copy
- **Authoring guidance** (modified) — `docs-eng-process/procedures/openup-create-task-spec.md`
- **Completion gate** (modified) — `docs-eng-process/procedures/openup-complete-task.md` step 1b
- **Skill mirrors** (regenerated) — `docs-eng-process/.claude-templates/skills/*/SKILL.md`
- **Worked failure** (read-only) — T-052's measure; iteration-98 retrospective Measure Read-Back

## Approach

Add one element to the measure contract — *where the number will be read* — and scope the
existing existence check to it. That converts a check the completing agent could always
satisfy from where they stood into one that has to be satisfied where the number will
actually come from. The change lands in three places that must agree: the rubric that grades
the spec, the skill that authors the measure, and the completion step that verifies it.
No script: criterion 12 is graded prose like every other criterion, and the judgment being
added ("does this instrument exist over there?") is exactly the kind a parser cannot make.

## Structure

**Modify:**
- `.claude/rubrics/task-spec-rubric.md` — criterion 12 gains the read-back environment and
  the wrong-environment gap.
- `docs-eng-process/.claude-templates/rubrics/task-spec-rubric.md` — identical change.
- `docs-eng-process/procedures/openup-create-task-spec.md` — the Success Measures template
  gains the environment clause.
- `docs-eng-process/procedures/openup-complete-task.md` — step 1b checks existence in the
  named environment.
- Both affected `SKILL.md` mirrors — regenerated, not hand-edited.
- `docs/roadmap.md` — status row for T-152.

**Do not touch:**
- `scripts/openup-spec-scenarios.py` — it validates Given/When/Then scenarios, a different
  criterion; adding measure parsing there would conflate two contracts.
- Rubric criterion 13 (Rollout) — the analogous environment question there is already
  handled by `project-config.yaml` `environments:`.
- `/openup-quick-task` — the quick track is exempt from measures by design.

## Operations

- [ ] Update criterion 12 in `.claude/rubrics/task-spec-rubric.md`: require a named
      read-back environment; add "instrument exists somewhere other than the read-back
      environment" as an explicit gap, citing T-052.
- [ ] Apply the identical change to
      `docs-eng-process/.claude-templates/rubrics/task-spec-rubric.md` and confirm
      `check-claude-sync.sh` reports the two in sync.
- [ ] Update the Success Measures guidance in
      `docs-eng-process/procedures/openup-create-task-spec.md` to require the environment,
      with the "this repo" one-clause case shown.
- [ ] Update step 1b of `docs-eng-process/procedures/openup-complete-task.md` to verify
      existence **in the named environment**; re-render the mirrors and sync templates.
- [ ] (tester) Verify: grading an existing spec that names no environment yields ❌ on
      criterion 12; this task's own spec satisfies the new rule; sync + check-docs clean.

## Norms

Inherits from:
- `.claude/rubrics/task-spec-rubric.md` — the criterion set being amended
- `docs-eng-process/conventions.md` — commit format; edit the pack, never the mirror
- `.claude/CLAUDE.openup.md` — legal exits, token-efficiency protocol

## Safeguards

- **Do not weaken criterion 12.** Every element it already requires (direction, magnitude,
  window, instrumentation, read-back date) stays; this adds one.
- **Do not make `n/a` easier.** The escape keeps its existing bar — an argued reason that
  survives review.
- **Edit the pack, never the mirror.** `.claude-templates/skills/*/SKILL.md` is regenerated
  by `render-skills-mirror.py`; a hand-edit there is overwritten.
- **The rubric's two copies must stay identical** — `check-claude-sync.sh` enforces it.
- **Reversibility.** Prose-only; `git revert` restores the prior contract exactly.
- **Token / size budget.** Criterion 12 stays ≤ ~20 lines; step 1b ≤ ~25.

## Success Measures

We expect **the number of success measures that are unanswerable at read-back because their
instrument does not exist in the read-back environment** to move **from 1 (T-052, found
2026-07-27) to 0** across **every measure authored after this change, assessed at the next
two retrospectives**. Instrumentation: the **Measure Read-Back table** in each retrospective
(`/openup-retrospective` step 4b already produces it, with a `can't tell` verdict reserved
for exactly this failure) — a post-change measure appearing as `can't tell` for
"instrumentation missing" falsifies the expectation. **Read-back environment: this repo** —
the retrospectives are authored here, so the instrument and the reader are the same place.
Read-back: at the second retrospective after this lands.

## Rollout

**Flagged? No.** This changes a rubric and two procedure documents, which are read fresh
each time a skill runs; there is no runtime path a flag could gate, and backing out is a
revert. Not user-facing (authoring process), so `n/a` for environment defaults and
in-flight users — no user state exists to strand.

## Verification

- `bash scripts/check-claude-sync.sh` reports `.claude/` and the templates in sync.
- `python3 scripts/render-skills-mirror.py --check` reports the mirrors in sync with the pack.
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-152/plan.md` exits 0.
- `python3 scripts/check-docs.py` exits 0; full suite green.
- This spec's own `## Success Measures` names a read-back environment (it does — "this repo").
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅, criterion 12
  graded against its own new wording.

---
id: T-019
title: Behavior Delta section in the task spec (Added/Modified/Removed vs Ring 1)
status: done   # proposed → ready → in-progress → done → verified
completed: 2026-06-12
priority: high
estimate: 1 session
plan: docs/plans/2026-06-12-clarity-self-briefing-continue-loop.md#t-019-a-behavior-delta-section-in-the-task-spec
depends-on: [T-007]
blocks: [T-020, T-021]
touches:
  - docs-eng-process/templates/task-spec.md                          # new ## Behavior Delta section
  - .claude/skills/openup-create-task-spec/SKILL.md                  # authoring step + sync-spec consumer note (+ mirror)
  - .claude/rubrics/task-spec-rubric.md                             # new criterion 10 (+ mirror)
  - docs-eng-process/.claude-templates/skills/openup-create-task-spec/SKILL.md  # parity mirror
  - docs-eng-process/.claude-templates/rubrics/task-spec-rubric.md  # parity mirror
  - docs/roadmap.md                                                 # T-019 status
claimed-by: null
claimed-at: null
worktree: null
last-synced: ""
---

# T-019 — Behavior Delta section in the task spec

## Story

> **As a** reviewer (or `/openup-sync-spec`) reading a task spec before it lands
> **I want** the spec to declare which *existing* product behavior it Adds / Modifies / Removes, each change naming the Ring-1 artifact + section it touches
> **So that** a misread of current behavior is visible at review time and the exact set of Ring-1 artifacts needing a back-propagation update is explicit, not reconstructed.

INVEST check:
✅ Independent (only depends on T-007, done) · ✅ Negotiable (section shape is conventional) · ✅ Valuable (closes the "silent misunderstanding of existing behavior" gap) · ✅ Estimable (3 artifacts + 2 mirrors) · ✅ Small (additive doc/skill/rubric edits, no code) · ✅ Testable (grep + sync check + rubric re-grade)

## Analysis Context

State the *why* the spec needs but the code can't show:
- **Domain.** Spec-authoring machinery — the REASONS-Canvas task-spec template, its
  authoring skill, and its rubric. Same surface T-015 extended for the Ambiguity Gate.
- **Scope boundaries.** This task only *produces* the Behavior Delta data (a new template
  section + the convention to fill it). It does NOT wire `/openup-sync-spec` to mechanically
  parse the section, and does NOT retrofit Behavior Delta into already-archived specs.
- **Definition of done.** The template carries a `## Behavior Delta` section with
  Added/Modified/Removed groups and a greenfield clause; the authoring skill instructs the
  analyst to fill it and names sync-spec as the consumer; the rubric grades it as a new
  criterion; `.claude/` ↔ `.claude-templates/` parity holds (`check-claude-sync.sh` exit 0).

**Assumption:** The section is placed immediately **after `## Requirements`** (behavior
delta maps requirements onto existing Ring-1 product behavior, so it reads best adjacent to
them). *(Vetoable at review.)*

**Assumption:** `/openup-sync-spec` *consumption* of the Modified/Removed list is **deferred**
to a follow-up — T-019 delivers the section + convention only. The list is human- and
agent-readable as prose regardless. *(Vetoable at review.)*

**Assumption:** Entry format is a bold group label (**Added** / **Modified** / **Removed**)
with a bullet list; each Modified/Removed bullet ends with a backticked
`docs/product/...　§section` citation. *(Vetoable at review.)*

## Requirements

Numbered, testable assertions:
1. `docs-eng-process/templates/task-spec.md` contains a `## Behavior Delta` section,
   positioned after `## Requirements`, with three labelled groups: **Added**, **Modified**,
   **Removed**.
2. The section's guidance requires every **Modified** and **Removed** entry to cite a Ring-1
   artifact **and section** (e.g. `docs/product/use-cases/UC-3.md §main-flow`).
3. The section documents the greenfield rendering: a task with no pre-existing behavior
   writes `n/a — all Added`.
4. `.claude/skills/openup-create-task-spec/SKILL.md` instructs a role (analyst, Round 1) to
   fill Behavior Delta, and states that `/openup-sync-spec` consumes the Modified/Removed list.
5. `.claude/rubrics/task-spec-rubric.md` gains a tenth criterion ("Behavior Delta
   completeness") grading artifact+section citation and explicit greenfield marking; the
   rubric's "9 criteria" references are updated to 10.
6. `scripts/check-claude-sync.sh` exits 0 (skill + rubric mirrored to `.claude-templates/`).

## Behavior Delta

How this task changes **existing product behavior** (Ring 1: `docs/product/`).

**n/a — all Added.** T-019 changes process tooling (the task-spec template, its authoring
skill, and its rubric), not Ring-1 *product* behavior — no use case, vision, or architecture
statement changes. This entry is the first dog-fooding instance of the section it introduces.

## Entities

- **task-spec template** (modified) — `docs-eng-process/templates/task-spec.md`
- **create-task-spec skill** (modified) — `.claude/skills/openup-create-task-spec/SKILL.md` (+ `.claude-templates/` mirror)
- **task-spec rubric** (modified) — `.claude/rubrics/task-spec-rubric.md` (+ `.claude-templates/` mirror)
- **parity checker** (read-only) — `scripts/check-claude-sync.sh`
- **sync-spec skill** (read-only, out of scope) — `.claude/skills/openup-sync-spec/SKILL.md`

## Approach

Mirror the exact pattern T-015 used to add the Ambiguity Gate: a new template *convention*,
a skill *step* that fills it, and a rubric *criterion* that grades it. The Behavior Delta
section is declarative — three groups (Added / Modified / Removed) where Modified/Removed
each carry a `path §section` citation into Ring 1, and a greenfield escape hatch
(`n/a — all Added`). Skill and rubric live in `.claude/` and are mirrored to
`.claude-templates/` via the existing sync script; the template is a single canonical file.

## Structure

**Add:**
- (none — no new files)

**Modify:**
- `docs-eng-process/templates/task-spec.md` — new `## Behavior Delta` section after Requirements
- `.claude/skills/openup-create-task-spec/SKILL.md` — analyst authoring step + sync-spec consumer note
- `.claude/rubrics/task-spec-rubric.md` — criterion 10 + count updates
- `docs-eng-process/.claude-templates/skills/openup-create-task-spec/SKILL.md` — parity mirror
- `docs-eng-process/.claude-templates/rubrics/task-spec-rubric.md` — parity mirror
- `docs/roadmap.md` — T-019 row → ready, then done at complete-task

**Do not touch:**
- `.claude/skills/openup-sync-spec/SKILL.md` — wiring sync-spec to *parse* the section is
  deferred (tempting: the plan names sync-spec as the beneficiary, but consumption is a
  separate change).
- `docs/changes/archive/*/plan.md` — completed specs are not retrofitted with the section.

## Operations

- [x] Add `## Behavior Delta` to `docs-eng-process/templates/task-spec.md` immediately after
      `## Requirements`: Added / Modified / Removed groups, the `path §section` citation rule
      for Modified/Removed, and the `n/a — all Added` greenfield clause.
- [x] Add an authoring instruction to `.claude/skills/openup-create-task-spec/SKILL.md`
      (Round 1, analyst fills Behavior Delta) plus a one-line note that `/openup-sync-spec`
      consumes the Modified/Removed list.
- [x] Add rubric criterion 10 "Behavior Delta completeness" to
      `.claude/rubrics/task-spec-rubric.md` and bump the "9 criteria" references to 10.
- [x] Mirror the skill + rubric edits to `.claude-templates/` with
      `scripts/check-claude-sync.sh --fix-from-live`.
- [x] (tester) Run `scripts/check-claude-sync.sh` (must exit 0) and re-grade this spec
      against the updated 10-criterion rubric; confirm all ✅.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.)
- The existing task-spec template + rubric — the convention this task extends.

## Safeguards

- **Token / size budget.** Behavior Delta section ≤ ~25 lines in the template; rubric
  criterion ≤ ~12 lines. Additive only — no existing section is rewritten.
- **Reversibility.** Pure doc/skill/rubric edits; revert by deleting the section, the skill
  step, and the criterion. No code paths, no migrations.
- **No-go zones.** Do not change the semantics of existing template sections; do not wire
  sync-spec parsing; do not retrofit archived specs.
- **Parity invariant.** `scripts/check-claude-sync.sh` must exit 0 before complete-task.

## Verification

- `scripts/check-claude-sync.sh` exits 0.
- `grep -A3 '## Behavior Delta' docs-eng-process/templates/task-spec.md` shows the three
  groups and the greenfield clause.
- The rubric contains criterion 10 and the grading-instructions count reads 10.
- Re-grade this spec against the updated rubric — every criterion ✅ or an explicit gap.
- Grade the final artifact against `.claude/rubrics/task-spec-rubric.md`.

---
id: T-001
title: REASONS-style task spec — template, skill, rubric
status: done
priority: high
estimate: 1–2 sessions
plan: docs/plans/2026-04-28-spdd-ideas-worth-adopting-in-openup.md#1
depends-on: []
blocks: [T-002]
completed: 2026-04-28
---

# T-001 — REASONS-style task spec: template, skill, rubric

## Story

> **As an** OpenUP developer-role agent
> **I want** an executable per-task blueprint that lives between the use case
>   and the code
> **So that** I can generate implementation deterministically without
>   re-deriving design intent from coarse-grained artifacts.

INVEST check: ✅ Independent (only blocks T-002 sync-spec), ✅ Negotiable (slot
names can be tuned), ✅ Valuable (closes the gap SPDD identifies), ✅ Estimable
(1–2 sessions), ✅ Small (template + skill + rubric, doc-only), ✅ Testable
(rubric grades each generated spec).

## Analysis Context

**Domain.** OpenUP artifacts cascade from project (vision, use case) → iteration
(iteration plan, task list) → code. The middle layer between "task line in
roadmap" and "code" is currently implicit in the developer's head; SPDD's
REASONS Canvas formalises it.

**Scope boundaries.** This task creates the artifact format and the skill that
produces it. It does **not** retrofit existing tasks (those upgrade lazily as
they're picked up). It does **not** introduce a hook to enforce task-spec
existence (defer to a later iteration if pain is observed).

**Definition of done.**
- Template exists and is referenced from skills-guide.
- `/openup-create-task-spec` skill produces a spec that passes its rubric.
- Developer-role teammate brief instructs reading the task spec verbatim.
- One real task is migrated to the new format as a smoke test (use T-003).

## Requirements

1. A reusable template captures all eight REASONS Canvas sections plus
   front-matter (id, status, priority, plan link, dependencies).
2. A skill (`/openup-create-task-spec`) drives an analyst + architect handoff
   to produce a spec from a task line in the roadmap or iteration plan.
3. A rubric grades each generated spec across 8 criteria, in the same shape
   as existing rubrics (`.claude/rubrics/*-rubric.md`).
4. Norms and Safeguards sections **inherit by reference** from
   `docs-eng-process/conventions.md`, `docs/conventions.md`, and the
   architecture notebook — they do not re-state rules.
5. The developer teammate brief points at the task spec as the primary
   input for code generation.

## Entities

- **Task spec** (new artifact type) — `docs/tasks/T-XXX-*.md`
- **Task spec template** (new) — `docs-eng-process/templates/task-spec.md`
- **Task spec skill** (new) — `.claude/skills/openup-artifacts/openup-create-task-spec/SKILL.md`
- **Task spec rubric** (new) — `.claude/rubrics/task-spec-rubric.md`
- **Developer teammate** (modified) — `.claude/teammates/developer.md` and `developer-compact.md`
- **Skills guide** (modified) — `docs-eng-process/skills-guide.md`

## Approach

Mirror the existing artifact triad pattern (template + skill + rubric) so
the shape is familiar. Keep the template under 100 lines: each section is
~5 lines plus inline guidance. The skill orchestrates analyst (Requirements,
Entities) and architect (Approach, Structure, Safeguards) in one round, then
developer (Operations) in a second. Norms is a one-liner pointing at
conventions.

## Structure

**Add:**
- `docs-eng-process/templates/task-spec.md`
- `.claude/skills/openup-artifacts/openup-create-task-spec/SKILL.md`
- `.claude/rubrics/task-spec-rubric.md`

**Modify:**
- `.claude/teammates/developer.md` — add to "Key References" and "How You Work" step 1
- `.claude/teammates/developer-compact.md` — add to "Quick Process" step 1
- `docs-eng-process/skills-guide.md` — register the new skill
- `docs/tasks/README.md` — replace "until T-001 lands" note with link to template

**Do not touch:**
- Hooks (no enforcement layer in this task)
- Existing artifact templates / rubrics (no cross-cutting changes)

## Operations

1. Draft `task-spec.md` template using the section list in `docs/tasks/README.md`. Include front-matter schema, inline section prompts, and a worked-example footnote.
2. Draft `task-spec-rubric.md` with 8 criteria: front-matter completeness, story INVEST-fit, requirements testability, entities accuracy, approach clarity, structure scope-fit, operations testability, norms/safeguards inheritance correctness.
3. Draft `openup-create-task-spec/SKILL.md` orchestrating analyst→architect→developer rounds; produce file at `docs/tasks/T-XXX-{slug}.md` with status `ready`.
4. Update `developer.md` + `developer-compact.md` to read task spec as step 1 of code work.
5. Register skill in `docs-eng-process/skills-guide.md`.
6. Smoke test: run the skill on T-003 (suitability stars) and confirm the produced spec scores ✅ on every rubric criterion.
7. Update `docs/tasks/README.md` to link to the new template.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, branch naming, doc standards.
- All new files: front-matter style matches existing templates in
  `docs-eng-process/templates/` (see `iteration-plan.md`, `vision.md`).
- Skill file structure matches existing skills in `.claude/skills/openup-artifacts/`.

## Safeguards

- **Token budget.** Template must fit comfortably in a developer-agent's
  context alongside the use case + architecture notebook excerpt. Hard cap:
  template body ≤ 120 lines including comments.
- **No duplication.** Norms and Safeguards sections must NOT inline rules
  from `conventions.md` or the architecture notebook — only reference them.
  Rationale: silent drift is the failure mode SPDD warns against.
- **Backward-compatible.** Existing tasks without task specs continue to
  function; the developer teammate brief reads "if a task spec exists, …".
- **Process compliance.** Skill must obey the token-efficiency protocol
  in `.claude/CLAUDE.openup.md` (one orchestrator, compact handoffs).

## Verification

- Run `/openup-create-task-spec` on the T-003 task line; manually grade the
  output against `task-spec-rubric.md` — every criterion ✅.
- Re-read `developer.md` end-to-end; the new step does not contradict TDD or
  spec-first rules already present.
- Sanity: `docs-eng-process/templates/task-spec.md` ≤ 120 lines.

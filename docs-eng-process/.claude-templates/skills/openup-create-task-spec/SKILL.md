---
name: openup-create-task-spec
description: Produce a REASONS-Canvas task spec from a roadmap line or feature description, ready for developer-role consumption
model: inherit
fit:
  great: [decomposing iteration-plan tasks into executable specs, formalizing ad-hoc work before coding starts]
  ok: [retrofitting specs onto in-progress work that lacks one]
  poor: [trivial doc-only edits (overhead exceeds value), exploratory spikes]
arguments:
  - name: task_id
    description: Task ID (T-XXX). Auto-allocates next free ID if not provided.
    required: false
  - name: title
    description: One-line task title. Required if task_id is new; reads from roadmap if existing.
    required: false
  - name: source
    description: "Where the task comes from: 'roadmap' (default), 'plan' (with plan path), or 'adhoc'."
    required: false
  - name: plan_ref
    description: "Path + section to the originating plan, e.g. 'docs/plans/2026-04-28-foo.md#3'"
    required: false
---

# Create Task Spec (REASONS Canvas)

This skill produces a per-task REASONS Canvas — the executable blueprint a
developer-role agent reads verbatim before generating code. It bridges the gap
between coarse roadmap lines / use cases and implementation.

## When to Use

Use this skill when:
- A roadmap task is about to enter implementation and has no spec yet.
- A plan item needs to be decomposed before assignment.
- Existing in-progress work needs a retroactive spec for handoff.

## When NOT to Use

Do NOT use this skill when:
- The change is a trivial typo / config tweak — use `/openup-quick-task`.
- The task spec already exists at `docs/tasks/T-XXX-*.md` — update via this
  skill (re-run), do not hand-edit (per the spec-first rule in `CLAUDE.openup.md`).
- You're at the *idea* stage and don't yet have requirements — run
  `/openup-plan-feature` first.

## Success Criteria

After this skill completes, ALL of these must be true:
- [ ] File exists at `docs/tasks/T-XXX-<slug>.md` matching the template at
      `docs-eng-process/templates/task-spec.md`.
- [ ] Front-matter is fully populated (`id`, `title`, `status`, `priority`, `estimate`).
- [ ] Status is `ready` (not `proposed`) — the rubric grades to all-✅.
- [ ] All eight rubric criteria in `.claude/rubrics/task-spec-rubric.md` are ✅.
- [ ] `docs/roadmap.md` references the new task with a status entry.

## Process

The skill is a two-round multi-role handoff. Use the token-efficiency protocol
(`.claude/CLAUDE.openup.md`): one orchestrator, compact handoffs, one specialist
per round.

### 1. Allocate Task ID and Read Context

- If `task_id` is missing, scan `docs/tasks/T-*.md` for the highest existing ID
  and allocate `T-{n+1}`.
- Read `docs/roadmap.md`, the originating plan (if `plan_ref` provided), and the
  use case(s) implicated.
- Generate filename: `docs/tasks/<task_id>-<slug>.md` from the title.
- Copy `docs-eng-process/templates/task-spec.md` to that path.

### 2. Round 1 — Analyst + Architect

Brief one analyst-role agent and one architect-role agent in compact form (max
6 bullets each). Inputs: roadmap line, plan section, use case excerpt.

- **Analyst** drafts: Story (INVEST), Analysis Context, Requirements, Entities.
- **Architect** drafts: Approach (3–5 lines), Structure (Add/Modify/Do-not-touch),
  Safeguards (invariants, no-go zones, token budgets).

Both write directly to the task-spec file under their respective sections. They
do NOT inline rules from `conventions.md` or the architecture notebook —
references only.

### 3. Round 2 — Developer

Brief one developer-role agent with the partially-filled task spec.

- **Developer** drafts: Operations (ordered, 3–8 testable steps).
- Developer also fills the Norms section with file references only (no copies).

### 4. Rubric Grading

Run `/openup-assess-completeness artifact: task-spec` (or apply
`.claude/rubrics/task-spec-rubric.md` inline). Grade each of 8 criteria.

- All ✅ → set `status: ready` in front-matter.
- Any ❌ → keep `status: proposed`, list gaps for revision, loop back to the
  responsible role for fixes.

### 5. Roadmap Update

Add or update the roadmap row for this task ID with status `ready` and a link
to the spec file.

## Output

Returns:
- Path to the created task spec
- Rubric grade summary (criteria satisfied / gaps)
- Final status (`ready` or `proposed`)

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Template not found | Path moved | Verify `docs-eng-process/templates/task-spec.md` exists |
| Norms section duplicates conventions.md content | Specialist inlined rules | Replace inline text with a path reference |
| Operations step is multi-action | Step bundles "implement X and Y" | Split into separate steps |
| Estimate doesn't match Structure scope | Misjudged size | Either tighten Structure or revise estimate |

## References

- Template: `docs-eng-process/templates/task-spec.md`
- Rubric: `.claude/rubrics/task-spec-rubric.md`
- Format origin: Martin Fowler, "Structured Prompt-Driven Development"
- Index: `docs/tasks/README.md`

## See Also

- [openup-create-iteration-plan](../create-iteration-plan/SKILL.md) — produces the roadmap lines this skill expands
- [openup-assess-completeness](../../openup-workflow/assess-completeness/SKILL.md) — rubric grading
- [openup-orchestrate](../../openup-orchestrate/SKILL.md) — runs the multi-role rounds

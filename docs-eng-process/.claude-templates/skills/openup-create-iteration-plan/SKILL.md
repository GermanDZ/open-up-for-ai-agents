---
name: openup-create-iteration-plan
description: Plan iteration based on current state and roadmap
model: sonnet
arguments:
  - name: iteration_number
    description: Iteration number to plan
    required: false
---

# Create Iteration Plan

This skill generates an iteration plan from the OpenUP template.

## When to Use

Use this skill when:
- Starting a new iteration and need to plan work
- In Construction phase planning iterations
- Need to select tasks from roadmap for iteration
- Assigning tasks to team members
- Defining iteration success criteria

## When NOT to Use

Do NOT use this skill when:
- Looking to start iteration (use `/openup-start-iteration`)
- Need to create roadmap (use project management)
- Iteration plan exists and only minor updates needed (edit directly)
- In Inception phase (use phase activities instead)

## Success Criteria

After using this skill, verify:
- [ ] Iteration plan file exists
- [ ] Iteration goal is clearly defined
- [ ] Tasks are selected from roadmap
- [ ] Task assignments are made
- [ ] Success criteria are specified
- [ ] Iteration timeline is stated

## Process

### Load Project Config (context + rules — do this first)

If `docs/project-config.yaml` exists, apply it before drafting (skip if
absent): inject its `context:` as `<project-context>` and its `rules.iteration-plan`
as `<project-rules>`, then confirm every injected rule holds before marking
the artifact complete. Rules are *additive* — they may add but never waive a
framework criterion. Full mechanism + precedence (the single source):
`docs-eng-process/project-config.md`.

### 1. Read Project Status

Read `docs/project-status.md` to get:
- Current phase
- Current iteration
- Iteration goals

### 2. Read Roadmap

Read `docs/roadmap.md` to identify:
- Pending tasks appropriate for this iteration
- Task priorities and dependencies

### 3. Determine Iteration Number

Use `$ARGUMENTS[iteration_number]` or auto-increment from current iteration.

### 4. Copy Template

Copy `docs-eng-process/templates/iteration-plan.md` to `docs/phases/<phase>/iteration-<n>-plan.md`

### 5. Fill in Iteration Plan

Update with:
- **Iteration number** and dates
- **Iteration goal**: Derived from roadmap and phase objectives
- **Selected tasks**: From roadmap, prioritized for this iteration
- **Task assignments**: Which roles will handle each task
- **Success criteria**: How to know the iteration succeeded
- **Risk assessment**: Any iteration-specific risks

### 5a. Write Instance Frontmatter (T-038 — doc traceability)

Replace the template's provenance frontmatter (`type: Template`,
`source_url`) with an **instance** block declaring this file as a typed
`iteration-plan` work-product. Per the v1 spine, an iteration-plan
traces-from one or more `work-item` ids — the work items the iteration
will deliver. Grade against the cross-cutting
[Doc Traceability Rubric](../../rubrics/doc-traceability-rubric.md).

Example block:

```yaml
---
type: iteration-plan        # required — v1 spine
id: IP-12                   # stable, project-unique
title: Iteration 12 — <Theme>
status: approved
traces-from: [WI-001, WI-002]   # the work items this iteration delivers
owner-role: project-manager
iteration: construction-2
---
```

If the project does not yet maintain explicit `work-item` instances under
`docs/work-items/`, leave `traces-from` empty for this iteration and
flag the gap in `## Open Questions` — backfilling work-items is a one-time
cost, and the validator will surface it as a `coverage-gap` for any
`work-item → traces-from → requirement` rule.

Field reference: [`docs-eng-process/doc-frontmatter.md`](../../../docs-eng-process/doc-frontmatter.md).
Validator: `python3 scripts/check-docs.py`.

### 6. Self-Critique

Apply the **Self-Critique SOP** (`docs-eng-process/sops/self-critique.md`) before
validating: take a hostile-reviewer stance, surface every load-bearing
assumption into the plan, and confirm the iteration goal and each task's success
criteria could actually fail — and that the selected work realistically fits the
phase's time box. List every weakness you find — including ones you are uncertain about — then fix or explicitly flag each one. Rank them and record the top one or two with their resolutions.

### 7. Validate Completeness

Re-check every item in **Success Criteria** (top of this skill) against the
document you produced; fix any gap before returning.

## Output

Returns:
- Path to iteration plan
- List of tasks planned
- Recommended team composition

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Template not found | Template path incorrect | Verify `docs-eng-process/templates/iteration-plan.md` exists |
| No tasks available | Roadmap is empty or all tasks complete | Review roadmap and add pending tasks |
| Invalid iteration number | Iteration number conflicts or gaps | Verify current iteration from project-status |

## References

- Iteration Plan Template: `docs-eng-process/templates/iteration-plan.md`
- Project Manager Role: `docs-eng-process/openup-knowledge-base/core/role/roles/project-manager-4.md`

## See Also

- [openup-start-iteration](../../openup-workflow/start-iteration/SKILL.md) - Begin new iteration
- [openup-complete-task](../../openup-workflow/complete-task/SKILL.md) - Mark iteration tasks complete
- [openup-construction](../../openup-phases/construction/SKILL.md) - Construction iteration planning

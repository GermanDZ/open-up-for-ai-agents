---
name: openup-create-iteration-plan
description: Plan iteration based on current state and roadmap
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

## Process

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

### 6. Validate Completeness

Ensure the iteration plan includes:
- Clear iteration goal
- List of tasks to complete
- Task assignments
- Success criteria
- Iteration timeline

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

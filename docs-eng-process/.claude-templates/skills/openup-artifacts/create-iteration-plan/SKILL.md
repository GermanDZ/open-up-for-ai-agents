---
name: create-iteration-plan
description: Plan iteration based on current state and roadmap
arguments:
  - name: iteration_number
    description: Iteration number to plan
    required: false
---

# Create Iteration Plan

This skill generates an iteration plan from the OpenUP template.

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

## References

- Iteration Plan Template: `docs-eng-process/templates/iteration-plan.md`
- Project Manager Role: `docs-eng-process/openup-knowledge-base/core/role/roles/project-manager-4.md`

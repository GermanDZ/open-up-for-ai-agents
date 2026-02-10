---
name: openup-start-iteration
description: Begin a new OpenUP iteration with proper phase context and task selection
arguments:
  - name: iteration_number
    description: The iteration number (optional, auto-increments if not provided)
    required: false
  - name: goal
    description: The iteration goal (optional, reads from project-status if not provided)
    required: false
  - name: task_id
    description: The task ID from roadmap to work on (optional, but recommended for task-based branching)
    required: false
---

# Start Iteration

This skill initializes a new OpenUP iteration by reading the current project state, identifying tasks from the roadmap, and creating a task-based branch for the work.

**IMPORTANT**: Branch creation requires proper planning. The skill will read the roadmap to identify the task and create an appropriately named branch based on the task type.

## When to Use

Use this skill when:
- Starting a new iteration in any phase
- Need to create iteration branch
- Ready to begin iteration work
- Need to update project status for new iteration
- Planning iteration work

## When NOT to Use

Do NOT use this skill when:
- Current iteration is still in progress (complete it first)
- Need to plan iteration without starting (use `/openup-create-iteration-plan`)
- Looking to complete iteration (use `/openup-complete-task`)
- Just need to switch branches (use git directly)

## Success Criteria

After using this skill, verify:
- [ ] Project status is updated with new iteration
- [ ] Iteration branch is created
- [ ] Iteration goal is defined
- [ ] Answered input requests are processed
- [ ] Log entry is created

## Process

### 1. Read Project Status

Read `docs/project-status.md` to establish context:
- Current phase (inception | elaboration | construction | transition)
- Current iteration number
- Previous iteration status

### 2. Read Roadmap and Identify Task

Read `docs/roadmap.md` to:
- Find the task specified by `$ARGUMENTS[task_id]`
- Extract task details: title, description, task type (feature, bugfix, refactor, etc.)
- Determine priority and dependencies
- **If task_id not provided or not found**: Ask user to specify which task from the roadmap

### 3. Check for Answered Input Requests

Check `docs/input-requests/` for files with `status: answered`. Process any answered requests before starting the new iteration.

### 4. Create New Branch

Follow the task-based branching SOP:
- Detect trunk branch (prefer `origin/HEAD`, fallback to `main`, `master`, or current)
- Check current branch lifecycle
- **Create new branch following task-based naming convention**:
  - Features: `feature/{task_id}-{short-description}`
  - Bugfixes: `bugfix/{task_id}-{short-description}`
  - Refactoring: `refactor/{task_id}-{short-description}`
  - Documentation: `docs/{task_id}-{short-description}`
  - Testing: `test/{task_id}-{short-description}`
  - Default: `task/{task_id}-{short-description}`

**Branch naming examples**:
- `feature/T-005-user-authentication`
- `bugfix/T-012-login-timeout`
- `refactor/T-008-api-cleanup`
- `docs/T-003-api-guide`

### 5. Initialize Iteration

Update `docs/project-status.md`:
- Increment `iteration` or use provided `$ARGUMENTS[iteration_number]`
- Set `iteration_goal` to provided `$ARGUMENTS[goal]` or derive from roadmap task
- Set `status` to `in-progress`
- Set `current_task` to the task_id
- Update `iteration_started` to today's date

### 6. Log Initialization

Create an entry in `docs/agent-logs/agent-runs.jsonl` documenting the iteration start with task context.

## Output

Returns a summary of:
- Current phase and iteration number
- Task being worked on (task_id, title)
- Iteration goal
- Active branch name
- Task details from roadmap

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Project status not found | docs/project-status.md doesn't exist | Initialize project with phase skill first |
| Task not found in roadmap | task_id not provided or doesn't exist | Check roadmap.md for valid task IDs |
| Invalid iteration number | Iteration number is not greater than current | Verify current iteration number |
| Branch creation failed | Git repository or branch issue | Check git status and resolve conflicts |
| Unanswered input requests | Pending input from stakeholders | Process answered requests or notify user |

## References

- Agent Workflow: `docs-eng-process/agent-workflow.md`
- Project Status Template: `docs-eng-process/openup-knowledge-base/core/role/roles/project-manager-4.md`

## See Also

- [openup-create-iteration-plan](../../openup-artifacts/create-iteration-plan/SKILL.md) - Plan iteration before starting
- [openup-complete-task](../complete-task/SKILL.md) - Complete iteration tasks
- [openup-retrospective](../retrospective/SKILL.md) - Create retrospective after iteration completes
- [openup-request-input](../request-input/SKILL.md) - Gather stakeholder input

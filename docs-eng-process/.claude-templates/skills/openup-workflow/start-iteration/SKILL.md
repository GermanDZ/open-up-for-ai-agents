---
name: start-iteration
description: Begin a new OpenUP iteration with proper phase context and task selection
arguments:
  - name: iteration_number
    description: The iteration number (optional, auto-increments if not provided)
    required: false
  - name: goal
    description: The iteration goal (optional, reads from project-status if not provided)
    required: false
---

# Start Iteration

This skill initializes a new OpenUP iteration by reading the current project state, creating an appropriate branch, and setting up the iteration context.

## Process

### 1. Read Project Status

Read `docs/project-status.md` to establish context:
- Current phase (inception | elaboration | construction | transition)
- Current iteration number
- Previous iteration status

### 2. Check for Answered Input Requests

Check `docs/input-requests/` for files with `status: answered`. Process any answered requests before starting the new iteration.

### 3. Create New Branch

Follow the branching SOP:
- Detect trunk branch (prefer `origin/HEAD`, fallback to `main`, `master`, or current)
- Check current branch lifecycle
- Create new branch following naming convention: `iteration/{phase}-it{iteration_number}`

### 4. Initialize Iteration

Update `docs/project-status.md`:
- Increment `iteration` or use provided `$ARGUMENTS[iteration_number]`
- Set `iteration_goal` to provided `$ARGUMENTS[goal]` or derive from roadmap
- Set `status` to `in-progress`
- Update `iteration_started` to today's date

### 5. Log Initialization

Create an entry in `docs/agent-logs/agent-runs.jsonl` documenting the iteration start.

## Output

Returns a summary of:
- Current phase and iteration number
- Iteration goal
- Active branch
- Recommended tasks from roadmap for this iteration

## References

- Agent Workflow: `docs-eng-process/agent-workflow.md`
- Project Status Template: `docs-eng-process/openup-knowledge-base/core/role/roles/project-manager-4.md`

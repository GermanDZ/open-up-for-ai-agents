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
    description: The task ID from roadmap to work on (required for task-based branching)
    required: true
  - name: team
    description: Team type to automatically deploy after initialization (feature, investigation, construction, elaboration, inception, transition, planning, full, or none)
    required: false
  - name: deploy_team
    description: "Whether to deploy a team after iteration initialization (true/false, default: false)"
    required: false
---

# Start Iteration

Initialize a new OpenUP iteration: read project state, create a task branch, and begin work.

## Success Criteria

After this skill completes, ALL of these must be true:

- [ ] Project status is updated with new iteration
- [ ] **BLOCKING CHECK**: `git rev-parse --abbrev-ref HEAD` returns a non-trunk branch name (not `main`, `master`, or whatever trunk is). If it returns trunk, the skill has FAILED — do not proceed.
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
- **If task_id not found**: Ask user to specify which task from the roadmap

### 3. Create Task Branch

**Execute these commands in order:**

```bash
# 1. Detect trunk
TRUNK=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
[ -z "$TRUNK" ] && TRUNK="main"
git rev-parse --verify "$TRUNK" 2>/dev/null || TRUNK="master"

# 2. Switch to trunk and pull latest
git checkout "$TRUNK"
git pull origin "$TRUNK" 2>/dev/null || true

# 3. Create branch (see branching.md for naming patterns)
git checkout -b {type}/{task_id}-{short-description}

# 4. VERIFY — this must NOT return trunk
git rev-parse --abbrev-ref HEAD
```

**If the branch already exists**, check its status:
- No unmerged commits → delete and recreate from trunk
- Has unmerged commits → create PR or merge first, then create new branch

### 4. Check for Answered Input Requests

Check `docs/input-requests/` for files with `status: answered`. Process any answered requests before continuing.

### 5. Initialize Iteration

Update `docs/project-status.md`:
- Increment `iteration` or use provided `$ARGUMENTS[iteration_number]`
- Set `iteration_goal` to provided `$ARGUMENTS[goal]` or derive from roadmap task
- Set `status` to `in-progress`
- Set `current_task` to the task_id
- Update `iteration_started` to today's date

### 6. Log Initialization

Create an entry in `docs/agent-logs/agent-runs.jsonl` documenting the iteration start with task context.

### 7. Deploy Team (Optional)

If `$ARGUMENTS[deploy_team]` is `true` or `$ARGUMENTS[team]` is specified:

1. Determine team composition based on `$ARGUMENTS[team]` or current phase:
   - **feature**: analyst, architect, developer, tester
   - **investigation**: architect, developer, tester
   - **construction**: developer, tester
   - **elaboration**: architect, developer, tester
   - **inception**: analyst, project-manager
   - **transition**: tester, project-manager, developer
   - **planning**: project-manager, analyst
   - **full**: all roles

2. Deploy the team using Task tool, brief each teammate with iteration context.

## Output

Returns a summary of:
- Current phase and iteration number
- Task being worked on (task_id, title)
- Iteration goal
- Active branch name (must be a non-trunk task branch)

## See Also

- [openup-complete-task](../complete-task/SKILL.md) - Complete iteration tasks
- [openup-create-iteration-plan](../../openup-artifacts/create-iteration-plan/SKILL.md) - Plan iteration before starting

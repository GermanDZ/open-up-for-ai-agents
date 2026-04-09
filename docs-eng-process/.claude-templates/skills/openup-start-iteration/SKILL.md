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
    description: "Whether to deploy a team after iteration initialization (true/false, default: true — pass 'false' to skip team deployment)"
    required: false
---

# Start Iteration

Initialize a new OpenUP iteration: read project state, create a task branch, and begin work.

## Success Criteria

After this skill completes, ALL of these must be true:

- [ ] **BLOCKING**: Team is deployed and PM is coordinating — verified before any implementation work begins
- [ ] Project status is updated with new iteration
- [ ] **BLOCKING**: `git rev-parse --abbrev-ref HEAD` returns a non-trunk branch name. If it returns trunk, the skill has FAILED — do not proceed.
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

### 3. Deploy Team — MANDATORY BEFORE ANY WORK

**⛔ STOP. Do not create a branch, write any code, or modify any files until the team is deployed.**

Team deployment is required for every iteration. Skip ONLY if `$ARGUMENTS[deploy_team]` is explicitly `"false"`.

1. **Auto-select team type** if `$ARGUMENTS[team]` is not specified:
   - Check task description for keywords:
     - "investigate", "research", "spike" → `openup-investigation-team`
     - "plan", "roadmap", "prioritize" → `openup-planning-team`
   - Otherwise fall back to phase default:
     - `inception` → `openup-inception-team` (analyst + project-manager)
     - `elaboration` → `openup-elaboration-team` (architect + developer)
     - `construction` → `openup-construction-team` (developer + tester) ← most common
     - `transition` → `openup-transition-team` (developer + tester + project-manager)

2. **Team type override**: if `$ARGUMENTS[team]` is provided, use it directly:
   - **feature**: analyst, architect, developer, tester
   - **investigation**: architect, developer, tester
   - **construction**: developer, tester
   - **elaboration**: architect, developer, tester
   - **inception**: analyst, project-manager
   - **transition**: tester, project-manager, developer
   - **planning**: project-manager, analyst
   - **full**: all roles
   - **none**: skip team deployment (same as `deploy_team: false`)

3. Deploy the team using the Agent tool — spawn each role with:
   - Iteration goal and task ID
   - Current phase and phase objectives
   - Relevant project docs (project-status.md, roadmap.md)
   - The PM's orchestrator role: decompose the task, brief each specialist, collect and synthesize outputs

4. **PM takes the lead**: after spawning, the project-manager agent coordinates all subsequent work for this iteration. Specialists (developer, architect, tester, analyst) receive focused subtasks from the PM.

### 4. Create Task Branch

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

### 5. Check for Answered Input Requests

Check `docs/input-requests/` for files with `status: answered`. Process any answered requests before continuing.

### 6. Initialize Iteration

> **Haiku/Scribe step** — you determine the new values (iteration number, goal, task_id),
> then delegate the file write:
>
> ```
> Agent(model="haiku", description="Initialize project-status for new iteration",
>   prompt="You are a Scribe. In docs/project-status.md update these fields:
>   - **Iteration**: [new number]
>   - **Iteration Goal**: [goal text]
>   - **Status**: in-progress
>   - **Current Task**: [task_id]
>   - **Iteration Started**: [YYYY-MM-DD]
>   - **Last Updated**: [YYYY-MM-DD]
>   - **Updated By**: openup-start-iteration
>   Report: each field changed from → to.")
> ```

### 7. Log Initialization

> **Haiku/Scribe step** — delegate the log append:
>
> ```
> Agent(model="haiku", description="Log iteration start",
>   prompt="You are a Scribe. Append a JSONL record to docs/agent-logs/agent-runs.jsonl:
>   {\"run_id\":\"[id]\",\"event\":\"iteration_start\",\"task_id\":\"[task_id]\",
>    \"goal\":\"[goal]\",\"branch\":\"[branch]\",\"phase\":\"[phase]\",\"ts\":\"[ts]\"}
>   Report: record appended.")
> ```

## Output

Returns a summary of:
- Current phase and iteration number
- Task being worked on (task_id, title)
- Iteration goal
- Active branch name (must be a non-trunk task branch)

## See Also

- [openup-complete-task](../complete-task/SKILL.md) - Complete iteration tasks
- [openup-create-iteration-plan](../../openup-artifacts/create-iteration-plan/SKILL.md) - Plan iteration before starting

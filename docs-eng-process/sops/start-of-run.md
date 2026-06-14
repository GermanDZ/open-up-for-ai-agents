# Start-of-Run SOP

> Extracted from `agent-workflow.md` so skills that need only the start-of-run
> procedure load this file instead of the whole operating-procedures document.

**Every agent run MUST begin with these steps in order:**

## Step 0: Check for Answered Input Requests

Before proceeding with normal workflow, check for answered input requests:

- Check `docs/input-requests/` directory for files with `status: answered` in frontmatter
- If answered requests exist:
  1. Process them in chronological order (oldest first)
  2. Read all answers from each request
  3. Use the information to continue the related task
  4. Update the request's `status` to `processed` in frontmatter
  5. Move the file to `docs/input-requests/archive/`
  6. Log the processing in the agent-run log
- After processing all answered requests, continue with normal start-of-run steps

**Note**: If the user explicitly asks to process input requests (e.g., "Continue with input-requests"), prioritize this step and process all answered requests before selecting new tasks.

## Step 1: Read Project Status and Learnings

Read `docs/project-status.md` to establish context:

- Extract `phase` (inception | elaboration | construction | transition)
- Extract `iteration` (current iteration number)
- Extract `iteration_goal` (what this iteration should achieve)
- Extract `status` (not-started | in-progress | blocked | completed)

Also read `.claude/memory/iteration-learnings.md` if it exists — scan for gotchas, decisions, and conventions from past iterations that apply to the current task. This is your institutional memory; don't repeat mistakes or redo decisions already made.

**If `status == blocked`**:
- Report all blockers to the user
- Request guidance before proceeding
- Do not proceed until blockers are resolved or explicitly overridden

**If `status == completed`**:
- Check if next phase should be started
- Propose phase transition to user
- **Do NOT automatically advance phase** (requires human approval)

## Step 2: Check for Pending Plans

If `docs/plans/` exists, check for plan files that have been saved but not yet started:

- Look for entries in `docs/roadmap.md` with `status: planned` that link to a file in `docs/plans/`
- For any such entry, **read the linked plan file** — it contains the full implementation plan created in a prior session
- When starting work on a planned task, treat the plan file as the authoritative spec: the decomposition, approach, and file list are already decided — do not re-plan

This is the mechanism for cross-session continuity: plan in one session, implement in another without losing context.

## Step 3: Read Roadmap and Select Task

Read `docs/roadmap.md` and select the next task:

- Filter tasks by `status == pending`
- If multiple possible targets and not specified: choose the **highest priority** task
- Priority tie-breakers (in order):
  1. Tasks explicitly marked as high priority
  2. Tasks blocking other work
  3. Tasks aligned with current `iteration_goal`
  4. Tasks with earliest due date
  5. First task in the list

## Step 4: Verify Phase Context

Ensure the selected task aligns with:
- Current `phase` from `docs/project-status.md`
- Current `iteration_goal` from `docs/project-status.md`

If the task doesn't fit:
- Log as out-of-scope in the agent-run log
- Request user approval or defer to backlog
- Do not proceed without explicit approval

## Step 4.5: Select Workflow Depth (Task-Size Gate)

Before branch/task execution, choose the lightest valid workflow:

- **Tiny, low-risk changes** (small docs/config/bug fix): use `/openup-quick-task` when allowed by project policy
- **Normal implementation tasks**: use `/openup-complete-task` for integrated commit + docs + logging
- **Iteration/phase-level work**: use full SOP + phase skills

**Goal**: reduce overhead while preserving required traceability for the scope of work.

## Step 5: Create Branch (if needed)

**MANDATORY**: Before starting any work, ensure you are on an appropriate branch. Never work directly on trunk. New tasks must start on a clean branch (either trunk or a branch that has been merged to trunk).

1. **Detect trunk branch** using this algorithm:
   - Prefer `origin/HEAD` if present locally
   - Else fall back to `main`
   - Else fall back to `master`
   - Else use current branch

2. **Check branch lifecycle** (see [Branching SOP](../agent-workflow.md#branching-sop) for details):
   - If `current branch == trunk`: Proceed to step 3 to create a new branch
   - If `current branch != trunk`: Check for unmerged commits using `git log <trunk>..HEAD --oneline`
     - **If unmerged commits exist**: 
       - **If origin is configured**: Create pull request and wait for user confirmation that PR is merged
       - **If origin is not configured**: Ask user to confirm merge to trunk before proceeding
       - **Do NOT proceed** with new task until branch is merged or user explicitly overrides
     - **If no unmerged commits or after merge/PR confirmation**: Proceed to step 3 to create a new branch

3. **Create a new branch for the new task**:
   - Use descriptive branch name following project conventions (typically `feature/`, `fix/`, `refactor/`, etc.)
   - Include task ID or brief description in branch name (e.g., `feature/T-001-login-endpoint`)
   - Create branch: `git checkout -b <branch-name>`

4. **Record branch information**:
   - Note the branch name and trunk detection result for inclusion in traceability logs
   - Always record what was detected as trunk in the run log
   - Record any merge/PR actions taken during branch lifecycle check

**CRITICAL**: Do not proceed to Role-Based Execution until you are on a non-trunk branch that has been merged to trunk (or is trunk itself, from which you've created a new branch). All work must happen on a feature branch, never directly on trunk.

**See [Branching SOP](../agent-workflow.md#branching-sop) for detailed branch lifecycle management, naming conventions, and rules.**

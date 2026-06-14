# Branching SOP

> Extracted from `agent-workflow.md` so skills that need only the branching
> procedure load this file instead of the whole operating-procedures document.

**Note**: This procedure is executed as part of
[Start-of-Run SOP](../agent-workflow.md#start-of-run-sop) Step 4, which happens
**before any work begins**. Branch creation is mandatory if you are on trunk, and
branches with unmerged commits must be merged to trunk before starting new tasks.

## Trunk Detection

Detect trunk branch (varies per repo) using this algorithm:

1. Prefer `origin/HEAD` if present locally
2. Else fall back to `main`
3. Else fall back to `master`
4. Else use current branch

**Always record what was detected** as trunk in the run log.

## Branch Lifecycle Check

**MANDATORY**: Before starting a new task, check if the current branch has unmerged commits. New tasks must start on a clean branch (either trunk or a branch that has been merged to trunk).

1. **If current branch == trunk**: Proceed to [Branch Creation Rules](#branch-creation-rules) to create a new branch for the work.

2. **If current branch != trunk**: Check for unmerged commits:
   - Run: `git log <trunk>..HEAD --oneline` to detect commits not in trunk
   - If commits exist (output is non-empty):
     - **If origin remote is configured** (`git remote get-url origin` succeeds):
       - Inform user: "Current branch has unmerged commits. Creating pull request with task context..."
       - Invoke `/create-pr` skill to create PR with proper description linking to roadmap task context:
         - Extract task_id from branch name (e.g., `feature/T-001-xyz` → `T-001`)
         - Generate PR description from `docs/roadmap.md` task entry
         - Push branch to origin: `git push -u origin <current-branch>`
         - Create PR using platform-specific tooling (GitHub `gh`, GitLab `glab`)
       - Wait for user confirmation: "PR has been merged to trunk" or "PR is ready for review"
       - **Do NOT proceed** with new task until PR is merged or user explicitly confirms to continue
     - **If origin remote is not configured**:
       - Ask user: "Current branch has unmerged commits. Merge to trunk before continuing? (yes/no)"
       - If user confirms "yes":
         - Switch to trunk: `git checkout <trunk>`
         - Merge branch: `git merge <previous-branch>`
         - Delete merged branch: `git branch -d <previous-branch>`
         - Proceed to create new branch for new task
       - If user confirms "no" or does not approve:
         - Stop and wait for user to handle merge manually
         - **Do NOT proceed** with new task until merge is complete
   - If no commits exist (output is empty) or after merge/PR confirmation:
     - Proceed to [Branch Creation Rules](#branch-creation-rules) to create a new branch for the new task

**CRITICAL**: Do not start a new task on a branch that has unmerged commits. This ensures clean branch history and prevents work from being lost.

## Branch Creation Rules

- **If current branch == trunk**: **MANDATORY** - Create a new branch for the work before starting any work
- **If current branch != trunk AND has been merged to trunk** (no unmerged commits): **MANDATORY** - Create a new branch for the new task
- **If current branch != trunk AND has unmerged commits**: **BLOCKED** - Handle merge/PR first (see [Branch Lifecycle Check](#branch-lifecycle-check))

**CRITICAL**: Branch creation happens BEFORE Role-Based Execution begins. Never start working before ensuring you are on an appropriate branch that has been merged to trunk (or is trunk itself).

## Branch Naming

Follow project conventions (typically `feature/`, `fix/`, `refactor/`, etc.)

- Include task ID or brief description when possible (e.g., `feature/T-001-login-endpoint`)
- Use descriptive names that indicate the work being done
- Keep branch names concise but informative

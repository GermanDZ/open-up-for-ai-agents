---
name: create-pr
description: Create a pull request with proper description linking to roadmap task context
arguments:
  - name: task_id
    description: The task ID from roadmap (e.g., T-001). Auto-detected from branch name if not provided.
    required: false
  - name: branch
    description: The branch to create PR from. Uses current branch if not provided.
    required: false
  - name: title
    description: Custom PR title. Auto-generated from task if not provided.
    required: false
  - name: base
    description: Base branch to merge into (e.g., main, develop). Auto-detected if not provided.
    required: false
---

# Create Pull Request

This skill creates a pull request with a structured description that links to the roadmap task context, ensuring traceability and proper documentation.

## Process

### 1. Detect Current State

1. **Detect current branch**:
   - If `$ARGUMENTS[branch]` is provided, use it
   - Otherwise, run `git rev-parse --abbrev-ref HEAD` to get current branch

2. **Check for unmerged commits**:
   - Run: `git log <trunk>..HEAD --oneline` (where trunk is auto-detected)
   - If no unmerged commits exist, inform user and exit gracefully
   - If unmerged commits exist, proceed

3. **Detect platform**:
   - Check for GitHub CLI: `command -v gh`
   - Check for GitLab CLI: `command -v glab`
   - If neither found, inform user they need to install one

4. **Check for remote**:
   - Run: `git remote get-url origin`
   - If no remote configured, prompt user to add one

### 2. Extract Task Context

1. **Determine task_id**:
   - If `$ARGUMENTS[task_id]` is provided, use it
   - Otherwise, extract from branch name using regex pattern: `([Tt]-?\d+)` or `(task[-_]?\d+)`
   - Example: `feature/T-001-login` → `T-001`

2. **Parse roadmap for task context**:
   - Read `docs/roadmap.md`
   - Find the task section matching the task_id
   - Extract: task description, priority, status, related requirements/risks

3. **Generate PR title** (if not provided):
   - Format: `[<task_id>] <task description>` or derived from branch name
   - Use `$ARGUMENTS[title]` if provided

### 3. Detect Trunk Branch

Follow the trunk detection algorithm from the Branching SOP:
1. Check `origin/HEAD` symbolic reference: `git symbolic-ref refs/remotes/origin/HEAD`
2. Fallback to common branch names in order: `main`, `master`, `develop`, `development`
3. Final fallback: current branch's remote tracking branch
4. Use `$ARGUMENTS[base]` if provided to override detection

**Always record what was detected** as trunk in the run log.

### 4. Generate PR Description

Use the template from `docs-eng-process/templates/pr-description.md` and populate with:
- **Summary**: Brief description of changes
- **Task Context**: task_id, description from roadmap, priority, related items
- **Changes Made**: Files changed (from git diff), commits from git log
- **Testing Performed**: Checklist for unit tests, integration tests, manual testing
- **Review Checklist**: Code style, documentation, tests, merge conflicts
- **Related Issues**: Links to related roadmap items or issues
- **Breaking Changes**: Note any breaking changes
- **Notes**: Additional context for reviewers

### 5. Push Branch and Create PR

1. **Push branch**:
   - Run: `git push -u origin <branch>`

2. **Create PR** based on detected platform:

   **GitHub (gh)**:
   ```bash
   gh pr create \
     --base <base> \
     --title "<title>" \
     --body "<description>" \
     --label "task:<task_id>"
   ```

   **GitLab (glab)**:
   ```bash
   glab mr create \
     --base <base> \
     --title "<title>" \
     --description "<description>" \
     --label "task:<task_id>"
   ```

3. **Handle errors gracefully**:
   - If branch already has PR: Inform user of existing PR URL
   - If push fails: Show error and suggest fixes
   - If CLI not installed: Provide installation instructions

### 6. Update Documentation (Optional)

Consider updating:
- `docs/roadmap.md`: Add PR URL to task entry
- `docs/project-status.md`: Note PR in Active Work Items

## Output

Returns a summary of:
- PR URL
- Branch name
- Task context linked
- Files changed
- Commits included

## Error Handling

- **No unmerged commits**: Inform user that current branch is up to date with trunk
- **No remote configured**: Prompt user to add remote with `git remote add origin <url>`
- **CLI not installed**: Provide installation instructions:
  - GitHub: `brew install gh` or https://cli.github.com/
  - GitLab: `brew install glab` or https://glab.readthedocs.io/
- **No task_id found**: Proceed with generic PR description (no task context)
- **Roadmap not found**: Proceed without task context, inform user

## References

- Branching SOP: `docs-eng-process/agent-workflow.md`
- PR Description Template: `docs-eng-process/templates/pr-description.md`
- Roadmap: `docs/roadmap.md`

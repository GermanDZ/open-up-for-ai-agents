---
name: openup-create-pr
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

Create a PR with a structured description linked to roadmap task context.

## Process

### 1. Detect Current State

1. Use `$ARGUMENTS[branch]` or `git rev-parse --abbrev-ref HEAD`.
2. Check for unmerged commits: `git log <trunk>..HEAD --oneline`. Exit if none.
3. Detect platform: `command -v gh` (GitHub) or `command -v glab` (GitLab).
4. Verify remote: `git remote get-url origin`.

### 2. Prepare Commits

1. **Trunk guard**: If on trunk (main/master/detected), create and switch to a feature branch (`git checkout -b feature/...` or `fix/...`).
2. **Check uncommitted changes**: `git status --porcelain`. If clean, skip to step 3.
3. **Organize atomic commits**: Group changes into logical units. Commit in dependency order (deps/config → types/interfaces → core logic → dependent features). Follow format from `docs-eng-process/conventions.md`.
4. **Apply test strategy**: Bundle tests with feature commits. For bug fixes, commit failing test first, then the fix.
5. **Lint before committing**: Run linter/formatter before each commit. Skip if none configured.
6. Full rules: `commit-procedure.md` in `complete-task/`.

### 3. Extract Task Context

1. Get task_id from `$ARGUMENTS[task_id]` or extract from branch name (regex `([Tt]-?\d+)`).
2. Read `docs/roadmap.md`, find task section, extract description/priority/status.
3. Generate title: `[<task_id>] <description>` or use `$ARGUMENTS[title]`.

### 4. Detect Trunk Branch

Use `$ARGUMENTS[base]` if provided; otherwise follow trunk detection in `docs-eng-process/agent-workflow.md` (Branching SOP). Record detected trunk in run log.

### 5. Generate PR Description

Use template from `docs-eng-process/templates/pr-description.md` and populate:
- Summary, Task Context (id, description, priority), Changes Made (git diff/log)
- Testing Performed, Review Checklist, Related Issues, Breaking Changes, Notes

### 6. Push Branch and Create PR

```bash
git push -u origin <branch>
# GitHub:
gh pr create --base <base> --title "<title>" --body "<description>" --label "task:<task_id>"
# GitLab:
glab mr create --base <base> --title "<title>" --description "<description>" --label "task:<task_id>"
```

### 7. Update Documentation (Optional)

- `docs/roadmap.md`: Add PR URL to task entry
- `docs/project-status.md`: Note PR in Active Work Items

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| No unmerged commits | Branch up to date with trunk | Inform user no PR needed |
| No remote configured | Git remote not set up | `git remote add origin <url>` |
| CLI not installed | gh/glab not available | `brew install gh` or `brew install glab` |
| No task_id found | Branch name has no task ID | Proceed without task context or provide manually |
| Roadmap not found | docs/roadmap.md missing | Proceed without task context, inform user |
| PR already exists | Branch already has open PR | Inform user of existing PR URL |
| On trunk branch | Working directly on main/master | Auto-create feature branch before committing |

## References

- Branching SOP: `docs-eng-process/agent-workflow.md`
- PR Description Template: `docs-eng-process/templates/pr-description.md`
- Roadmap: `docs/roadmap.md`

## See Also

- [openup-complete-task](../complete-task/SKILL.md) - Complete task and create PR
- [openup-start-iteration](../start-iteration/SKILL.md) - Start iteration with branch creation

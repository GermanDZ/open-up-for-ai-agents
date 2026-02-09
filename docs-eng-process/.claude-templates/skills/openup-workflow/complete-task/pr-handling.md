# Pull Request Handling for Complete Task

This document provides detailed procedures for creating pull requests when completing a task.

## Overview

When `create_pr=true`, the complete-task skill will optionally create a pull request after committing changes and updating documentation.

## Prerequisites

Before creating a PR, verify:
1. All changes are committed
2. No uncommitted changes remain
3. Roadmap is updated
4. Task is marked complete

## PR Creation Process

### 1. Verify Unmerged Commits

Check if current branch has unmerged commits:
```bash
git log <trunk>..HEAD --oneline
```

- **If output is empty**: No unmerged commits, PR is not needed
- **If output shows commits**: Proceed with PR creation

### 2. Invoke Create-PR Skill

Call the `/openup-create-pr` skill with:
- `task_id`: The task ID being completed
- Let the skill auto-detect branch and generate description

### 3. Handle Results

**Success**: PR created
- Provide PR URL to user
- Document PR URL in roadmap (optional)
- Update project status (optional)

**No PR Needed**:
- Inform user branch is up to date
- No action required

**Failure**:
- Explain error to user
- Provide next steps
- Suggest manual PR creation if needed

## Example Scenarios

### Scenario 1: Successful PR Creation

```
Task T-005 completed.
✓ All changes committed (abc123def)
✓ Roadmap updated
✓ Traceability logs created

Pull request created:
https://github.com/user/repo/pull/42
```

### Scenario 2: No Unmerged Commits

```
Task T-005 completed.
✓ All changes committed (abc123def)
✓ Roadmap updated
✓ Traceability logs created

No pull request needed: Branch is up to date with main.
```

### Scenario 3: PR Creation Failed

```
Task T-005 completed.
✓ All changes committed (abc123def)
✓ Roadmap updated
✓ Traceability logs created

Pull request creation failed: GitHub CLI not installed.
To create PR manually:
1. Push branch: git push -u origin feature/T-005-auth
2. Create PR at: https://github.com/user/repo/compare
```

## Integration with Complete-Task

The complete-task skill handles PR creation as follows:

```
If create_pr == "true":
    1. Verify unmerged commits exist
    2. If yes: Call /openup-create-pr skill
    3. If no: Inform user PR not needed
    4. Report result to user
```

## Manual PR Creation

If automatic PR creation fails, user can create PR manually:

### GitHub
```bash
# Install GitHub CLI
brew install gh

# Create PR
gh pr create \
  --base main \
  --title "[T-005] Implement user authentication" \
  --body "Implementation complete..."
```

### GitLab
```bash
# Install GitLab CLI
brew install glab

# Create MR
glab mr create \
  --base main \
  --title "[T-005] Implement user authentication" \
  --description "Implementation complete..."
```

### Web Interface

1. Navigate to repository
2. Click "Pull requests" or "Merge requests"
3. Click "New" or "Create"
4. Select source and target branches
5. Fill in title and description
6. Create PR

## Documentation Updates

After PR creation, consider updating:

### Roadmap
```markdown
## T-005: Implement user authentication

**Status**: completed
**PR**: https://github.com/user/repo/pull/42
```

### Project Status
```markdown
### Active Work Items

| Task ID | Description | Status | PR |
|---------|-------------|--------|-----|
| T-005   | User auth   | completed | #42 |
```

## Verification Checklist

After PR creation, verify:
- [ ] PR URL is valid and accessible
- [ ] PR title includes task ID
- [ ] PR description links to task context
- [ ] PR is labeled with task ID
- [ ] User is notified of PR URL

## References

- Create-PR Skill: `../create-pr/SKILL.md`
- Branching SOP: `docs-eng-process/agent-workflow.md`
- PR Description Template: `docs-eng-process/templates/pr-description.md`

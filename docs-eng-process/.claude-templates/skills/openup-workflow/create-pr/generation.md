# PR Generation Procedures

This document provides detailed procedures for generating PR titles, descriptions, and creating the pull request.

## Overview

PR generation consists of:
1. Extracting task context from roadmap
2. Generating PR title
3. Generating PR description
4. Creating the PR via CLI

## Extracting Task Context

### Determine Task ID

**Method 1: Use Argument**

If `task_id` argument provided, use it directly.

**Method 2: Extract from Branch Name**

Use regex patterns:
- `([Tt]-?\d+)` - Matches T-001, t001, T-001
- `(task[-_]?\d+)` - Matches task-1, task_1

Examples:
- `feature/T-001-login` → `T-001`
- `bugfix/t-023-auth-error` → `T-023`
- `feature/task-5-new-ui` → `task-5`

### Parse Roadmap

Read `docs/roadmap.md` and extract task context:

```markdown
## T-005: Implement user authentication

**Priority**: high
**Status**: in-progress
**Assigned to**: developer

**Description**: Add user authentication with login form and JWT tokens.

**Related Requirements**:
- REQ-001: User authentication
- REQ-005: Session management
```

Extract:
- Task ID
- Description
- Priority
- Status
- Related requirements
- Related risks

## Generating PR Title

### Format Options

**With Task ID**:
```
[T-005] Implement user authentication
```

**From Branch Name**:
```
Feature/T-005-auth: Implement user authentication
```

**Custom Title**:
If `title` argument provided, use it directly.

### Title Guidelines

- Keep under 72 characters
- Include task ID for traceability
- Use imperative mood
- Be descriptive but concise

## Generating PR Description

### Template Structure

Use `docs-eng-process/templates/pr-description.md` as base:

```markdown
## Summary
[Brief description of changes]

## Task Context
- **Task ID**: T-005
- **Description**: [from roadmap]
- **Priority**: [from roadmap]
- **Related**: [requirements/risks]

## Changes Made
### Files Changed
[list from git diff --name-only]

### Commits
[list from git log --oneline]

## Testing Performed
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Edge cases tested

## Review Checklist
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Tests are included
- [ ] No merge conflicts

## Related Issues
- Links to related tasks or issues

## Breaking Changes
[None or description]

## Notes
[Additional context for reviewers]
```

### Populating the Template

#### Summary
One or two sentences describing what was done.

#### Task Context
Fill with extracted roadmap information.

#### Changes Made

**Files Changed**:
```bash
git diff <trunk>...HEAD --name-only
```

**Commits**:
```bash
git log <trunk>...HEAD --oneline
```

#### Testing Performed
Checklist of testing completed.

#### Review Checklist
Standard review items.

#### Related Issues
Links to related roadmap items, issues, or requirements.

#### Breaking Changes
Note any breaking changes. If none, write "None."

#### Notes
Any additional context helpful for reviewers.

## Creating the PR

### GitHub (gh)

```bash
gh pr create \
  --base <base> \
  --title "<title>" \
  --body "<description>" \
  --label "task:<task_id>"
```

**Example**:
```bash
gh pr create \
  --base main \
  --title "[T-005] Implement user authentication" \
  --body "$(cat pr-description.md)" \
  --label "task:T-005"
```

### GitLab (glab)

```bash
glab mr create \
  --base <base> \
  --title "<title>" \
  --description "<description>" \
  --label "task:<task_id>"
```

**Example**:
```bash
glab mr create \
  --base main \
  --title "[T-005] Implement user authentication" \
  --description "$(cat pr-description.md)" \
  --label "task:T-005"
```

## Handling Errors

### Branch Already Has PR

**Detection**:
```bash
gh pr view --json url  # GitHub
glab mr view  # GitLab
```

**Action**: Inform user of existing PR URL

### Push Failed

**Common causes**:
- Authentication issue
- Network problem
- Protected branch

**Action**: Show error and suggest fixes

### CLI Not Installed

**Action**: Provide installation instructions

GitHub:
```bash
brew install gh
# or visit: https://cli.github.com/
```

GitLab:
```bash
brew install glab
# or visit: https://glab.readthedocs.io/
```

## Updating Documentation

After PR creation, optionally update:

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
- [ ] PR exists at returned URL
- [ ] Title includes task ID
- [ ] Description is complete
- [ ] Task label is applied
- [ ] User is notified with URL

## References

- PR Description Template: `docs-eng-process/templates/pr-description.md`
- GitHub CLI PR Create: https://cli.github.com/manual/gh_pr_create
- GitLab CLI MR Create: https://glab.readthedocs.io/en/latest/mr/mr_create.html

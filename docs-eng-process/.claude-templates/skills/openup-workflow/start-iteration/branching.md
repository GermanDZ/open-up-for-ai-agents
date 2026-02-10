# Branching Procedures for Start Iteration

This document provides detailed procedures for creating task-based branches following OpenUP branching conventions.

## Overview

**IMPORTANT**: OpenUP uses task-based branching, not iteration-based branching. Each branch is named according to the specific task being worked on, ensuring clear traceability between code changes and roadmap tasks.

### Task-Based Branch Naming Convention

```
{task-type}/{task_id}-{short-description}
```

Where `task-type` is determined by the nature of the work:
- `feature/` - New features or functionality
- `bugfix/` - Bug fixes or defect resolution
- `refactor/` - Code refactoring or restructuring
- `docs/` - Documentation updates
- `test/` - Test additions or improvements
- `task/` - Default for other task types

### Branch Naming Examples

| Task Type | Task ID | Description | Branch Name |
|-----------|---------|-------------|-------------|
| Feature | T-005 | User authentication | `feature/T-005-user-authentication` |
| Bugfix | T-012 | Login timeout issue | `bugfix/T-012-login-timeout` |
| Refactor | T-008 | API cleanup | `refactor/T-008-api-cleanup` |
| Documentation | T-003 | API guide | `docs/T-003-api-guide` |
| Test | T-015 | Integration tests | `test/T-015-integration-tests` |
| Generic | T-007 | Configuration | `task/T-007-configuration` |

### Branch Name Generation Rules

1. **Derive task type** from roadmap task tags or description
2. **Use exact task_id** from roadmap (e.g., T-005)
3. **Create short description** (max 50 chars, kebab-case):
   - Remove articles (a, an, the)
   - Use lowercase
   - Replace spaces with hyphens
   - Limit to key words

## Branch Creation Process

### 1. Read Roadmap Task

Before creating a branch, the team lead must:
1. Read `docs/roadmap.md` to find the task
2. Extract task details: id, title, type, description
3. Validate task is ready to start (not blocked, dependencies met)

### 2. Determine Task Type

Based on task tags, description, or category:

| Task Pattern | Branch Type |
|--------------|-------------|
| "Implement", "Add", "Create" | `feature/` |
| "Fix", "Bug", "Issue" | `bugfix/` |
| "Refactor", "Clean up", "Restructure" | `refactor/` |
| "Document", "Doc", "Guide" | `docs/` |
| "Test", "Testing", "Spec" | `test/` |
| Other | `task/` |

### 3. Generate Branch Name

**Format**: `{task-type}/{task_id}-{short-description}`

**Examples**:
- Task: `T-005: Implement user authentication system`
- Branch: `feature/T-005-user-authentication`

- Task: `T-012: Fix login timeout bug`
- Branch: `bugfix/T-012-login-timeout`

- Task: `T-008: Refactor API endpoints`
- Branch: `refactor/T-008-api-endpoints`

### 4. Detect Trunk Branch

Follow the trunk detection algorithm:

```bash
# Method 1: Check origin/HEAD
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'

# Method 2: Fallback to common names
# Try: main, master, develop, development

# Method 3: Use current branch's remote tracking branch
git for-each-ref --format='%(upstream:short)' $(git symbolic-ref -q HEAD)
```

### 5. Create Task Branch

**Switch to trunk first**:
```bash
git checkout <trunk>
git pull origin <trunk>
```

**Create new task branch**:
```bash
git checkout -b {task-type}/{task_id}-{short-description}
```

**Examples**:
```bash
# Feature branch
git checkout -b feature/T-005-user-authentication

# Bugfix branch
git checkout -b bugfix/T-012-login-timeout

# Refactor branch
git checkout -b refactor/T-008-api-cleanup
```

### 6. Push Branch to Remote

```bash
git push -u origin {task-type}/{task_id}-{short-description}
```

## Merging Task Branches

### When to Merge

Merge task branch when:
- Task is complete and tested
- All acceptance criteria met
- Code review approved
- Tests pass
- Ready for integration

### Merge Process

```bash
# 1. Switch to trunk
git checkout <trunk>

# 2. Pull latest
git pull origin <trunk>

# 3. Merge task branch
git merge {task-type}/{task_id}-{short-description}

# 4. Run tests
npm test  # or equivalent

# 5. Push merge
git push origin <trunk>

# 6. Delete task branch (optional)
git branch -d {task-type}/{task_id}-{short-description}
```

### Pull Request Workflow

When using pull requests:

1. Create PR from task branch to trunk
2. PR title should reference task: `[T-005] Implement user authentication`
3. PR description should include:
   - Task ID and title from roadmap
   - Summary of changes
   - Testing performed
   - Related tasks or dependencies

## Cleaning Up Old Branches

### List Task Branches

```bash
# List all task branches
git branch | grep -E '^(feature|bugfix|refactor|docs|test|task)/'

# List branches for specific task
git branch | grep T-005
```

### Delete Local Branches

```bash
# Safe delete (only if merged)
git branch -d feature/T-005-user-authentication

# Force delete (even if not merged)
git branch -D feature/T-005-user-authentication
```

### Delete Remote Branches

```bash
git push origin --delete feature/T-005-user-authentication
```

## Task Branch Tracking

### Branch-to-Task Mapping

Each branch name contains the task ID for traceability:

```
feature/T-005-user-authentication  →  T-005 in roadmap
bugfix/T-012-login-timeout        →  T-012 in roadmap
refactor/T-008-api-cleanup        →  T-008 in roadmap
```

### Updating Roadmap

When creating/merging branches:
1. Update task status in `docs/roadmap.md`
2. Track branch name in task metadata
3. Link PR/merge to task for traceability

## Troubleshooting

### Branch Already Exists

If task branch already exists:
1. Check if task is complete (branch can be reused)
2. If complete and merged, delete old branch and create new one
3. If incomplete, continue on existing branch

### Cannot Create Branch

If branch creation fails:
1. Check for uncommitted changes
2. Resolve merge conflicts if any
3. Ensure trunk branch is up to date
4. Verify branch name doesn't contain invalid characters

### Push Fails

If push fails:
1. Check remote configuration
2. Verify authentication
3. Check if branch already exists on remote
4. Use `--force-with-lease` if necessary (with caution)

## Verification Checklist

After creating task branch, verify:
- [ ] Branch name includes task_id from roadmap
- [ ] Branch type matches task nature (feature, bugfix, etc.)
- [ ] Branch is based on latest trunk
- [ ] Branch is pushed to remote
- [ ] Project status is updated with current task
- [ ] Team is notified of new branch

## Traceability

### Git Commit Messages

When committing on task branches, reference the task:

```
[T-005] Add login form UI component

Implements the login form with email and password fields.
Related to T-005: User authentication system.
```

### Pull Request Titles

PR titles should clearly link to tasks:

```
[T-005] Implement User Authentication System
[T-012] Fix Login Timeout Bug
[T-008] Refactor API Endpoints
```

### Documentation Updates

When completing tasks:
1. Update task status in roadmap
2. Mark task_id in commit messages
3. Reference task_id in PR descriptions
4. Link branch to task in any relevant docs

## References

- Branching SOP: `docs-eng-process/agent-workflow.md`
- Git Branch Documentation: https://git-scm.com/docs/git-branch
- OpenUP Iteration Guidelines: `docs-eng-process/openup-knowledge-base/practice-management/risk_value_lifecycle/`

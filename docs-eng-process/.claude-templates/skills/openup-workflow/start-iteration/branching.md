# Branching Procedures for Start Iteration

This document provides detailed procedures for creating iteration branches following OpenUP branching conventions.

## Overview

Each iteration should have its own branch following the naming convention:
```
iteration/{phase}-it{iteration_number}
```

Examples:
- `iteration/inception-it1`
- `iteration/elaboration-it2`
- `iteration/construction-it3`

## Branch Creation Process

### 1. Detect Trunk Branch

Follow the trunk detection algorithm:

```bash
# Method 1: Check origin/HEAD
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'

# Method 2: Fallback to common names
# Try: main, master, develop, development

# Method 3: Use current branch's remote tracking branch
git for-each-ref --format='%(upstream:short)' $(git symbolic-ref -q HEAD)
```

### 2. Check Current Branch Lifecycle

Determine if current branch should be used or new branch created:

**Use current branch if**:
- Already on trunk branch
- Branch name follows iteration convention
- No uncommitted changes

**Create new branch if**:
- On feature branch that's complete
- Need to start fresh iteration
- Team convention requires iteration branches

### 3. Create Iteration Branch

**Switch to trunk first**:
```bash
git checkout <trunk>
git pull origin <trunk>
```

**Create new iteration branch**:
```bash
git checkout -b iteration/{phase}-it{iteration_number}
```

**Examples**:
```bash
# Inception, iteration 1
git checkout -b iteration/inception-it1

# Elaboration, iteration 2
git checkout -b iteration/elaboration-it2

# Construction, iteration 3
git checkout -b iteration/construction-it3
```

### 4. Push Branch to Remote

```bash
git push -u origin iteration/{phase}-it{iteration_number}
```

## Branch Naming Convention

### Format

```
iteration/{phase}-it{number}
```

### Components

- `iteration/` - Prefix indicating iteration branch
- `{phase}` - OpenUP phase (inception, elaboration, construction, transition)
- `it{number}` - Iteration number with 'it' prefix

### Examples

| Phase | Iteration | Branch Name |
|-------|-----------|-------------|
| Inception | 1 | `iteration/inception-it1` |
| Elaboration | 1 | `iteration/elaboration-it1` |
| Elaboration | 2 | `iteration/elaboration-it2` |
| Construction | 1 | `iteration/construction-it1` |
| Construction | 5 | `iteration/construction-it5` |
| Transition | 1 | `iteration/transition-it1` |

## Alternative Branching Strategies

### Feature-Based Branches

Some teams prefer feature-based branches within iterations:

```
iteration/construction-it3/
├── feature/T-005-auth
├── feature/T-006-profile
└── feature/T-007-notifications
```

### Task-Based Branches

For smaller tasks:

```
iteration/construction-it3/
├── task/T-005
├── task/T-006
└── task/T-007
```

### Select Strategy

Consider:
- Team size
- Task complexity
- CI/CD pipeline
- Code review workflow

## Merging Iteration Branches

### When to Merge

Merge iteration branch when:
- All iteration tasks are complete
- Tests pass
- Code is reviewed
- Ready for integration

### Merge Process

```bash
# 1. Switch to trunk
git checkout <trunk>

# 2. Pull latest
git pull origin <trunk>

# 3. Merge iteration branch
git merge iteration/{phase}-it{number}

# 4. Push merge
git push origin <trunk>

# 5. Delete iteration branch (optional)
git branch -d iteration/{phase}-it{number}
```

## Cleaning Up Old Branches

### List Iteration Branches

```bash
git branch | grep iteration/
```

### Delete Local Branches

```bash
git branch -d iteration/inception-it1
```

### Delete Remote Branches

```bash
git push origin --delete iteration/inception-it1
```

## Troubleshooting

### Branch Already Exists

If iteration branch already exists:
1. Check if iteration is complete
2. If complete, start new iteration with incremented number
3. If incomplete, continue on existing branch

### Cannot Create Branch

If branch creation fails:
1. Check for uncommitted changes
2. Resolve merge conflicts if any
3. Ensure trunk branch is up to date

### Push Fails

If push fails:
1. Check remote configuration
2. Verify authentication
3. Check if branch exists on remote

## Verification Checklist

After creating iteration branch, verify:
- [ ] Branch follows naming convention
- [ ] Branch is based on latest trunk
- [ ] Branch is pushed to remote
- [ ] Project status is updated
- [ ] Team is notified of new branch

## References

- Branching SOP: `docs-eng-process/agent-workflow.md`
- Git Branch Documentation: https://git-scm.com/docs/git-branch
- OpenUP Iteration Guidelines: `docs-eng-process/openup-knowledge-base/practice-management/risk_value_lifecycle/`

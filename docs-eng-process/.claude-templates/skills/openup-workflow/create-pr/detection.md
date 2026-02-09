# Detection Procedures for Create PR

This document provides detailed procedures for detecting the current state when creating a pull request.

## Overview

Before creating a PR, the skill must detect:
1. Current branch
2. Unmerged commits
3. Platform (GitHub or GitLab)
4. Remote repository
5. Trunk branch

## Detecting Current Branch

### Method 1: Use Argument

If `branch` argument is provided, use it directly.

### Method 2: Git Command

```bash
git rev-parse --abbrev-ref HEAD
```

Output: Current branch name (e.g., `feature/T-005-auth`)

## Detecting Unmerged Commits

### Purpose

Determine if there are commits on current branch that haven't been merged to trunk.

### Process

1. **Detect trunk branch** (see below)
2. **Check for unmerged commits**:
   ```bash
   git log <trunk>..HEAD --oneline
   ```

### Interpretation

- **Empty output**: No unmerged commits, PR not needed
- **Output shows commits**: Proceed with PR creation

### Examples

```bash
# No unmerged commits
$ git log main..HEAD --oneline
# (no output - PR not needed)

# Unmerged commits exist
$ git log main..HEAD --oneline
abc123def Add login form
def456ghi Implement auth service
# (proceed with PR creation)
```

## Detecting Platform

### GitHub CLI

```bash
command -v gh
```

- **Returns path**: GitHub CLI is installed
- **Empty return**: GitHub CLI not installed

### GitLab CLI

```bash
command -v glab
```

- **Returns path**: GitLab CLI is installed
- **Empty return**: GitLab CLI not installed

### Neither Found

If neither CLI is found:
1. Inform user they need to install one
2. Provide installation instructions
3. Exit gracefully

## Detecting Remote

### Check for Origin

```bash
git remote get-url origin
```

### Interpretation

- **Returns URL**: Remote is configured
- **Error**: No remote configured

### No Remote Scenario

If no remote is configured:
1. Prompt user to add remote
2. Example: `git remote add origin <url>`
3. Exit and let user configure

## Detecting Trunk Branch

### Algorithm

Follow this priority order:

1. **Check origin/HEAD**:
   ```bash
   git symbolic-ref refs/remotes/origin/HEAD
   ```
   Output: `refs/remotes/origin/<branch-name>`

2. **Fallback to common names** (in order):
   - `main`
   - `master`
   - `develop`
   - `development`

3. **Final fallback**: Current branch's remote tracking branch

4. **Override**: Use `base` argument if provided

### Always Record Trunk

Document what was detected as trunk in the run log for traceability.

## Complete Detection Example

```bash
# 1. Get current branch
$ branch=$(git rev-parse --abbrev-ref HEAD)
$ echo $branch
feature/T-005-auth

# 2. Detect trunk
$ trunk=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
$ echo ${trunk:-main}
main

# 3. Check for unmerged commits
$ git log $trunk..HEAD --oneline
abc123def Add login form
def456ghi Implement auth service

# 4. Detect platform
$ command -v gh
/usr/bin/gh

# 5. Check remote
$ git remote get-url origin
git@github.com:user/repo.git
```

## State Summary Table

| Check | Command | Success Output | Failure Action |
|-------|---------|----------------|----------------|
| Current branch | `git rev-parse --abbrev-ref HEAD` | Branch name | Use argument or error |
| Unmerged commits | `git log <trunk>..HEAD` | Commit list | Exit: no PR needed |
| Platform | `command -v gh` | CLI path | Check glab, then error |
| Remote | `git remote get-url origin` | Remote URL | Prompt user |
| Trunk | `git symbolic-ref ...` | Branch name | Try main/master |

## Verification Checklist

After detection, verify:
- [ ] Current branch is identified
- [ ] Unmerged commits exist (or exit gracefully)
- [ ] Platform CLI is available
- [ ] Remote is configured
- [ ] Trunk branch is detected
- [ ] Detection results are logged

## References

- Git Branch Documentation: https://git-scm.com/docs/git-branch
- GitHub CLI: https://cli.github.com/
- GitLab CLI: https://glab.readthedocs.io/

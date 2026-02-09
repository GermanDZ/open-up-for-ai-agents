# Commit Procedure for Complete Task

This document provides detailed procedures for committing changes when completing a task.

## Prerequisites

Before committing, ensure:
- All implementation work is complete
- All tests pass
- Code has been reviewed (if applicable)
- Documentation has been updated

## Commit Steps

### 1. Stage Changes

Stage all changes for commit:
```bash
git add -A
```

Or selectively stage specific files:
```bash
git add <file1> <file2>
```

### 2. Create Commit Message

Generate a descriptive commit message:

**Format**:
```
Complete task <task_id>: <task description>

<optional detailed description>

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

**Examples**:
- `Complete task T-005: Implement user authentication`
- `Complete task T-012: Add error handling to API endpoints`
- `Complete task T-003: Fix login form validation bug`

### 3. Create the Commit

```bash
git commit -m "<commit message>"
```

### 4. Verify Commit

Verify the commit was created successfully:
```bash
git log -1 --oneline
```

Expected output: `<commit-sha> Complete task <task_id>: <description>`

Record the commit SHA for traceability logging.

### 5. Verify No Uncommitted Changes

Ensure no uncommitted changes remain:
```bash
git status --porcelain
```

Expected output: Empty (no output)

If there are uncommitted changes, stage and commit them.

## Troubleshooting

### Pre-commit Hook Failures

If a pre-commit hook fails:
1. Read the error message carefully
2. Fix the identified issues
3. Try the commit again

### Merge Conflicts

If there are merge conflicts:
1. Resolve the conflicts
2. Stage the resolved files
3. Complete the commit

### Large Files

If committing large files:
1. Consider if they should be in repository
2. Use Git LFS if appropriate
3. Add to .gitignore if not needed

## Verification Checklist

After committing, verify:
- [ ] Commit message includes task ID
- [ ] Commit message describes changes
- [ ] All relevant files are included
- [ ] No uncommitted changes remain
- [ ] Commit SHA is recorded

## References

- Git Commit Documentation: https://git-scm.com/docs/git-commit
- Traceability Logging SOP: `docs-eng-process/agent-workflow.md`

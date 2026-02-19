---
name: openup-quick-task
description: Fast iteration mode for small changes - simplified workflow with minimal overhead
arguments:
  - name: task
    description: Brief description of the task to complete
    required: true
  - name: task_id
    description: Roadmap task ID (optional, creates task if not provided)
    required: false
  - name: skip_branch
    description: "Skip branch creation (default: false)"
    required: false
  - name: skip_commit
    description: "Skip auto-commit (default: false)"
    required: false
  - name: skip_logging
    description: "Skip traceability logging (default: false)"
    required: false
---

# Quick Task - Fast Iteration Mode

**Quick Task** is a lightweight workflow for small changes and rapid iteration. It combines multiple steps into a single command while maintaining essential OpenUP practices.

## When to Use

Use Quick Task for:
- Small bug fixes (< 50 lines changed)
- Documentation updates
- Configuration changes
- Quick experiments
- Hot fixes

**Target**: Complete tasks in 50% less time than standard workflow.

## When NOT to Use

Do NOT use for:
- New features (use standard workflow)
- Major refactoring (use `/openup-start-iteration`)
- Tasks requiring architecture review (use full team)
- Multi-hour development work

## Process

### 1. Quick Context Load

```bash
# Load minimal context only
python3 .claude/scripts/batch-context.py --minimal
```

### 2. Quick Branch (optional)

If not skipping branching:
```bash
# Detect trunk and create quick branch
BRANCH_NAME="quick/$(date +%Y%m%d-%H%M%S)-$(echo $task | tr ' ' '-' | head -c 20)"
git checkout -b $BRANCH_NAME
```

### 3. Execute Task

Implement the change:
- Read task description
- Make necessary changes
- Verify the fix works

### 4. Quick Commit (optional)

If not skipping commit:
```bash
git add .
git commit -m "quick: $task

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

### 5. Quick Log (optional)

If not skipping logging:
```bash
echo "$(date -Iseconds) | quick-task | $task" >> docs/agent-logs/quick-tasks.log
```

## Output

Returns:
- Task completed confirmation
- Files changed (count)
- Branch name (if created)
- Commit hash (if committed)

## Comparison: Standard vs Quick

| Step | Standard Workflow | Quick Task |
|------|-------------------|------------|
| Read project-status | Full document | Minimal only |
| Create branch | Task-based naming | Timestamp-based |
| SOP compliance | Full Start-of-Run | Skipped |
| Documentation | Full update | Minimal |
| Log entry | Full JSONL | Simple log line |
| **Typical time** | ~8 minutes | ~4 minutes |

## Examples

### Quick Bug Fix
```
/openup-quick-task task: "Fix typo in README.md"
```

### Documentation Update
```
/openup-quick-task task: "Update API docs for new endpoint"
```

### Skip Branching
```
/openup-quick-task task: "Add comment to utils.py" skip_branch: true
```

### Full Control
```
/openup-quick-task task: "Hot fix auth bug" skip_commit: false skip_logging: true
```

## Success Criteria

- [ ] Task completed
- [ ] Changes verified
- [ ] Branch created (if not skipped)
- [ ] Committed (if not skipped)
- [ ] Logged (if not skipped)

## Smart Features

**Auto-detect skip opportunities:**
- If already on feature branch → skip branching
- If no git changes → skip commit
- If single file change → minimal logging

**Auto-categorize task:**
- Bug fixes → `bugfix/` prefix
- Docs → `docs/` prefix
- Hot fixes → `hotfix/` prefix

## See Also

- [openup-start-iteration](../start-iteration/SKILL.md) - Full iteration workflow
- [openup-complete-task](../complete-task/SKILL.md) - Task completion with PR
- [openup-tdd-workflow](../tdd-workflow/SKILL.md) - TDD cycle

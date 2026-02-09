---
name: complete-task
description: Mark a task as complete, update roadmap, commit changes, and prepare traceability logs
arguments:
  - name: task_id
    description: The task ID to mark as complete (e.g., T-001)
    required: true
  - name: commit_message
    description: Custom commit message (optional, auto-generates if not provided)
    required: false
---

# Complete Task

This skill finalizes a completed task by committing all changes, updating documentation, and preparing traceability logs.

## Process

### 1. Verify Task Completion

Before marking a task as complete, verify:
- All implementation work is done
- All tests pass
- Documentation is updated

### 2. Commit All Changes

**MANDATORY**: All changes must be committed before proceeding.

1. Stage all changes: `git add -A` (or selectively stage)
2. Create commit with descriptive message:
   - Use `$ARGUMENTS[commit_message]` if provided
   - Otherwise auto-generate: "Complete task $ARGUMENTS[task_id]: <task description>"
   - Include task ID in commit message
3. Verify commit exists: `git log -1 --oneline`
4. Record commit SHA

### 3. Verify No Uncommitted Changes

Run `git status --porcelain` and verify it returns empty.

### 4. Update Roadmap

Update `docs/roadmap.md`:
- Mark task `$ARGUMENTS[task_id]` as `completed`
- Add completion date
- Update any dependencies

### 5. Update Project Status

Update `docs/project-status.md`:
- Update "Active Work Items" table
- Update `last_updated` and `updated_by` fields

### 6. Create Traceability Logs

Create both markdown and JSONL logs (see Traceability Logging SOP):
- Markdown log: `docs/agent-logs/YYYY/MM/DD/<timestamp>-<agent>-<branch>.md`
- JSONL entry: Append to `docs/agent-logs/agent-runs.jsonl`
- Include commit SHAs in the logs

## Output

Returns a summary of:
- Task completed
- Commit SHA
- Files changed
- Log locations

## References

- Agent Workflow End-of-Run SOP: `docs-eng-process/agent-workflow.md`
- Traceability Logging SOP: `docs-eng-process/agent-workflow.md`

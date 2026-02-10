---
name: openup-complete-task
description: Mark a task as complete, update roadmap, commit changes, and prepare traceability logs
arguments:
  - name: task_id
    description: The task ID to mark as complete (e.g., T-001)
    required: true
  - name: commit_message
    description: Custom commit message (optional, auto-generates if not provided)
    required: false
  - name: create_pr
    description: Create a pull request after completing the task (optional, default false)
    required: false
---

# Complete Task

This skill finalizes a completed task by committing all changes, updating documentation, and preparing traceability logs.

## When to Use

Use this skill when:
- A task implementation is complete and ready to commit
- All tests pass for the task
- Documentation has been updated
- Ready to update roadmap and mark task complete
- Need to create traceability logs for the work

## When NOT to Use

Do NOT use this skill when:
- Still implementing the task (finish implementation first)
- Tests are failing (fix tests first)
- Just need to commit without updating roadmap (use git directly)
- Looking to create PR without completing task (use `/openup-create-pr`)

## Success Criteria

After using this skill, verify:
- [ ] All changes are committed with descriptive message
- [ ] No uncommitted changes remain
- [ ] Roadmap is updated to mark task complete
- [ ] Project status is updated
- [ ] Traceability logs are created with commit SHAs
- [ ] PR is created (if create_pr=true)

## Process Summary

1. Verify task completion
2. Commit all changes
3. Update documentation
4. Create traceability logs
5. Optionally create PR

## Detailed Steps

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

Create both markdown and JSONL logs:
- Markdown log: `docs/agent-logs/YYYY/MM/DD/<timestamp>-<agent>-<branch>.md`
- JSONL entry: Append to `docs/agent-logs/agent-runs.jsonl`
- Include commit SHAs in the logs

### 7. Optionally Create Pull Request

If `$ARGUMENTS[create_pr] == "true"`:

1. **Verify current branch has unmerged commits**:
   - Run: `git log <trunk>..HEAD --oneline`
   - Proceed only if unmerged commits exist

2. **Invoke `/openup-create-pr` skill**:
   - Pass `task_id: $ARGUMENTS[task_id]`
   - Let the skill auto-detect branch and generate description

3. **Inform user of result**:
   - If PR created successfully: Provide PR URL
   - If PR creation failed: Explain error and provide next steps
   - If no unmerged commits: Inform user that PR is not needed

Example usage:
```
/openup-complete-task task_id: T-005 create_pr: true
```

## Output

Returns a summary of:
- Task completed
- Commit SHA
- Files changed
- Log locations
- PR URL (if create_pr was true)

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Uncommitted changes remain | Not all files were staged/committed | Run `git add -A && git commit` |
| Commit failed | Pre-commit hook or merge conflict | Resolve issue and retry commit |
| Roadmap task not found | Task ID doesn't exist in roadmap | Verify task ID or update roadmap first |
| PR creation failed | No unmerged commits or remote issue | Check branch status and remote |

## References

- Agent Workflow End-of-Run SOP: `docs-eng-process/agent-workflow.md`
- Traceability Logging SOP: `docs-eng-process/agent-workflow.md`

## See Also

- [openup-assess-completeness](../assess-completeness/SKILL.md) - Assess task completeness before marking complete
- [openup-create-pr](../create-pr/SKILL.md) - Create pull request separately
- [openup-log-run](../log-run/SKILL.md) - Traceability logging details
- [openup-start-iteration](../start-iteration/SKILL.md) - Begin next iteration

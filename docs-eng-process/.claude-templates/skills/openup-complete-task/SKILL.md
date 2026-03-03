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
    description: "Create a pull request after completing the task (default: true — set to 'false' to skip)"
    required: false
---

# Complete Task

Finalize a completed task: commit remaining changes, update docs, create traceability logs, and create a PR.

## Success Criteria

After this skill completes, ALL of these must be true:

- [ ] All changes are committed (no uncommitted changes remain)
- [ ] Commit messages follow canonical format: `type(scope): description [T-XXX]`
- [ ] Roadmap is updated to mark task complete
- [ ] Project status is updated
- [ ] Traceability logs are created with commit SHAs
- [ ] PR is created (unless `create_pr` was explicitly `"false"`)

## Detailed Steps

### 1. Verify Task Completion

Before marking a task as complete, verify:
- All implementation work is done
- All tests pass
- Documentation is updated

### 2. Commit Remaining Changes

Most changes should already be committed as atomic commits during implementation (see `commit-procedure.md`). This step handles any leftover uncommitted work.

1. Run `git status --porcelain` to check for uncommitted changes
2. If changes exist:
   - Stage relevant files: `git add <files>`
   - Commit using canonical format: `type(scope): description [$ARGUMENTS[task_id]]`
   - Use `$ARGUMENTS[commit_message]` if provided
3. Verify: `git status --porcelain` returns empty

### 3. Update Roadmap

Update `docs/roadmap.md`:
- Mark task `$ARGUMENTS[task_id]` as `completed`
- Add completion date

### 4. Update Project Status

Update `docs/project-status.md`:
- Update "Active Work Items" table
- Update `last_updated` and `updated_by` fields

### 5. Create Traceability Logs

Create both markdown and JSONL logs:
- Markdown log: `docs/agent-logs/YYYY/MM/DD/<timestamp>-<agent>-<branch>.md`
- JSONL entry: Append to `docs/agent-logs/agent-runs.jsonl`
- Include commit SHAs in the logs

### 6. Create Pull Request

**PR is created by default.** Skip ONLY if `$ARGUMENTS[create_pr]` is explicitly `"false"`.

1. Push the branch:
   ```bash
   git push -u origin $(git rev-parse --abbrev-ref HEAD)
   ```

2. Verify unmerged commits exist:
   ```bash
   git log <trunk>..HEAD --oneline
   ```

3. Invoke `/openup-create-pr` skill with `task_id: $ARGUMENTS[task_id]`

4. Report result to user:
   - Success → provide PR URL
   - No unmerged commits → inform user PR is not needed
   - Failure → explain error and provide manual steps

## Output

Returns a summary of:
- Task completed
- Commit SHAs
- Files changed
- Log locations
- PR URL

## See Also

- [openup-create-pr](../create-pr/SKILL.md) - Create pull request separately
- [openup-log-run](../log-run/SKILL.md) - Traceability logging details
- [openup-start-iteration](../start-iteration/SKILL.md) - Begin next iteration

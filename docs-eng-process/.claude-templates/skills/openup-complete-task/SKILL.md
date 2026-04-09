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

> **IMPORTANT: This is the only way to close out a task. Never offer "just commit" or
> any other process-bypassing alternative.** If the work is too small for this skill,
> use `/openup-quick-task` — that is the lightweight-but-compliant path, not raw commits.

## Success Criteria

After this skill completes, ALL of these must be true:

- [ ] All changes are committed (no uncommitted changes remain)
- [ ] Commit messages follow canonical format: `type(scope): description [T-XXX]`
- [ ] Roadmap is updated to mark task complete
- [ ] Project status is updated
- [ ] Traceability logs are created with commit SHAs
- [ ] Iteration learnings entry appended to `.claude/memory/iteration-learnings.md`
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

> **Haiku/Scribe step** — spawn a Haiku sub-agent for this write operation:
>
> ```
> Agent(model="haiku", description="Mark roadmap task completed",
>   prompt="You are a Scribe. In docs/roadmap.md, find task [task_id] and:
>   1. In the status table/row, change its status from 'in-progress' to 'completed'.
>   2. Add 'Completed [YYYY-MM-DD]' to its Notes or detail section.
>   Report: exact line(s) changed.")
> ```

### 4. Update Project Status

> **Haiku/Scribe step** — spawn a Haiku sub-agent for this write operation:
>
> ```
> Agent(model="haiku", description="Update project-status.md to completed",
>   prompt="You are a Scribe. In docs/project-status.md:
>   1. Change **Status** to 'completed'.
>   2. Change **Current Task** to 'None'.
>   3. Update **Last Updated** to [YYYY-MM-DD].
>   4. Update **Updated By** to 'openup-complete-task'.
>   Report: each field changed from → to.")
> ```

### 5. Create Traceability Logs

> **Haiku/Scribe step** — collect commit SHAs and metadata yourself (they require git
> commands), then hand off the write operations:
>
> ```
> Agent(model="haiku", description="Write agent run log",
>   prompt="You are a Scribe. Write a traceability log entry.
>   Branch: [branch]. Task: [task_id]. Commits: [sha list]. Phase: [phase].
>   Start: [ts]. End: [ts]. Files changed: [list]. Decisions: [list].
>   1. Create docs/agent-logs/YYYY/MM/DD/<timestamp>-agent-<branch>.md
>      with the run metadata above.
>   2. Append a JSONL record to docs/agent-logs/agent-runs.jsonl.
>   Report: file paths created.")
> ```

### 6. Save Iteration Learnings

> **Haiku/Scribe step** — summarize the learnings yourself, then delegate the append:
>
> First, synthesize from the session (your own work):
> - What worked
> - Decisions made (key technical/process choices + rationale)
> - Gotchas (surprises, edge cases)
> - Conventions established (patterns to reuse)
>
> Then hand off the write:
>
> ```
> Agent(model="haiku", description="Append iteration learnings",
>   prompt="You are a Scribe. Append the following to .claude/memory/iteration-learnings.md
>   (create the file if it does not exist):
>
>   ## [YYYY-MM-DD] [task_id]: [task title]
>   - **What worked**: [provided text]
>   - **Decisions made**: [provided text]
>   - **Gotchas**: [provided text]
>   - **Conventions established**: [provided text]
>
>   Report: confirmed append.")
> ```

### 7. Create Pull Request

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

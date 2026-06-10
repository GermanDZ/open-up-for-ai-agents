---
name: openup-complete-task
description: Mark a task as complete, update roadmap, commit changes, and prepare traceability logs
model: inherit
fit:
  great: [finishing a roadmap-tracked task, ending an iteration cleanly]
  ok: [closing out ad-hoc work that needs commit + roadmap update]
  poor: [mid-task checkpoints, abandoning work-in-progress]
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
- [ ] Iteration gates pass (`openup-state.py check-gates`) and state is archived
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

> **Scribe step** — delegate to the `openup-scribe` agent (Agent tool,
> subagent_type: "openup-scribe"). You determine the values; the scribe only
> writes. Brief it with:
>
> ```
> Agent(subagent_type="openup-scribe", description="Mark roadmap task completed",
>   prompt="In docs/roadmap.md, find task [task_id] and:
>   1. In the status table/row, change its status from 'in-progress' to 'completed'.
>   2. Add 'Completed [YYYY-MM-DD]' to its Notes or detail section.
>   Report: exact line(s) changed.")
> ```

Once the roadmap is updated, record the gate:

```bash
python3 scripts/openup-state.py set-gate roadmap_synced true
```

### 4. Update Project Status

> **Scribe step** — delegate to the `openup-scribe` agent (Agent tool,
> subagent_type: "openup-scribe"). You determine the values; the scribe only
> writes. Brief it with:
>
> ```
> Agent(subagent_type="openup-scribe", description="Update project-status.md to completed",
>   prompt="In docs/project-status.md:
>   1. Change **Status** to 'completed'.
>   2. Change **Current Task** to 'None'.
>   3. Update **Last Updated** to [YYYY-MM-DD].
>   4. Update **Updated By** to 'openup-complete-task'.
>   Report: each field changed from → to.")
> ```

### 5. Create Traceability Logs

> **Scribe step** — collect commit SHAs and metadata yourself (they require git
> commands), then delegate the writes to the `openup-scribe` agent (Agent tool,
> subagent_type: "openup-scribe"). Brief it with:
>
> ```
> Agent(subagent_type="openup-scribe", description="Write agent run log",
>   prompt="Write a traceability log entry.
>   Branch: [branch]. Task: [task_id]. Commits: [sha list]. Phase: [phase].
>   Start: [ts]. End: [ts]. Files changed: [list]. Decisions: [list].
>   1. Create docs/agent-logs/YYYY/MM/DD/<timestamp>-agent-<branch>.md
>      with the run metadata above.
>   2. Append a JSONL record to docs/agent-logs/agent-runs.jsonl.
>   Report: file paths created.")
> ```

### 6. Save Iteration Learnings

> **Scribe step** — summarize the learnings yourself, then delegate the append
> to the `openup-scribe` agent (Agent tool, subagent_type: "openup-scribe"):
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
> Agent(subagent_type="openup-scribe", description="Append iteration learnings",
>   prompt="Append the following to .claude/memory/iteration-learnings.md
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

### 7. Check Gates and Archive Iteration State

**Verify all required gates pass before finalizing.** If this exits nonzero, completion is **blocked** — surface the unmet gates (printed one per line on stderr) and resolve each before continuing:

```bash
python3 scripts/openup-state.py check-gates
```

(Quick-track iterations were started with `--track quick`; for those use `check-gates --require log_written,roadmap_synced`.)

Once gates pass, archive the iteration state and the **change folder** (Ring 2 → `docs/changes/archive/`).

**If the task has a change folder** (`docs/changes/{task_id}/` exists — the standard three-ring case):

```bash
# 1. Archive .openup/state.json INTO the change folder as state.json (validate, copy, remove live file)
python3 scripts/openup-state.py archive "docs/changes/{task_id}/state.json"
# 2. Move the whole change folder into the archive ring (preserves history)
git mv "docs/changes/{task_id}" "docs/changes/archive/{task_id}"
```

**Otherwise** (legacy / quick-track task with no change folder), archive the state into the dated agent-logs tree:

```bash
python3 scripts/openup-state.py archive \
  "docs/agent-logs/$(date -u +%Y)/$(date -u +%m)/$(date -u +%d)/state-{task_id}.json"
```

Either way the live `.openup/state.json` is removed by the `archive` command. Commit the archive move with the task's other completion commits.

### 8. Create Pull Request

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

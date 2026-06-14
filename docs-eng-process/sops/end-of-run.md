# End-of-Run SOP

> Extracted from `agent-workflow.md` so skills that need only the end-of-run
> procedure load this file instead of the whole operating-procedures document.

**⚠️ MANDATORY: Every agent run MUST complete these steps before stopping. A task is NOT complete until all steps are finished.**

**Every agent run MUST end with these steps in order:**

## Step 1: Commit All Changes

**REQUIRED**: All changes made during the task must be committed to git before proceeding.

1. **Stage all changes**: `git add -A` (or selectively stage specific files)
2. **Create commit**: `git commit -m "<descriptive commit message>"`
   - Include task ID/description in the commit message
   - Make the commit message descriptive of what was accomplished
3. **Verify commit exists**: `git log -1 --oneline` to confirm the commit was created
4. **Record commit SHA**: Note the commit SHA for inclusion in traceability logs

**CRITICAL**: If there are any uncommitted changes, the task is NOT complete. Do NOT proceed to the next step until `git status --porcelain` shows no changes.

## Step 2: Verify No Uncommitted Changes

**REQUIRED**: Verify that all changes are committed:

- Run `git status --porcelain`
- If any output is shown, there are uncommitted changes - return to Step 1
- Only proceed when `git status --porcelain` returns empty (no output)

**MANDATORY**: You MUST NOT declare a task finished or stop the run if there are uncommitted changes. Uncommitted changes mean the task execution history is not persisted.

## Step 3: Create Traceability Logs

**REQUIRED**: Create both markdown and JSONL logs (see [Traceability Logging SOP](../agent-workflow.md#traceability-logging-sop)):

1. Create markdown log at `docs/agent-logs/YYYY/MM/DD/<timestamp>-<agent>-<branch>.md`
2. Append JSONL entry to `docs/agent-logs/agent-runs.jsonl`
3. **Include commit SHAs**: The `commits` field in the JSONL must contain the actual commit SHAs from Step 1
4. Verify the logs reference the commits that were just created

## Step 4: Update Documentation

**REQUIRED**: Update project documentation to reflect completed work:

- Update phase notes in `docs/phases/{phase}/notes.md`
- If permission was granted: update `docs/project-status.md` (Active Work Items table, `last_updated`, `updated_by`)
- If permission was granted: update `docs/roadmap.md` (mark task as completed)
- Create/update decision records if architectural decisions were made

## Step 5: Final Verification

Before stopping, verify:

- [ ] All changes are committed (Step 1 complete)
- [ ] No uncommitted changes exist (Step 2 verified)
- [ ] Traceability logs created with commit SHAs (Step 3 complete)
- [ ] Documentation updated (Step 4 complete)
- [ ] Task is marked as complete in roadmap (if permission granted)

## Output Size Discipline (All Steps)

During end-of-run execution, keep command output compact:

- Prefer command summaries over full stdout dumps
- For noisy tools, report counts, failure summary, and a short tail excerpt
- Avoid re-running state checks unless new information is expected

**ONLY after all steps are complete**: Inform the user that the task is finished and stop. Do not proceed to additional tasks in this run.

## Failure to Complete End-of-Run SOP

If an agent stops without completing the End-of-Run SOP:

- The task execution history is lost (not persisted in git)
- Traceability is broken (logs may reference non-existent commits)
- The task should be considered incomplete
- Future agents will not have a complete history of work performed

**Therefore, completing the End-of-Run SOP is not optional - it is a mandatory requirement for task completion.**

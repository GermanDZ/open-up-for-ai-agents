---
name: openup-log-run
description: Create traceability logs (markdown + JSONL) for the current agent run
arguments:
  - name: run_id
    description: Unique identifier for this run (optional, auto-generates if not provided)
    required: false
---

# Log Run

This skill creates traceability logs for the current agent run, following the Traceability Logging SOP.

**IMPORTANT**: This skill should only be called AFTER all changes are committed. The logs require actual commit SHAs.

## When to Use

Use this skill when:
- Completing work that should be logged for traceability
- Need to document agent activities for audit trail
- Creating record of work for future reference
- Completing a task or iteration
- After committing all changes

## When NOT to Use

Do NOT use this skill when:
- Changes are not yet committed (commit first)
- Looking to commit changes (use git directly)
- Just need to save work without logging (use git)
- Run is incomplete and will continue

## Success Criteria

After using this skill, verify:
- [ ] Markdown log exists with all required fields
- [ ] JSONL entry is valid and appended
- [ ] Commit SHAs are correctly recorded
- [ ] Log files are in correct directory structure
- [ ] All required metadata is included

## Prerequisites

Before calling this skill, ensure:
1. All changes are committed to git
2. `git status --porcelain` returns empty (no uncommitted changes)
3. Commit SHAs are available for reference

## Process

### 1. Generate Run ID

If `$ARGUMENTS[run_id]` is not provided, generate one:
- Format: `YYYY-MM-DDTHH:MM:SSZ-agent-branch`
- Use current timestamp, agent name, and current branch

### 2. Collect Run Metadata

Collect the following information:
- Current branch: `git branch --show-current`
- Trunk branch: Detect using algorithm (prefer `origin/HEAD`, fallback to `main`, `master`, or current)
- Start/end timestamps
- Phase from `docs/project-status.md`
- Commits created during run: `git log --oneline <since>...HEAD`

### 3. Read Project Context

Read `docs/project-status.md` to extract:
- Current phase
- Iteration goals
- Active work items

### 4. Create Markdown Log

Create `docs/agent-logs/YYYY/MM/DD/<timestamp>-<agent>-<branch>.md` with:
- Run metadata (branch, trunk, timestamps)
- Roles assumed and any role switches
- Tasks performed (one per primary-role task boundary)
- **Commit SHAs**: List all commits created during this run
- Consulting-role usage within tasks
- Key decisions/assumptions + links to relevant docs
- Initial instructions/prompt (verbatim)
- Start/end timestamps

### 5. Append JSONL Entry

Append to `docs/agent-logs/agent-runs.jsonl`:

```json
{
  "run_id": "<generated-or-provided-run-id>",
  "agent": "claude",
  "branch": "<current-branch>",
  "trunk": "<detected-trunk>",
  "start": "<start-timestamp>",
  "end": "<end-timestamp>",
  "phase": "<current-phase>",
  "iteration_goals": ["<goal1>", "<goal2>"],
  "prompt_hash": "sha256:abc...",
  "md_log_path": "<path-to-markdown-log>",
  "tasks": [
    {
      "role": "<primary-role>",
      "objective": "<task-objective>",
      "start": "<task-start>",
      "end": "<task-end>",
      "commits": ["<sha1>", "<sha2>"],
      "docs_updated": ["<doc-path1>"],
      "consulting_roles": ["<consulting-role>"]
    }
  ],
  "decisions": ["<decision-doc-path>"],
  "notes": "<run-summary>"
}
```

### 6. Verify Logs

Verify:
- Markdown log exists and is readable
- JSONL entry is valid JSON
- Commit SHAs referenced in logs actually exist
- All required fields are populated

## Output

Returns:
- Path to markdown log
- Confirmation of JSONL update
- List of commits logged
- Run ID

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Uncommitted changes | Files not committed before logging | Commit changes first with `git add -A && git commit` |
| Invalid JSONL | JSON format error in entry | Verify JSON syntax before appending |
| Missing commits | No commits found for run | Verify commits exist and run is complete |
| Directory not found | docs/agent-logs/ doesn't exist | Create directory structure first |

## References

- Traceability Logging SOP: `docs-eng-process/agent-workflow.md`
- End-of-Run SOP: `docs-eng-process/agent-workflow.md`

## See Also

- [openup-complete-task](../complete-task/SKILL.md) - Calls this skill automatically
- [openup-start-iteration](../start-iteration/SKILL.md) - Logs iteration start

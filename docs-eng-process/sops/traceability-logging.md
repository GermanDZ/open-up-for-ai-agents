# Traceability Logging SOP

> Extracted from `agent-workflow.md` so skills that need only the logging
> procedure load this file instead of the whole operating-procedures document.

**Always write run logs** for every agent execution.

**⚠️ MANDATORY PREREQUISITE**: Commits must exist before creating logs. The `commits` field in logs must reference actual commit SHAs that exist in the git repository. Do not create logs until all changes are committed (see [End-of-Run SOP](../agent-workflow.md#end-of-run-sop) Step 1).

## Markdown Log

Create: `docs/agent-logs/YYYY/MM/DD/<timestamp>-<agent>-<branch>.md`

Include:
- Run metadata (branch, trunk, timestamps)
- Roles assumed and any role switches
- Tasks performed (one per primary-role task boundary)
- **Commit SHAs**: List all commits created during this run
- Consulting-role usage within tasks
- Key decisions/assumptions + links to relevant docs
- Initial instructions/prompt (verbatim)
- Start/end timestamps

## JSONL Index

Append to: `docs/agent-logs/agent-runs.jsonl`

**Schema** (one JSON object per line):

```json
{
  "run_id": "2026-01-13T14:30:00Z-claude-feature/xyz",
  "agent": "claude",
  "branch": "feature/xyz",
  "trunk": "main",
  "start": "2026-01-13T14:30:00Z",
  "end": "2026-01-13T15:45:00Z",
  "phase": "construction",
  "iteration_goals": ["Deliver login endpoint with tests", "Update roadmap and notes"],
  "prompt_hash": "sha256:abc...",
  "md_log_path": "docs/agent-logs/2026/01/13/2026-01-13T14-30-00Z-claude-feature-xyz.md",
  "tasks": [
    {
      "role": "developer",
      "objective": "Implement login endpoint",
      "start": "2026-01-13T14:35:00Z",
      "end": "2026-01-13T15:10:00Z",
      "commits": ["abc1234", "def5678"],
      "docs_updated": ["docs/phases/construction/notes.md"],
      "consulting_roles": ["architect"]
    }
  ],
  "decisions": ["docs/decisions/adr-001-backend-stack.md"],
  "notes": "Brief run summary / anomalies"
}
```

**Required fields**:
- `run_id`, `agent`, `branch`, `trunk`, `start`, `end`, `phase`, `iteration_goals`, `prompt_hash`, `md_log_path`, `tasks`
- `tasks[]`: `role`, `objective`, `start`, `end`, `commits`, `docs_updated`, `consulting_roles`

**MANDATORY**: The `commits` field must contain actual commit SHAs that exist in the repository.

**Validation before logging**:
1. Verify commits exist: `git log --oneline` should show the commits you plan to reference
2. Verify no uncommitted changes: `git status --porcelain` should be empty
3. Only after both checks pass, create the logs with commit SHAs

**If no commits exist**: Do not create logs. Return to [End-of-Run SOP](../agent-workflow.md#end-of-run-sop) Step 1 to commit changes first.

## Single Closure Path Rule

To avoid duplicate workflow overhead and duplicate logs:

- If `/openup-complete-task` was used successfully, do **not** run `/openup-log-run` again in the same closure flow
- Use `/openup-log-run` directly only when `/openup-complete-task` is not being used
- If logging failed during `/openup-complete-task`, run `/openup-log-run` as a recovery action and note the failure/recovery in logs

**See [End-of-Run SOP](../agent-workflow.md#end-of-run-sop) for the complete mandatory procedure that must be followed before creating logs.**

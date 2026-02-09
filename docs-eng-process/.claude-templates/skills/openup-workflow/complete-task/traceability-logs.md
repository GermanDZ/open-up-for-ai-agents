# Traceability Logging Procedures

This document provides detailed procedures for creating traceability logs when completing a task.

## Overview

Traceability logs serve two purposes:
1. **Markdown logs** - Human-readable record of agent activities
2. **JSONL logs** - Machine-readable record for analysis and reporting

## Log Locations

- Markdown logs: `docs/agent-logs/YYYY/MM/DD/<timestamp>-<agent>-<branch>.md`
- JSONL log: `docs/agent-logs/agent-runs.jsonl`

## Creating Markdown Logs

### Directory Structure

Create directories if they don't exist:
```bash
mkdir -p docs/agent-logs/YYYY/MM/DD
```

### Log Content

The markdown log should include:

#### Frontmatter
```yaml
---
run_id: "<generated-run-id>"
agent: "claude"
branch: "<current-branch>"
trunk: "<detected-trunk>"
start: "<start-timestamp>"
end: "<end-timestamp>"
phase: "<current-phase>"
---
```

#### Body
- Roles assumed and any role switches
- Tasks performed (one per primary-role task boundary)
- **Commit SHAs**: List all commits created during this run
- Consulting-role usage within tasks
- Key decisions/assumptions + links to relevant docs
- Initial instructions/prompt (verbatim)

#### Example Entry

```markdown
## Task 1: Implement feature X

**Role**: developer
**Start**: 2026-02-09T10:00:00Z
**End**: 2026-02-09T11:30:00Z

**Description**: Implemented user authentication feature with login form.

**Commits**:
- abc123def - Add login form component
- def456ghi - Implement authentication service

**Docs Updated**:
- docs/design/auth-design.md

**Consulting Roles**: architect (for design guidance)

**Key Decisions**:
- Used JWT for session management
- Login form validates on client and server
```

## Creating JSONL Entries

### JSONL Format

JSONL (JSON Lines) is a format where each line is a valid JSON object.

### Entry Structure

```json
{
  "run_id": "2026-02-09T10:00:00Z-claude-feature-auth",
  "agent": "claude",
  "branch": "feature/T-005-auth",
  "trunk": "main",
  "start": "2026-02-09T10:00:00Z",
  "end": "2026-02-09T11:30:00Z",
  "phase": "construction",
  "iteration_goals": ["Implement authentication", "Add user profile"],
  "prompt_hash": "sha256:abc123...",
  "md_log_path": "docs/agent-logs/2026/02/09/2026-02-09T10:00:00Z-claude-feature-T-005-auth.md",
  "tasks": [
    {
      "role": "developer",
      "objective": "Implement user authentication",
      "start": "2026-02-09T10:00:00Z",
      "end": "2026-02-09T11:30:00Z",
      "commits": ["abc123def", "def456ghi"],
      "docs_updated": ["docs/design/auth-design.md"],
      "consulting_roles": ["architect"]
    }
  ],
  "decisions": [],
  "notes": "Successfully implemented authentication feature"
}
```

### Appending to JSONL

Append the JSON entry to the file:
```bash
echo '{"run_id": "...", ...}' >> docs/agent-logs/agent-runs.jsonl
```

## Run ID Generation

Format: `YYYY-MM-DDTHH:MM:SSZ-agent-branch`

Examples:
- `2026-02-09T10:00:00Z-claude-feature-T-005-auth`
- `2026-02-09T14:30:00Z-claude-fix-bug-123`

## Trunk Detection

Detect trunk branch using this algorithm:
1. Check `origin/HEAD` symbolic reference
2. Fallback to common names: `main`, `master`, `develop`, `development`
3. Final fallback: current branch's remote tracking branch

## Verification

After creating logs, verify:

### Markdown Log
- [ ] File exists at correct path
- [ ] All required fields are populated
- [ ] Commit SHAs are valid
- [ ] Links to docs work

### JSONL Entry
- [ ] JSON is valid (use `jq` to verify)
- [ ] Entry was appended to file
- [ ] All required fields present
- [ ] Arrays are properly formatted

## Troubleshooting

### Invalid JSON

If JSON is invalid:
1. Use `jq` to validate: `cat docs/agent-logs/agent-runs.jsonl | jq -L .`
2. Fix syntax errors
3. Retry appending

### Missing Commits

If commits are missing:
1. Verify commits exist: `git log --oneline`
2. Check commit SHAs are correct
3. Update logs with correct SHAs

### Directory Issues

If directories don't exist:
1. Create directory structure
2. Ensure write permissions
3. Retry log creation

## References

- Traceability Logging SOP: `docs-eng-process/agent-workflow.md`
- End-of-Run SOP: `docs-eng-process/agent-workflow.md`

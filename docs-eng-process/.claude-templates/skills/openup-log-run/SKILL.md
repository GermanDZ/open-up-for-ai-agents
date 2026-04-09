---
name: openup-log-run
description: Create traceability logs (markdown + JSONL) for the current agent run
arguments:
  - name: run_id
    description: Unique identifier for this run (optional, auto-generates if not provided)
    required: false
---

# Log Run

Create traceability logs for the current agent run. **Call only AFTER all changes are committed** (logs require actual commit SHAs).

> **Haiku/Scribe step** — this entire skill is mechanical. Spawn a Haiku sub-agent with
> the scribe role to execute it. Brief template:
>
> ```
> Agent(model="haiku", description="Write agent run log",
>   prompt="You are a Scribe. Write a traceability log entry.
>   Branch: [branch]. Commits: [sha list]. Phase: [phase]. Task: [task_id].
>   Start: [ts]. End: [ts]. Files changed: [list].
>   1. Create docs/agent-logs/YYYY/MM/DD/<timestamp>-agent-<branch>.md
>      with the run metadata, commits, and key decisions listed below: [decisions].
>   2. Append a JSONL record to docs/agent-logs/agent-runs.jsonl.
>   Report: paths created and JSONL record written.")
> ```
>
> Collect the commit SHAs and metadata yourself (they require git commands), then
> hand off the write operations to the scribe.

## Prerequisites

- `git status --porcelain` returns empty (all changes committed)
- Commit SHAs are available for reference

## Process

### 1. Generate Run ID

If `$ARGUMENTS[run_id]` is not provided, generate: `YYYY-MM-DDTHH:MM:SSZ-agent-branch`

### 2. Collect Run Metadata

- Branch: `git branch --show-current`
- Trunk: detect via `origin/HEAD`, fallback `main`/`master`
- Start/end timestamps
- Phase from `docs/project-status.md`
- Commits: `git log --oneline <since>...HEAD`

### 3. Create Markdown Log

Create `docs/agent-logs/YYYY/MM/DD/<timestamp>-<agent>-<branch>.md` with:
- Run metadata (branch, trunk, timestamps)
- Roles assumed and switches
- Tasks performed (one per primary-role task boundary)
- Commit SHAs created during run
- Consulting-role usage
- Key decisions/assumptions + doc links
- Initial instructions/prompt (verbatim)

### 4. Append JSONL Entry

Append to `docs/agent-logs/agent-runs.jsonl`:

```json
{"run_id":"<id>","agent":"claude","branch":"<branch>","trunk":"<trunk>","start":"<ts>","end":"<ts>","phase":"<phase>","iteration_goals":["..."],"prompt_hash":"sha256:...","md_log_path":"<path>","tasks":[{"role":"<role>","objective":"<obj>","start":"<ts>","end":"<ts>","commits":["<sha>"],"docs_updated":["<path>"],"consulting_roles":["<role>"]}],"decisions":["<path>"],"notes":"<summary>"}
```

### 5. Verify

- Markdown log exists and is readable
- JSONL entry is valid JSON
- Commit SHAs referenced actually exist
- All required fields are populated

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Uncommitted changes | Files not committed | `git add -A && git commit` first |
| Invalid JSONL | JSON format error | Verify syntax before appending |
| Missing commits | No commits for run | Verify run is complete |
| Directory not found | docs/agent-logs/ missing | Create directory structure first |

## References

- Traceability Logging SOP: `docs-eng-process/agent-workflow.md`

## See Also

- [openup-complete-task](../complete-task/SKILL.md) - Calls this skill automatically
- [openup-start-iteration](../start-iteration/SKILL.md) - Logs iteration start

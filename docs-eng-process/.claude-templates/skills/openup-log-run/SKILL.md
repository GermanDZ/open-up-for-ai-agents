---
name: openup-log-run
description: Create traceability logs (markdown + JSONL) for the current agent run
model: haiku
fit:
  great: [end-of-session wrap-up after commits, audit-required workflows]
  ok: [mid-session checkpoints when commits exist]
  poor: [pre-commit runs (no SHAs to log), trivial sessions handled by hooks]
arguments:
  - name: run_id
    description: Unique identifier for this run (optional, auto-generates if not provided)
    required: false
---

# Log Run

Create traceability logs for the current agent run. **Call only AFTER all changes are committed** (logs require actual commit SHAs).

> **Scribe step** — this entire skill is mechanical. Delegate to the
> `openup-scribe` agent (Agent tool, subagent_type: "openup-scribe"). You
> determine the values; the scribe only writes. Brief it with:
>
> **Timestamps come from the clock, never the model**: capture
> `START=$(python3 scripts/openup-state.py get started_at 2>/dev/null || echo unknown)`
> and `END=$(date -u +%Y-%m-%dT%H:%M:%SZ)`, and pass those concrete values into
> the scribe brief for the human-readable `.md`:
>
> ```
> Agent(subagent_type="openup-scribe", description="Write agent run log",
>   prompt="Write a traceability log entry.
>   Branch: [branch]. Commits: [sha list]. Phase: [phase]. Task: [task_id].
>   Start: $START. End: $END. Files changed: [list].
>   Create docs/agent-logs/YYYY/MM/DD/<timestamp>-agent-<branch>.md
>   with the run metadata, commits, and key decisions listed below: [decisions].
>   Report: path created.")
> ```
>
> Then append the machine-readable record with the **deterministic logger** (it
> stamps `ts` itself — do not hand-author a JSONL line):
>
> ```bash
> python3 scripts/openup-state.py log-event \
>   --event run_log --task-id "[task_id]" --branch "[branch]" --phase "[phase]"
> ```
>
> Collect the commit SHAs and metadata yourself (they require git commands), then
> hand off the markdown write to the scribe.

## Prerequisites

- `git status --porcelain` returns empty (all changes committed)
- Commit SHAs are available for reference

## Process

### 1. Generate Run ID

If `$ARGUMENTS[run_id]` is not provided, generate: `YYYY-MM-DDTHH:MM:SSZ-agent-branch`

### 2. Collect Run Metadata

- Branch: `git branch --show-current`
- Trunk: detect via `origin/HEAD`, fallback `main`/`master`
- Start/end timestamps — **clock-sourced**: `started_at` from
  `python3 scripts/openup-state.py get started_at`, end from `date -u`. Never
  author timestamps by hand.
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

Append the record with the **deterministic logger**, which stamps `ts` from the
system clock — the model never supplies a timestamp:

```bash
python3 scripts/openup-state.py log-event \
  --event run_log --task-id "<id>" --branch "<branch>" --phase "<phase>"
```

This replaces hand-authoring a JSONL line (the source of the fabricated
round-number times the audit found). The script appends one well-formed record
to `docs/agent-logs/agent-runs.jsonl`.

### 5. Record the log gate

Once the markdown log and JSONL record are written, flip the iteration-state gate (no-op if there is no active `.openup/state.json`):

```bash
python3 scripts/openup-state.py set-gate log_written true 2>/dev/null || true
```

### 6. Verify

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

- Traceability Logging SOP: `docs-eng-process/sops/traceability-logging.md`

## See Also

- [openup-complete-task](../complete-task/SKILL.md) - Calls this skill automatically
- [openup-start-iteration](../start-iteration/SKILL.md) - Logs iteration start

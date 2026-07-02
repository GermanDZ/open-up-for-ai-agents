---
name: openup-quick-task
description: Fast iteration mode for small changes - simplified workflow with minimal overhead
model: inherit
fit:
  great: [typo fixes, doc updates, single-file config tweaks, hotfixes]
  ok: [small bug fixes under ~50 LOC, single-component refactors]
  poor: [new features, multi-role work, architectural changes, anything needing a rubric]
arguments:
  - name: task
    description: Brief description of the task to complete
    required: true
  - name: task_id
    description: Roadmap task ID (optional, creates task if not provided)
    required: false
  - name: skip_branch
    description: "Skip branch creation (default: false)"
    required: false
  - name: skip_commit
    description: "Skip auto-commit (default: false)"
    required: false
  - name: skip_logging
    description: "Skip traceability logging (default: false)"
    required: false
---

# Quick Task - Fast Iteration Mode

**Quick Task** is a lightweight workflow for small changes and rapid iteration. It combines multiple steps into a single command while maintaining essential OpenUP practices.

## When to Use

Use Quick Task for:
- Small bug fixes (< 50 lines changed)
- Documentation updates
- Configuration changes
- Quick experiments
- Hot fixes

## When NOT to Use

Do NOT use for:
- New features (use standard workflow)
- Major refactoring (use `/openup-start-iteration`)
- Tasks requiring architecture review (use full team)
- Multi-hour development work

## Process

### 1. Quick Context Load

Load only the **Ring 1 product truth** the change needs — typically just the
roadmap row and the single file you are touching. Do **not** scan all of `docs/`
(see the Three-Ring context scoping in `.claude/CLAUDE.md`).

### 2. Quick Branch (optional)

If not skipping branching:
```bash
# Detect trunk and create quick branch
BRANCH_NAME="quick/$(date +%Y%m%d-%H%M%S)-$(echo $task | tr ' ' '-' | head -c 20)"
git checkout -b $BRANCH_NAME
```

Then initialize iteration state on the **quick** track — this is the same `quick` track `/openup-start-iteration` selects for tiny scopes (see [tracks.md](../../../docs-eng-process/tracks.md)). The quick track only requires the `log_written` and `roadmap_synced` gates — there is no plan or team gate:

```bash
python3 scripts/openup-state.py init \
  --task-id "{task_id or generated id}" \
  --iteration 0 \
  --phase construction \
  --track quick \
  --branch "$(git rev-parse --abbrev-ref HEAD)" \
  --worktree "$(git rev-parse --show-toplevel)" \
  --force
```

(If branching is skipped and no `.openup/state.json` will exist, skip this and the gate steps below — quick tasks remain lightweight.)

### 3. Execute Task

Implement the change:
- Read task description
- Make necessary changes
- Verify the fix works

### 4. Quick Commit (optional)

If not skipping commit:
```bash
git add .
git commit -m "quick: $task"
# (append your harness's standard commit trailers, if any — do not hardcode a model name)
```

### 5. Rubric Check (artifact tasks only)

If the task produced a new or updated work product (use case, architecture notebook, iteration plan, test plan, vision), run a quick rubric check:

- Detect artifact type from changed files
- Load the matching rubric from `.claude/rubrics/`
- Grade each criterion: ✅ satisfied / ❌ gap
- If any gaps: fix them before proceeding (quick tasks still need quality output)

Skip this step for pure code changes (bug fixes, refactors, configuration).

### 6. Quick Log (optional)

> **Scribe step** — delegate both writes to the `openup-scribe` agent (Agent
> tool, subagent_type: "openup-scribe"). You determine the values; the scribe
> only writes. Brief it with:
>
> ```
> Agent(subagent_type="openup-scribe", description="Write quick-task log entry",
>   prompt="1. Append this line to docs/agent-logs/quick-tasks.log:
>      [ISO timestamp] | quick-task | [task description]
>   2. [Only if task produced an artifact or decision] Append to
>      .claude/memory/iteration-learnings.md:
>      ## [YYYY-MM-DD] quick: [task]
>      - What changed: [brief]
>      - Conventions established: [any patterns worth reusing]
>   Report: files written.")
> ```

After the log is written, record the gates and verify the quick-track required set. If `check-gates` exits nonzero, resolve the unmet gates before finishing:

```bash
python3 scripts/openup-state.py set-gate log_written true 2>/dev/null || true
python3 scripts/openup-state.py set-gate roadmap_synced true 2>/dev/null || true
python3 scripts/openup-state.py check-gates --require log_written,roadmap_synced 2>/dev/null || true
```

### 7. Archive State (if state was created)

```bash
python3 scripts/openup-state.py archive \
  "docs/agent-logs/$(date -u +%Y)/$(date -u +%m)/$(date -u +%d)/state-quick-$(date -u +%H%M%S).json" 2>/dev/null || true
```

## Output

Returns:
- Task completed confirmation
- Files changed (count)
- Branch name (if created)
- Commit hash (if committed)

## Comparison: Standard vs Quick

| Step | Standard Workflow | Quick Task |
|------|-------------------|------------|
| Read project-status | Full document | Minimal only |
| Create branch | Task-based naming | Timestamp-based |
| SOP compliance | Full Start-of-Run | Skipped |
| Documentation | Full update | Minimal |
| Log entry | Full JSONL | Simple log line |

## Examples

### Quick Bug Fix
```
/openup-quick-task task: "Fix typo in README.md"
```

### Documentation Update
```
/openup-quick-task task: "Update API docs for new endpoint"
```

### Skip Branching
```
/openup-quick-task task: "Add clarifying comment to a source file" skip_branch: true
```

### Full Control
```
/openup-quick-task task: "Hot fix auth bug" skip_commit: false skip_logging: true
```

## Success Criteria

- [ ] Task completed
- [ ] Changes verified
- [ ] Branch created (if not skipped)
- [ ] Committed (if not skipped)
- [ ] Logged (if not skipped)

## Defaults to Apply

When executing the steps above:
- Already on a non-trunk feature branch → treat `skip_branch` as true.
- No git changes at commit time → skip the commit step.
- Pick the branch prefix from the task type: `bugfix/`, `docs/`, or `hotfix/` instead of `quick/` when it clearly applies.

## See Also

- [openup-start-iteration](../start-iteration/SKILL.md) - Full iteration workflow
- [openup-complete-task](../complete-task/SKILL.md) - Task completion with PR
- [openup-tdd-workflow](../tdd-workflow/SKILL.md) - TDD cycle

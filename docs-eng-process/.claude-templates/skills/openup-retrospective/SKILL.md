---
name: openup-retrospective
description: Generate iteration retrospective with feedback and action items
model: sonnet
fit:
  great: [end-of-iteration reflection, capturing patterns to feed forward]
  ok: [mid-iteration when blockers pile up and a reset is needed]
  poor: [single-task wrap-ups (use complete-task notes), trivial iterations]
arguments:
  - name: iteration_number
    description: Iteration to review (optional, defaults to current)
    required: false
  - name: include_metrics
    description: "Include git metrics (true/false, default: true)"
    required: false
---

# Retrospective

Generate an iteration retrospective capturing what went well, what to improve, and action items.

## Process

### 1. Determine Iteration

If `$ARGUMENTS[iteration_number]` is provided, use it. Otherwise read `docs/project-status.md` for the current iteration number.

### 2. Read Project Context

Read `docs/project-status.md` for: iteration goal, dates, team members, overall status.

### 3. Analyze Completed Tasks

Read `docs/roadmap.md` to identify: tasks planned, completed, not completed, and added during iteration. Note complexity, challenges, and successes for each.

### 4. Gather Feedback

Review these sources for patterns and issues:
- `docs/agent-logs/` - Agent run logs
- `docs/risk-list.md` - Risks emerged or mitigated
- `docs/roadmap.md` - Velocity (completed vs planned), blocked items
- Git commit messages

### 4b. Measure Read-Back (success measures whose date has passed)

This is the step that closes the loop between per-feature success measures
(task-spec `## Success Measures`, rubric criterion 12) and value
prioritization — without it, measures are write-only and the roadmap ordering
stays opinion-based.

1. Scan archived change folders (`docs/changes/archive/T-NNN/design.md`) for
   recorded success-measure grades + read-back dates (written by
   `/openup-complete-task` step 1b). Skip `n/a` entries.
2. For each entry whose **read-back date has passed** and has no recorded
   outcome yet: read the instrumentation named in the expectation (the event /
   metric / query) and record **actual vs expected** — including "instrumentation
   exists but nobody can produce the number" (that is a finding, not a skip).
3. Write the results into the retrospective document's **Measure Read-Back**
   section (see step 6): expectation, actual, verdict (met / missed / can't
   tell), one-line interpretation.
4. **Hand the section to the product-manager role** (`.claude/teammates/product-manager.md`):
   it consumes these verdicts to re-rank pending roadmap entries, updating each
   moved entry's `Value` rationale to cite the evidence ("UC-12's measure
   missed by 80% — demoting the follow-on entries below the X work"). The
   re-rank is the product-manager's call; the retrospective only delivers the
   evidence.
5. Note read-backs that come due **before** the next expected retrospective as
   action items with owners, so they aren't silently skipped.

### 5. Collect Metrics (if `$ARGUMENTS[include_metrics] == "true"`)

```bash
# Commits in iteration period
git log --oneline --since="$start_date" --until="$end_date" | wc -l

# Lines changed
git diff --stat trunk...HEAD

# Active contributors
git shortlog -sn --since="$start_date" --until="$end_date"
```

Task metrics: tasks planned, tasks completed, completion rate (completed / planned * 100%).

### 6. Create Retrospective Document

Create `docs/iteration-retrospectives/iteration-{n}-retrospective.md` with sections:
- **Iteration Overview**: number, date range, goal, participants
- **Summary**: overall assessment, key achievements, major challenges
- **What Went Well**: process, technical, collaboration successes
- **What to Improve**: process issues, technical challenges, gaps
- **Measure Read-Back**: for each success measure due (step 4b) — expectation, actual, verdict (met / missed / can't tell), interpretation; plus the product-manager's resulting re-rank decisions (entries moved + updated `Value` rationale), or "no re-rank — evidence supports current order"
- **Action Items**: specific action, owner, due date, priority for each improvement
- **Metrics** (if included): task completion stats, git stats
- **Next Iteration Considerations**: carry forward, changes, risks to monitor

### 7. Update Project Status

In `docs/project-status.md`: add link to retrospective, note ongoing action items, update iteration status.

### 8. Reset the Retro-Cadence Counter (T-011)

Running this retrospective satisfies the cadence, so reset the durable counter. This zeroes
`.openup/retro.json` and clears `gates.retro_due` in any live `.openup/state.json`:

```bash
python3 scripts/openup-state.py retro reset
```

After this, `/openup-start-iteration` will permit `full`-track starts again until 5 more
tasks complete. See [state-file.md](../../../../docs-eng-process/state-file.md).

## Output

Returns: retrospective document path, counts of what went well / what to improve / action items, overall iteration rating, key metrics (if included).

## See Also

- [openup-start-iteration](../start-iteration/SKILL.md) - Start next iteration
- [openup-complete-task](../complete-task/SKILL.md) - Complete iteration tasks
- [openup-assess-completeness](../assess-completeness/SKILL.md) - Assess iteration completeness before retrospective
- [openup-create-iteration-plan](../openup-artifacts/create-iteration-plan/SKILL.md) - Plan next iteration based on retrospective

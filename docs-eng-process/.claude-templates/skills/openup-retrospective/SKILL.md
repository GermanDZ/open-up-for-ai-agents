---
name: openup-retrospective
description: Generate iteration retrospective with feedback and action items
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
- **Action Items**: specific action, owner, due date, priority for each improvement
- **Metrics** (if included): task completion stats, git stats
- **Next Iteration Considerations**: carry forward, changes, risks to monitor

### 7. Update Project Status

In `docs/project-status.md`: add link to retrospective, note ongoing action items, update iteration status.

## Output

Returns: retrospective document path, counts of what went well / what to improve / action items, overall iteration rating, key metrics (if included).

## See Also

- [openup-start-iteration](../start-iteration/SKILL.md) - Start next iteration
- [openup-complete-task](../complete-task/SKILL.md) - Complete iteration tasks
- [openup-assess-completeness](../assess-completeness/SKILL.md) - Assess iteration completeness before retrospective
- [openup-create-iteration-plan](../openup-artifacts/create-iteration-plan/SKILL.md) - Plan next iteration based on retrospective

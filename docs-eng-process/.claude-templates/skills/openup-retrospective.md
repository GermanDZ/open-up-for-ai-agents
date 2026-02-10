---
name: openup-retrospective
description: Generate iteration retrospective with feedback and action items
arguments:
  - name: iteration_number
    description: Iteration to review (optional, defaults to current)
    required: false
  - name: include_metrics
    description: Include git metrics (true/false, default: true)
    required: false
---

# Retrospective

This skill generates an iteration retrospective document capturing what went well, what to improve, and action items for continuous improvement.

## When to Use

Use this skill when:
- Completing an iteration
- Need to capture lessons learned
- Preparing for next iteration planning
- Implementing continuous improvement
- Ending Construction or Transition iteration

## When NOT to Use

Do NOT use this skill when:
- Mid-iteration and just checking progress (use project status)
- Iteration hasn't started yet
- Looking for project status update (use project-status.md)
- Only need git statistics (use git log directly)

## Success Criteria

After using this skill, verify:
- [ ] Retrospective document is created
- [ ] What went well is documented
- [ ] What to improve is identified
- [ ] Action items are defined with owners
- [ ] Metrics are included (if requested)
- [ ] Next iteration considerations are noted

## Process Summary

1. Read project status and determine iteration
2. Analyze completed tasks
3. Gather feedback from team and artifacts
4. Collect metrics (if requested)
5. Generate retrospective document

## Detailed Steps

### 1. Determine Iteration

If `$ARGUMENTS[iteration_number]` is provided:
- Use that iteration number
- Read iteration-specific information

If not provided:
- Read `docs/project-status.md` for current iteration
- Use current iteration number

### 2. Read Project Context

Read `docs/project-status.md` for:
- Iteration goal
- Iteration dates
- Team members involved
- Overall iteration status

### 3. Analyze Completed Tasks

Read `docs/roadmap.md` to identify:
- Tasks planned for this iteration
- Tasks completed
- Tasks not completed
- Tasks added during iteration

For each completed task:
- Note complexity
- Note any challenges
- Note successes

### 4. Gather Feedback Sources

**From Project Artifacts:**
- `docs/agent-logs/` - Agent run logs for issues
- `docs/test-logs/` - Test logs for quality issues
- `docs/risk-list.md` - Risks that emerged or were mitigated
- Git commit messages - Patterns and issues

**From Roadmap:**
- Velocity (tasks completed vs planned)
- Story points (if tracked)
- Blocked items and reasons

**From Status Updates:**
- Project status updates
- Any team notes or comments

### 5. Collect Metrics (Optional)

If `$ARGUMENTS[include_metrics] == "true"`:

**Git Metrics:**
```bash
# Count commits
git log --oneline --since="$start_date" --until="$end_date" | wc -l

# Count pull requests
# (Project-specific, check for PRs)

# Lines changed
git diff --stat trunk...HEAD

# Active contributors
git shortlog -sn --since="$start_date" --until="$end_date"
```

**Task Metrics:**
- Tasks planned: count from roadmap
- Tasks completed: count completed in roadmap
- Completion rate: completed / planned * 100%

### 6. Structure the Retrospective

Using the iteration retrospective template, create:

**Iteration Overview:**
- Iteration number
- Date range
- Goal
- Participants

**Summary:**
- Overall assessment (successful, mixed, challenging)
- Key achievements
- Major challenges

**What Went Well:**
- Process successes
- Technical wins
- Collaboration highlights
- Tools that worked well

**What to Improve:**
- Process issues
- Technical challenges
- Communication gaps
- Tool limitations

**Action Items:**
- Specific improvements
- Owners assigned
- Due dates
- Priority

**Metrics (if included):**
- Task completion statistics
- Git statistics
- Quality metrics

**Next Iteration Considerations:**
- What to carry forward
- What to change
- Risks to monitor

### 7. Generate Action Items

Convert "What to Improve" into actionable items:

For each improvement:
1. Define specific action
2. Assign owner (role or person)
3. Set due date (next iteration or specific date)
4. Set priority
5. Define success criteria

Example:
```
| Action | Owner | Due Date | Priority |
|--------|-------|----------|----------|
| Set up automated testing pipeline | Developer | Next iteration | High |
| Improve requirements documentation | Analyst | Iteration N+2 | Medium |
```

### 8. Create Retrospective Document

Create `docs/iteration-retrospectives/iteration-{n}-retrospective.md` using the template:
- Fill in all sections
- Include metrics table
- Link to related artifacts

### 9. Update Project Status

In `docs/project-status.md`:
- Add link to retrospective in iteration history
- Note any ongoing action items
- Update status if iteration is complete

## Output

Returns a summary of:
- Retrospective document created
- What went well (count)
- What to improve (count)
- Action items created
- Overall iteration rating
- Key metrics (if included)

## Example Usage

```
/openup-retrospective include_metrics: true
```

```
/openup-retrospective iteration_number: 3 include_metrics: false
```

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Iteration not found | Iteration number doesn't exist | Verify iteration number or omit for current |
| No project status | docs/project-status.md doesn't exist | Initialize project first |
| No tasks completed | Iteration just started | Complete some work first |
| Git metrics fail | Invalid date range or no commits | Check dates and git history |

## References

- Iteration Retrospective Template: `docs-eng-process/templates/iteration-retrospective.md`
- Agile Retrospective Practices: OpenUP knowledge base
- Agent Workflow: `docs-eng-process/agent-workflow.md`

## See Also

- [openup-start-iteration](../start-iteration/SKILL.md) - Start next iteration
- [openup-complete-task](../complete-task/SKILL.md) - Complete iteration tasks
- [openup-assess-completeness](../assess-completeness/SKILL.md) - Assess iteration completeness before retrospective
- [openup-create-iteration-plan](../openup-artifacts/create-iteration-plan/SKILL.md) - Plan next iteration based on retrospective

---
name: openup-orchestrate
description: Run a full orchestrated iteration — PM decomposes the goal, delegates to specialist roles, collects outputs, and synthesizes results
arguments:
  - name: task_id
    description: The task ID to orchestrate (must match a task in docs/roadmap.md)
    required: true
  - name: team
    description: "Team type to use (feature, construction, elaboration, inception, transition, investigation, planning, full). Auto-selected from phase if not provided."
    required: false
  - name: dry_run
    description: "Preview the orchestration plan without spawning teammates (true/false, default: false)"
    required: false
---

# Orchestrate Iteration

The Project Manager orchestrates a full iteration by decomposing the goal into role-specific subtasks, delegating to specialist teammates, collecting their outputs, and synthesizing a coherent result.

This skill implements the coordinator + specialist pattern: the PM acts as an orchestrator (coordinator) that spawns focused agents (specialists) with isolated task contexts, then integrates their outputs.

## Prerequisites

- Iteration must already be initialized via `/openup-start-iteration`
- Feature branch must be active (`git rev-parse --abbrev-ref HEAD` returns a non-trunk branch)
- `docs/iteration-plan.md` must exist with the iteration goal and acceptance criteria

## Process

### 1. Load Iteration Context

Read the following (in order):
1. `docs/iteration-plan.md` — iteration goal, acceptance criteria, task list
2. `docs/project-status.md` — current phase, active task
3. `docs/roadmap.md` — task details for `$ARGUMENTS[task_id]`
4. `.claude/memory/iteration-learnings.md` — past learnings to avoid repeating mistakes

### 2. Decompose Goal into Role Subtasks

Analyze the iteration goal and break it down by role. For each role in the active team, determine:
- **What this role needs to contribute** to achieve the iteration goal
- **What context this role specifically needs** (not the full project — just what's relevant)
- **What deliverable this role should produce** (specific document, code, decision, test)
- **What "done" looks like for this role** (criteria from the relevant rubric if applicable)

Document the decomposition before spawning any teammates:

```
Orchestration Plan for [task_id]:

Analyst: [subtask] → Deliverable: [output] → Done when: [criteria]
Architect: [subtask] → Deliverable: [output] → Done when: [criteria]
Developer: [subtask] → Deliverable: [output] → Done when: [criteria]
Tester: [subtask] → Deliverable: [output] → Done when: [criteria]
```

If `$ARGUMENTS[dry_run]` is `true`: output this plan and stop. Do not spawn teammates.

### 3. Select and Spawn Team

If team is not already active, determine the team type:
- Use `$ARGUMENTS[team]` if provided
- Otherwise auto-select based on phase (same logic as `/openup-start-iteration` step 7)

Spawn only the roles needed for this iteration's decomposition. Do not spawn roles that have no meaningful contribution to this specific task.

### 4. Brief Each Specialist

Send each teammate a focused brief using the PM's delegation format:

```
[ROLE]: Your task for this iteration is: [focused scope].

Context you need:
- [specific doc 1 with path]
- [specific doc 2 with path]
- [constraint or decision that affects their work]

Deliverable: [specific output — section of a document, code changes, test results]

Done when:
- [criterion 1]
- [criterion 2]
- [criterion 3]
```

**Key rule**: Give each specialist only the context they need. Do not dump the full project into every brief.

### 5. Collect Specialist Outputs

As each specialist completes their work, collect:
- Their deliverable (document, code, test results, recommendation)
- Any blockers or dependencies they identified
- Any decisions that require PM or cross-role coordination

Check each output against the "done when" criteria from their brief. If criteria are not met, send a follow-up brief with specific gaps to address.

### 6. Synthesize Results

Integrate all specialist outputs:
1. Merge document contributions (architecture decisions + implementation + test coverage)
2. Resolve any conflicts between specialist recommendations
3. Verify the combined output satisfies the iteration acceptance criteria from `docs/iteration-plan.md`
4. Run `/openup-assess-completeness scope: iteration` to get a final rubric-based assessment

If the assessment returns `needs_revision`: identify which specialist needs to address which gaps, and send targeted follow-up briefs (back to step 4 for the relevant role).

### 7. Save Orchestration Learnings

Append to `.claude/memory/iteration-learnings.md`:

```markdown
## [YYYY-MM-DD] [task_id]: [task title] — Orchestrated

- **Team composition**: [roles used and why]
- **Delegation that worked well**: [what made a particular brief effective]
- **Coordination overhead**: [where handoffs created friction and how to avoid next time]
- **Synthesis challenges**: [conflicts between specialist outputs and how resolved]
```

### 8. Hand Off to Complete Task

Once all acceptance criteria are met and the rubric assessment is `satisfied`, invoke `/openup-complete-task task_id: $ARGUMENTS[task_id]` to commit, log, and create the PR.

## Output

Returns:
- Orchestration plan (role → subtask → deliverable mapping)
- Per-specialist status (delivered / needs revision)
- Synthesis result (acceptance criteria met / gaps remaining)
- Final assessment result (satisfied / needs_revision)

## See Also

- [openup-start-iteration](../openup-start-iteration/SKILL.md) - Initialize iteration before orchestrating
- [openup-assess-completeness](../openup-assess-completeness/SKILL.md) - Rubric-based quality gate
- [openup-complete-task](../openup-complete-task/SKILL.md) - Finalize after orchestration
- [openup-deploy-team](../openup-deploy-team/SKILL.md) - Deploy team separately if needed

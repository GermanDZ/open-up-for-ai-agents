---
name: openup-deploy-team
description: Deploy an OpenUP agent team to work on the current iteration
arguments:
  - name: team_type
    description: Type of team to create (feature, investigation, construction, elaboration, inception, transition, planning, full)
    required: false
  - name: roles
    description: Specific roles to include (analyst, architect, developer, tester, project-manager). Comma-separated.
    required: false
---

# Deploy Team

This skill deploys an OpenUP agent team to work on the current iteration. It reads the iteration context and creates the appropriate team with proper role assignments.

## When to Use

Use this skill **after** `/openup-start-iteration` has completed:
- Iteration is initialized
- Branch is created
- Project status is updated
- Roadmap has the task

Then use this skill to deploy the team.

## When NOT to Use

Do NOT use this skill:
- Before `/openup-start-iteration` has been called
- Without knowing the iteration goal
- For non-OpenUP work

## Process

### 1. Read Current Iteration Context

Read `docs/project-status.md` to get:
- Current phase
- Current iteration number
- Current iteration goal
- Current task (if set)

### 2. Determine Team Composition

Based on the iteration goal and team_type:
- **feature**: analyst, architect, developer, tester
- **investigation**: architect, developer, tester
- **construction**: developer, tester (+ architect, analyst as needed)
- **elaboration**: architect, developer, tester (+ analyst as needed)
- **inception**: analyst, project-manager (+ architect as needed)
- **transition**: tester, project-manager, developer (+ analyst as needed)
- **planning**: project-manager, analyst (+ architect, developer as needed)
- **full**: all roles

Or use custom roles from `$ARGUMENTS[roles]`

### 3. Create the Team

Spawn teammates using the Task tool with appropriate subagent types.

### 4. Brief the Team

Send initial message to all teammates with:
- Iteration goal
- Current phase
- Task context
- Expected workflow
- Coordination instructions

### 5. Set Up Coordination

Ensure the team lead knows to:
- Monitor progress
- Assign tasks to appropriate roles
- Use `/openup-complete-task` when work is done

## Output

Returns:
- Team composition
- Team member assignments
- Current iteration context
- Expected workflow

## Example Usage

```
/openup-deploy-team team_type: feature
```

Or with specific roles:
```
/openup-deploy-team roles: analyst,developer,tester
```

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| No iteration found | docs/project-status.md doesn't exist or no active iteration | Run /openup-start-iteration first |
| Unknown team type | team_type parameter not recognized | Use one of: feature, investigation, construction, elaboration, inception, transition, planning, full |
| Cannot spawn team | Agent teams not enabled | Set CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 |

## See Also

- [openup-start-iteration](../openup-start-iteration/SKILL.md) - Initialize iteration first
- [openup-complete-task](../openup-complete-task/SKILL.md) - Complete work when done
- [Team configurations](../../teams/) - Team definition files

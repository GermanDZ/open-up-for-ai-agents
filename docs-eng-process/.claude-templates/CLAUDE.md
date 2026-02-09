# OpenUP Agent Team Instructions

This file provides instructions for using OpenUP agent teams with Claude Code.

## About OpenUP

OpenUP (Open Unified Process) is a lean, iterative software development methodology with four phases:

1. **Inception** - Define scope, vision, and feasibility
2. **Elaboration** - Establish architecture baseline
3. **Construction** - Build the system incrementally
4. **Transition** - Deploy to users

## Agent Teams

This project is configured with OpenUP role-based agent teams. Each teammate represents an OpenUP role and follows specific instructions for that role.

### Available Roles

| Role | Focus | Key Work Products |
|------|-------|-------------------|
| **analyst** | Requirements, stakeholder communication | Vision, Use Cases, Requirements |
| **architect** | Architecture design, technical decisions | Architecture Notebook |
| **developer** | Implementation, unit testing | Design, Code, Unit Tests |
| **project-manager** | Planning, coordination | Project Plan, Iteration Plan, Risk List |
| **tester** | Test planning, execution | Test Cases, Test Scripts, Test Logs |

### Team Configurations

#### Full Team (All Roles)
For comprehensive project work involving all aspects of development:

```
Create an OpenUP agent team with all roles: analyst, architect, developer, project-manager, and tester.
```

#### Feature Team (Analyst, Architect, Developer, Tester)
For implementing new features requiring requirements, design, implementation, and testing:

```
Create an OpenUP agent team for feature implementation. Spawn analyst for requirements, architect for design, developer for implementation, and tester for validation.
```

#### Investigation Team (Architect, Developer, Tester)
For debugging and technical investigation:

```
Create an OpenUP agent team to investigate this issue. Spawn architect to analyze the architecture, developer to find root cause, and tester to verify the fix.
```

#### Planning Team (Analyst, Project Manager)
For iteration planning and roadmap updates:

```
Create an OpenUP agent team for iteration planning. Spawn analyst to review requirements and project-manager to update the plan.
```

## How to Use Agent Teams

### Step 1: Enable Agent Teams

Agent teams must be enabled in your environment:

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

Or add to `settings.json`:
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

### Step 2: Create a Team

Ask Claude to create a team with the appropriate roles for your task:

```
Create an OpenUP agent team with [list of roles] to [describe task].
```

### Step 3: Coordinate Work

The team lead will coordinate work across teammates. You can:
- Message individual teammates directly (Shift+Up/Down in in-process mode)
- Ask the lead to assign specific tasks to specific roles
- Monitor progress through the shared task list

### Step 4: Clean Up

When work is complete, ask the lead to clean up the team:

```
Clean up the team
```

## Role-Based Instructions

Each teammate has specific instructions based on their OpenUP role:

- **Analyst instructions**: `.claude/teammates/analyst.md`
- **Architect instructions**: `.claude/teammates/architect.md`
- **Developer instructions**: `.claude/teammates/developer.md`
- **Project Manager instructions**: `.claude/teammates/project-manager.md`
- **Tester instructions**: `.claude/teammates/tester.md`

These instructions are automatically loaded when teammates are spawned.

## OpenUP Knowledge Base

Role definitions and process guidance are available in:

- `docs-eng-process/openup-knowledge-base/core/role/roles/` - Role definitions
- `docs-eng-process/openup-knowledge-base/practice-management/risk_value_lifecycle/` - Lifecycle and phases
- `docs-eng-process/agent-workflow.md` - Agent operating procedures

## Project State Documents

The team uses these documents to track project state:

- `docs/project-status.md` - Current phase, iteration, goals
- `docs/roadmap.md` - Prioritized task backlog
- `docs/vision.md` - Project vision (Inception/Elaboration)
- `docs/risk-list.md` - Project risks
- `docs/architecture-notebook.md` - Architecture decisions (Elaboration+)

## Example Workflows

### Starting a New Feature

```
Create an OpenUP agent team to implement the [feature name] feature.

Spawn:
- analyst: to gather requirements and define acceptance criteria
- architect: to design the component architecture
- developer: to implement the feature
- tester: to create and execute tests

The analyst should first create use cases for this feature, then the architect should design it, then the developer should implement it with tests.
```

### Architecture Review

```
Create an OpenUP agent team to review the current architecture.

Spawn:
- architect: to lead the review and document findings
- developer: to provide implementation feedback
- tester: to assess testability implications

The team should review docs/architecture-notebook.md and identify any improvements or concerns.
```

### Bug Investigation

```
Create an OpenUP agent team to investigate [bug description].

Spawn:
- developer: to analyze the code and find root cause
- architect: to assess architectural implications
- tester: to verify the fix and prevent regression

The team should work together to understand, fix, and test the bug.
```

### Iteration Planning

```
Create an OpenUP agent team for iteration planning.

Spawn:
- project-manager: to lead the planning session
- analyst: to review and prioritize requirements
- architect: to assess technical feasibility
- developer: to provide effort estimates

The team should review docs/roadmap.md and create docs/iteration-plan.md for the upcoming iteration.
```

## Display Modes

Agent teams support two display modes:

- **In-process** (default): All teammates in main terminal, use Shift+Up/Down to navigate
- **Split panes**: Each teammate in separate pane (requires tmux or iTerm2)

Configure in settings.json:
```json
{
  "teammateMode": "in-process" | "auto" | "tmux"
}
```

## Best Practices

1. **Start with the right roles**: Only spawn teammates for roles needed for the task
2. **Use clear prompts**: Explain what each role should focus on
3. **Let teammates collaborate**: They can message each other directly
4. **Monitor progress**: Check in on teammates and redirect if needed
5. **Clean up when done**: Remove teammates after work is complete

## Troubleshooting

If teammates aren't appearing:
- Press Shift+Down to cycle through active teammates (in-process mode)
- Check that agent teams are enabled (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`)
- Verify the task is complex enough to warrant a team

If teammates stop on errors:
- Check their output using Shift+Up/Down (in-process) or click pane (split)
- Give additional instructions or spawn a replacement teammate

For more information on agent teams, see: https://code.claude.com/docs/en/agent-teams

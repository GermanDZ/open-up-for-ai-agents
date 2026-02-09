# OpenUP Teams Guide

This guide documents all OpenUP team configurations available for different development scenarios.

## What are Teams?

Teams are groups of AI agents that collaborate on tasks. Each agent (teammate) assumes a specific OpenUP role and follows role-based instructions. Teams enable parallel work and role-based expertise.

## Available Roles

| Role | Focus | Key Work Products |
|------|-------|-------------------|
| **analyst** | Requirements, stakeholder communication | Vision, Use Cases, Requirements |
| **architect** | Architecture design, technical decisions | Architecture Notebook |
| **developer** | Implementation, unit testing | Design, Code, Unit Tests |
| **project-manager** | Planning, coordination | Project Plan, Iteration Plan, Risk List |
| **tester** | Test planning, execution | Test Cases, Test Scripts, Test Logs |

## Creating Teams

To create a team, use this format:

```
Create an OpenUP agent team for [scenario].

Spawn teammates for:
- [role]: to [describe their focus]
- [role]: to [describe their focus]
```

## Team Configurations

### Phase-Specific Teams

These teams are optimized for specific OpenUP phases.

#### Inception Team

**Roles**: analyst (lead), project-manager (lead), architect (as needed)

**Best for**:
- Defining project vision
- Identifying key stakeholders
- Creating initial project plan
- Identifying major risks

**Example prompt**:
```
Create an OpenUP agent team for the Inception phase.

Spawn teammates for:
- analyst: to lead requirements gathering and vision definition
- project-manager: to lead planning and coordination
```

**Team config**: `docs-eng-process/.claude-templates/teams/openup-inception-team.md`

#### Elaboration Team

**Roles**: architect (lead), developer (lead), tester, analyst (as needed)

**Best for**:
- Designing architecture
- Implementing architectural baseline
- Validating architecture through testing
- Detailing critical use cases

**Example prompt**:
```
Create an OpenUP agent team for the Elaboration phase.

Spawn teammates for:
- architect: to lead architecture design
- developer: to implement the architectural baseline
- tester: to validate the architecture through testing
```

**Team config**: `docs-eng-process/.claude-templates/teams/openup-elaboration-team.md`

#### Construction Team

**Roles**: developer (lead), tester (lead), architect (as needed), analyst (as needed)

**Best for**:
- Implementing features
- Iterative testing
- Bug fixing
- Preparing for beta testing

**Example prompt**:
```
Create an OpenUP agent team for the Construction phase.

Spawn teammates for:
- developer: to lead implementation
- tester: to lead testing and quality assurance
```

**Team config**: `docs-eng-process/.claude-templates/teams/openup-construction-team.md`

#### Transition Team

**Roles**: tester (lead), developer, project-manager (lead), analyst (as needed)

**Best for**:
- Final testing and validation
- Bug fixing
- Deployment coordination
- User acceptance

**Example prompt**:
```
Create an OpenUP agent team for the Transition phase.

Spawn teammates for:
- tester: to lead final testing and validation
- developer: to fix bugs and support deployment
- project-manager: to coordinate deployment and release
```

**Team config**: `docs-eng-process/.claude-templates/teams/openup-transition-team.md`

### Task-Specific Teams

These teams are optimized for specific types of work.

#### Full Team

**Roles**: analyst, architect, developer, project-manager, tester

**Best for**:
- Comprehensive project work
- Cross-phase initiatives
- Major feature releases

**Example prompt**:
```
Create an OpenUP agent team with all roles: analyst, architect, developer, project-manager, and tester.

Each teammate should follow their role instructions in .claude/teammates/{role}.md.
```

**Team config**: `docs-eng-process/.claude-templates/teams/openup-full-team.md`

#### Feature Team

**Roles**: analyst, architect, developer, tester

**Best for**:
- Implementing new features end-to-end
- Requirements through deployment

**Example prompt**:
```
Create an OpenUP agent team for feature implementation.

Spawn teammates for:
- analyst: to gather requirements and define acceptance criteria
- architect: to design the feature architecture
- developer: to implement the feature
- tester: to create and execute tests

The analyst should first create use cases, then the architect should design, then the developer should implement with tests.
```

**Team config**: `docs-eng-process/.claude-templates/teams/openup-feature-team.md`

#### Investigation Team

**Roles**: architect (lead), developer (lead), tester (lead)

**Best for**:
- Debugging issues
- Root cause analysis
- Performance problems
- Architecture review

**Example prompt**:
```
Create an OpenUP investigation team to investigate [issue description].

Spawn teammates for:
- architect: to analyze the architecture and identify root causes
- developer: to analyze the code and implement the fix
- tester: to reproduce the issue and verify the fix
```

**Team config**: `docs-eng-process/.claude-templates/teams/openup-investigation-team.md`

#### Planning Team

**Roles**: project-manager (lead), analyst, architect (as needed), developer (as needed)

**Best for**:
- Iteration planning
- Roadmap updates
- Project estimation
- Risk assessment

**Example prompt**:
```
Create an OpenUP agent team for iteration planning.

Spawn teammates for:
- project-manager: to lead the planning session
- analyst: to review and prioritize requirements
- architect: to assess technical feasibility
```

**Team config**: `docs-eng-process/.claude-templates/teams/openup-planning-team.md`

## Team Collaboration Patterns

### Analyst ↔ Architect
**Topics**: Requirements feasibility, architectural implications
**When**: During requirements gathering and architecture design

### Architect ↔ Developer
**Topics**: Architecture constraints, implementation feedback
**When**: During architecture implementation

### Developer ↔ Tester
**Topics**: Test coverage, bug fixing, TDD
**When**: During implementation and testing

### All ↔ Project Manager
**Topics**: Status updates, planning, blockers
**When**: Throughout the project

### Tester ↔ Analyst
**Topics**: Acceptance criteria, requirements validation
**When**: During test planning and requirements review

## Task Assignment Guidelines

When assigning tasks to teammates:

| Task Type | Primary Role | Consulting Roles |
|-----------|--------------|------------------|
| Vision and requirements | analyst | architect, project-manager |
| Architecture design | architect | analyst, developer |
| Implementation | developer | architect, tester |
| Testing | tester | analyst, developer |
| Planning and tracking | project-manager | all roles |
| Technical feasibility | architect | analyst, project-manager |
| Effort estimation | developer | architect, project-manager |
| Risk assessment | project-manager | architect, analyst |

## Team Display Modes

Teams support two display modes:

### In-Process (Default)
All teammates in main terminal, use Shift+Up/Down to navigate between them.

### Split Panes
Each teammate in separate pane (requires tmux or iTerm2).

Configure in `.claude/settings.json`:
```json
{
  "teammateMode": "in-process" | "auto" | "tmux"
}
```

## Choosing the Right Team

| Situation | Use This Team |
|-----------|--------------|
| Starting a new project | Inception Team |
| Defining architecture | Elaboration Team |
| Building features | Construction Team |
| Preparing for release | Transition Team |
| Implementing a feature | Feature Team |
| Debugging an issue | Investigation Team |
| Planning iteration | Planning Team |
| Comprehensive work | Full Team |

## Best Practices

1. **Start with the minimum roles**: Only spawn teammates for roles needed
2. **Add roles as needed**: You can add more teammates during the session
3. **Use clear prompts**: Explain what each role should focus on
4. **Let teammates collaborate**: They can message each other directly
5. **Monitor progress**: Check in on teammates and redirect if needed
6. **Clean up when done**: Remove teammates after work is complete

## Example Workflows

### Implementing a Feature
```
Create an OpenUP agent team for feature implementation.

The analyst should gather requirements and create use cases.
The architect should design the feature architecture.
The developer should implement the feature with tests.
The tester should validate the feature meets requirements.
```

### Debugging an Issue
```
Create an OpenUP investigation team to investigate the login timeout issue.

The team should:
1. Reproduce the issue
2. Analyze the code and architecture
3. Find the root cause
4. Implement a fix
5. Verify the fix works
6. Add tests to prevent regression
```

### Iteration Planning
```
Create an OpenUP planning team for iteration planning.

The team should:
1. Review the current iteration status
2. Identify candidate tasks for the next iteration
3. Assess technical feasibility and effort
4. Prioritize tasks based on value and dependencies
5. Create the iteration plan
```

## References

- Team configs are located in: `docs-eng-process/.claude-templates/teams/`
- Role instructions are located in: `.claude/teammates/`
- CLAUDE.md: `docs-eng-process/.claude-templates/CLAUDE.md`

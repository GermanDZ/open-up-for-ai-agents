# OpenUP Agent Team Instructions

This file provides instructions for using OpenUP agent teams with Claude Code.

## About OpenUP

OpenUP (Open Unified Process) is a lean, iterative software development methodology with four phases:

1. **Inception** - Define scope, vision, and feasibility
2. **Elaboration** - Establish architecture baseline
3. **Construction** - Build the system incrementally
4. **Transition** - Deploy to users

## OpenUP Skills

OpenUP provides skills that automate common workflow operations. Skills are invoked using the `/` command.

### Phase Skills

Guide you through each OpenUP phase:

- `/openup-inception` - Initialize and manage Inception phase activities
- `/openup-elaboration` - Initialize and manage Elaboration phase activities
- `/openup-construction` - Initialize and manage Construction phase activities
- `/openup-transition` - Initialize and manage Transition phase activities

Example:
```
/openup-inception activity: initiate
```

### Artifact Skills

Create OpenUP work products from templates:

- `/openup-create-vision` - Generate vision document
- `/openup-create-use-case` - Create use case specification
- `/openup-detail-use-case` - Transform high-level use case into detailed scenarios with test cases
- `/openup-shared-vision` - Create shared technical vision for team alignment
- `/openup-create-architecture-notebook` - Generate/update architecture documentation
- `/openup-create-risk-list` - Create or update risk assessment
- `/openup-create-iteration-plan` - Plan iteration based on current state
- `/openup-create-test-plan` - Generate test cases and scripts
- `/openup-create-documentation` - Generate user guides, API references, troubleshooting, and tutorials

Example:
```
/openup-create-vision project_name: "MyApp" problem_statement: "Users need a way to..."
```

### Workflow Skills

Automate workflow operations:

- `/openup-start-iteration` - Begin new iteration (reads project-status, updates iteration)
- `/openup-complete-task` - Mark task complete, update roadmap, commit changes, optionally create PR
- `/openup-create-pr` - Create pull request with roadmap task context
- `/openup-assess-completeness` - Lightweight readiness assessment before task completion or phase transition
- `/openup-retrospective` - Generate iteration retrospective with feedback and action items
- `/openup-tdd-workflow` - Guide Test-Driven Development cycle adapted for AI agents
- `/openup-request-input` - Create input request document for async stakeholder communication
- `/openup-phase-review` - Check phase completion criteria and prepare for review
- `/openup-log-run` - Create traceability logs (markdown + JSONL)

Example:
```
/openup-start-iteration iteration_number: 2 goal: "Complete user authentication"
```

See [skills guide](docs-eng-process/skills-guide.md) for complete skill documentation.

## Agent Teams

OpenUP supports role-based agent teams. Each teammate represents an OpenUP role and follows specific instructions.

### Available Roles

| Role | Focus | Key Work Products |
|------|-------|-------------------|
| **analyst** | Requirements, stakeholder communication | Vision, Use Cases, Requirements |
| **architect** | Architecture design, technical decisions | Architecture Notebook |
| **developer** | Implementation, unit testing | Design, Code, Unit Tests |
| **project-manager** | Planning, coordination | Project Plan, Iteration Plan, Risk List |
| **tester** | Test planning, execution | Test Cases, Test Scripts, Test Logs |

### Team Configurations

#### Phase-Specific Teams
- `/openup-inception` phase: analyst + project-manager (+ architect as needed)
- `/openup-elaboration` phase: architect + developer + tester (+ analyst as needed)
- `/openup-construction` phase: developer + tester (+ architect + analyst as needed)
- `/openup-transition` phase: tester + project-manager + developer (+ analyst as needed)

#### Task-Specific Teams

**Full Team** (All Roles)
```
Create an OpenUP agent team with all roles: analyst, architect, developer, project-manager, and tester.
```

**Feature Team** (Analyst, Architect, Developer, Tester)
```
Create an OpenUP agent team for feature implementation. Spawn analyst for requirements, architect for design, developer for implementation, and tester for validation.
```

**Investigation Team** (Architect, Developer, Tester)
```
Create an OpenUP agent team to investigate this issue. Spawn architect to analyze the architecture, developer to find root cause, and tester to verify the fix.
```

**Planning Team** (Analyst, Project Manager)
```
Create an OpenUP agent team for iteration planning. Spawn analyst to review requirements and project-manager to update the plan.
```

See [teams guide](docs-eng-process/teams-guide.md) for complete team documentation.

## Critical Requirement: All Work Must Be in an Iteration

**IMPORTANT**: Before any team begins work, the team lead MUST use the `/openup-start-iteration` skill to initialize an iteration. All work must be tracked as part of an iteration, regardless of team type or task scope.

The team lead should:
1. First call `/openup-start-iteration` with appropriate iteration number and goal
2. Then proceed with the assigned work
3. Use `/openup-complete-task` when work is finished

This ensures proper tracking, documentation, and adherence to the OpenUP iterative process.

## How to Use Agent Teams

### Step 1: Enable Agent Teams

Agent teams must be enabled in your environment:

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

Or add to `.claude/settings.json`:
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

### Step 2: Configure Settings (Optional)

Copy `docs-eng-process/.claude-templates/settings.json.example` to `.claude/settings.json` for quality enforcement hooks.

### Step 3: Create a Team

Ask Claude to create a team with the appropriate roles for your task:

```
Create an OpenUP agent team with [list of roles] to [describe task].
```

### Step 4: Coordinate Work

The team lead will coordinate work across teammates. You can:
- Message individual teammates directly (Shift+Up/Down in in-process mode)
- Ask the lead to assign specific tasks to specific roles
- Monitor progress through the shared task list

### Step 5: Clean Up

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

## Quality Hooks

OpenUP includes optional quality enforcement hooks in `.claude/settings.json`:

- **Pre-commit**: Check for required documentation
- **Post-edit**: Prompt for documentation updates
- **Stop**: Verify completion criteria before stopping

See `docs-eng-process/.claude-templates/settings.json.example` for hook configuration.

## Example Workflows

### Starting Inception

```
/openup-inception activity: initiate
Create an OpenUP agent team for inception phase. Spawn analyst and project-manager.
```

### Implementing a Feature

```
Create an OpenUP agent team to implement the [feature name] feature.

Spawn:
- analyst: to gather requirements and define acceptance criteria
- architect: to design the component architecture
- developer: to implement the feature
- tester: to create and execute tests

The analyst should first create use cases for this feature, then the architect should design it, then the developer should implement it with tests.
```

### Debugging an Issue

```
Create an OpenUP investigation team. Spawn architect to analyze, developer to find root cause, tester to verify fix.
```

### Creating Architecture Documentation

```
/openup-create-architecture-notebook system_name: "MyApp" architectural_concerns: "scalability, security"
```

### Creating Shared Technical Vision

```
/openup-shared-vision technical_objectives: "scalability, security" scope_focus: "user authentication"
```

### Detailing Use Cases

```
/openup-detail-use-case use_case_name: "user-login" generate_tests: true
```

### Creating User Documentation

```
/openup-create-documentation doc_type: user-guide feature: user-authentication
```

### Running Iteration Retrospective

```
/openup-retrospective include_metrics: true
```

### Test-Driven Development

```
/openup-tdd-workflow feature: payment-processing phase: full
```

### Assessing Completeness

```
/openup-assess-completeness scope: iteration
```

### Completing a Task and Creating PR

```
/openup-complete-task task_id: T-005 create_pr: true
```

### Phase Review

```
/openup-phase-review
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

## Updating OpenUP Skills

To get the latest skills, teammates, and teams from the framework:

### Option 1: Using sync-from-framework.sh (Recommended)

```bash
# First time: Copy script to your project
cp /path/to/open-up-for-ai-agents/scripts/sync-from-framework.sh ./scripts/
chmod +x ./scripts/sync-from-framework.sh

# Pull latest framework updates
cd /path/to/open-up-for-ai-agents && git pull

# Sync to your project
cd /path/to/your-project
./scripts/sync-from-framework.sh --framework-path /path/to/open-up-for-ai-agents
```

### Option 2: Manual Copy

```bash
FRAMEWORK="/path/to/open-up-for-ai-agents"
cp -r "$FRAMEWORK/docs-eng-process/.claude-templates/skills" .claude/
cp -r "$FRAMEWORK/docs-eng-process/.claude-templates/teammates" .claude/
cp -r "$FRAMEWORK/docs-eng-process/.claude-templates/teams" .claude/
```

See [scripts/README.md](../scripts/README.md) for more details.

## Best Practices

1. **Use skills for common operations**: Skills automate repetitive tasks and ensure consistency
2. **Start with the right roles**: Only spawn teammates for roles needed for the task
3. **Use clear prompts**: Explain what each role should focus on
4. **Let teammates collaborate**: They can message each other directly
5. **Monitor progress**: Check in on teammates and redirect if needed
6. **Clean up when done**: Remove teammates after work is complete

## Troubleshooting

If teammates aren't appearing:
- Press Shift+Down to cycle through active teammates (in-process mode)
- Check that agent teams are enabled (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`)
- Verify the task is complex enough to warrant a team

If teammates stop on errors:
- Check their output using Shift+Up/Down (in-process) or click pane (split)
- Give additional instructions or spawn a replacement teammate

For more information on agent teams, see: https://code.claude.com/docs/en/agent-teams

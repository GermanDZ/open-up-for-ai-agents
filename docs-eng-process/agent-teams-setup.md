# Agent Teams Setup Guide

This document describes how to set up and use Claude Code agent teams with OpenUP roles in your project.

## Overview

This framework includes pre-configured agent team templates based on OpenUP (Open Unified Process) roles. Each teammate has specific instructions, work products, and collaboration patterns defined by the OpenUP methodology.

## Quick Start

### 1. Enable Agent Teams

Set the environment variable to enable agent teams in Claude Code:

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

Or add to your `settings.json`:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

### 2. Set Up in a New Project

When you bootstrap a new project using `scripts/bootstrap-project.sh`, agent team templates are automatically installed.

For an existing project, run the setup script:

```bash
./scripts/setup-agent-teams.sh
```

This copies the following files to your `.claude/` directory:

- `.claude/teammates/*.md` - Individual role instructions for each OpenUP role
- `.claude/teams/*.md` - Team configuration files
- `.claude/CLAUDE.openup.md` - Shared OpenUP agent team instructions

Your project-owned `.claude/CLAUDE.md` is preserved; the setup script adds a short reference line to the OpenUP instructions if missing.

### 3. Create a Team

Once set up, you can create agent teams in Claude Code:

```
Create an OpenUP agent team with analyst, architect, developer, and tester roles to implement a new feature.
```

## Available Roles

| Role | Focus | Key Documents |
|------|-------|---------------|
| **analyst** | Requirements gathering, stakeholder communication | Vision, Use Cases, Requirements |
| **architect** | Architecture design, technical decisions | Architecture Notebook |
| **developer** | Implementation, unit testing | Design, Code, Unit Tests |
| **project-manager** | Planning, coordination | Project Plan, Iteration Plan, Risk List |
| **tester** | Test planning, execution | Test Cases, Test Scripts, Test Logs |

## Team Configurations

### Full Team

All five roles for comprehensive project work:

```
Create an OpenUP agent team with all roles: analyst, architect, developer, project-manager, and tester.
```

### Feature Team

For implementing features:

```
Create an OpenUP agent team for feature implementation.
Spawn analyst for requirements, architect for design, developer for implementation, and tester for validation.
```

### Investigation Team

For debugging and investigation:

```
Create an OpenUP agent team to investigate this bug.
Spawn architect to analyze, developer to find root cause, and tester to verify the fix.
```

### Planning Team

For iteration planning:

```
Create an OpenUP agent team for iteration planning.
Spawn analyst to review requirements and project-manager to update the plan.
```

## Role Instructions

Each teammate has detailed instructions based on their OpenUP role:

- `.claude/teammates/analyst.md` - Analyst role instructions
- `.claude/teammates/architect.md` - Architect role instructions
- `.claude/teammates/developer.md` - Developer role instructions
- `.claude/teammates/project-manager.md` - Project Manager role instructions
- `.claude/teammates/tester.md` - Tester role instructions

These instructions include:

- Role definition and responsibilities
- Skills and expertise required
- Work products created/modified
- Tasks performed
- How the role works
- When to involve other roles
- Key references in the OpenUP knowledge base

## Team Workflow

The team follows the OpenUP iterative workflow:

1. **Inception** - Analyst + Project Manager lead
   - Define vision and scope
   - Identify key use cases
   - Document major risks

2. **Elaboration** - Architect + Developer lead
   - Establish architecture baseline
   - Detail architecturally significant requirements
   - Create initial design

3. **Construction** - Developer + Tester lead
   - Build system incrementally
   - Implement tests
   - Integrate components

4. **Transition** - Developer + Project Manager lead
   - Deploy to users
   - Verify acceptance
   - Close project

## Display Modes

### In-Process Mode (Default)

All teammates run in your main terminal. Navigate between them:

- **Shift+Up/Down** - Select a teammate
- **Type** - Send message to selected teammate
- **Enter** - View selected teammate's session
- **Escape** - Interrupt current turn
- **Ctrl+T** - Toggle task list

### Split-Pane Mode

Each teammate gets its own pane. Requires **tmux** or **iTerm2**:

```bash
# Install tmux
brew install tmux  # macOS
sudo apt install tmux  # Ubuntu

# Or enable iTerm2 Python API
# iTerm2 → Settings → General → Magic → Enable Python API
```

Configure in `settings.json`:

```json
{
  "teammateMode": "tmux"  // or "in-process"
}
```

## Working with Teams

### Assigning Tasks

Ask the team lead to assign specific tasks:

```
Assign the requirements gathering task to the analyst.
```

Teammates can also self-claim tasks from the shared task list.

### Messaging Teammates

Direct message a specific teammate:

- **In-process**: Select teammate with Shift+Up/Down, then type your message
- **Split-pane**: Click into the teammate's pane and type

### Monitoring Progress

Check the shared task list to see what each teammate is working on.

### Cleaning Up

When work is complete:

```
Clean up the team
```

This removes shared resources. Teammates should be shut down first:

```
Ask the analyst teammate to shut down.
```

## Example Workflows

### Implementing a New Feature

```
Create an OpenUP agent team to implement user authentication.

Spawn:
- analyst: to define requirements and use cases
- architect: to design the auth architecture
- developer: to implement the auth system
- tester: to create and run security tests

The analyst should start by documenting the requirements in docs/use-cases/.
Then the architect should design the system in docs/architecture-notebook.md.
Then the developer should implement it with tests.
Finally, the tester should verify security and functionality.
```

### Architecture Review

```
Create an OpenUP agent team to review our architecture.

Spawn:
- architect: to lead the review
- developer: to provide implementation feedback
- tester: to assess testability

The team should review docs/architecture-notebook.md and identify any issues or improvements.
```

### Bug Investigation

```
Create an OpenUP agent team to fix the login bug.

Spawn:
- developer: to analyze and fix the code
- tester: to reproduce and verify the fix
- architect: to assess if there are architectural implications

The developer should find the root cause, fix it, then the tester should verify it works.
```

### Iteration Planning

```
Create an OpenUP agent team for iteration planning.

Spawn:
- project-manager: to lead planning
- analyst: to review and prioritize requirements
- architect: to assess technical feasibility
- developer: to provide effort estimates

The team should review docs/roadmap.md and create docs/iteration-plan.md.
```

## Troubleshooting

### Teammates Not Appearing

- Press **Shift+Down** to cycle through active teammates (in-process mode)
- Verify agent teams are enabled: `echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`
- Check that your task is complex enough to warrant a team

### Teammates Stopping on Errors

- Check their output using Shift+Up/Down (in-process) or click pane (split)
- Give additional instructions directly to the teammate
- Or spawn a replacement teammate

### Too Many Permission Prompts

Pre-approve common operations in your permission settings before spawning teammates.

### Lead Stops Too Early

Tell the lead to wait for teammates:

```
Wait for your teammates to complete their tasks before proceeding.
```

## Customization

### Adding Custom Roles

Create a new teammate instruction file:

```bash
# Create custom role
.claude/teammates/custom-role.md
```

Reference it when creating teams:

```
Create a team with analyst, architect, and custom-role.
```

### Modifying Role Instructions

Edit the teammate instruction files in `.claude/teammates/` to customize behavior for your project.

### Adding Team Configurations

Create new team configurations in `.claude/teams/` for common patterns in your project.

## Resources

- [Claude Code Agent Teams Documentation](https://code.claude.com/docs/en/agent-teams)
- [OpenUP Knowledge Base](openup-knowledge-base/)
- [Agent Workflow](agent-workflow.md) - Operating procedures for agents
- [How to Work](how-to-work.md) - Process overview

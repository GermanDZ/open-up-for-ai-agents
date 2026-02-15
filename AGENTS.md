# AI Agent Entrypoint

This repository provides OpenUP (Open Unified Process) templates and configurations for use with Claude Code's AI agents.

## Key Principles

### Before Implementing Any Feature

1. **Check naming conventions**: Look at existing code for established patterns (URL parameters, form fields, API params, cookies)
2. **Check frontend-backend correspondence**: Ensure naming and data flow align between frontend components and backend handlers

### Before Creating a PR

1. Run tests/CI to verify all checks pass
2. **Manual verification** (if applicable): Test the feature in its runtime environment (e.g., browser for web apps)
3. Create PR with link to issue

## Quick Start

**For using OpenUP in your own project**, copy the templates:

```bash
# Copy Claude Code configurations
cp -r docs-eng-process/.claude-templates/teammates .claude/
cp -r docs-eng-process/.claude-templates/teams .claude/
cp docs-eng-process/.claude-templates/CLAUDE.md .claude/
cp -r docs-eng-process/.claude-templates/skills .claude/
cp docs-eng-process/.claude-templates/settings.json.example .claude/settings.json

# Copy OpenUP documentation
cp -r docs-eng-process/openup-knowledge-base docs-eng-process/
cp docs-eng-process/agent-workflow.md docs-eng-process/
cp docs-eng-process/skills-guide.md docs-eng-process/
cp docs-eng-process/teams-guide.md docs-eng-process/
cp -r docs-eng-process/templates docs-eng-process/

# Enable agent teams
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

## Documentation

👉 **[docs-eng-process/README.md](docs-eng-process/README.md)** - Canonical entrypoint for all AI agents

**Key Documentation**:
- **[.claude/CLAUDE.md](.claude/CLAUDE.md)** - How to use OpenUP skills and teams (setup instructions included)
- **[docs-eng-process/agent-workflow.md](docs-eng-process/agent-workflow.md)** - Complete agent operating procedures
- **[docs-eng-process/skills-guide.md](docs-eng-process/skills-guide.md)** - All OpenUP skills documentation
- **[docs-eng-process/teams-guide.md](docs-eng-process/teams-guide.md)** - Team configuration reference
- **[docs-eng-process/init-prompts.md](docs-eng-process/init-prompts.md)** - Copy/paste prompts to initialize a new project

## What's Included

### Skills (`.claude/skills/`)
Reusable workflow operations that can be invoked with `/`:
- **Phase skills**: `/inception`, `/elaboration`, `/construction`, `/transition`
- **Artifact skills**: `/create-vision`, `/create-use-case`, `/create-architecture-notebook`, etc.
- **Workflow skills**: `/start-iteration`, `/complete-task`, `/request-input`, `/phase-review`, `/log-run`

### Teams (`.claude/teams/`)
Pre-configured agent teams for different scenarios:
- **Phase teams**: Inception, Elaboration, Construction, Transition
- **Task teams**: Feature, Investigation, Planning, Full Team

### Teammates (`.claude/teammates/`)
Role-based instructions for AI agents:
- **analyst.md** - Requirements and stakeholder communication
- **architect.md** - Architecture design and technical decisions
- **developer.md** - Implementation and unit testing
- **project-manager.md** - Planning and coordination
- **tester.md** - Test planning and execution

### Templates (`docs-eng-process/templates/`)
OpenUP work product templates:
- Vision, Use Case, Architecture Notebook, Risk List, Iteration Plan, etc.

### Quality Hooks (`.claude/settings.json.example`)
Optional quality enforcement:
- Pre-commit documentation checks
- Post-edit documentation prompts
- Stop verification for completion criteria

## How Templates Work

This repository contains **templates** that can be copied to other projects. The templates are organized in `docs-eng-process/.claude-templates/`:

```
docs-eng-process/.claude-templates/
├── CLAUDE.md              # Main instructions (with setup guide)
├── settings.json.example  # Example settings with hooks
├── skills/                # Reusable workflow skills
│   ├── openup-phases/     # Phase-specific skills
│   ├── openup-artifacts/  # Artifact creation skills
│   └── openup-workflow/   # Workflow automation skills
├── teams/                 # Team configurations
│   ├── openup-full-team.md
│   ├── openup-inception-team.md
│   ├── openup-elaboration-team.md
│   ├── openup-construction-team.md
│   ├── openup-transition-team.md
│   ├── openup-feature-team.md
│   ├── openup-investigation-team.md
│   └── openup-planning-team.md
└── teammates/             # Role-based instructions
    ├── analyst.md
    ├── architect.md
    ├── developer.md
    ├── project-manager.md
    └── tester.md
```

## Example Usage

After copying templates to your project:

```
# Start a new iteration
/start-iteration goal: "Implement user authentication"

# Create a team for the work
Create an OpenUP agent team for construction phase. Spawn developer and tester.

# Create artifacts
/create-architecture-notebook system_name: "MyApp"

# Complete work
/complete-task task_id: T-001

# Review phase
/phase-review
```

## About OpenUP

OpenUP (Open Unified Process) is a lean, iterative software development methodology with four phases:

1. **Inception** - Define scope, vision, and feasibility
2. **Elaboration** - Establish architecture baseline
3. **Construction** - Build the system incrementally
4. **Transition** - Deploy to users

Each phase has specific objectives, work products, and completion criteria. The skills and teams in this repository are designed to support the OpenUP methodology with Claude Code's AI agents.

---

**Note**: This file exists for tool compatibility. The authoritative process documentation lives in `docs-eng-process/`.

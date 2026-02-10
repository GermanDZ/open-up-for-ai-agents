# OpenUP for AI Agents - Quick Start Guide

Get started with OpenUP in 5 minutes. This guide covers everything you need to begin using AI agent teams for software development.

## What is OpenUP?

OpenUP (Open Unified Process) is a lean methodology for iterative software development. This framework adapts OpenUP for AI agent teams, providing:

- **Role-based agents** (Analyst, Architect, Developer, Tester, Project Manager)
- **Automated workflows** via skills (one-command operations)
- **Project tracking** (iterations, roadmap, vision)
- **Traceability** (logs, git integration)

## Prerequisites

1. **Claude Code** with agent teams enabled:
   ```bash
   export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
   ```

2. **Git** repository initialized

3. **Python 3.10+** (for parsing scripts)

## One-Command Setup

The fastest way to get started:

```
/openup-init
```

This will:
- Create project structure (`docs/`, `.claude/`)
- Generate initial documents
- Configure agent teams
- Provide next steps

**Answer the prompts:**
- Project name: MyProject
- Project type: web/api/library/cli
- Initial phase: inception (recommended for new projects)

## Manual Setup (Alternative)

If you prefer manual setup:

```bash
# 1. Copy skills to your project
cp -r docs-eng-process/.claude-templates/skills .claude/
cp -r docs-eng-process/.claude-templates/teammates .claude/

# 2. Create docs directory
mkdir -p docs/{input-requests,use-cases,agent-logs}

# 3. Initialize project status
cat > docs/project-status.md << 'EOF'
# Project Status

**Project**: MyProject
**Phase**: inception
**Iteration**: 0
**Iteration Goal**: Project initialization
**Status**: initialized
**Current Task**: None
**Started**: [today's date]
**Last Updated**: [today's date]
**Updated By**: user
EOF

# 4. Create roadmap
cat > docs/roadmap.md << 'EOF'
# Project Roadmap

## T-001: Initialize OpenUP Project
**Status**: completed
**Priority**: high

## T-002: Define Project Vision
**Status**: pending
**Priority**: high
EOF
```

## Your First Iteration

### Step 1: Start an Iteration

```
/openup-start-iteration task_id: T-002 goal: "Define project vision"
```

This creates a branch and updates project status.

### Step 2: Create a Team

```
Create an OpenUP agent team for inception phase.
Spawn analyst and project-manager.
```

### Step 3: Do the Work

The analyst will:
- Create vision document: `/openup-create-vision`
- Define use cases: `/openup-create-use-case`

The project manager will:
- Plan iteration: `/openup-create-iteration-plan`
- Update roadmap

### Step 4: Complete the Task

```
/openup-complete-task task_id: T-002
```

This commits changes and updates the roadmap.

## Essential Skills

### Project Management
- `/openup-start-iteration` - Begin new iteration
- `/openup-complete-task` - Finish task and commit
- `/openup-create-pr` - Create pull request

### Documentation
- `/openup-create-vision` - Project vision
- `/openup-create-use-case` - Use case spec
- `/openup-create-architecture-notebook` - Architecture docs

### Quality
- `/openup-assess-completeness` - Check readiness
- `/openup-retrospective` - Iteration retrospective
- `/openup-tdd-workflow` - Test-driven development

### Quick Operations
- `/openup-quick-task` - Fast iteration for small changes
- `/openup-init` - Initialize new project

## Common Workflows

### Quick Bug Fix
```
/openup-quick-task task: "Fix typo in README"
```

### Feature Development
```
/openup-start-iteration task_id: T-005
[Work on feature]
/openup-complete-task task_id: T-005 create_pr: true
```

### Architecture Decision
```
Create OpenUP investigation team. Spawn architect and developer.
[Discuss and document decision]
/openup-create-architecture-notebook
```

## Project Structure

```
my-project/
├── .claude/
│   ├── skills/           # Automated operations
│   ├── teammates/        # Role instructions
│   ├── teams/            # Team configurations
│   ├── cache/            # Cached parsed data
│   └── config/           # Settings (tiered-context.md)
├── docs/
│   ├── project-status.md # Current iteration state
│   ├── roadmap.md        # Task backlog
│   ├── vision.md         # Project vision
│   ├── input-requests/   # Stakeholder questions
│   ├── use-cases/        # Use case specs
│   └── agent-logs/       # Activity logs
└── docs-eng-process/     # Framework documentation
```

## Tips for Success

1. **Always work in iterations** - Use `/openup-start-iteration` before any work
2. **Use caching** - Scripts cache results automatically for 30-50% token savings
3. **Choose the right tier** - Use minimal for quick tasks, full for phase reviews
4. **Let agents collaborate** - They can message each other directly
5. **Clean up teams** - Remove teammates when work is complete

## Token Optimization

Enable these practices to reduce token usage:

```bash
# Use minimal context for quick tasks
python3 .claude/scripts/batch-context.py --minimal

# Check token usage
python3 .claude/scripts/token-tracker.py stats

# Use compact role instructions
# Set OPENUP_CONTEXT_TIER=minimal in environment
```

## Getting Help

- **Skills reference**: `docs-eng-process/skills-guide.md`
- **Teams guide**: `docs-eng-process/teams-guide.md`
- **Agent workflow**: `docs-eng-process/agent-workflow.md`
- **Troubleshooting**: `docs-eng-process/USER-GUIDE.md`

## Next Steps

1. ✅ Initialize your project: `/openup-init`
2. ✅ Start first iteration: `/openup-start-iteration`
3. ✅ Create your team with appropriate roles
4. ✅ Use skills to automate workflows
5. ✅ Review and iterate with `/openup-retrospective`

**Welcome to OpenUP for AI Agents! 🚀**

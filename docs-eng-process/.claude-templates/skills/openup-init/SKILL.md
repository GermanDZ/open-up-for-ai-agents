---
name: openup-init
description: One-command project setup for OpenUP - interactive initialization wizard
arguments:
  - name: project_name
    description: The project name (optional, will prompt if not provided)
    required: false
  - name: project_type
    description: "Type of project: web, api, library, mobile (optional, will prompt if not provided)"
    required: false
  - name: skip_teams
    description: "Skip agent team setup (default: false)"
    required: false
---

# OpenUP Init - Interactive Project Setup

This skill provides a **one-command initialization** for OpenUP projects, replacing the complex multi-step setup process with an interactive conversational flow.

## When to Use

Use this skill when:
- Starting a new OpenUP project
- Setting up OpenUP in an existing repository
- Need quick project initialization without manual steps

## When NOT to Use

Do NOT use this skill when:
- Project is already initialized (use phase skills instead)
- Need to customize individual components (manual setup recommended)

## Success Criteria

After using this skill, verify:
- [ ] Project structure is created
- [ ] Initial documents are generated
- [ ] Agent teams are configured (if enabled)
- [ ] Git is initialized (if needed)

## Process

### 1. Gather Project Information

If not provided via arguments, interactively prompt for:

**Project Name**: What would you like to call this project?

**Project Type**: What type of project is this?
- `web` - Web application (frontend/backend)
- `api` - REST/GraphQL API service
- `library` - Reusable code library/package
- `mobile` - Mobile application
- `cli` - Command-line tool
- `other` - Specify

**Initial Phase**: Which phase should we start in?
- `inception` - Define scope and vision (default for new projects)
- `elaboration` - Architecture planning (for projects with vision)
- `construction` - Active development
- `transition` - Deployment preparation

### 2. Create Project Structure

Create the following directories:
```
docs/
├── input-requests/      # Stakeholder input documents
├── use-cases/           # Use case specifications
└── agent-logs/          # Agent activity logs
```

### 3. Generate Initial Documents

#### Project Status (`docs/project-status.md`)
```markdown
# Project Status

**Project**: [PROJECT_NAME]
**Phase**: [INITIAL_PHASE]
**Iteration**: 0
**Iteration Goal**: Project initialization
**Status**: initialized
**Current Task**: None
**Started**: [DATE]
**Last Updated**: [DATE]
**Updated By**: openup-init
```

#### Roadmap (`docs/roadmap.md`)
```markdown
# Project Roadmap

## T-001: Initialize OpenUP Project Structure
**Status**: completed
**Priority**: high
**Description**: Initial project setup and documentation structure

## T-002: [Next Task Placeholder]
**Status**: pending
**Priority**: medium
**Description**: [To be defined]
```

### 4. Configure Agent Teams (if not skipped)

**Check if agent teams are enabled:**
```bash
# Check environment variable
if [ -z "$CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS" ]; then
  echo "Agent teams not enabled. Enable with:"
  echo "export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1"
fi
```

**Create initial team configuration:**
- Set default team type based on project type and phase
- Create `.claude/settings.json` with recommended hooks

### 5. Initialize Git (if needed)

Check if git is initialized:
```bash
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  git init
  # Create initial commit
fi
```

### 6. Create Initial Branch (Optional)

If starting with inception phase:
- Detect trunk branch
- Create branch: `inception/initialize-project`
- Update project status

## Output

Returns a summary of:
- Project name and type
- Initial phase
- Created files and directories
- Next steps

## Smart Defaults

The skill uses intelligent defaults based on project type:

| Project Type | Default Phase | Recommended Team | Initial Tasks |
|--------------|---------------|------------------|---------------|
| web | inception | analyst + architect | Requirements, Architecture |
| api | elaboration | architect + developer | API design, Implementation |
| library | construction | developer + tester | Implementation, Testing |
| mobile | inception | analyst + architect | Requirements, UX Design |
| cli | construction | developer | Implementation |

## Quick Start Templates

### Web Application
```bash
/openup-init project_name: "MyWebApp" project_type: web
```

### API Service
```bash
/openup-init project_name: "MyAPI" project_type: api
```

### Code Library
```bash
/openup-init project_name: "MyLib" project_type: library
```

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Directory not empty | Project already initialized | Use existing structure or specify new location |
| Git not found | Git not installed | Install git or use --no-git flag |
| Permission denied | Cannot create directories | Check directory permissions |

## Next Steps

After initialization:

1. **For Inception Phase**: Use `/openup-inception activity: initiate`
2. **Create Vision**: Use `/openup-create-vision`
3. **Start First Iteration**: Use `/openup-start-iteration`
4. **Spawn Team**: Create appropriate agent team for your phase

## See Also

- [openup-inception](../openup-phases/inception/SKILL.md) - Inception phase guidance
- [openup-create-vision](../openup-artifacts/create-vision/SKILL.md) - Vision document creation
- [Agent Teams Setup](../../docs-eng-process/agent-teams-setup.md) - Team configuration guide

## Examples

### Minimal Setup
```
/openup-init
# Prompts for all information interactively
```

### Full Setup with Teams
```
/openup-init project_name: "ECommerce" project_type: web
# Creates web app structure with team configuration
```

### Existing Project
```
/openup-init project_name: "ExistingAPI" project_type: api skip_teams: true
# Adds OpenUP to existing project without team setup
```

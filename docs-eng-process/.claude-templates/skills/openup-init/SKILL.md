---
name: openup-init
description: One-command project setup for OpenUP - interactive initialization wizard
model: inherit
arguments:
  - name: project_name
    description: The project name (optional, will prompt if not provided)
    required: false
  - name: project_type
    description: Type of project: web, api, library, mobile (optional, will prompt if not provided)
    required: false
  - name: skip_teams
    description: Skip agent team setup (default: false)
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

### ⚠️ Gate awareness — scaffold with Bash, not Write/Edit

A fresh project has **no `.openup/state.json` yet** (the first iteration has not
started). The `gate-edits.py` PreToolUse hook therefore **blocks the `Write`,
`Edit`, and `NotebookEdit` tools** on any non-exempt path — including
`docs/project-status.md`, `docs/roadmap.md`, and `docs/project-config.yaml` —
because no iteration plan is persisted. This is by design: you cannot start an
iteration in a project that does not exist yet.

The gate only fires on the editing **tools**, so create every bootstrap file
with the **`Bash` tool** (`cp` for templates, `cat > … << 'EOF'` heredocs for
generated files, `mkdir -p` for directories). Bash file creation is gate-exempt.

Do **not** reach for `Write`/`Edit` during initialization — the hook will block
them and the run will stall. Once `/openup-init` has scaffolded the project, the
first real change goes through `/openup-start-iteration` (or `/openup-quick-task`),
which persists state and unblocks the editing tools normally.

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

Create the following directories **with Bash** (gate-exempt):
```bash
mkdir -p docs/input-requests docs/use-cases docs/agent-logs
# docs/input-requests  — Stakeholder input documents
# docs/use-cases       — Use case specifications
# docs/agent-logs      — Agent activity logs
```

### 3. Generate Initial Documents

Write each file below **with Bash** — `cp` for templates, `cat > FILE << 'EOF'`
heredocs for the generated content. The markdown shown is the file *content*, not
a `Write`-tool call (see "Gate awareness" above).

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

#### Project Config (`docs/project-config.yaml`)

Emit a starter `docs/project-config.yaml` by copying
`docs-eng-process/templates/project-config.example.yaml`, then prompt the user to
fill in the `context:` block (stack, domain, key stakeholders) for this project.
It is the project-owned home for facts + per-artifact rules injected into every
`/openup-create-*` prompt — see `docs-eng-process/project-config.md`. The file is
optional: leaving the placeholders means the framework defaults apply unchanged.

After copying, **append** this commented `environments:` starter (the template is
OpenUP-layer read-only, so the block is added here, not there):

```yaml
# environments:           # ordered deployment chain, first = closest to the team
#   - name: staging
#     promotion: "smoke suite green; no Sev-1 defects open"
#   - name: beta
#     promotion: "beta-user acceptance recorded; success-measure instrumentation emitting"
#   - name: production
```

Uncommented, the chain is consumed by `/openup-transition` (one promotion
checklist per hop) and by task-spec `## Rollout` default states. The three names
are the documented example, **not** a schema — any ordered list works. Left
commented, deployment behaves as the single-hop framework default.

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
- Next steps — point the user at the **Skill Fit Matrix** in `docs-eng-process/QUICK-REFERENCE.md` so they pick `/quick-task` vs `/start-iteration` vs `/orchestrate` correctly

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

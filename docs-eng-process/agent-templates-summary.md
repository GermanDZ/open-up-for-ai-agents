# OpenUP Agent Teams - Template Summary

This document provides an overview of the Claude Code agent team templates that are included in this framework.

## What Are Agent Teams?

Claude Code agent teams allow you to spawn multiple independent AI agents (teammates) that work together on a task. Each teammate can have a different role and specialization, and they can communicate directly with each other.

## OpenUP Agent Team Templates

This framework includes pre-configured agent team templates based on OpenUP (Open Unified Process) roles. When you set up a host project using this framework, you get:

### 1. Teammate Instructions (`docs-eng-process/.claude-templates/teammates/*.md`)

Each OpenUP role has a dedicated instruction file that defines:

- **Role Definition** - What the role is responsible for
- **Key Responsibilities** - Primary duties
- **Skills and Expertise** - Required capabilities
- **Work Products** - Documents/artifacts created/modified
- **Tasks Performed** - Activities the role undertakes
- **How to Work** - Step-by-step workflow
- **When to Involve Other Roles** - Collaboration patterns
- **Key References** - Links to OpenUP knowledge base

Available roles:
- **analyst.md** - Requirements gathering, stakeholder communication
- **architect.md** - Architecture design, technical decisions
- **developer.md** - Implementation, unit testing
- **project-manager.md** - Planning, coordination, risk management
- **tester.md** - Test planning, execution, results analysis

### 2. Team Configurations (`docs-eng-process/.claude-templates/teams/*.md`)

Pre-defined team configurations for common scenarios:

- **openup-full-team.md** - All five roles working together

Each team configuration defines:
- Team member roles and their focus
- Collaboration patterns between roles
- Example prompts for creating the team
- Task assignment guidelines

### 3. CLAUDE.md Template (`docs-eng-process/.claude-templates/CLAUDE.md`)

Shared OpenUP instructions (synced into projects as `.claude/CLAUDE.openup.md`):

- How to enable agent teams
- Available team configurations
- How to create teams
- Role-based instructions reference
- Example workflows for common scenarios
- Display modes and interaction patterns
- Best practices and troubleshooting

## How Templates Are Used

### In a New Project (Bootstrap)

When you run `scripts/bootstrap-project.sh` to create a new project:

1. The `docs-eng-process/` directory is copied to the new project
2. The `scripts/setup-agent-teams.sh` script is run automatically
3. This copies template files to the project's `.claude/` directory:

```
.claude/
├── teammates/
│   ├── analyst.md
│   ├── architect.md
│   ├── developer.md
│   ├── project-manager.md
│   └── tester.md
├── teams/
│   └── openup-full-team.md
├── CLAUDE.openup.md
└── CLAUDE.md
```

### In an Existing Project

For an existing project that already has `docs-eng-process/`:

1. Run `scripts/setup-agent-teams.sh`
2. The script copies templates to `.claude/`
3. Teammate instructions are loaded when teammates are spawned

## Template Architecture

```
docs-eng-process/
├── .claude-templates/          # Templates for host projects
│   ├── teammates/              # Role-specific instructions
│   │   ├── analyst.md
│   │   ├── architect.md
│   │   ├── developer.md
│   │   ├── project-manager.md
│   │   └── tester.md
│   ├── teams/                  # Team configuration files
│   │   └── openup-full-team.md
│   └── CLAUDE.md               # OpenUP instructions template
├── openup-knowledge-base/       # OpenUP role definitions
│   └── core/role/roles/
│       ├── analyst-6.md        # Source for analyst role
│       ├── architect-6.md      # Source for architect role
│       ├── developer-11.md     # Source for developer role
│       ├── project-manager-4.md # Source for PM role
│       └── tester-5.md         # Source for tester role
├── agent-teams-setup.md        # Setup guide for users
├── agent-workflow.md           # Agent operating procedures
└── init-prompts.md             # Project initialization prompts
```

## Template Content Sources

The teammate instruction files are derived from the OpenUP knowledge base:

| Template File | Source Document |
|---------------|-----------------|
| `analyst.md` | `openup-knowledge-base/core/role/roles/analyst-6.md` |
| `architect.md` | `openup-knowledge-base/core/role/roles/architect-6.md` |
| `developer.md` | `openup-knowledge-base/core/role/roles/developer-11.md` |
| `project-manager.md` | `openup-knowledge-base/core/role/roles/project-manager-4.md` |
| `tester.md` | `openup-knowledge-base/core/role/roles/tester-5.md` |

## Customization

You can customize the templates for your specific project needs:

### Modifying Role Instructions

Edit files in `docs-eng-process/.claude-templates/teammates/` to change role behavior for all future projects.

### Adding Custom Roles

Create new role files in `docs-eng-process/.claude-templates/teammates/` following the same structure.

### Custom Team Configurations

Add new team configurations in `docs-eng-process/.claude-templates/teams/` for specific workflows.

## Setup Script

The `scripts/setup-agent-teams.sh` script handles:

1. Checking for template existence
2. Creating `.claude/` directory structure
3. Copying teammate instructions
4. Copying team configurations
5. Copying CLAUDE.openup.md
6. Ensuring `.claude/CLAUDE.md` references the OpenUP instructions
7. Handling existing files (with `--force` option)
8. Providing dry-run mode (`--dry-run`)

## Example Usage

### Creating a Full Team

```
Create an OpenUP agent team with all roles: analyst, architect, developer, project-manager, and tester.
```

### Creating a Feature Team

```
Create an OpenUP agent team to implement the user profile feature.
Spawn analyst for requirements, architect for design, developer for implementation, and tester for validation.
```

### Creating an Investigation Team

```
Create an OpenUP agent team to investigate the login bug.
Spawn developer to analyze, architect to assess implications, and tester to verify the fix.
```

## Related Documentation

- **[agent-teams-setup.md](agent-teams-setup.md)** - Complete setup and usage guide
- **[agent-workflow.md](agent-workflow.md)** - Agent operating procedures
- **[how-to-work.md](how-to-work.md)** - OpenUP process overview
- **[conventions.md](conventions.md)** - Commit conventions and branching rules

## Future Enhancements

Potential improvements to the agent team templates:

1. **Additional Roles**
   - Product Owner (distinct from Analyst)
   - DevOps / Deployment specialist
   - Security specialist
   - UI/UX designer

2. **Specialized Teams**
   - Security review team
   - Performance optimization team
   - Documentation team
   - Migration team

3. **Phase-Specific Teams**
   - Inception kickoff team
   - Elaboration architecture team
   - Construction sprint team
   - Transition deployment team

4. **Skill-Based Roles**
   - Frontend specialist
   - Backend specialist
   - Database specialist
   - API integration specialist

## Contributing

To add new role templates or team configurations:

1. Create the template file in `docs-eng-process/.claude-templates/`
2. Follow the existing structure and format
3. Reference the appropriate OpenUP knowledge base documents
4. Update this summary document
5. Update `agent-teams-setup.md` with examples

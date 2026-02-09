# OpenUP Framework Scripts

This directory contains utility scripts for working with the OpenUP framework.

## Available Scripts

### bootstrap-project.sh

Bootstrap a new project from the OpenUP template.

**Usage:**
```bash
./bootstrap-project.sh <project-name> [--base-dir <directory>]
```

**What it does:**
- Creates a new project directory
- Copies `docs-eng-process/` with all OpenUP documentation
- Copies entrypoint files (README.md, AGENTS.md, .gitignore, .gitattributes)
- Sets up agent team templates automatically
- Initializes git repository
- Creates initial commit

**Example:**
```bash
./bootstrap-project.sh my-awesome-project --base-dir ~/projects
```

### setup-agent-teams.sh

Set up Claude Code agent teams in an existing project.

**Usage:**
```bash
./setup-agent-teams.sh [OPTIONS]
```

**Options:**
- `--force` - Overwrite existing .claude files
- `--dry-run` - Show what would be done without making changes

**What it does:**
- Copies teammate instructions to `.claude/teammates/`
- Copies team configurations to `.claude/teams/`
- Copies CLAUDE.md with team usage instructions

**Example:**
```bash
# First time setup
./setup-agent-teams.sh

# Force overwrite existing files
./setup-agent-teams.sh --force

# Preview changes
./setup-agent-teams.sh --dry-run
```

### update-from-template.sh

Update an existing project with the latest template changes.

**Usage:**
```bash
./update-from-template.sh [OPTIONS] [project_path]
```

**Options:**
- `--dry-run` - Show what would change without modifying files
- `--backup` - Create backups before overwriting files
- `--what-new` - Show what's new in the template without updating
- `--force` - Update even if versions match
- `--template-dir DIR` - Use local template directory instead of downloading
- `--skip-cleanup` - Keep downloaded template directory

**What it does:**
- Downloads latest template from GitHub (or uses local directory)
- Compares template with project files
- Updates `docs-eng-process/` with latest changes
- Updates `.claude/` teammates and teams

**Example:**
```bash
# Check what's new
./update-from-template.sh --what-new

# Dry run to preview changes
./update-from-template.sh --dry-run

# Update current project with backup
./update-from-template.sh --backup

# Update specific project
./update-from-template.sh /path/to/project

# Use local template directory
./update-from-template.sh --template-dir ~/dev/open-up-for-ai-agents
```

### update-openup.sh

Convenience wrapper script for running updates. This script is meant to be copied to your project and customized with the path to your local framework clone.

**Usage:**
```bash
# After copying to your project and customizing
./scripts/update-openup.sh [OPTIONS]
```

**Setup:**
```bash
# Copy to your project
cp /path/to/open-up-for-ai-agents/scripts/update-from-template.sh ./scripts/

# Create convenience wrapper
cat > scripts/update-openup.sh << 'EOF'
#!/bin/bash
TEMPLATE_DIR="/path/to/open-up-for-ai-agents"
bash scripts/update-from-template.sh --template-dir "$TEMPLATE_DIR" "$@"
EOF
chmod +x scripts/update-openup.sh
```

**Note**: For a one-liner approach, the repository needs to be public. Since this is a private repo, use one of the approaches above.

## Quick Reference

| Task | Script |
|------|--------|
| Create new project | `bootstrap-project.sh <name>` |
| Set up agent teams | `setup-agent-teams.sh` |
| Update from template | `update-from-template.sh --template-dir <path>` |
| Update (with submodule) | `update-from-template.sh --template-dir .openup-template` |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENUP_TEMPLATE_URL` | Git URL for template updates | `https://github.com/GermanDZ/open-up-for-ai-agents.git` |
| `OPENUP_TEMPLATE_BRANCH` | Branch to use for updates | `main` |

## Related Documentation

- **[Updating](../docs-eng-process/updating.md)** - Detailed update guide
- **[Agent Teams Setup](../docs-eng-process/agent-teams-setup.md)** - Setting up agent teams
- **[Getting Started](../docs-eng-process/getting-started.md)** - Project initialization guide

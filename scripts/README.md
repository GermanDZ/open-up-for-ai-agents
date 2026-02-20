# OpenUP Framework Scripts

This directory contains utility scripts for working with the OpenUP framework.

**Canonical update guidance lives in** `docs-eng-process/updating.md`. Use that guide to choose the right update path and keep this file for script-level details.

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

### sync-from-framework.sh

**NEW**: Sync OpenUP skills, teammates, and teams from framework repository to your project.

**Usage:**
```bash
./sync-from-framework.sh [OPTIONS]
```

**Options:**
- `--dry-run` - Show what would be synced without making changes
- `--verbose` - Show detailed output
- `--framework-path PATH` - Path to framework repository (auto-detects if not provided)

**What it syncs:**
- ✅ Skills: `.claude/skills/` ← `framework/docs-eng-process/.claude-templates/skills/`
- ✅ Teammates: `.claude/teammates/` ← `framework/docs-eng-process/.claude-templates/teammates/`
- ✅ Teams: `.claude/teams/` ← `framework/docs-eng-process/.claude-templates/teams/`
- ⚠️ Skips: `.claude/CLAUDE.md` (preserves your customizations)

**Example:**
```bash
# Auto-detect framework location
./sync-from-framework.sh

# Specify framework path
./sync-from-framework.sh --framework-path ~/projects/open-up-for-ai-agents

# Dry run first to preview
./sync-from-framework.sh --dry-run --verbose
```

**When to use:**
- ✅ To pull latest skills after framework updates
- ✅ To sync new teammates or teams
- ✅ When you get "Unknown skill" errors

**Important:** This script is meant to be **copied to your project**, not run from the framework repository.

### sync-templates-to-claude.sh

**For framework developers only**: Updates the framework's own `.claude/` directory from templates.

**Usage:**
```bash
# Only run this from within the framework repository
./scripts/sync-templates-to-claude.sh [--dry-run] [--verbose]
```

**What it does:**
- Syncs `docs-eng-process/.claude-templates/` → `.claude/` within the framework repo
- Updates skills, teammates, and teams
- Used when developing the framework itself

**When to use:**
- ⚠️ Only if you're maintaining the framework repository
- After modifying files in `docs-eng-process/.claude-templates/`
- ❌ NOT for projects using the framework (use `sync-from-framework.sh` instead)

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

| Task | Script | Context |
|------|--------|---------|
| **Create new project** | `bootstrap-project.sh <name>` | From framework repo |
| **Set up agent teams** | `setup-agent-teams.sh` | From framework repo or in project |
| **Update project (full)** | `update-from-template.sh --template-dir <path>` | In your project |
| **Sync .claude files only** | `sync-from-framework.sh --framework-path <path>` | In your project |
| **Update framework's .claude** | `sync-templates-to-claude.sh` | In framework repo only |

## Common Workflows

### Initial Project Setup

```bash
# Option A: Bootstrap new project
cd /path/to/open-up-for-ai-agents
./scripts/bootstrap-project.sh my-project --base-dir ~/projects

# Option B: Add to existing project
cd ~/projects/existing-project
/path/to/open-up-for-ai-agents/scripts/setup-agent-teams.sh
```

### Updating an Existing Project

Before updating, check `docs-eng-process/updating.md` for the decision tree. If you only need skills/teams/teammates, use `sync-from-framework.sh`. Use `update-from-template.sh` when you want full documentation updates.

**Common: Use sync-from-framework.sh**

This is the fastest way to get latest skills, teammates, and teams:

```bash
# 1. Copy script to your project (first time only)
cp /path/to/open-up-for-ai-agents/scripts/sync-from-framework.sh ./scripts/
chmod +x ./scripts/sync-from-framework.sh

# 2. Pull latest framework updates
cd /path/to/open-up-for-ai-agents
git pull

# 3. Sync to your project
cd ~/projects/my-project
./scripts/sync-from-framework.sh
```

**Alternative: Use update-from-template.sh**

This updates documentation and other files in addition to `.claude/`:

```bash
cd ~/projects/my-project
/path/to/open-up-for-ai-agents/scripts/update-from-template.sh \
  --template-dir /path/to/open-up-for-ai-agents \
  --backup
```

### Troubleshooting: ".claude files not updating"

**Problem:** Running `update-from-template.sh --force` doesn't update `.claude/skills/`

**Root cause:** The `update-from-template.sh` script copies from your project's `docs-eng-process/.claude-templates/`, which doesn't exist in projects using the framework. That directory only exists in the framework repository.

**Solution:** Use `sync-from-framework.sh` instead:

```bash
# This copies from the framework's .claude-templates to your project's .claude
./scripts/sync-from-framework.sh --framework-path /path/to/open-up-for-ai-agents
```

**What each script does:**

| Script | Source | Destination | Use Case |
|--------|--------|-------------|----------|
| `update-from-template.sh` | Framework root | Project root | Update docs, templates, full sync |
| `sync-from-framework.sh` | Framework `.claude-templates/` | Project `.claude/` | **Update skills/teammates/teams** |
| `sync-templates-to-claude.sh` | Framework `.claude-templates/` | Framework `.claude/` | Framework development only |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENUP_TEMPLATE_URL` | Git URL for template updates | `https://github.com/GermanDZ/open-up-for-ai-agents.git` |
| `OPENUP_TEMPLATE_BRANCH` | Branch to use for updates | `main` |

## Related Documentation

- **[Updating](../docs-eng-process/updating.md)** - Detailed update guide
- **[Agent Teams Setup](../docs-eng-process/agent-teams-setup.md)** - Setting up agent teams
- **[Getting Started](../docs-eng-process/getting-started.md)** - Project initialization guide

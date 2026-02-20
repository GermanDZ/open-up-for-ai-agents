# OpenUP Update Hub

This page is the canonical guide for updating projects that use the OpenUP framework. Use it to choose the right update path and the smallest command that matches your goal.

## Quick Decision Guide

Use the table below to pick the correct update path.

| Goal | Recommended Script | What It Updates |
|------|--------------------|-----------------|
| Update OpenUP docs and templates | `update-from-template.sh` | `docs-eng-process/` + `.claude/teammates` + `.claude/teams` + `.claude/CLAUDE.md` |
| Update skills/teammates/teams only | `sync-from-framework.sh` | `.claude/skills` + `.claude/teammates` + `.claude/teams` |

**Important:** `update-from-template.sh` does **not** update `.claude/skills/` in most projects because `docs-eng-process/.claude-templates/` exists only in the framework repo. If you see "Unknown skill" errors, run `sync-from-framework.sh`.

## Recommended Default

If you only need the latest skills, teammates, and teams, use `sync-from-framework.sh`. Use `update-from-template.sh` when you specifically want to update `docs-eng-process/` content.

## Quick Sync: Skills, Teammates, Teams Only

Use this when you want the latest OpenUP skills without changing documentation files.

```bash
# 1. Copy script to your project (first time only)
cp /path/to/open-up-for-ai-agents/scripts/sync-from-framework.sh ./scripts/
chmod +x ./scripts/sync-from-framework.sh

# 2. Pull latest framework updates
cd /path/to/open-up-for-ai-agents
git pull

# 3. Sync to your project
cd /path/to/your-project
./scripts/sync-from-framework.sh
```

For options and troubleshooting, see `scripts/README.md` in the framework repo.

## Update Methods

### Method 1: Using the Framework Copy (Recommended for Private Repos)

Since the template repository is private, copy the update script to your project and use it:

```bash
# From your project directory
# Copy the update script from your local framework clone
cp /path/to/open-up-for-ai-agents/scripts/update-from-template.sh ./scripts/

# Run it
./scripts/update-from-template.sh --template-dir /path/to/open-up-for-ai-agents
```

**Or add this as a git submodule** (recommended):

```bash
# In your project, add the framework as a submodule
git submodule add https://github.com/GermanDZ/open-up-for-ai-agents.git .openup-template

# Then update using the submodule
./scripts/update-from-template.sh --template-dir .openup-template
```

**Or use a symlink** (for local development):

```bash
# In your project, create a symlink to the framework
ln -s /path/to/open-up-for-ai-agents .openup-template

# Update using the symlink
./scripts/update-from-template.sh --template-dir .openup-template
```

### Method 2: Manual Clone and Update

Clone the template to a temporary location and update:

```bash
# From your project directory
TEMPLATE_DIR=$(mktemp -d)
git clone https://github.com/GermanDZ/open-up-for-ai-agents.git $TEMPLATE_DIR

# Or with SSH (if you have access)
git clone git@github.com:GermanDZ/open-up-for-ai-agents.git $TEMPLATE_DIR

# Run update
/path/to/open-up-for-ai-agents/scripts/update-from-template.sh --template-dir $TEMPLATE_DIR

# Cleanup
rm -rf $TEMPLATE_DIR
```

### Method 3: Using the Local Update Script (If you have the framework locally)

If you have a local copy of the template:

```bash
# From your project directory
/path/to/open-up-for-ai-agents/scripts/update-from-template.sh
```

### Method 4: Manual Copy

For manual control, you can copy files directly:

```bash
# Clone or pull the latest template
git clone --depth 1 https://github.com/GermanDZ/open-up-for-ai-agents.git /tmp/openup-template

# Copy docs-eng-process
rsync -av --delete /tmp/openup-template/docs-eng-process/ /path/to/your-project/docs-eng-process/

# Copy .claude templates
rsync -av /tmp/openup-template/docs-eng-process/.claude-templates/ /path/to/your-project/.claude/
```

## Script Options

The `update-from-template.sh` script supports several options:

```bash
update-from-template.sh [OPTIONS] [project_path]
```

| Option | Description |
|--------|-------------|
| `--dry-run` | Show what would change without modifying files |
| `--backup` | Create backups before overwriting files |
| `--what-new` | Show what's new without updating |
| `--force` | Update even if versions match |
| `--template-dir DIR` | Use local template directory instead of downloading |
| `--skip-cleanup` | Keep downloaded template directory |
| `-h, --help` | Show help message |

## Examples

### Check What's New

See what changes would be made without actually updating:

```bash
./scripts/update-from-template.sh --what-new
```

### Dry Run

Preview the changes:

```bash
./scripts/update-from-template.sh --dry-run
```

### Update with Backups

Update and create backups of modified files:

```bash
./scripts/update-from-template.sh --backup
```

### Update a Specific Project

Update a project at a specific path:

```bash
./scripts/update-from-template.sh /path/to/your-project
```

### Use Local Template

Update using a local clone of the template:

```bash
./scripts/update-from-template.sh --template-dir ~/dev/open-up-for-ai-agents
```

## What Gets Updated

The update process updates:

1. **docs-eng-process/** - All framework documentation and templates
2. **.claude/teammates/** - Agent teammate instructions
3. **.claude/teams/** - Team configuration files
4. **.claude/CLAUDE.md** - Agent team usage instructions

## What Does NOT Get Updated

The update process preserves:

- **docs/** - Your project documentation (vision, roadmap, etc.)
- **src/** - Your source code
- **tests/** - Your tests
- **.git/** - Git history
- Any other files not in `docs-eng-process/` or `.claude/`

## Version Tracking

The template uses a version file (`docs-eng-process/.template-version`) to track updates. When you update:

1. The script compares template version with your project version
2. If versions match and `--force` is not used, no update occurs
3. After update, your project's version is updated to match the template

## Handling Conflicts

If you've modified files in `docs-eng-process/`, the update will overwrite them. To preserve your changes:

### Option 1: Use --backup

```bash
./scripts/update-from-template.sh --backup
```

Then restore any files you want to keep from the backups.

### Option 2: Use Git

If your project uses Git, you can see and manage conflicts:

```bash
# Before updating
git status

# After updating
git diff docs-eng-process/

# Accept/reject changes as needed
git checkout -- docs-eng-process/some-file.md  # Keep your version
git add docs-eng-process/other-file.md          # Accept new version
```

### Option 3: Manual Merge

For more control, manually merge the changes:

```bash
# Download template to temp directory
git clone --depth 1 https://github.com/GermanDZ/open-up-for-ai-agents.git /tmp/openup

# Use diff/merge tools
meld docs-eng-process /tmp/openup/docs-eng-process
```

## Update Workflow

Recommended update workflow for full template updates:

1. **Check what's new**
   ```bash
   ./scripts/update-from-template.sh --what-new
   ```

2. **Ensure clean git state**
   ```bash
   git status  # Should be clean or with only your project changes
   ```

3. **Run dry run**
   ```bash
   ./scripts/update-from-template.sh --dry-run
   ```

4. **Update with backup**
   ```bash
   ./scripts/update-from-template.sh --backup
   ```

5. **Review changes**
   ```bash
   git diff docs-eng-process/
   ```

6. **Commit the update**
   ```bash
   git add docs-eng-process/ .claude/
   git commit -m "Update OpenUP framework to v1.5.0"
   ```

7. **Test**
   - Verify agent workflow still works
   - Check documentation builds correctly
   - Run any tests

## Alternative: One-Liner for Public Repositories

**Note**: If you make the template repository public, you can use a one-liner:

```bash
curl -s https://raw.githubusercontent.com/GermanDZ/open-up-for-ai-agents/main/scripts/update-openup.sh | bash
```

This requires:
1. The repository to be public
2. The `update-openup.sh` script to be in the main branch

## Recommended Setup for Private Repos

### Option 1: Git Submodule (Recommended)

Add the framework as a git submodule in your project:

```bash
# In your project directory
git submodule add https://github.com/GermanDZ/open-up-for-ai-agents.git .openup-template
git commit -m "Add OpenUP template as submodule"
```

Then create a convenience script `scripts/update-openup.sh`:

```bash
#!/bin/bash
TEMPLATE_DIR="$(git rev-parse --show-toplevel)/.openup-template"
bash "$TEMPLATE_DIR/scripts/update-from-template.sh" --template-dir "$TEMPLATE_DIR" "$@"
```

Now you can simply run:
```bash
./scripts/update-openup.sh
```

To update the submodule itself:
```bash
git submodule update --remote .openup-template
```

### Option 2: Symlink (For Local Development)

Create a symlink to your local framework clone:

```bash
# In your project directory
ln -s /path/to/open-up-for-ai-agents .openup-template

# Create update script
cat > scripts/update-openup.sh << 'EOF'
#!/bin/bash
bash .openup-template/scripts/update-from-template.sh --template-dir .openup-template "$@"
EOF
chmod +x scripts/update-openup.sh
```

### Option 3: Copy Script to Each Project

Copy the update script to each project:

```bash
# In your project directory
mkdir -p scripts
cp /path/to/open-up-for-ai-agents/scripts/update-from-template.sh scripts/

# Create convenience wrapper
cat > scripts/update-openup.sh << 'EOF'
#!/bin/bash
TEMPLATE_DIR="/path/to/open-up-for-ai-agents"
bash scripts/update-from-template.sh --template-dir "$TEMPLATE_DIR" "$@"
EOF
chmod +x scripts/update-openup.sh
```

## Automating Updates

For automated updates, you can:

1. **Schedule with cron** (Linux/Mac):
   ```bash
   # Run weekly update check
   0 0 * * 0 cd /path/to/project && curl -s https://raw.githubusercontent.com/GermanDZ/open-up-for-ai-agents/main/scripts/update-openup.sh | bash -s -- --what-new
   ```

2. **GitHub Actions**:
   ```yaml
   name: Check for OpenUP Updates
   on:
     schedule:
       - cron: '0 0 * * 0'
   jobs:
     check-updates:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Check updates
           run: |
             curl -s https://raw.githubusercontent.com/GermanDZ/open-up-for-ai-agents/main/scripts/update-openup.sh | bash -s -- --what-new
   ```

3. **Pre-commit hook**:
   ```bash
   # .git/hooks/pre-commit
   ./scripts/update-from-template.sh --what-new
   ```

## Troubleshooting

### "Template version matches project version"

This means you're already on the latest version. Use `--force` to update anyway:

```bash
./scripts/update-from-template.sh --force
```

### "docs-eng-process directory not found"

You must run the script from your project's root directory (where `docs-eng-process/` is located).

### "Failed to download template"

Check your internet connection and the repository URL. You can also download manually and use `--template-dir`:

```bash
git clone https://github.com/GermanDZ/open-up-for-ai-agents.git /tmp/openup
./scripts/update-from-template.sh --template-dir /tmp/openup
```

### "Permission denied when running script"

Make the script executable:

```bash
chmod +x scripts/update-from-template.sh
```

## Related Documentation

- **[Bootstrap](getting-started.md)** - Creating new projects
- **[Agent Teams Setup](agent-teams-setup.md)** - Setting up agent teams
- **[Agent Workflow](agent-workflow.md)** - Operating procedures

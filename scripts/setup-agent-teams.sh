#!/bin/bash
# setup-agent-teams.sh - Set up Claude Code agent teams in the host project

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect project root
# First, try to use the script location to find templates (for when called from another project)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# But use current working directory as the target project root
PROJECT_ROOT="$(pwd)"

# Function to print error and exit
error_exit() {
    echo -e "${RED}Error: $1${NC}" >&2
    exit 1
}

# Function to print warning
warn() {
    echo -e "${YELLOW}Warning: $1${NC}" >&2
}

# Function to print success
success() {
    echo -e "${GREEN}$1${NC}"
}

# Function to print info
info() {
    echo -e "${BLUE}$1${NC}"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Set up Claude Code agent teams for the current project.

This script copies agent team templates (teammate instructions, team configs,
skills, and CLAUDE.openup.md) to the project's .claude directory and ensures
the project's CLAUDE.md includes a reference.

Options:
  -h, --help           Show this help message
  --force              Overwrite existing .claude files
  --dry-run            Show what would be done without making changes

Examples:
  $0
  $0 --force
  $0 --dry-run

EOF
}

# Parse command-line arguments
FORCE=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            error_exit "Unknown option: $1. Use --help for usage information."
            ;;
    esac
done

# Template locations
TEMPLATES_DIR="$TEMPLATE_ROOT/docs-eng-process/.claude-templates"
CLAUDE_DIR="$PROJECT_ROOT/.claude"

# Check if templates directory exists
if [ ! -d "$TEMPLATES_DIR" ]; then
    error_exit "Templates directory not found: $TEMPLATES_DIR"
fi

# Check if CLAUDE.md template exists
CLAUDE_TEMPLATE="$TEMPLATES_DIR/CLAUDE.md"
if [ ! -f "$CLAUDE_TEMPLATE" ]; then
    error_exit "CLAUDE.md template not found: $CLAUDE_TEMPLATE"
fi

# Files to copy
TEAMMATES_DIR="$CLAUDE_DIR/teammates"
TEAMS_DIR="$CLAUDE_DIR/teams"
SKILLS_DIR="$CLAUDE_DIR/skills"
CLAUDE_OPENUP_DEST="$CLAUDE_DIR/CLAUDE.openup.md"
CLAUDE_DEST="$CLAUDE_DIR/CLAUDE.md"
OPENUP_REF_PATH=".claude/CLAUDE.openup.md"
OPENUP_REF_TEXT="This project follows OpenUP. See $OPENUP_REF_PATH for the shared OpenUP instructions."

# Function to copy file with backup
copy_file() {
    local src="$1"
    local dest="$2"

    if [ "$DRY_RUN" = true ]; then
        echo "Would copy: $src -> $dest"
        if [ -f "$dest" ]; then
            echo "  (would backup existing: ${dest}.bak)"
        fi
        return 0
    fi

    if [ -f "$dest" ] && [ "$FORCE" = false ]; then
        warn "File exists, skipping: $dest (use --force to overwrite)"
        return 0
    fi

    # Backup existing file
    if [ -f "$dest" ]; then
        cp "$dest" "${dest}.bak"
        info "Backed up: $dest -> ${dest}.bak"
    fi

    # Create destination directory if needed
    mkdir -p "$(dirname "$dest")"

    # Copy file
    cp "$src" "$dest"
    success "Created: $dest"
}

# Function to copy directory
copy_dir() {
    local src="$1"
    local dest="$2"

    if [ "$DRY_RUN" = true ]; then
        echo "Would copy directory: $src -> $dest"
        return 0
    fi

    # Create destination directory
    mkdir -p "$dest"

    # Copy all files
    for file in "$src"/*; do
        if [ -f "$file" ]; then
            local filename="$(basename "$file")"
            copy_file "$file" "$dest/$filename"
        fi
    done
}

# Function to copy skills directory (each skill is a subdirectory with SKILL.md)
copy_skills_dir() {
    local src="$1"
    local dest="$2"

    if [ "$DRY_RUN" = true ]; then
        echo "Would copy skills directory: $src -> $dest"
        return 0
    fi

    # Create destination directory
    mkdir -p "$dest"

    # Copy each skill subdirectory
    for skill_dir in "$src"/*/; do
        if [ -d "$skill_dir" ]; then
            local skill_name="$(basename "$skill_dir")"
            local dest_skill_dir="$dest/$skill_name"
            mkdir -p "$dest_skill_dir"
            for file in "$skill_dir"*; do
                if [ -f "$file" ]; then
                    local filename="$(basename "$file")"
                    copy_file "$file" "$dest_skill_dir/$filename"
                fi
            done
        fi
    done
}

ensure_openup_reference() {
    local target_file="$1"

    if [ ! -f "$target_file" ]; then
        return 0
    fi

    if ! grep -Fq "$OPENUP_REF_TEXT" "$target_file"; then
        if [ "$DRY_RUN" = true ]; then
            echo "Would add OpenUP reference to: $target_file"
            return 0
        fi
        echo "" >> "$target_file"
        echo "$OPENUP_REF_TEXT" >> "$target_file"
        success "Updated: $target_file"
    fi
}

create_claude_stub() {
    local target_file="$1"

    if [ "$DRY_RUN" = true ]; then
        echo "Would add: $target_file"
        return 0
    fi

    mkdir -p "$(dirname "$target_file")"
    cat > "$target_file" << EOF
# Project Instructions

Add project-specific instructions here.

$OPENUP_REF_TEXT
EOF
    success "Created: $target_file"
}

# Main execution
echo ""
info "Setting up Claude Code agent teams..."
echo ""

if [ "$DRY_RUN" = false ]; then
    # Create .claude directory structure
    mkdir -p "$TEAMMATES_DIR"
    mkdir -p "$TEAMS_DIR"
    mkdir -p "$SKILLS_DIR"
fi

# Copy teammate instructions
if [ -d "$TEMPLATES_DIR/teammates" ]; then
    info "Setting up teammate instructions..."
    copy_dir "$TEMPLATES_DIR/teammates" "$TEAMMATES_DIR"
else
    warn "Teammates template directory not found: $TEMPLATES_DIR/teammates"
fi

# Copy team configurations
if [ -d "$TEMPLATES_DIR/teams" ]; then
    info "Setting up team configurations..."
    copy_dir "$TEMPLATES_DIR/teams" "$TEAMS_DIR"
else
    warn "Teams template directory not found: $TEMPLATES_DIR/teams"
fi

# Copy skills
if [ -d "$TEMPLATES_DIR/skills" ]; then
    info "Setting up skills..."
    copy_skills_dir "$TEMPLATES_DIR/skills" "$SKILLS_DIR"
else
    warn "Skills template directory not found: $TEMPLATES_DIR/skills"
fi

# Copy settings.json (only if it doesn't already exist, to preserve user customizations)
SETTINGS_SRC="$TEMPLATES_DIR/settings.json.example"
SETTINGS_DEST="$CLAUDE_DIR/settings.json"
if [ -f "$SETTINGS_SRC" ]; then
    if [ ! -f "$SETTINGS_DEST" ]; then
        info "Setting up settings.json..."
        copy_file "$SETTINGS_SRC" "$SETTINGS_DEST"
    else
        info "settings.json already exists, skipping (preserving user customizations)"
    fi
fi

# Copy OpenUP instructions
info "Setting up CLAUDE.openup.md..."
copy_file "$CLAUDE_TEMPLATE" "$CLAUDE_OPENUP_DEST"

# Ensure project CLAUDE.md exists and references OpenUP instructions
if [ -f "$CLAUDE_DEST" ]; then
    ensure_openup_reference "$CLAUDE_DEST"
else
    create_claude_stub "$CLAUDE_DEST"
fi

# Summary
echo ""
success "Agent team setup complete!"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo "Dry run completed. No files were modified."
    echo "Run without --dry-run to apply changes."
else
    echo "Created files:"
    echo "  - .claude/skills/ (workflow skills - /openup-* commands)"
    echo "  - .claude/teammates/ (role instructions)"
    echo "  - .claude/teams/ (team configurations)"
    echo "  - .claude/settings.json (agent teams enabled)"
    echo "  - .claude/CLAUDE.openup.md (OpenUP instructions)"
    echo "  - .claude/CLAUDE.md (project instructions)"
    echo ""
    echo "Next steps:"
    echo "1. Start Claude Code in this project"
    echo "2. Run /openup-init to initialize your project"
    echo "3. Or create a team: 'Create an OpenUP agent team with [roles]'"
    echo ""
    echo "For more information, see .claude/CLAUDE.openup.md"
fi
echo ""

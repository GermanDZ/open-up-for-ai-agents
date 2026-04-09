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

RUBRICS_DIR="$CLAUDE_DIR/rubrics"
HOOKS_DIR="$CLAUDE_DIR/scripts/hooks"

if [ "$DRY_RUN" = false ]; then
    # Create .claude directory structure
    mkdir -p "$TEAMMATES_DIR"
    mkdir -p "$TEAMS_DIR"
    mkdir -p "$SKILLS_DIR"
    mkdir -p "$RUBRICS_DIR"
    mkdir -p "$HOOKS_DIR"
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

# Copy rubrics
if [ -d "$TEMPLATES_DIR/rubrics" ]; then
    info "Setting up quality rubrics..."
    copy_dir "$TEMPLATES_DIR/rubrics" "$RUBRICS_DIR"
else
    warn "Rubrics template directory not found: $TEMPLATES_DIR/rubrics"
fi

# Copy hook scripts
if [ -d "$TEMPLATES_DIR/scripts/hooks" ]; then
    info "Setting up hook scripts..."
    copy_dir "$TEMPLATES_DIR/scripts/hooks" "$HOOKS_DIR"
else
    warn "Hooks template directory not found: $TEMPLATES_DIR/scripts/hooks"
fi

# Merge OpenUP hooks into the project's settings.json.
# All non-hooks fields (defaultMode, permissions, env, etc.) are always preserved.
# With --force, OpenUP hooks (identified by /.claude/scripts/hooks/ in their command)
#   are replaced with the canonical set; any custom hooks you've added are kept.
# Without --force, the file is only written if it doesn't exist yet.
SETTINGS_SRC="$TEMPLATES_DIR/settings.json.example"
SETTINGS_DEST="$CLAUDE_DIR/settings.json"
if [ -f "$SETTINGS_SRC" ]; then
    if [ ! -f "$SETTINGS_DEST" ]; then
        info "Setting up settings.json..."
        copy_file "$SETTINGS_SRC" "$SETTINGS_DEST"
    elif [ "$FORCE" = true ]; then
        if [ "$DRY_RUN" = true ]; then
            echo "Would merge OpenUP hooks from: $SETTINGS_SRC -> $SETTINGS_DEST"
            echo "  (custom hooks preserved; only /.claude/scripts/hooks/ entries updated)"
        else
            cp "$SETTINGS_DEST" "${SETTINGS_DEST}.bak"
            info "Backed up: $SETTINGS_DEST -> ${SETTINGS_DEST}.bak"
            python3 - "$SETTINGS_SRC" "$SETTINGS_DEST" <<'PYEOF'
import json, sys

OPENUP_MARKER = "/.claude/scripts/hooks/"

def is_openup_hook(hook):
    return OPENUP_MARKER in hook.get("command", "")

def merge_hooks(existing, incoming):
    """Keep custom hooks, replace OpenUP hooks with incoming canonical set."""
    custom = [h for h in existing if not is_openup_hook(h)]
    openup = [h for h in incoming if is_openup_hook(h)]
    return openup + custom  # OpenUP hooks first, custom hooks after

def merge_event(existing_event, new_event):
    """Merge two lists of matcher objects for one hook event."""
    by_matcher = {item.get("matcher", ""): item for item in existing_event}
    result = []
    seen = set()
    for new_item in new_event:
        matcher = new_item.get("matcher", "")
        seen.add(matcher)
        if matcher in by_matcher:
            merged = dict(new_item)
            merged["hooks"] = merge_hooks(
                by_matcher[matcher].get("hooks", []),
                new_item.get("hooks", [])
            )
            result.append(merged)
        else:
            result.append(new_item)
    # Keep existing matchers not in the template
    for item in existing_event:
        if item.get("matcher", "") not in seen:
            result.append(item)
    return result

src_path, dest_path = sys.argv[1], sys.argv[2]
try:
    with open(src_path) as f:
        src = json.load(f)
    with open(dest_path) as f:
        dest = json.load(f)

    src_hooks = src.get("hooks", {})
    dest_hooks = dest.get("hooks", {})
    merged = {}

    for event in set(list(src_hooks) + list(dest_hooks)):
        if event in src_hooks and event in dest_hooks:
            merged[event] = merge_event(dest_hooks[event], src_hooks[event])
        elif event in src_hooks:
            merged[event] = src_hooks[event]
        else:
            merged[event] = dest_hooks[event]

    dest["hooks"] = merged
    with open(dest_path, "w") as f:
        json.dump(dest, f, indent=2)
        f.write("\n")
    print(f"Merged OpenUP hooks into {dest_path} (custom hooks preserved)")
except Exception as e:
    print(f"Warning: could not merge settings.json: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
            success "Updated: $SETTINGS_DEST"
        fi
    else
        info "settings.json already exists — OpenUP hooks not updated (use --force to update)"
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
    echo "  - .claude/rubrics/ (work product quality rubrics)"
    echo "  - .claude/scripts/hooks/ (automation hooks)"
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

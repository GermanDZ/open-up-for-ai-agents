#!/bin/bash
# update-from-template.sh - Update a project's docs-eng-process from the latest template

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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

# Function to print header
header() {
    echo ""
    echo -e "${CYAN}=== $1 ===${NC}"
    echo ""
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS] [project_path]

Update a project's docs-eng-process and .claude directories from the latest
OpenUP template from https://github.com/GermanDZ/open-up-for-ai-agents

Arguments:
  project_path          Path to the project to update (default: current directory)

Options:
  --template-dir DIR    Path to the template directory (default: auto-downloaded)
  --dry-run             Show what would be done without making changes
  --backup              Create backups before overwriting files
  --skip-cleanup        Keep downloaded template directory
  --force               Update even if versions match
  --what-new            Show what's new in the template without updating
  -h, --help           Show this help message

Environment Variables:
  OPENUP_TEMPLATE_URL   Git URL to clone template from
                        (default: https://github.com/GermanDZ/open-up-for-ai-agents.git)
  OPENUP_TEMPLATE_BRANCH Branch to checkout (default: main)

Examples:
  # Update current directory project
  $0

  # Update specific project
  $0 /path/to/project

  # Dry run to see what would change
  $0 --dry-run

  # Update with backups
  $0 --backup

  # Use local template directory
  $0 --template-dir /path/to/open-up-for-ai-agents

  # Show what's new without updating
  $0 --what-new

EOF
}

# Default values
PROJECT_PATH=""
TEMPLATE_DIR=""
DRY_RUN=false
BACKUP=false
SKIP_CLEANUP=false
FORCE=false
WHAT_NEW=false

# Environment variables with defaults
TEMPLATE_URL="${OPENUP_TEMPLATE_URL:-https://github.com/GermanDZ/open-up-for-ai-agents.git}"
TEMPLATE_BRANCH="${OPENUP_TEMPLATE_BRANCH:-main}"

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --template-dir)
            TEMPLATE_DIR="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --backup)
            BACKUP=true
            shift
            ;;
        --skip-cleanup)
            SKIP_CLEANUP=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --what-new)
            WHAT_NEW=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        -*)
            error_exit "Unknown option: $1. Use --help for usage information."
            ;;
        *)
            if [ -z "$PROJECT_PATH" ]; then
                PROJECT_PATH="$1"
            else
                error_exit "Multiple project paths provided. Use --help for usage information."
            fi
            shift
            ;;
    esac
done

# Default project path to current directory
if [ -z "$PROJECT_PATH" ]; then
    PROJECT_PATH="$(pwd)"
fi

# Normalize project path
PROJECT_PATH="$(cd "$PROJECT_PATH" 2>/dev/null && pwd)" || error_exit "Project path does not exist: $PROJECT_PATH"

# Validate project has docs-eng-process
if [ ! -d "$PROJECT_PATH/docs-eng-process" ]; then
    error_exit "Project does not have docs-eng-process directory: $PROJECT_PATH"
fi

# Get template directory
TEMP_TEMPLATE_DIR=""
if [ -z "$TEMPLATE_DIR" ]; then
    # Create temporary directory for template
    TEMP_TEMPLATE_DIR="$(mktemp -d)/open-up-for-ai-agents"
    TEMPLATE_DIR="$TEMP_TEMPLATE_DIR"

    # Clone the template
    header "Downloading latest template"
    info "Cloning from: $TEMPLATE_URL"
    info "Branch: $TEMPLATE_BRANCH"
    echo ""

    if [ "$DRY_RUN" = true ] || [ "$WHAT_NEW" = true ]; then
        info "Would clone: git clone --depth 1 --branch $TEMPLATE_BRANCH $TEMPLATE_URL $TEMPLATE_DIR"
    else
        if ! git clone --depth 1 --branch "$TEMPLATE_BRANCH" "$TEMPLATE_URL" "$TEMPLATE_DIR" 2>/dev/null; then
            error_exit "Failed to clone template from $TEMPLATE_URL"
        fi
        success "Template cloned to: $TEMPLATE_DIR"
    fi
else
    # Use provided template directory
    TEMPLATE_DIR="$(cd "$TEMPLATE_DIR" 2>/dev/null && pwd)" || error_exit "Template directory does not exist: $TEMPLATE_DIR"
fi

# Check template directory exists
if [ ! -d "$TEMPLATE_DIR/docs-eng-process" ]; then
    error_exit "Template directory does not have docs-eng-process: $TEMPLATE_DIR"
fi

# Function to get version from file
get_version() {
    local dir="$1"
    local version_file="$dir/docs-eng-process/.template-version"

    if [ -f "$version_file" ]; then
        cat "$version_file"
    else
        echo "unknown"
    fi
}

# Get versions
TEMPLATE_VERSION=$(get_version "$TEMPLATE_DIR")
PROJECT_VERSION=$(get_version "$PROJECT_PATH")

# Show what's new mode
if [ "$WHAT_NEW" = true ]; then
    header "What's New in Template"
    info "Template version: $TEMPLATE_VERSION"
    info "Project version: $PROJECT_VERSION"
    echo ""

    # Show new files
    info "New files in template (not in project):"
    echo ""
    find "$TEMPLATE_DIR/docs-eng-process" -type f | while read -r template_file; do
        rel_path="${template_file#$TEMPLATE_DIR/docs-eng-process/}"
        project_file="$PROJECT_PATH/docs-eng-process/$rel_path"

        if [ ! -e "$project_file" ]; then
            echo "  + $rel_path"
        fi
    done

    echo ""
    info "New files in .claude templates (not in project):"
    echo ""

    if [ -d "$TEMPLATE_DIR/docs-eng-process/.claude-templates" ]; then
        find "$TEMPLATE_DIR/docs-eng-process/.claude-templates" -type f | while read -r template_file; do
            rel_path="${template_file#$TEMPLATE_DIR/docs-eng-process/.claude-templates/}"
            project_file="$PROJECT_PATH/.claude/$rel_path"

            if [ ! -e "$project_file" ]; then
                echo "  + .claude/$rel_path"
            fi
        done
    fi

    echo ""
    info "Modified files (different from template):"
    echo ""
    find "$TEMPLATE_DIR/docs-eng-process" -type f | while read -r template_file; do
        rel_path="${template_file#$TEMPLATE_DIR/docs-eng-process/}"
        project_file="$PROJECT_PATH/docs-eng-process/$rel_path"

        if [ -f "$project_file" ]; then
            if ! cmp -s "$template_file" "$project_file"; then
                echo "  ~ $rel_path"
            fi
        fi
    done

    echo ""

    # Cleanup temp directory if we created it
    if [ -n "$TEMP_TEMPLATE_DIR" ] && [ -d "$TEMP_TEMPLATE_DIR" ] && [ "$SKIP_CLEANUP" = false ]; then
        rm -rf "$(dirname "$TEMP_TEMPLATE_DIR")"
    fi

    exit 0
fi

# Check versions
if [ "$TEMPLATE_VERSION" = "$PROJECT_VERSION" ] && [ "$FORCE" = false ]; then
    info "Template version ($TEMPLATE_VERSION) matches project version ($PROJECT_VERSION)"
    info "Use --force to update anyway"
    exit 0
fi

# Backup function
backup_file() {
    local file="$1"
    local backup_path="${file}.backup-$(date +%Y%m%d-%H%M%S)"

    if [ "$BACKUP" = true ]; then
        cp "$file" "$backup_path"
        info "Backed up: $file -> $backup_path"
    fi
}

# Counters
FILES_UPDATED=0
FILES_ADDED=0
FILES_SKIPPED=0
BACKUPS_CREATED=0

# Function to sync directory
sync_directory() {
    local src_dir="$1"
    local dest_dir="$2"
    local exclude_patterns="$3"

    info "Syncing: $src_dir -> $dest_dir"
    echo ""

    # Create destination directory if it doesn't exist
    if [ "$DRY_RUN" = false ]; then
        mkdir -p "$dest_dir"
    fi

    # Find all files in source
    find "$src_dir" -type f | grep -v "/.DS_Store$" | while read -r src_file; do
        # Get relative path
        rel_path="${src_file#$src_dir/}"
        dest_file="$dest_dir/$rel_path"

        # Check exclusions
        should_skip=false
        if [ -n "$exclude_patterns" ]; then
            echo "$exclude_patterns" | while read -r pattern; do
                if [[ "$rel_path" == $pattern ]]; then
                    should_skip=true
                    break
                fi
            done
        fi

        if [ "$should_skip" = true ]; then
            FILES_SKIPPED=$((FILES_SKIPPED + 1))
            return
        fi

        # Check if file exists in destination
        if [ -f "$dest_file" ]; then
            # Check if files are different
            if ! cmp -s "$src_file" "$dest_file"; then
                if [ "$DRY_RUN" = true ]; then
                    echo "  Would update: $rel_path"
                else
                    # Backup if requested
                    if [ "$BACKUP" = true ]; then
                        backup_file "$dest_file"
                        BACKUPS_CREATED=$((BACKUPS_CREATED + 1))
                    fi

                    # Copy file
                    cp "$src_file" "$dest_file"
                    echo "  Updated: $rel_path"
                    FILES_UPDATED=$((FILES_UPDATED + 1))
                fi
            fi
        else
            if [ "$DRY_RUN" = true ]; then
                echo "  Would add: $rel_path"
            else
                # Create directory structure
                mkdir -p "$(dirname "$dest_file")"
                # Copy file
                cp "$src_file" "$dest_file"
                echo "  Added: $rel_path"
                FILES_ADDED=$((FILES_ADDED + 1))
            fi
        fi
    done
}

# Main update process
header "Updating Project"
info "Project: $PROJECT_PATH"
info "Template version: $TEMPLATE_VERSION"
info "Project version: $PROJECT_VERSION"
echo ""

if [ "$DRY_RUN" = true ]; then
    warn "DRY RUN MODE - No files will be modified"
    echo ""
fi

# Update docs-eng-process
header "Updating docs-eng-process"
sync_directory \
    "$TEMPLATE_DIR/docs-eng-process" \
    "$PROJECT_PATH/docs-eng-process" \
    ""

# Update .claude directory (teammates and teams)
if [ -d "$TEMPLATE_DIR/docs-eng-process/.claude-templates" ]; then
    header "Updating .claude directory"
    sync_directory \
        "$TEMPLATE_DIR/docs-eng-process/.claude-templates/teammates" \
        "$PROJECT_PATH/.claude/teammates" \
        ""

    sync_directory \
        "$TEMPLATE_DIR/docs-eng-process/.claude-templates/teams" \
        "$PROJECT_PATH/.claude/teams" \
        ""

    openup_ref_path=".claude/CLAUDE.openup.md"
    openup_ref_text="This project follows OpenUP. See $openup_ref_path for the shared OpenUP instructions."

    ensure_openup_reference() {
        local target_file="$1"

        if [ ! -f "$target_file" ]; then
            return
        fi

        if ! grep -Fq "$openup_ref_text" "$target_file"; then
            if [ "$DRY_RUN" = true ]; then
                echo "  Would add OpenUP reference to: .claude/CLAUDE.md"
            else
                echo "" >> "$target_file"
                echo "$openup_ref_text" >> "$target_file"
            fi
        fi
    }

    create_claude_stub() {
        local target_file="$1"

        if [ "$DRY_RUN" = true ]; then
            echo "  Would add: .claude/CLAUDE.md"
            return
        fi

        mkdir -p "$PROJECT_PATH/.claude"
        cat > "$target_file" << EOF
# Project Instructions

Add project-specific instructions here.

$openup_ref_text
EOF
        echo "  Added: .claude/CLAUDE.md"
        FILES_ADDED=$((FILES_ADDED + 1))
    }

    # Sync OpenUP template into .claude/CLAUDE.openup.md
    if [ -f "$TEMPLATE_DIR/docs-eng-process/.claude-templates/CLAUDE.md" ]; then
        if [ "$DRY_RUN" = true ]; then
            echo "  Would update: .claude/CLAUDE.openup.md"
        else
            mkdir -p "$PROJECT_PATH/.claude"
            cp "$TEMPLATE_DIR/docs-eng-process/.claude-templates/CLAUDE.md" "$PROJECT_PATH/.claude/CLAUDE.openup.md"
            echo "  Updated: .claude/CLAUDE.openup.md"
            FILES_UPDATED=$((FILES_UPDATED + 1))
        fi
    fi

    # Keep project CLAUDE.md user-owned; only add reference or create stub
    if [ -f "$PROJECT_PATH/.claude/CLAUDE.md" ]; then
        ensure_openup_reference "$PROJECT_PATH/.claude/CLAUDE.md"
    else
        create_claude_stub "$PROJECT_PATH/.claude/CLAUDE.md"
    fi
fi

# Update version file
if [ "$DRY_RUN" = false ]; then
    echo "$TEMPLATE_VERSION" > "$PROJECT_PATH/docs-eng-process/.template-version"
    echo "  Updated: .template-version"
fi

# Summary
header "Summary"
if [ "$DRY_RUN" = true ]; then
    echo "Dry run completed. No files were modified."
    echo "Run without --dry-run to apply changes."
else
    success "Update completed!"
    echo ""
    echo "Files added:    $FILES_ADDED"
    echo "Files updated:  $FILES_UPDATED"
    echo "Files skipped:  $FILES_SKIPPED"
    if [ "$BACKUP" = true ]; then
        echo "Backups created: $BACKUPS_CREATED"
    fi
    echo ""
    echo "Template version: $TEMPLATE_VERSION"
    echo ""
    echo "Next steps:"
    echo "1. Review the changes with: git diff"
    echo "2. Test that everything works correctly"
    echo "3. Commit the updates"
    echo ""
    if [ "$BACKUP" = true ]; then
        echo "Backup files created with .backup-YYYYMMDD-HHMMSS suffix"
        echo "Remove them when you're sure everything works: find . -name '*.backup-*' -delete"
    fi
fi

# Cleanup temp directory if we created it
if [ -n "$TEMP_TEMPLATE_DIR" ] && [ -d "$TEMP_TEMPLATE_DIR" ] && [ "$SKIP_CLEANUP" = false ]; then
    rm -rf "$(dirname "$TEMP_TEMPLATE_DIR")"
fi

echo ""

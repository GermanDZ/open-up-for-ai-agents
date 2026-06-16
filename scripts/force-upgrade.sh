#!/bin/bash
# force-upgrade.sh - Fully force-upgrade a project to the latest OpenUP framework
#
# Use this for projects that were initially started with an OLD version of
# OpenUP. A plain update is not enough for those projects: depending on how old
# the install is, it can be missing whole categories of files that the modern
# framework expects (skills, hooks, rubrics, subagents, settings.json wiring,
# the process CLIs, the doc-traceability rails, ...).
#
# This script brings the project all the way up to the current framework by
# orchestrating the two canonical installers, both run in --force mode so the
# version check never short-circuits:
#
#   1. update-from-template.sh --force   -> docs-eng-process/, teammates, teams,
#                                           CLAUDE.openup.md, process CLIs,
#                                           .template-version
#   2. setup-agent-teams.sh --force      -> the full .claude/ superset: skills,
#                                           teammates, teams, agents, rubrics,
#                                           hooks, settings.json (hooks merged,
#                                           custom hooks preserved), process CLIs
#
# By default the latest framework is cloned from GitHub; pass --template-dir to
# use a local checkout instead.

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

error_exit() {
    echo -e "${RED}Error: $1${NC}" >&2
    exit 1
}

warn() {
    echo -e "${YELLOW}Warning: $1${NC}" >&2
}

success() {
    echo -e "${GREEN}$1${NC}"
}

info() {
    echo -e "${BLUE}$1${NC}"
}

header() {
    echo ""
    echo -e "${CYAN}=== $1 ===${NC}"
    echo ""
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS] [project_path]

Force-upgrade a project that was started with an old OpenUP version to the
latest framework. Installs docs-eng-process/ AND the full .claude/ superset
(skills, teammates, teams, agents, rubrics, hooks, settings.json, process
CLIs), regardless of the project's current template version.

Arguments:
  project_path          Path to the project to upgrade (default: current directory)

Options:
  --template-dir DIR    Path to a local framework checkout (default: auto-downloaded)
  --dry-run             Show what would be done without making changes
  --backup              Create .backup-* copies before overwriting docs-eng-process files
  --skip-cleanup        Keep the downloaded framework directory
  -h, --help            Show this help message

Environment Variables:
  OPENUP_TEMPLATE_URL    Git URL to clone the framework from
                         (default: https://github.com/GermanDZ/open-up-for-ai-agents.git)
  OPENUP_TEMPLATE_BRANCH Branch to checkout (default: main)

Examples:
  # Upgrade the project in the current directory from the latest framework
  $0

  # Upgrade a specific project
  $0 /path/to/project

  # Preview the upgrade without touching files
  $0 --dry-run

  # Upgrade using a local framework checkout
  $0 --template-dir ~/dev/open-up-for-ai-agents
EOF
}

# Defaults
PROJECT_PATH=""
TEMPLATE_DIR=""
DRY_RUN=false
BACKUP=false
SKIP_CLEANUP=false

TEMPLATE_URL="${OPENUP_TEMPLATE_URL:-https://github.com/GermanDZ/open-up-for-ai-agents.git}"
TEMPLATE_BRANCH="${OPENUP_TEMPLATE_BRANCH:-main}"

# Parse arguments
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

# Default and normalize project path
if [ -z "$PROJECT_PATH" ]; then
    PROJECT_PATH="$(pwd)"
fi
PROJECT_PATH="$(cd "$PROJECT_PATH" 2>/dev/null && pwd)" || error_exit "Project path does not exist: $PROJECT_PATH"

# This is an upgrade, not a first-time install: the project must already look
# like an OpenUP project. Old installs always have docs-eng-process/, which is
# also what update-from-template.sh requires.
if [ ! -d "$PROJECT_PATH/docs-eng-process" ]; then
    error_exit "$PROJECT_PATH does not have a docs-eng-process/ directory.
This looks like a first-time install, not an upgrade. See docs-eng-process/updating.md
('First-Time Install Into an Existing Project') in the framework."
fi

# Resolve the framework directory (clone the latest by default).
TEMP_TEMPLATE_DIR=""
if [ -z "$TEMPLATE_DIR" ]; then
    TEMP_TEMPLATE_DIR="$(mktemp -d)/open-up-for-ai-agents"
    TEMPLATE_DIR="$TEMP_TEMPLATE_DIR"

    header "Downloading latest framework"
    info "Cloning from: $TEMPLATE_URL"
    info "Branch: $TEMPLATE_BRANCH"
    echo ""

    if ! git clone --depth 1 --branch "$TEMPLATE_BRANCH" "$TEMPLATE_URL" "$TEMPLATE_DIR" 2>/dev/null; then
        error_exit "Failed to clone framework from $TEMPLATE_URL"
    fi
    success "Framework cloned to: $TEMPLATE_DIR"
else
    TEMPLATE_DIR="$(cd "$TEMPLATE_DIR" 2>/dev/null && pwd)" || error_exit "Template directory does not exist: $TEMPLATE_DIR"
fi

# Validate the framework checkout has what both installers need.
if [ ! -d "$TEMPLATE_DIR/docs-eng-process" ]; then
    error_exit "Framework directory has no docs-eng-process/: $TEMPLATE_DIR"
fi
if [ ! -f "$TEMPLATE_DIR/scripts/update-from-template.sh" ] || [ ! -f "$TEMPLATE_DIR/scripts/setup-agent-teams.sh" ]; then
    error_exit "Framework directory is missing the installer scripts: $TEMPLATE_DIR/scripts"
fi

# Cleanup the temp clone on exit (unless asked to keep it).
cleanup_template() {
    if [ -n "$TEMP_TEMPLATE_DIR" ] && [ -d "$TEMP_TEMPLATE_DIR" ] && [ "$SKIP_CLEANUP" = false ]; then
        rm -rf "$(dirname "$TEMP_TEMPLATE_DIR")"
    fi
}
trap cleanup_template EXIT

# Report the version delta (informational; the upgrade runs regardless).
get_version() {
    local version_file="$1/docs-eng-process/.template-version"
    if [ -f "$version_file" ]; then
        cat "$version_file"
    else
        echo "unknown"
    fi
}
TEMPLATE_VERSION="$(get_version "$TEMPLATE_DIR")"
PROJECT_VERSION="$(get_version "$PROJECT_PATH")"

header "Force-Upgrading Project"
info "Project:          $PROJECT_PATH"
info "Project version:  $PROJECT_VERSION"
info "Latest version:   $TEMPLATE_VERSION"
if [ "$DRY_RUN" = true ]; then
    echo ""
    warn "DRY RUN MODE - No files will be modified"
fi

# Step 1: docs-eng-process + version + teammates/teams + process CLIs (forced).
header "Step 1/2: docs-eng-process & process docs"
STEP1_ARGS=(--force --template-dir "$TEMPLATE_DIR")
[ "$DRY_RUN" = true ] && STEP1_ARGS+=(--dry-run)
[ "$BACKUP" = true ] && STEP1_ARGS+=(--backup)
# --skip-cleanup so update-from-template.sh never deletes our shared clone;
# this script owns the temp directory's lifecycle.
STEP1_ARGS+=(--skip-cleanup "$PROJECT_PATH")
bash "$TEMPLATE_DIR/scripts/update-from-template.sh" "${STEP1_ARGS[@]}" \
    || error_exit "docs-eng-process update failed"

# Step 2: the full .claude/ superset (forced). setup-agent-teams.sh targets the
# current working directory and reads templates relative to its own location, so
# run the framework's copy from inside the project.
header "Step 2/2: .claude superset (skills, hooks, rubrics, agents, settings)"
STEP2_ARGS=(--force)
[ "$DRY_RUN" = true ] && STEP2_ARGS+=(--dry-run)
( cd "$PROJECT_PATH" && bash "$TEMPLATE_DIR/scripts/setup-agent-teams.sh" "${STEP2_ARGS[@]}" ) \
    || error_exit ".claude setup failed"

# Summary
header "Summary"
if [ "$DRY_RUN" = true ]; then
    echo "Dry run completed. No files were modified."
    echo "Run without --dry-run to apply the upgrade."
else
    success "Force-upgrade completed!"
    echo ""
    echo "Upgraded to template version: $TEMPLATE_VERSION"
    echo ""
    echo "Next steps:"
    echo "1. Review the changes with: git -C \"$PROJECT_PATH\" diff"
    echo "2. Run the project's tests / workflow to confirm everything still works"
    echo "3. Commit the upgrade"
    echo ""
    echo "Note: forced overwrites leave .bak copies next to changed .claude files."
    if [ "$BACKUP" = true ]; then
        echo "      docs-eng-process backups use the .backup-YYYYMMDD-HHMMSS suffix."
    fi
    echo "      Once you've confirmed the upgrade, remove them, e.g.:"
    echo "        find \"$PROJECT_PATH/.claude\" -name '*.bak' -delete"
    if [ "$BACKUP" = true ]; then
        echo "        find \"$PROJECT_PATH\" -name '*.backup-*' -delete"
    fi
fi
echo ""

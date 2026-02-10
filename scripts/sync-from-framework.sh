#!/bin/bash
#
# Sync OpenUP Framework Updates Script
#
# This script is meant to be copied to projects that use the OpenUP framework.
# It syncs the latest skills, teammates, and documentation from the framework repository.
#
# Usage: ./scripts/sync-from-framework.sh [--dry-run] [--verbose] [--framework-path PATH]
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script options
DRY_RUN=false
VERBOSE=false
FRAMEWORK_PATH=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --verbose|-v)
      VERBOSE=true
      shift
      ;;
    --framework-path)
      FRAMEWORK_PATH="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: $0 [--dry-run] [--verbose] [--framework-path PATH]"
      echo ""
      echo "Options:"
      echo "  --dry-run            Show what would be synced without actually syncing"
      echo "  --verbose            Show detailed output"
      echo "  --framework-path     Path to the OpenUP framework repository (auto-detects if not provided)"
      echo "  --help               Show this help message"
      echo ""
      echo "This script syncs OpenUP skills, teammates, teams, and documentation from"
      echo "the framework repository to your project."
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      exit 1
      ;;
  esac
done

# Functions
log_info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

log_verbose() {
  if [ "$VERBOSE" = true ]; then
    echo -e "${BLUE}[VERBOSE]${NC} $1"
  fi
}

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Auto-detect framework path if not provided
if [ -z "$FRAMEWORK_PATH" ]; then
  log_info "Auto-detecting framework repository..."

  # Check if we're in the framework repository itself
  # Framework repo has sync-templates-to-claude.sh script
  if [ -f "$PROJECT_ROOT/scripts/sync-templates-to-claude.sh" ]; then
    log_error "You appear to be in the framework repository itself."
    log_error "This script is meant to be run from projects that USE the framework."
    log_error "Use ./scripts/sync-templates-to-claude.sh instead."
    exit 1
  fi

  # Look for framework in common locations
  POSSIBLE_PATHS=(
    "$PROJECT_ROOT/../open-up-for-ai-agents"
    "$HOME/personal-code/ai-dev-framework/open-up-for-ai-agents"
    "$HOME/projects/open-up-for-ai-agents"
    "$HOME/dev/open-up-for-ai-agents"
    "$HOME/code/open-up-for-ai-agents"
  )

  for path in "${POSSIBLE_PATHS[@]}"; do
    if [ -f "$path/docs-eng-process/.claude-templates/CLAUDE.md" ]; then
      FRAMEWORK_PATH="$path"
      log_success "Found framework at: $FRAMEWORK_PATH"
      break
    fi
  done

  if [ -z "$FRAMEWORK_PATH" ]; then
    log_error "Could not auto-detect framework repository."
    log_error "Please specify the path with --framework-path"
    log_error ""
    log_error "Example:"
    log_error "  $0 --framework-path ~/projects/open-up-for-ai-agents"
    exit 1
  fi
fi

# Validate framework path
FRAMEWORK_TEMPLATES="$FRAMEWORK_PATH/docs-eng-process/.claude-templates"
if [ ! -d "$FRAMEWORK_TEMPLATES" ]; then
  log_error "Invalid framework path: $FRAMEWORK_PATH"
  log_error "Could not find: $FRAMEWORK_TEMPLATES"
  exit 1
fi

# Define project paths
CLAUDE_DIR="$PROJECT_ROOT/.claude"
DOCS_PROCESS_DIR="$PROJECT_ROOT/docs-eng-process"

# Display header
echo ""
echo "=========================================="
echo "  OpenUP Framework Sync Script"
echo "=========================================="
echo ""
if [ "$DRY_RUN" = true ]; then
  log_warn "DRY RUN MODE - No files will be modified"
fi
echo ""
echo "Framework: $FRAMEWORK_PATH"
echo "Project: $PROJECT_ROOT"
echo ""

# Counter for summary
TOTAL_FILES=0
SYNCED_FILES=0
SKIPPED_FILES=0

# Sync function
sync_item() {
  local src="$1"
  local dest="$2"
  local item_name="$3"

  TOTAL_FILES=$((TOTAL_FILES + 1))

  if [ "$DRY_RUN" = true ]; then
    log_info "Would sync: $item_name"
    SYNCED_FILES=$((SYNCED_FILES + 1))
    return
  fi

  # Create destination directory if needed
  mkdir -p "$(dirname "$dest")"

  if [ -e "$dest" ]; then
    # Check if files are different
    if ! diff -qr "$src" "$dest" > /dev/null 2>&1; then
      log_verbose "Updating: $item_name"
      cp -r "$src" "$dest"
      SYNCED_FILES=$((SYNCED_FILES + 1))
    else
      log_verbose "Skipping (unchanged): $item_name"
      SKIPPED_FILES=$((SKIPPED_FILES + 1))
    fi
  else
    log_verbose "Creating: $item_name"
    cp -r "$src" "$dest"
    SYNCED_FILES=$((SYNCED_FILES + 1))
  fi
}

# Sync skills
log_info "Syncing skills from framework..."
echo ""

for skill_category in openup-phases openup-artifacts openup-workflow; do
  src_dir="$FRAMEWORK_TEMPLATES/skills/$skill_category"
  if [ -d "$src_dir" ]; then
    dest_dir="$CLAUDE_DIR/skills/$skill_category"
    log_verbose "Processing category: $skill_category"

    for skill_src in "$src_dir"/*; do
      if [ -d "$skill_src" ] || [ -f "$skill_src" ]; then
        skill_name=$(basename "$skill_src")
        sync_item "$skill_src" "$dest_dir/$skill_name" "skills/$skill_category/$skill_name"
      fi
    done
  fi
done

# Sync teammates
log_info "Syncing teammates from framework..."
echo ""
src_dir="$FRAMEWORK_TEMPLATES/teammates"
if [ -d "$src_dir" ]; then
  dest_dir="$CLAUDE_DIR/teammates"
  for teammate in "$src_dir"/*.md; do
    if [ -f "$teammate" ]; then
      teammate_name=$(basename "$teammate")
      sync_item "$teammate" "$dest_dir/$teammate_name" "teammates/$teammate_name"
    fi
  done
fi

# Sync teams
log_info "Syncing teams from framework..."
echo ""
src_dir="$FRAMEWORK_TEMPLATES/teams"
if [ -d "$src_dir" ]; then
  dest_dir="$CLAUDE_DIR/teams"
  for team in "$src_dir"/*.md; do
    if [ -f "$team" ]; then
      team_name=$(basename "$team")
      sync_item "$team" "$dest_dir/$team_name" "teams/$team_name"
    fi
  done
fi

# Sync documentation (optional - ask user if they want this)
log_info "Checking documentation..."
echo ""

if [ ! -d "$DOCS_PROCESS_DIR" ]; then
  log_warn "No docs-eng-process directory found."
  log_warn "To get OpenUP documentation, copy from framework:"
  log_warn "  mkdir -p docs-eng-process"
  log_warn "  cp -r $FRAMEWORK_PATH/docs-eng-process/openup-knowledge-base docs-eng-process/"
  log_warn "  cp -r $FRAMEWORK_PATH/docs-eng-process/templates docs-eng-process/"
  log_warn "  cp $FRAMEWORK_PATH/docs-eng-process/*.md docs-eng-process/"
else
  log_verbose "Documentation directory exists (not syncing to preserve local changes)"
fi

# Sync CLAUDE.md template (but warn about local changes)
log_info "Checking CLAUDE.md..."
echo ""

src_claude="$FRAMEWORK_TEMPLATES/CLAUDE.md"
dest_claude="$CLAUDE_DIR/CLAUDE.md"

if [ ! -f "$dest_claude" ]; then
  log_info "Creating CLAUDE.md from framework template"
  if [ "$DRY_RUN" = false ]; then
    sync_item "$src_claude" "$dest_claude" "CLAUDE.md"
  fi
else
  log_warn "CLAUDE.md exists - skipping to preserve local changes"
  log_warn "  To manually update, see: $src_claude"
  SKIPPED_FILES=$((SKIPPED_FILES + 1))
fi

# Display summary
echo ""
echo "=========================================="
echo "  Summary"
echo "=========================================="
echo ""
echo "Total items processed: $TOTAL_FILES"
if [ "$DRY_RUN" = false ]; then
  echo "Items synced: $SYNCED_FILES"
  echo "Items skipped (unchanged): $SKIPPED_FILES"
else
  echo "Items that would be synced: $SYNCED_FILES"
fi
echo ""

if [ "$DRY_RUN" = true ]; then
  log_info "Dry run complete. Run without --dry-run to apply changes."
else
  log_success "OpenUP framework synced successfully!"
  echo ""
  log_info "Skills are now available. Try: /openup-inception activity: initiate"
fi
echo ""

#!/bin/bash
#
# Update OpenUP Skills Script
#
# This script syncs OpenUP skills, templates, and documentation from the
# dev process directory to the project's .claude directory.
#
# Usage: ./scripts/update-openup-skills.sh [--dry-run] [--verbose]
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
    --help|-h)
      echo "Usage: $0 [--dry-run] [--verbose]"
      echo ""
      echo "Options:"
      echo "  --dry-run    Show what would be copied without actually copying"
      echo "  --verbose    Show detailed output"
      echo "  --help       Show this help message"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      exit 1
      ;;
  esac
done

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Define source and destination paths
DEV_PROCESS_DIR="$PROJECT_ROOT/docs-eng-process/.claude-templates"
CLAUDE_DIR="$PROJECT_ROOT/.claude"

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

# Check if source directory exists
if [ ! -d "$DEV_PROCESS_DIR" ]; then
  log_error "Dev process directory not found: $DEV_PROCESS_DIR"
  exit 1
fi

# Create .claude directory if it doesn't exist
if [ ! -d "$CLAUDE_DIR" ]; then
  log_info "Creating .claude directory"
  if [ "$DRY_RUN" = false ]; then
    mkdir -p "$CLAUDE_DIR"
  fi
fi

# Counter for summary
TOTAL_FILES=0
COPIED_FILES=0
SKIPPED_FILES=0

# Copy function
copy_item() {
  local src="$1"
  local dest="$2"
  local item_name="$3"

  TOTAL_FILES=$((TOTAL_FILES + 1))

  if [ "$DRY_RUN" = true ]; then
    log_info "Would copy: $item_name"
    COPIED_FILES=$((COPIED_FILES + 1))
    return
  fi

  if [ -e "$dest" ]; then
    # Check if files are different
    if ! diff -q "$src" "$dest" > /dev/null 2>&1; then
      log_verbose "Updating: $item_name"
      cp -r "$src" "$dest"
      COPIED_FILES=$((COPIED_FILES + 1))
    else
      log_verbose "Skipping (unchanged): $item_name"
      SKIPPED_FILES=$((SKIPPED_FILES + 1))
    fi
  else
    log_verbose "Creating: $item_name"
    cp -r "$src" "$dest"
    COPIED_FILES=$((COPIED_FILES + 1))
  fi
}

# Display header
echo ""
echo "=========================================="
echo "  OpenUP Skills Update Script"
echo "=========================================="
echo ""
if [ "$DRY_RUN" = true ]; then
  log_warn "DRY RUN MODE - No files will be modified"
fi
echo ""
echo "Source: $DEV_PROCESS_DIR"
echo "Destination: $CLAUDE_DIR"
echo ""

# Sync skills
log_info "Syncing skills..."
echo ""

# Sync all skill categories
for skill_category in openup-phases openup-artifacts openup-workflow; do
  src_dir="$DEV_PROCESS_DIR/skills/$skill_category"
  if [ -d "$src_dir" ]; then
    dest_dir="$CLAUDE_DIR/skills/$skill_category"
    mkdir -p "$dest_dir"

    log_verbose "Processing category: $skill_category"

    # Copy each skill directory
    for skill_src in "$src_dir"/*; do
      if [ -d "$skill_src" ]; then
        skill_name=$(basename "$skill_src")
        copy_item "$skill_src" "$dest_dir/$skill_name" "skills/$skill_category/$skill_name"
      elif [ -f "$skill_src" ]; then
        skill_name=$(basename "$skill_src")
        copy_item "$skill_src" "$dest_dir/$skill_name" "skills/$skill_category/$skill_name"
      fi
    done
  fi
done

# Sync teammates
log_info "Syncing teammates..."
echo ""
src_dir="$DEV_PROCESS_DIR/teammates"
if [ -d "$src_dir" ]; then
  dest_dir="$CLAUDE_DIR/teammates"
  mkdir -p "$dest_dir"

  for teammate in "$src_dir"/*.md; do
    if [ -f "$teammate" ]; then
      teammate_name=$(basename "$teammate")
      copy_item "$teammate" "$dest_dir/$teammate_name" "teammates/$teammate_name"
    fi
  done
fi

# Sync teams
log_info "Syncing teams..."
echo ""
src_dir="$DEV_PROCESS_DIR/teams"
if [ -d "$src_dir" ]; then
  dest_dir="$CLAUDE_DIR/teams"
  mkdir -p "$dest_dir"

  for team in "$src_dir"/*.md; do
    if [ -f "$team" ]; then
      team_name=$(basename "$team")
      copy_item "$team" "$dest_dir/$team_name" "teams/$team_name"
    fi
  done
fi

# Sync CLAUDE.md (but preserve local customizations)
log_info "Checking CLAUDE.md..."
echo ""
src_claude_md="$DEV_PROCESS_DIR/CLAUDE.md"
dest_claude_md="$CLAUDE_DIR/CLAUDE.md"

if [ -f "$src_claude_md" ]; then
  if [ ! -f "$dest_claude_md" ]; then
    log_info "Creating CLAUDE.md from template"
    if [ "$DRY_RUN" = false ]; then
      cp "$src_claude_md" "$dest_claude_md"
    fi
    COPIED_FILES=$((COPIED_FILES + 1))
  else
    log_warn "CLAUDE.md already exists - skipping to preserve local changes"
    log_warn "  Manually merge changes if needed from: $src_claude_md"
    SKIPPED_FILES=$((SKIPPED_FILES + 1))
  fi
fi

# Display summary
echo ""
echo "=========================================="
echo "  Summary"
echo "=========================================="
echo ""
echo "Total items processed: $TOTAL_FILES"
if [ "$DRY_RUN" = false ]; then
  echo "Items updated: $COPIED_FILES"
  echo "Items skipped (unchanged): $SKIPPED_FILES"
else
  echo "Items that would be updated: $COPIED_FILES"
fi
echo ""

if [ "$DRY_RUN" = true ]; then
  log_info "Dry run complete. Run without --dry-run to apply changes."
else
  log_success "OpenUP skills updated successfully!"
  echo ""
  log_info "New skills available:"
  echo "  /openup-inception"
  echo "  /openup-elaboration"
  echo "  /openup-construction"
  echo "  /openup-transition"
  echo "  /openup-create-vision"
  echo "  /openup-create-use-case"
  echo "  /openup-detail-use-case (NEW)"
  echo "  /openup-shared-vision (NEW)"
  echo "  /openup-create-architecture-notebook"
  echo "  /openup-create-risk-list"
  echo "  /openup-create-iteration-plan"
  echo "  /openup-create-test-plan"
  echo "  /openup-create-documentation (NEW)"
  echo "  /openup-start-iteration"
  echo "  /openup-complete-task"
  echo "  /openup-create-pr"
  echo "  /openup-assess-completeness (NEW)"
  echo "  /openup-retrospective (NEW)"
  echo "  /openup-tdd-workflow (NEW)"
  echo "  /openup-request-input"
  echo "  /openup-phase-review"
  echo "  /openup-log-run"
fi
echo ""

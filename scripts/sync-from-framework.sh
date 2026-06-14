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
UPDATE_CLAUDE=false
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
    --update-claude)
      UPDATE_CLAUDE=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [--dry-run] [--verbose] [--framework-path PATH] [--update-claude]"
      echo ""
      echo "Options:"
      echo "  --dry-run            Show what would be synced without actually syncing"
      echo "  --verbose            Show detailed output"
      echo "  --framework-path     Path to the OpenUP framework repository (auto-detects if not provided)"
      echo "  --update-claude       Overwrite existing .claude/CLAUDE.md from the framework template"
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

# The updater scripts are refreshed in place at the end of this run (see the
# "Syncing updater scripts" step), so no manual cp is needed anymore.

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

# Skills are in subdirectories with SKILL.md inside
src_dir="$FRAMEWORK_TEMPLATES/skills"
dest_dir="$CLAUDE_DIR/skills"

if [ -d "$src_dir" ]; then
  for skill_dir in "$src_dir"/*/; do
    if [ -d "$skill_dir" ]; then
      skill_name=$(basename "$skill_dir")
      skill_file="$skill_dir/SKILL.md"
      if [ -f "$skill_file" ]; then
        sync_item "$skill_file" "$dest_dir/$skill_name/SKILL.md" "skills/$skill_name"
      fi
    fi
  done
fi

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

# Sync scripts (Python utility scripts)
log_info "Syncing utility scripts from framework..."
echo ""
src_dir="$FRAMEWORK_TEMPLATES/scripts"
if [ -d "$src_dir" ]; then
  dest_dir="$CLAUDE_DIR/scripts"
  mkdir -p "$dest_dir"
  for script in "$src_dir"/*.py; do
    if [ -f "$script" ]; then
      script_name=$(basename "$script")
      sync_item "$script" "$dest_dir/$script_name" "scripts/$script_name"
      # Make scripts executable
      if [ "$DRY_RUN" = false ] && [ -f "$dest_dir/$script_name" ]; then
        chmod +x "$dest_dir/$script_name"
      fi
    fi
  done
fi

# Sync config files
log_info "Syncing config files from framework..."
echo ""
src_dir="$FRAMEWORK_TEMPLATES/config"
if [ -d "$src_dir" ]; then
  dest_dir="$CLAUDE_DIR/config"
  mkdir -p "$dest_dir"
  for config in "$src_dir"/*.md; do
    if [ -f "$config" ]; then
      config_name=$(basename "$config")
      sync_item "$config" "$dest_dir/$config_name" "config/$config_name"
    fi
  done
fi

# Sync rubrics (quality rubrics used by skills' grading steps)
log_info "Syncing rubrics from framework..."
echo ""
src_dir="$FRAMEWORK_TEMPLATES/rubrics"
if [ -d "$src_dir" ]; then
  dest_dir="$CLAUDE_DIR/rubrics"
  mkdir -p "$dest_dir"
  for rubric in "$src_dir"/*.md; do
    if [ -f "$rubric" ]; then
      rubric_name=$(basename "$rubric")
      sync_item "$rubric" "$dest_dir/$rubric_name" "rubrics/$rubric_name"
    fi
  done
fi

# Sync hook scripts (automation hooks wired up via settings.json below)
log_info "Syncing hook scripts from framework..."
echo ""
src_dir="$FRAMEWORK_TEMPLATES/scripts/hooks"
if [ -d "$src_dir" ]; then
  dest_dir="$CLAUDE_DIR/scripts/hooks"
  mkdir -p "$dest_dir"
  for hook in "$src_dir"/*; do
    if [ -f "$hook" ]; then
      hook_name=$(basename "$hook")
      sync_item "$hook" "$dest_dir/$hook_name" "scripts/hooks/$hook_name"
      # Make hooks executable
      if [ "$DRY_RUN" = false ] && [ -f "$dest_dir/$hook_name" ]; then
        chmod +x "$dest_dir/$hook_name"
      fi
    fi
  done
fi

# Sync the OpenUP process CLIs (scripts/openup-*.py) into the project's scripts/
# so the workflow skills can run. The list ships from the framework's
# scripts/process-manifest.txt; the helper backs up locally-modified files.
log_info "Syncing process CLIs from framework..."
echo ""
CLI_HELPER="$FRAMEWORK_PATH/scripts/lib/install-process-clis.sh"
if [ -f "$CLI_HELPER" ]; then
  # shellcheck source=/dev/null
  source "$CLI_HELPER"
  if [ "$DRY_RUN" = false ]; then
    mkdir -p "$PROJECT_ROOT/scripts"
  fi
  install_process_clis "$FRAMEWORK_PATH/scripts" "$PROJECT_ROOT/scripts" "$DRY_RUN" false
else
  log_warn "install-process-clis.sh not found in framework — skipping process CLI sync"
fi

# Refresh the updater scripts themselves (sync-from-framework.sh,
# update-from-template.sh) so a project's tooling never drifts. The helper writes
# via temp + atomic rename, so refreshing THIS running script is safe.
log_info "Syncing updater scripts from framework..."
echo ""
UPDATER_HELPER="$FRAMEWORK_PATH/scripts/lib/install-updater.sh"
if [ -f "$UPDATER_HELPER" ]; then
  # shellcheck source=/dev/null
  source "$UPDATER_HELPER"
  if [ "$DRY_RUN" = false ]; then
    mkdir -p "$PROJECT_ROOT/scripts"
  fi
  install_updater "$FRAMEWORK_PATH/scripts" "$PROJECT_ROOT/scripts" "$DRY_RUN" false
else
  log_warn "install-updater.sh not found in framework — skipping updater sync"
fi

# Create cache directory if it doesn't exist
log_info "Ensuring cache directory exists..."
echo ""
if [ "$DRY_RUN" = false ]; then
  mkdir -p "$CLAUDE_DIR/cache"
  log_verbose "Created cache directory: $CLAUDE_DIR/cache"
else
  log_info "[DRY RUN] Would create cache directory"
fi

# Check for settings.json
#
# Hooks live in .claude/scripts/hooks/ (synced above) but only fire if they are
# wired into settings.json. So when settings.json already exists we MERGE the
# OpenUP hooks in (identified by the /.claude/scripts/hooks/ marker), preserving
# every non-hook field and any custom hooks the project added. A .bak is written
# first. When it doesn't exist yet we create it from the template.
log_info "Checking settings.json..."
echo ""
SETTINGS_SRC="$FRAMEWORK_TEMPLATES/settings.json.example"
SETTINGS_DEST="$CLAUDE_DIR/settings.json"
if [ -f "$SETTINGS_SRC" ]; then
  if [ ! -f "$SETTINGS_DEST" ]; then
    log_warn "No settings.json found. Creating from template..."
    if [ "$DRY_RUN" = false ]; then
      cp "$SETTINGS_SRC" "$SETTINGS_DEST"
      log_success "Created settings.json with recommended defaults"
      SYNCED_FILES=$((SYNCED_FILES + 1))
    else
      log_info "[DRY RUN] Would create settings.json"
    fi
  else
    if [ "$DRY_RUN" = true ]; then
      log_info "[DRY RUN] Would merge OpenUP hooks into settings.json"
      log_info "  (custom hooks preserved; only /.claude/scripts/hooks/ entries updated)"
    else
      cp "$SETTINGS_DEST" "${SETTINGS_DEST}.bak"
      log_verbose "Backed up: $SETTINGS_DEST -> ${SETTINGS_DEST}.bak"
      if python3 - "$SETTINGS_SRC" "$SETTINGS_DEST" <<'PYEOF'
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

    for event in sorted(set(list(src_hooks) + list(dest_hooks))):
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
      then
        log_success "Merged OpenUP hooks into settings.json (custom hooks preserved)"
        SYNCED_FILES=$((SYNCED_FILES + 1))
      else
        log_warn "Could not merge settings.json; restoring backup"
        mv "${SETTINGS_DEST}.bak" "$SETTINGS_DEST"
      fi
    fi
  fi
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
dest_claude_openup="$CLAUDE_DIR/CLAUDE.openup.md"
openup_ref_path=".claude/CLAUDE.openup.md"

openup_ref_text="This project follows OpenUP. See $openup_ref_path for the shared OpenUP instructions."

ensure_openup_reference() {
  local target_file="$1"

  if [ ! -f "$target_file" ]; then
    return
  fi

  if ! grep -Fq "$openup_ref_text" "$target_file"; then
    if [ "$DRY_RUN" = false ]; then
      echo "" >> "$target_file"
      echo "$openup_ref_text" >> "$target_file"
    else
      log_info "[DRY RUN] Would add OpenUP reference to $target_file"
    fi
  fi
}

create_claude_stub() {
  local target_file="$1"

  if [ "$DRY_RUN" = false ]; then
    cat > "$target_file" << EOF
# Project Instructions

Add project-specific instructions here.

$openup_ref_text
EOF
  else
    log_info "[DRY RUN] Would create $target_file"
  fi
}

# Always sync the OpenUP template to a dedicated file in .claude
if [ -f "$src_claude" ]; then
  log_info "Syncing OpenUP template to CLAUDE.openup.md"
  if [ "$DRY_RUN" = false ]; then
    sync_item "$src_claude" "$dest_claude_openup" "CLAUDE.openup.md"
  fi
else
  log_warn "OpenUP template not found at: $src_claude"
fi

if [ ! -f "$dest_claude" ]; then
  log_info "Creating CLAUDE.md stub"
  create_claude_stub "$dest_claude"
else
  if [ "$UPDATE_CLAUDE" = true ]; then
    log_info "Updating CLAUDE.md from framework template"
    if [ "$DRY_RUN" = false ]; then
      sync_item "$src_claude" "$dest_claude" "CLAUDE.md"
      ensure_openup_reference "$dest_claude"
    fi
  else
    log_warn "CLAUDE.md exists - skipping to preserve local changes"
    log_warn "  OpenUP template is available at: $openup_ref_path"
    log_warn "  To overwrite CLAUDE.md, run with --update-claude"
    ensure_openup_reference "$dest_claude"
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

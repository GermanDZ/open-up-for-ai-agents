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

# Check if this script is outdated
check_script_version() {
  local framework_script="$1/scripts/sync-from-framework.sh"
  local current_script="${BASH_SOURCE[0]}"

  if [ -f "$framework_script" ]; then
    if ! cmp -s "$current_script" "$framework_script"; then
      log_warn "Your sync script is outdated!"
      log_warn "Run the following to update:"
      log_warn "  cp $framework_script $current_script"
      echo ""
    fi
  fi
}

# Self-commit the tracked files this sync overwrote (T-052).
#
# A sync overwrites tracked process CLIs (the scripts/<name> from
# process-manifest.txt) and completes the T-046 untrack — leaving them MODIFIED
# but uncommitted. The on-stop guard can't tell a sync's overwrite from
# abandoned lane work, so it blocks the next /openup-next lane from stopping
# (observed looping to the override cap). Fix: the sync owns its blast radius —
# it stages EXACTLY the paths it wrote and makes one chore(process) commit, so
# the tree is clean on return and on-stop never sees sync changes.
#
# Guards: dry-run, not-a-git-repo, mid-rebase/merge, and "nothing it wrote is
# dirty" all skip cleanly. NEVER a blanket `git add -A`/`git add .` — only the
# captured pathspecs, so unrelated user work is never swept in (Requirement 3).
commit_synced_changes() {
  [ "$DRY_RUN" = false ] || return 0
  git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
    log_verbose "Not a git work tree — leaving synced files for you to commit."
    return 0
  }

  # Don't entangle the sync commit with an in-progress conflict resolution.
  local gitdir
  gitdir="$(git -C "$PROJECT_ROOT" rev-parse --git-dir 2>/dev/null)" || return 0
  case "$gitdir" in /*) ;; *) gitdir="$PROJECT_ROOT/$gitdir" ;; esac
  if [ -e "$gitdir/MERGE_HEAD" ] || [ -d "$gitdir/rebase-merge" ] || [ -d "$gitdir/rebase-apply" ]; then
    log_warn "Rebase/merge in progress — leaving synced changes uncommitted (commit them yourself)."
    return 0
  fi

  # The exact tracked paths a sync writes: the process CLIs (from the manifest)
  # plus the T-046 migration target. Everything else the sync touches lands in
  # the gitignored .claude/ runtime copy, so it never needs committing.
  local captured=() f
  while IFS= read -r f; do
    [ -n "$f" ] && captured+=("scripts/$f")
  done < <(_process_cli_manifest "$FRAMEWORK_PATH/scripts")
  captured+=("docs/agent-logs/agent-runs.jsonl")
  captured+=("docs-eng-process/.template-version")

  # Stage the written paths ONE AT A TIME (never a blanket `git add -A`). A
  # single multi-pathspec `git add` aborts entirely if any pathspec matches
  # nothing (e.g. agent-runs.jsonl when the T-046 migration didn't run here), so
  # we add per-path and swallow the misses. (The T-046 deletion, when it ran, is
  # already staged by the migration; it's picked up by the diff below.)
  local p
  for p in "${captured[@]}"; do
    git -C "$PROJECT_ROOT" add -A -- "$p" 2>/dev/null || true
  done

  # Exactly the captured paths that actually have staged changes — diff tolerates
  # non-matching pathspecs (unlike add), so the agent-runs miss is harmless here.
  local staged=()
  while IFS= read -r p; do
    [ -n "$p" ] && staged+=("$p")
  done < <(git -C "$PROJECT_ROOT" diff --cached --name-only -- "${captured[@]}" 2>/dev/null)

  if [ "${#staged[@]}" -eq 0 ]; then
    log_verbose "No sync-written tracked files changed — nothing to commit."
    return 0
  fi

  # Attribute the commit to the framework version when we can read it.
  local fw_sha msg
  fw_sha="$(git -C "$FRAMEWORK_PATH" rev-parse --short HEAD 2>/dev/null || true)"
  if [ -n "$fw_sha" ]; then
    msg="chore(process): sync OpenUP framework to $fw_sha [openup-skip]"
  else
    msg="chore(process): sync OpenUP framework [openup-skip]"
  fi

  # Partial-commit form (explicit staged pathspecs): commits ONLY these paths,
  # leaving any unrelated staged user work untouched (Requirement 3).
  if git -C "$PROJECT_ROOT" commit -m "$msg" -- "${staged[@]}" >/dev/null 2>&1; then
    log_success "Committed framework-synced tooling: $msg"
  else
    log_warn "Could not commit synced tooling — please commit it yourself: $msg"
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

# Check if this script needs updating
check_script_version "$FRAMEWORK_PATH"

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

# T-047: carry T-046's data migration — untrack the now-derived agent-runs.jsonl
# (logic lives in scripts/lib/migrate-data.sh so it is unit-testable).
log_info "Checking T-046 migration (agent-runs.jsonl untrack)..."
echo ""
MIGRATE_HELPER="$FRAMEWORK_PATH/scripts/lib/migrate-data.sh"
if [ -f "$MIGRATE_HELPER" ]; then
  # shellcheck source=/dev/null
  source "$MIGRATE_HELPER"
  if git -C "$PROJECT_ROOT" ls-files --error-unmatch "docs/agent-logs/agent-runs.jsonl" >/dev/null 2>&1; then
    migrate_untrack_agent_runs "$PROJECT_ROOT" "$DRY_RUN"
    [ "$DRY_RUN" = false ] && log_success "T-046 migration: untracked agent-runs.jsonl (staged — commit to finish)"
  else
    log_verbose "T-046 migration: agent-runs.jsonl already untracked — nothing to do"
  fi
else
  log_warn "migrate-data.sh not found in framework — skipping T-046 migration"
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
        original_text = f.read()
    dest = json.loads(original_text)

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
    new_text = json.dumps(dest, indent=2) + "\n"
    if new_text == original_text:
        # Exit 2 = success, no change (idempotent)
        sys.exit(2)
    with open(dest_path, "w") as f:
        f.write(new_text)
    print(f"Merged OpenUP hooks into {dest_path} (custom hooks preserved)")
except Exception as e:
    print(f"Warning: could not merge settings.json: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
      then
        log_success "Merged OpenUP hooks into settings.json (custom hooks preserved)"
        SYNCED_FILES=$((SYNCED_FILES + 1))
      elif [ $? -eq 2 ]; then
        log_verbose "settings.json already up-to-date (no change)"
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
  log_warn "  cp -r $FRAMEWORK_PATH/openup-knowledge-base ."
  log_warn "  cp -r $FRAMEWORK_PATH/docs-eng-process/templates docs-eng-process/"
  log_warn "  cp $FRAMEWORK_PATH/docs-eng-process/*.md docs-eng-process/"
else
  log_verbose "Documentation directory exists (not syncing to preserve local changes)"

  # The version marker is NOT free-form local content — it records which
  # framework revision the synced CLIs/skills came from. The sync overwrites
  # that content, so the marker must move with it; otherwise it drifts (a
  # project shows an old version while running current tooling, which
  # openup-doctor then flags). Mirror the framework's marker on every sync.
  fw_version_file="$FRAMEWORK_PATH/docs-eng-process/.template-version"
  if [ -f "$fw_version_file" ]; then
    if [ "$DRY_RUN" = true ]; then
      log_info "[DRY-RUN] Would update .template-version to $(cat "$fw_version_file")"
    elif ! cmp -s "$fw_version_file" "$DOCS_PROCESS_DIR/.template-version"; then
      cp "$fw_version_file" "$DOCS_PROCESS_DIR/.template-version"
      log_success "Updated .template-version -> $(cat "$fw_version_file")"
      SYNCED_FILES=$((SYNCED_FILES + 1))
    fi
  fi
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

# T-056: Bootstrap — emit .openup-version + patch .gitignore so .claude/settings.json
# is tracked (the only file a fresh clone needs to trigger the SessionStart hook).
log_info "Checking web/ephemeral session bootstrap..."
echo ""

OPENUP_VERSION_FILE="$PROJECT_ROOT/.openup-version"
GITIGNORE_FILE="$PROJECT_ROOT/.gitignore"

# Emit .openup-version (vendored by default) if absent; never overwrite an
# existing pin — the project owns this value.
if [ ! -f "$OPENUP_VERSION_FILE" ]; then
  if [ "$DRY_RUN" = false ]; then
    echo "vendored" > "$OPENUP_VERSION_FILE"
    log_success "Created .openup-version (default: vendored)"
    SYNCED_FILES=$((SYNCED_FILES + 1))
  else
    log_info "[DRY RUN] Would create .openup-version"
  fi
else
  log_verbose ".openup-version already exists ($(cat "$OPENUP_VERSION_FILE")) — skipping"
fi

# Patch .gitignore: swap the broad /.claude ignore for the settings-only pattern.
# Idempotent: only runs when the old pattern is present.
if [ -f "$GITIGNORE_FILE" ] && grep -qxF '/.claude' "$GITIGNORE_FILE"; then
  if [ "$DRY_RUN" = false ]; then
    # Replace the bare /.claude line with the two-line pattern
    sed -i.bak 's|^/\.claude$|/.claude/*\
!/.claude/settings.json|' "$GITIGNORE_FILE" && rm -f "${GITIGNORE_FILE}.bak"
    log_success "Patched .gitignore: /.claude → /.claude/* + !/.claude/settings.json"
    SYNCED_FILES=$((SYNCED_FILES + 1))
  else
    log_info "[DRY RUN] Would patch .gitignore (/.claude → /.claude/* + !/.claude/settings.json)"
  fi
else
  log_verbose ".gitignore already has the settings-only pattern (or does not exist) — skipping"
fi
echo ""

# Self-commit the tracked files this sync overwrote (T-052) so the working tree
# is clean on return and on-stop.py never mistakes them for abandoned lane work.
if [ "$DRY_RUN" = false ]; then
  log_info "Committing framework-synced tooling..."
  echo ""
  commit_synced_changes
  echo ""
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

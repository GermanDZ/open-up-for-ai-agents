#!/bin/bash
# update-openup-simple.sh — pipe-safe OpenUP updater (no heredocs).
#
# Thin wrapper that delegates to the canonical scripts/update-from-template.sh,
# so it ships EXACTLY what every other update path does (docs-eng-process/, the
# .claude/ assets, the process CLIs, and the updater scripts) and never clobbers
# your project-owned .claude/CLAUDE.md. It adds only offline support: pass
# --template-dir to update from a local framework clone instead of cloning.
#
# Usage:
#   curl -sL https://raw.githubusercontent.com/GermanDZ/open-up-for-ai-agents/main/scripts/update-openup-simple.sh | bash
#   ./scripts/update-openup-simple.sh --template-dir /path/to/open-up-for-ai-agents
# Any extra flags (--dry-run, --what-new, --backup, …) pass through to
# update-from-template.sh.

set -e

GREEN='\033[0;32m'
NC='\033[0m'

REPO_URL="${OPENUP_REPO_URL:-https://github.com/GermanDZ/open-up-for-ai-agents.git}"
BRANCH="${OPENUP_BRANCH:-main}"

# Parse --template-dir / --branch; collect the rest to pass through.
TEMPLATE_DIR=""
PASSTHRU=()
while [ $# -gt 0 ]; do
    case "$1" in
        --template-dir)
            TEMPLATE_DIR="$2"
            shift 2
            ;;
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        *)
            PASSTHRU+=("$1")
            shift
            ;;
    esac
done

echo -e "${GREEN}OpenUP Framework Update${NC}"
echo ""

if [ ! -d "docs-eng-process" ]; then
    echo "Error: docs-eng-process directory not found."
    echo "Please run this script from your project's root directory."
    exit 1
fi

# Resolve the template source: a caller-provided local clone, or a fresh clone.
CLONED_DIR=""
if [ -n "$TEMPLATE_DIR" ]; then
    if [ ! -d "$TEMPLATE_DIR/docs-eng-process" ]; then
        echo "Error: --template-dir '$TEMPLATE_DIR' has no docs-eng-process/ directory"
        exit 1
    fi
else
    TEMPLATE_DIR="/tmp/openup-update-$$"
    CLONED_DIR="$TEMPLATE_DIR"
    echo "Downloading latest template from: $REPO_URL (branch: $BRANCH)"
    if ! git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$TEMPLATE_DIR" 2>/dev/null; then
        echo "Error: Failed to download template"
        rm -rf "$TEMPLATE_DIR"
        exit 1
    fi
fi

# Delegate to the canonical updater (no rsync; preserves project-owned files).
EXIT_CODE=0
bash "$TEMPLATE_DIR/scripts/update-from-template.sh" \
    --template-dir "$TEMPLATE_DIR" "${PASSTHRU[@]}" || EXIT_CODE=$?

[ -n "$CLONED_DIR" ] && rm -rf "$CLONED_DIR"

if [ "$EXIT_CODE" -eq 0 ]; then
    echo ""
    echo -e "${GREEN}Update complete!${NC}"
fi
exit "$EXIT_CODE"

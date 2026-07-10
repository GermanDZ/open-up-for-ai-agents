#!/bin/bash
# update-openup.sh - Update script to run from any project directory.
#
# RECOMMENDED USAGE (download, review, then run — do NOT pipe to a shell):
#   git clone --depth 1 --branch v2.1.0 \
#     https://github.com/GermanDZ/open-up-for-ai-agents.git /tmp/openup
#   # review /tmp/openup, then:
#   bash /tmp/openup/scripts/update-openup.sh
#
# By default this script pins to the latest released TAG (never `main`). Override with:
#   OPENUP_REF=v2.1.0  ./scripts/update-openup.sh   # pin to an exact tag (recommended)
#   OPENUP_BRANCH=main ./scripts/update-openup.sh   # opt in to the unpinned tip (NOT recommended)
#
# Piping a remote script straight into `bash` is intentionally not the documented
# default — it runs unreviewed, unpinned remote code. Clone a tag and run it locally.

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
REPO_URL="${OPENUP_REPO_URL:-https://github.com/GermanDZ/open-up-for-ai-agents.git}"
TEMP_DIR="/tmp/openup-update-$$"

# Resolve the ref to clone: explicit OPENUP_REF wins; else an explicit (unpinned)
# OPENUP_BRANCH; else the latest released tag. Never silently default to `main`.
resolve_ref() {
    if [ -n "$OPENUP_REF" ]; then echo "$OPENUP_REF"; return 0; fi
    if [ -n "$OPENUP_BRANCH" ]; then
        echo -e "${YELLOW}Warning: OPENUP_BRANCH=$OPENUP_BRANCH is unpinned — prefer OPENUP_REF=<tag> for reproducible updates.${NC}" >&2
        echo "$OPENUP_BRANCH"; return 0
    fi
    local latest
    latest=$(git ls-remote --tags --refs --sort=-v:refname "$REPO_URL" 'v*' 2>/dev/null | head -n1 | sed 's@.*/@@')
    if [ -z "$latest" ]; then
        echo -e "${YELLOW}Error: no release tag on $REPO_URL and no OPENUP_REF/OPENUP_BRANCH set.${NC}" >&2
        echo "Set OPENUP_REF=<tag> (recommended) or OPENUP_BRANCH=main (unpinned) explicitly." >&2
        return 1
    fi
    echo "$latest"
}
BRANCH="$(resolve_ref)" || exit 1

echo -e "${GREEN}OpenUP Framework Update Script${NC}"
echo ""

# Check if we're in a project directory
if [ ! -d "docs-eng-process" ]; then
    echo "Error: docs-eng-process directory not found."
    echo "Please run this script from your project's root directory."
    exit 1
fi

echo "Updating from: $REPO_URL (ref: $BRANCH)"
echo ""

# Clone the pinned template
echo "Downloading template at $BRANCH..."
if ! git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$TEMP_DIR" 2>/dev/null; then
    echo "Error: Failed to download template"
    rm -rf "$TEMP_DIR"
    exit 1
fi

if [ ! -d "$TEMP_DIR/docs-eng-process" ]; then
    echo "Error: Failed to download template"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Run the update script
echo ""
echo "Running update..."
bash "$TEMP_DIR/scripts/update-from-template.sh" --template-dir "$TEMP_DIR" "$@" || EXIT_CODE=$?

# Cleanup
rm -rf "$TEMP_DIR"

if [ ${EXIT_CODE:-0} -eq 0 ]; then
    echo ""
    echo -e "${GREEN}Update complete!${NC}"
fi

exit ${EXIT_CODE:-0}

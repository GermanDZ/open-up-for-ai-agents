#!/bin/bash
# update-openup-simple.sh - Minimal inline update (no update-from-template.sh dependency).
#
# RECOMMENDED USAGE (download, review, then run — do NOT pipe to a shell):
#   git clone --depth 1 --branch v2.0.0 \
#     https://github.com/GermanDZ/open-up-for-ai-agents.git /tmp/openup
#   # review /tmp/openup, then:
#   bash /tmp/openup/scripts/update-openup-simple.sh
#
# Pins to the latest released TAG by default (never `main`). Override with:
#   OPENUP_REF=v2.0.0  (pin to an exact tag, recommended) | OPENUP_BRANCH=main (unpinned)

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

REPO_URL="${OPENUP_REPO_URL:-https://github.com/GermanDZ/open-up-for-ai-agents.git}"
TEMP_DIR="/tmp/openup-update-$$"

# Resolve the ref to clone: OPENUP_REF > explicit OPENUP_BRANCH > latest tag. Never `main` silently.
resolve_ref() {
    if [ -n "$OPENUP_REF" ]; then echo "$OPENUP_REF"; return 0; fi
    if [ -n "$OPENUP_BRANCH" ]; then
        echo -e "${YELLOW}Warning: OPENUP_BRANCH=$OPENUP_BRANCH is unpinned — prefer OPENUP_REF=<tag>.${NC}" >&2
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

echo -e "${GREEN}OpenUP Framework Update${NC}"
echo ""

if [ ! -d "docs-eng-process" ]; then
    echo "Error: docs-eng-process directory not found."
    echo "Please run this script from your project's root directory."
    exit 1
fi

echo "Downloading template at $BRANCH from: $REPO_URL"
git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$TEMP_DIR" 2>/dev/null || {
    echo "Error: Failed to download template"
    rm -rf "$TEMP_DIR"
    exit 1
}

# Sync docs-eng-process
echo ""
echo "Syncing docs-eng-process..."
rsync -av --delete "$TEMP_DIR/docs-eng-process/" "docs-eng-process/" \
    --exclude='.DS_Store' \
    --exclude='.git' \
    --exclude='*.backup-*'

# Sync .claude templates if they exist
if [ -d "$TEMP_DIR/docs-eng-process/.claude-templates" ]; then
    echo "Syncing .claude directory..."
    mkdir -p .claude/teammates .claude/teams
    rsync -av "$TEMP_DIR/docs-eng-process/.claude-templates/teammates/" ".claude/teammates/" 2>/dev/null || true
    rsync -av "$TEMP_DIR/docs-eng-process/.claude-templates/teams/" ".claude/teams/" 2>/dev/null || true
    if [ -f "$TEMP_DIR/docs-eng-process/.claude-templates/CLAUDE.md" ]; then
        cp "$TEMP_DIR/docs-eng-process/.claude-templates/CLAUDE.md" ".claude/CLAUDE.md" 2>/dev/null || true
    fi
fi

# Copy version file
if [ -f "$TEMP_DIR/docs-eng-process/.template-version" ]; then
    cp "$TEMP_DIR/docs-eng-process/.template-version" "docs-eng-process/.template-version"
fi

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo -e "${GREEN}Update complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Review changes with: git diff"
echo "2. Test that everything works"
echo "3. Commit the updates"

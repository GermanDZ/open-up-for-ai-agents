#!/bin/bash
# Simple inline update script - no HERE documents, safe for piping
# Usage: curl -sL https://raw.githubusercontent.com/GermanDZ/open-up-for-ai-agents/main/scripts/update-openup-simple.sh | bash

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

REPO_URL="${OPENUP_REPO_URL:-https://github.com/GermanDZ/open-up-for-ai-agents.git}"
BRANCH="${OPENUP_BRANCH:-main}"
TEMP_DIR="/tmp/openup-update-$$"

echo -e "${GREEN}OpenUP Framework Update${NC}"
echo ""

if [ ! -d "docs-eng-process" ]; then
    echo "Error: docs-eng-process directory not found."
    echo "Please run this script from your project's root directory."
    exit 1
fi

echo "Downloading latest template from: $REPO_URL"
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

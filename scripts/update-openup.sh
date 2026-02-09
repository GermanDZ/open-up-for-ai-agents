#!/bin/bash
# update-openup.sh - One-liner update script to run from any project directory
# Usage: curl -s https://raw.githubusercontent.com/GermanDZ/open-up-for-ai-agents/main/scripts/update-openup.sh | bash

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
REPO_URL="${OPENUP_REPO_URL:-https://github.com/GermanDZ/open-up-for-ai-agents.git"
BRANCH="${OPENUP_BRANCH:-main}"
TEMP_DIR="/tmp/openup-update-$$"

echo -e "${GREEN}OpenUP Framework Update Script${NC}"
echo ""

# Check if we're in a project directory
if [ ! -d "docs-eng-process" ]; then
    echo "Error: docs-eng-process directory not found."
    echo "Please run this script from your project's root directory."
    exit 1
fi

echo "Updating from: $REPO_URL (branch: $BRANCH)"
echo ""

# Clone the latest template
echo "Downloading latest template..."
git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$TEMP_DIR" 2>/dev/null

if [ ! -d "$TEMP_DIR/docs-eng-process" ]; then
    echo "Error: Failed to download template"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Run the update script
echo ""
echo "Running update..."
bash "$TEMP_DIR/scripts/update-from-template.sh" --template-dir "$TEMP_DIR" "$@"

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo -e "${GREEN}Update complete!${NC}"

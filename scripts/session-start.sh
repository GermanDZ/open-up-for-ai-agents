#!/bin/bash
# SessionStart hook: regenerate .claude/ and install project runtime deps.
# Registered in .claude/settings.json under "SessionStart".
# Idempotent, non-interactive, synchronous — skills are ready before the
# agent loop runs (no discovery race).

set -e

PROJECT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_DIR" || exit 1

# Regenerate .claude/ from templates (vendored or fetched framework version)
bash scripts/install-openup.sh

# Install project runtime deps so scripts/ work in fresh environments
if [ -f "requirements.txt" ]; then
  python3 -m pip install -q -r requirements.txt 2>/dev/null || true
fi

exit 0

#!/bin/bash
# Resolve which framework version to install, fetch it if needed, sync to .claude/.
#
# Version precedence:
#   1. $OPENUP_FRAMEWORK_VERSION  — per-session env override
#   2. .openup-version file       — project pin (vendored / latest / vX.Y.Z)
#   3. default: "vendored"        — committed templates, fully offline
#
# On any network/fetch failure the script falls back to vendored so a session
# never starts without skills.

set -e

PROJECT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_DIR" || exit 1

OPENUP_VERSION="${OPENUP_FRAMEWORK_VERSION:-}"
if [ -z "$OPENUP_VERSION" ] && [ -f ".openup-version" ]; then
  OPENUP_VERSION="$(cat .openup-version | xargs)"
fi
OPENUP_VERSION="${OPENUP_VERSION:-vendored}"

echo "OpenUP Bootstrap: version=${OPENUP_VERSION}"

TEMPLATES_DIR=""

if [ "$OPENUP_VERSION" = "vendored" ]; then
  TEMPLATES_DIR="docs-eng-process/.claude-templates"
  if [ ! -d "$TEMPLATES_DIR" ]; then
    echo "Error: vendored templates not found at $TEMPLATES_DIR" >&2
    exit 1
  fi
else
  CACHE_DIR=".openup-cache"
  mkdir -p "$CACHE_DIR"

  RESOLVED_VERSION="$OPENUP_VERSION"

  if [ "$OPENUP_VERSION" = "latest" ]; then
    RESOLVED_VERSION="$(git ls-remote --tags --refs \
      https://github.com/anthropics/open-up-for-ai-agents.git 2>/dev/null \
      | grep -o 'refs/tags/v[0-9.]*' | sed 's|refs/tags/||' | sort -V | tail -1)"

    if [ -z "$RESOLVED_VERSION" ]; then
      echo "Warning: could not resolve latest tag, falling back to vendored" >&2
      TEMPLATES_DIR="docs-eng-process/.claude-templates"
    fi
  fi

  # Normalize vX.Y.Z → vX.Y.Z (accept both "2.0.0" and "v2.0.0")
  case "$RESOLVED_VERSION" in
    v*) ;;
    [0-9]*) RESOLVED_VERSION="v${RESOLVED_VERSION}" ;;
  esac

  if [ -z "$TEMPLATES_DIR" ] && [ -n "$RESOLVED_VERSION" ]; then
    FETCH_DIR="${CACHE_DIR}/${RESOLVED_VERSION}"
    if [ ! -d "$FETCH_DIR" ]; then
      echo "Fetching OpenUP ${RESOLVED_VERSION}..."
      git clone --depth 1 --branch "$RESOLVED_VERSION" \
        https://github.com/anthropics/open-up-for-ai-agents.git \
        "$FETCH_DIR" 2>/dev/null || {
        echo "Warning: fetch failed, falling back to vendored" >&2
        TEMPLATES_DIR="docs-eng-process/.claude-templates"
      }
    fi
    [ -z "$TEMPLATES_DIR" ] && \
      TEMPLATES_DIR="${FETCH_DIR}/docs-eng-process/.claude-templates"
  fi
fi

# Final fallback guard
if [ -z "$TEMPLATES_DIR" ] || [ ! -d "$TEMPLATES_DIR" ]; then
  echo "Falling back to vendored templates" >&2
  TEMPLATES_DIR="docs-eng-process/.claude-templates"
fi

export OPENUP_TEMPLATES_DIR="$TEMPLATES_DIR"
bash scripts/sync-templates-to-claude.sh

exit 0

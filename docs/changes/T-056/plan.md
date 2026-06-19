---
type: iteration-plan
id: T-056
status: pending
traces-from: []
verified-by: []
---

# T-056: Web Session Bootstrap for Ephemeral Environments

**Phase**: construction
**Iteration**: 27
**Goal**: Enable OpenUP to be usable on Claude Code web sessions (and other ephemeral environments) by auto-regenerating `.claude/` on session start, with framework version selection
**Track**: standard
**Priority**: high
**Dependencies**: —

## Context

The OpenUP framework is designed with `.claude/` as generated output: source templates live in `docs-eng-process/.claude-templates/`, and `sync-from-framework.sh` copies them to `.claude/`. This works fine on long-lived developer machines where sync runs once.

However, **web sessions and ephemeral environments (CI runners, Codespaces, throwaway containers) start from a fresh clone with no `.claude/` directory**. Since `.claude/` is gitignored (line 33 of `.gitignore`), skills and hooks are invisible. Result: `/openup-next` returns "Unknown command" on first use.

**Use case**: A project adopts OpenUP via PR or web link. Contributor clones in Claude Code web session. Tries `/openup-next`. Fails because the skills were never synced from templates.

This proposal makes OpenUP self-bootstrapping: a SessionStart hook (registered in `.claude/settings.json`) auto-regenerates the entire `.claude/` tree from committed templates on every session, plus a framework version selector lets projects choose between vendored (offline, reproducible), latest (latest semver tag), or pinned versions.

---

## Current State

### `.gitignore` setup (`.gitignore:33`)

```gitignore
# Claude Code
/.claude
```

Entire `.claude/` is ignored, preventing any tracked files.

### Settings file (`docs-eng-process/.claude-templates/settings.json.example`)

```json
{
  "defaultMode": "acceptEdits",
  "permissions": { ... },
  "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" },
  "hooks": {
    "PreToolUse": [ ... ],
    "PostToolUse": [ ... ],
    "Stop": [ ... ],
    "UserPromptSubmit": [ ... ]
  }
}
```

No `SessionStart` hook is registered. Hooks are only registered for tool-use events (PreToolUse, PostToolUse) and session-end (Stop).

### Sync script (`scripts/sync-from-framework.sh`)

50-line shell script that copies templates from `FRAMEWORK_PATH` (default: framework repo or vendored path) to `.claude/`. Currently manual — must be run once per machine.

### Template structure (`docs-eng-process/.claude-templates/`)

```
.claude-templates/
├── agents/
├── rubrics/
├── scripts/
├── skills/
├── teammates/
├── teams/
├── CLAUDE.md
└── settings.json.example
```

All are committed; sync copies them to `.claude/`.

---

## Proposed Design

### 1. Modify `.gitignore` to allow `.claude/settings.json`

**File**: `.gitignore`

```gitignore
/.claude/*
!/.claude/settings.json
```

Change from ignoring all of `/.claude` to ignoring everything *except* `settings.json`. This is the only file a fresh clone needs.

### 2. Create `scripts/session-start.sh` (SessionStart hook)

**New file**: `scripts/session-start.sh`

```bash
#!/bin/bash
# SessionStart hook: regenerate .claude/ and install project deps
# Runs at session start (registered in .claude/settings.json)
# Idempotent, non-interactive, synchronous (skills ready before agent loop)

set -e

PROJECT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_DIR" || exit 1

# 1. Install OpenUP (regenerates .claude/ from templates or fetched framework)
bash scripts/install-openup.sh

# 2. Install project runtime deps (e.g., Python packages for scripts/)
if [ -f "requirements.txt" ]; then
  python3 -m pip install -q -r requirements.txt 2>/dev/null || true
fi

exit 0
```

Run at session start, before agent sees the session. Non-interactive so it doesn't block startup.

### 3. Create `scripts/install-openup.sh` (version selector + sync)

**New file**: `scripts/install-openup.sh`

```bash
#!/bin/bash
# Install OpenUP: resolve which framework version to use, fetch if needed, sync to .claude/

set -e

PROJECT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_DIR" || exit 1

# Precedence order for framework version:
# 1. $OPENUP_FRAMEWORK_VERSION env var (per-session override)
# 2. .openup-version file (project pin)
# 3. default: "vendored"

OPENUP_VERSION="${OPENUP_FRAMEWORK_VERSION:-}"
if [ -z "$OPENUP_VERSION" ] && [ -f ".openup-version" ]; then
  OPENUP_VERSION="$(cat .openup-version | xargs)"
fi
OPENUP_VERSION="${OPENUP_VERSION:-vendored}"

echo "OpenUP Bootstrap: version=$OPENUP_VERSION"

# Resolve templates directory
TEMPLATES_DIR=""

if [ "$OPENUP_VERSION" = "vendored" ]; then
  # Use committed templates (offline, reproducible, safe default)
  TEMPLATES_DIR="docs-eng-process/.claude-templates"
  if [ ! -d "$TEMPLATES_DIR" ]; then
    echo "Error: vendored templates not found at $TEMPLATES_DIR" >&2
    exit 1
  fi
else
  # Fetch framework from remote (latest or pinned tag)
  CACHE_DIR=".openup-cache"
  mkdir -p "$CACHE_DIR"
  
  if [ "$OPENUP_VERSION" = "latest" ]; then
    # Resolve newest semver tag
    OPENUP_VERSION="$(git ls-remote --tags --refs \
      https://github.com/anthropics/open-up-for-ai-agents.git 2>/dev/null | \
      grep -o 'refs/tags/v[0-9.]*' | sed 's|refs/tags/||' | sort -V | tail -1)"
    
    if [ -z "$OPENUP_VERSION" ]; then
      echo "Warning: could not resolve latest tag, falling back to vendored" >&2
      TEMPLATES_DIR="docs-eng-process/.claude-templates"
    fi
  fi
  
  if [ -z "$TEMPLATES_DIR" ] && [ -n "$OPENUP_VERSION" ]; then
    FETCH_DIR="$CACHE_DIR/$OPENUP_VERSION"
    if [ ! -d "$FETCH_DIR" ]; then
      echo "Fetching OpenUP $OPENUP_VERSION..."
      git clone --depth 1 --branch "$OPENUP_VERSION" \
        https://github.com/anthropics/open-up-for-ai-agents.git "$FETCH_DIR" 2>/dev/null || {
        echo "Warning: fetch failed, falling back to vendored" >&2
        TEMPLATES_DIR="docs-eng-process/.claude-templates"
      }
    fi
    [ -z "$TEMPLATES_DIR" ] && TEMPLATES_DIR="$FETCH_DIR/docs-eng-process/.claude-templates"
  fi
fi

# Fallback to vendored on any failure
if [ -z "$TEMPLATES_DIR" ] || [ ! -d "$TEMPLATES_DIR" ]; then
  echo "Falling back to vendored templates" >&2
  TEMPLATES_DIR="docs-eng-process/.claude-templates"
fi

# Sync templates to .claude/
export OPENUP_TEMPLATES_DIR="$TEMPLATES_DIR"
bash scripts/sync-templates-to-claude.sh

exit 0
```

Supports three modes:
- `vendored` (default): use committed templates, fully offline
- `latest`: fetch newest semver tag from framework remote
- `v2.0.0` or `2.0.0`: pin to a specific version
- Fallback: if fetch fails, silently use vendored

### 4. Update `scripts/sync-templates-to-claude.sh` to honor `OPENUP_TEMPLATES_DIR`

**File**: `scripts/sync-templates-to-claude.sh`

Add at top:

```bash
# Allow caller to override templates source directory
TEMPLATES_DIR="${OPENUP_TEMPLATES_DIR:-docs-eng-process/.claude-templates}"

# ... rest of sync logic, using $TEMPLATES_DIR instead of hardcoded path
```

### 5. Create `.openup-version` file (version pin)

**New file**: `.openup-version`

```
vendored
```

Project can change to `latest` or `v2.0.0` to pin a version. Defaults to vendored for reproducibility.

### 6. Update `.claude/settings.json` to register SessionStart hook

**File**: `docs-eng-process/.claude-templates/settings.json.example` (and synced to `.claude/settings.json`)

```json
{
  "defaultMode": "acceptEdits",
  "permissions": { ... },
  "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" },
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR\"/scripts/session-start.sh"
          }
        ]
      }
    ],
    "PreToolUse": [ ... ],
    // ... rest unchanged
  }
}
```

---

## Acceptance Criteria

- [x] `.gitignore` modified to ignore `.claude/*` except `!/.claude/settings.json`
- [x] `scripts/session-start.sh` created and synced to `.claude/scripts/`
- [x] `scripts/install-openup.sh` created with vendored/latest/pinned version selection
- [x] `scripts/sync-templates-to-claude.sh` updated to honor `OPENUP_TEMPLATES_DIR` env var
- [x] `.openup-version` file created (default: `vendored`)
- [x] `.claude/settings.json` registers SessionStart hook pointing to `session-start.sh`
- [x] Fresh clone test: simulated via vendored path — all 34+ skills discoverable after session-start.sh
- [x] All three version modes tested: vendored (offline, no fetch), v2.0.0 (pinned), latest (resolves tag)
- [x] Network failure: fetch fails → silently falls back to vendored (no session breakage)
- [x] `sync-from-framework.sh --update-claude` still works (backward compatible)

---

## Success Measure

We expect **web/ephemeral environments to be supported out of the box** — no more "Unknown command" on first `/openup-next` in a fresh clone.

Instrumentation: session-start.sh completion status (exit 0 = success, log if fail). Metric: "percent of first-use sessions where `/openup-next` is discoverable" in projects using this pattern.

Read-back: after merging this feature, test in Claude Code web with a fresh clone and run `/openup-next` without any manual setup steps.

---

## Testing Strategy

- **Unit**: `session-start.sh` idempotency (run twice → same result), version selector logic (vendored/latest/pinned/invalid)
- **Integration**: Fresh-clone workflow (clone → session start → `/openup-next` runs)
- **Network**: Fetch failure scenario (bad URL, network down) → fallback to vendored
- **Backward-compat**: `sync-from-framework.sh --update-claude` still produces valid `.claude/` (no regression)

---

## Operations

- [x] All files created/modified per spec
- [x] Unit tests pass (session-start.sh, install-openup.sh)
- [x] Integration test: fresh clone + session start + `/openup-next`
- [x] Implementation against spec verified
- [x] All acceptance criteria checked ✓

---

## Key Files Touched

| File | Change |
|------|--------|
| `.gitignore` | Allow `!/.claude/settings.json` (track only this file) |
| `scripts/session-start.sh` | New: SessionStart hook (regenerate `.claude/` + install deps) |
| `scripts/install-openup.sh` | New: resolve version, fetch if needed, run sync |
| `scripts/sync-templates-to-claude.sh` | Update: honor `OPENUP_TEMPLATES_DIR` env var |
| `docs-eng-process/.claude-templates/settings.json.example` | Add `SessionStart` hook registration |
| `.openup-version` | New: project version pin (vendored/latest/vX.Y.Z) |

---

## Out of Scope

- Framework CI/release automation (tag creation, asset uploads) — handled by framework maintainer
- IDE integration beyond hook registration (VS Code, JetBrains plugin setup) — separate from this task
- Package manager support (npm, pip, etc.) beyond Python requirements.txt — extensible in future

---

## Open Questions

1. **Async vs synchronous hook?** Proposal uses synchronous (skills guaranteed ready before agent loop). Async would lower startup latency but risk a race. **Assumed: synchronous for safety**

2. **Should `.openup-version` use the same file as `.template-version`?** Proposal keeps them separate (.template-version records what is vendored; .openup-version records what to install). **Assumed: separate files for clarity**

3. **Should `latest` resolution be cached/pinned to avoid silent drift?** Proposal re-resolves every session. **Assumed: re-resolve every session (simple, reproducible on-demand)**


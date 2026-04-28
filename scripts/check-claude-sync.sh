#!/bin/bash
#
# check-claude-sync.sh — verify .claude/ and docs-eng-process/.claude-templates/
# are in sync.
#
# Why this exists: .claude/ is gitignored at the repo root, but the framework
# ships content to other projects via docs-eng-process/.claude-templates/.
# Editing .claude/ alone is a silent-drift footgun — projects updating from
# the framework would never see the change. This script catches divergence
# before it lands in a commit.
#
# Usage:
#   scripts/check-claude-sync.sh             # check, exit 1 on mismatch
#   scripts/check-claude-sync.sh --fix-from-live   # mirror .claude/ -> templates
#   scripts/check-claude-sync.sh --fix-from-templates  # mirror templates -> .claude/

set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LIVE="$ROOT/.claude"
TPL="$ROOT/docs-eng-process/.claude-templates"

MODE="check"
case "${1:-}" in
  --fix-from-live)      MODE="fix-from-live" ;;
  --fix-from-templates) MODE="fix-from-templates" ;;
  --help|-h)
    sed -n '2,18p' "$0" | sed 's/^# \?//'
    exit 0
    ;;
  "") ;;
  *)
    echo "Unknown option: $1" >&2; exit 2 ;;
esac

if [ ! -d "$LIVE" ] || [ ! -d "$TPL" ]; then
  echo "[check-claude-sync] missing $LIVE or $TPL — nothing to check"
  exit 0
fi

# Build the (live, template) path pairs.
# Layout rules:
#   .claude/CLAUDE.openup.md           <-> templates/CLAUDE.md
#   .claude/teammates/X.md             <-> templates/teammates/X.md
#   .claude/rubrics/X.md               <-> templates/rubrics/X.md
#   .claude/skills/openup-{cat}/X/SKILL.md  <-> templates/skills/openup-X/SKILL.md
#       where {cat} ∈ {phases, artifacts, workflow}
#   .claude/skills/openup-X/SKILL.md   <-> templates/skills/openup-X/SKILL.md
#       (top-level prefixed: quick-task, orchestrate, plan-feature, init)

PAIRS=()

add_pair() { PAIRS+=("$1|$2"); }

# CLAUDE.md
[ -f "$LIVE/CLAUDE.openup.md" ] && add_pair "$LIVE/CLAUDE.openup.md" "$TPL/CLAUDE.md"

# Teammates
if [ -d "$LIVE/teammates" ]; then
  for f in "$LIVE/teammates"/*.md; do
    [ -f "$f" ] || continue
    add_pair "$f" "$TPL/teammates/$(basename "$f")"
  done
fi

# Rubrics
if [ -d "$LIVE/rubrics" ]; then
  for f in "$LIVE/rubrics"/*.md; do
    [ -f "$f" ] || continue
    add_pair "$f" "$TPL/rubrics/$(basename "$f")"
  done
fi

# Nested skills (phases, artifacts, workflow)
for cat in openup-phases openup-artifacts openup-workflow; do
  catdir="$LIVE/skills/$cat"
  [ -d "$catdir" ] || continue
  for skilldir in "$catdir"/*/; do
    [ -d "$skilldir" ] || continue
    name=$(basename "$skilldir")
    src="$skilldir/SKILL.md"
    [ -f "$src" ] || continue
    add_pair "$src" "$TPL/skills/openup-$name/SKILL.md"
  done
done

# Top-level prefixed skills
for skilldir in "$LIVE/skills"/openup-*/; do
  [ -d "$skilldir" ] || continue
  parent_name=$(basename "$skilldir")
  # Skip the category dirs handled above
  case "$parent_name" in
    openup-phases|openup-artifacts|openup-workflow) continue ;;
  esac
  src="$skilldir/SKILL.md"
  [ -f "$src" ] || continue
  add_pair "$src" "$TPL/skills/$parent_name/SKILL.md"
done

# Compare
DRIFT=0
DRIFT_LIST=()
ONLY_LIVE=()
ONLY_TPL=()

for pair in "${PAIRS[@]}"; do
  live="${pair%%|*}"
  tpl="${pair##*|}"
  if [ ! -f "$tpl" ]; then
    ONLY_LIVE+=("$live -> (missing) $tpl")
    DRIFT=$((DRIFT+1))
    continue
  fi
  if ! diff -q "$live" "$tpl" >/dev/null 2>&1; then
    DRIFT_LIST+=("$live <-> $tpl")
    DRIFT=$((DRIFT+1))
  fi
done

# Detect template-only files (live missing). Iterate the same template paths.
for pair in "${PAIRS[@]}"; do :; done   # noop, but keeps array referenced
# Walk all template skill dirs and check for ones with no live counterpart
if [ -d "$TPL/skills" ]; then
  for tpldir in "$TPL/skills"/openup-*/; do
    [ -d "$tpldir" ] || continue
    name=$(basename "$tpldir" | sed 's/^openup-//')
    tplfile="$tpldir/SKILL.md"
    [ -f "$tplfile" ] || continue
    found=0
    for cand in \
      "$LIVE/skills/openup-phases/$name/SKILL.md" \
      "$LIVE/skills/openup-artifacts/$name/SKILL.md" \
      "$LIVE/skills/openup-workflow/$name/SKILL.md" \
      "$LIVE/skills/openup-$name/SKILL.md"; do
      [ -f "$cand" ] && { found=1; break; }
    done
    if [ "$found" -eq 0 ]; then
      ONLY_TPL+=("(missing live) $tplfile")
      DRIFT=$((DRIFT+1))
    fi
  done
fi

# Report
if [ "$DRIFT" -eq 0 ]; then
  echo "[check-claude-sync] ✓ .claude/ and .claude-templates/ in sync ($((${#PAIRS[@]})) files compared)"
  exit 0
fi

if [ "$MODE" = "fix-from-live" ]; then
  echo "[check-claude-sync] mirroring .claude/ -> .claude-templates/ ..."
  for pair in "${PAIRS[@]}"; do
    live="${pair%%|*}"; tpl="${pair##*|}"
    if [ -f "$live" ]; then
      mkdir -p "$(dirname "$tpl")"
      cp "$live" "$tpl"
    fi
  done
  echo "[check-claude-sync] done. Re-run without flags to verify."
  exit 0
fi

if [ "$MODE" = "fix-from-templates" ]; then
  echo "[check-claude-sync] mirroring .claude-templates/ -> .claude/ ..."
  for pair in "${PAIRS[@]}"; do
    live="${pair%%|*}"; tpl="${pair##*|}"
    if [ -f "$tpl" ]; then
      mkdir -p "$(dirname "$live")"
      cp "$tpl" "$live"
    fi
  done
  echo "[check-claude-sync] done. Re-run without flags to verify."
  exit 0
fi

echo "[check-claude-sync] ✗ .claude/ and .claude-templates/ have drifted ($DRIFT issue(s))" >&2
echo "" >&2
if [ "${#DRIFT_LIST[@]}" -gt 0 ]; then
  echo "Differing files:" >&2
  printf '  %s\n' "${DRIFT_LIST[@]}" >&2
fi
if [ "${#ONLY_LIVE[@]}" -gt 0 ]; then
  echo "" >&2
  echo "In .claude/ but missing from templates:" >&2
  printf '  %s\n' "${ONLY_LIVE[@]}" >&2
fi
if [ "${#ONLY_TPL[@]}" -gt 0 ]; then
  echo "" >&2
  echo "In templates but missing from .claude/:" >&2
  printf '  %s\n' "${ONLY_TPL[@]}" >&2
fi
echo "" >&2
echo "Fix one of:" >&2
echo "  scripts/check-claude-sync.sh --fix-from-live      # if .claude/ is canonical" >&2
echo "  scripts/check-claude-sync.sh --fix-from-templates # if templates are canonical" >&2
exit 1

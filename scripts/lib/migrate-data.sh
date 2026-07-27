#!/usr/bin/env bash
# migrate-data.sh — one-time, idempotent data migrations applied by
# sync-from-framework.sh when a project adopts a framework update. Each function
# acts ONLY when migration is needed and never commits (the user commits, like
# the rest of the sync). Sourced by the sync script and by the test suite.

# T-047: carry T-046's migration. agent-runs.jsonl became a gitignored DERIVED
# view (run events now shard to docs/agent-logs/runs/*.jsonl). A project that
# still TRACKS the old shared file keeps hitting the GitHub PR conflicts T-046
# fixed, so untrack it. Idempotent — acts only when tracked; stages, never
# commits. Args: <project_root> <dry_run:true|false>.
migrate_untrack_agent_runs() {
  local root="$1" dry="$2"
  local rel="docs/agent-logs/agent-runs.jsonl"
  if ! git -C "$root" ls-files --error-unmatch "$rel" >/dev/null 2>&1; then
    return 0  # absent or already untracked → clean no-op
  fi
  if [ "$dry" = true ]; then
    echo "[DRY RUN] Would untrack $rel (git rm --cached) and add it to .gitignore"
    return 0
  fi
  local gi="$root/.gitignore"
  if ! grep -qxF "$rel" "$gi" 2>/dev/null; then
    printf '\n# T-046: derived run-log consolidation (source = docs/agent-logs/runs/*.jsonl)\n%s\n' "$rel" >> "$gi"
  fi
  git -C "$root" rm --cached --quiet "$rel" >/dev/null 2>&1 || true
  return 0
}

# T-155: give the two INVOLUNTARILY shared .claude/memory/ append-only files
# `merge=union` in the consumer's .gitattributes. bootstrap-project.sh copies
# .gitattributes, but ONLY at initial bootstrap — so without this the attribute
# reaches new projects only, and never the existing ones where the collision
# actually occurs (which is the whole point).
#
# APPENDS, never overwrites: a consumer's own attributes must survive. Idempotent
# per entry — matches on the PATH, not the whole line, so a consumer that wrote
# its own variant is left alone rather than duplicated. Creates the file when the
# project has none. Never commits (the user commits, like the rest of the sync).
#
# Mitigation, not a fix: git runs merge drivers LOCALLY only — GitHub does not
# run them server-side, so a PR that conflicts on these files still conflicts.
# Args: <project_root> <dry_run:true|false>. Echoes one line per action taken.
migrate_gitattributes_merge_union() {
  local root="$1" dry="$2"
  local ga="$root/.gitattributes"
  local added=0 path
  for path in ".claude/memory/bypass-log.md" ".claude/memory/iteration-learnings.md"; do
    if [ -f "$ga" ] && grep -qF "$path" "$ga" 2>/dev/null; then
      continue  # already covered → clean no-op
    fi
    if [ "$dry" = true ]; then
      echo "[DRY RUN] Would add '$path merge=union' to .gitattributes"
      continue
    fi
    if [ ! -f "$ga" ]; then
      {
        printf '# OpenUP: merge behavior for shared append-only files (T-155).\n'
        printf '# Reduces LOCAL merge conflicts only — GitHub does not run merge\n'
        printf '# drivers server-side, so PR conflicts on these files remain.\n'
      } > "$ga"
    fi
    printf '%s merge=union\n' "$path" >> "$ga"
    added=$((added + 1))
  done
  [ "$added" -gt 0 ] && echo "Patched .gitattributes: merge=union for $added shared .claude/memory/ file(s)"
  return 0
}

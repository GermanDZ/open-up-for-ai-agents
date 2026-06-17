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

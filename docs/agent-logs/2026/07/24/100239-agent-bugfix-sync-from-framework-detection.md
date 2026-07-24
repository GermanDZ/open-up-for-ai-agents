# Agent Run — T-126 sync-from-framework detection fix

- **Task:** T-126 — sync-from-framework.sh false "framework repository itself" abort in consumers
- **Branch:** bugfix/sync-from-framework-detection
- **Track:** quick
- **Phase:** construction
- **End:** 2026-07-24T10:02:39Z

## Commits
- bbfa984 fix(sync): detect framework by sync-templates-to-claude.sh, not template tree [T-126]
- ee1422b chore(process): sweep hook-managed logs [openup-skip]
- 6706b09 chore(process): archive quick-task state for T-126 [openup-skip]

## Files changed
- scripts/sync-from-framework.sh — self-detection guard + auto-detect probe key on scripts/sync-templates-to-claude.sh (framework-only) instead of docs-eng-process/.claude-templates/ (present in consumers too)
- scripts/tests/test_sync_from_framework_detection.py — 3 hermetic regression tests

## Decisions
- Framework identity marker must be a framework-ONLY artifact; the .claude-templates/ mirror is distributed to consumers so it can never be the marker.
- Verified fix by copying the script into the consuming project (kaze-webapp) and running a dry-run: auto-detects framework and proceeds instead of aborting.

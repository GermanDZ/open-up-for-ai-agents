# T-057 Design Notes

## Implementation Verification (1a)

All 8 requirements ✅ against the diff (`git diff main...HEAD`):

- R1 ✅ on-task-request.py: both `sys.exit(2)` → `sys.exit(0)` — `.claude-templates/scripts/hooks/on-task-request.py` lines 185, 202
- R2 ✅ stderr messages still emitted — print() statements unchanged; test_t010_tracks assertions confirm
- R3 ✅ gate-edits.py: `"docs/iteration-plans/"` added to EXEMPT_PREFIXES — test_allows_iteration_plans_without_state passes
- R4 ✅ gate-edits.py: `"docs/roadmap.md"` added to EXEMPT_PREFIXES — test_allows_roadmap_without_state passes
- R5 ✅ complete-task Step 9 added: `gh pr merge --merge --delete-branch` + `git pull origin main`
- R6 ✅ auto_merge: false skip condition present in Step 9
- R7 ✅ fail-open branch present in Step 9 (logs PR URL + manual steps on non-zero exit)
- R8 ✅ parity: check-claude-sync.sh ✓ at commit (65 files)

## Success Measure (1b)

n/a — internal process tooling. Observed behavior in next downstream session. No instrumentation to verify.

## Assumptions Confirmed

- Merge commit (--merge, not --squash): confirmed per user direction
- Auto-merge default-on: retained
- Active-iteration branch of on-task-request also exit 0: implemented

## Key Decision

Step 9 executes in the main repo context (after step 7b removed the worktree). Used `git pull origin main` (no `git checkout main`) because the main repo is already on main at that point.

## Test Coverage

287 tests run, 1 pre-existing macOS symlink failure (test_docs_index — /var vs /private/var). 0 regressions. +7 changed/added tests for T-057.

## Sync Check Approach

Worktree's .claude/ populated via `sync-templates-to-claude.sh` before commit. check-claude-sync.sh passed in worktree (65 files compared). Live main repo .claude/ files were gate-blocked (no active iteration in main repo); they will sync on next session start after merge.

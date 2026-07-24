# Agent Run — T-125 on-stop bypass-log exemption

- **Task:** T-125 — on-stop.py infinite-commit-loop on tracked .claude/memory/bypass-log.md
- **Branch:** bugfix/on-stop-bypass-log-exempt
- **Track:** quick
- **Phase:** construction
- **End:** 2026-07-24T10:04:56Z

## Commits (rebased onto harness-optional after T-126)
- fix(on-stop): exempt .claude/memory/bypass-log.md from dirty-block [T-125]
- fix(on-stop): shell-quote swept paths, add -- guard [T-125] (security review follow-up)

## Files changed
- docs-eng-process/.claude-templates/scripts/hooks/on-stop.py — add .claude/memory/bypass-log.md to EXEMPT_DIRTY_PREFIXES; generalize the sweep-commit to git-add whichever exempt paths are dirty; shlex.quote each path + '--' guard against a crafted filename.
- scripts/tests/test_t006_hooks.py — 2 new tests (bypass-log exempt does not block; feature-branch sweep folds bypass-log too); updated sweep-message assertion.

## Decisions
- Any hook-managed tracked file that lags HEAD by one append (writes a record naming the commit that just happened) must be exempt from on-stop's dirty-block, matching the run-log shard fix; else on-stop tail-chases forever on projects that track it.
- Root cause confirmed via kaze-webapp (read-only sibling), which tracks bypass-log.md; this dev repo gitignores all of .claude/ so the gap was invisible here.

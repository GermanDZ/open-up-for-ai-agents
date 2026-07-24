# Agent Run Log: T-121 Tool Bug Sweep

**Branch:** feat/T-121-tool-bug-sweep  
**Task:** T-121 — Cycle-engine + tool bug sweep (B1, B2, B4–B7; B3 deferred)  
**Phase:** construction  
**Track:** standard (solo, worktree)  
**Session:** 2026-07-16T12:51:28Z → 2026-07-16T13:10:58Z

## Commits

- 4d04474 chore(T-121): record session_begin in run log
- 3748da3 docs(T-121): defer B3 (prose-safe classification) — match-anywhere is a tested contract
- b655127 fix(engine): tool + cycle bug sweep B1,B2,B4-B7
- c4ea045 chore(T-121): fold run-log shard
- a34090f docs(T-121): completion verification — 6/6 requirements graded
- e42c6c9 docs(T-121): sync roadmap + project status; iteration note

## Files Changed

- scripts/openup_agent/tools.py
- scripts/openup_agent/cycle.py
- scripts/tests/test_openup_agent_tools.py
- scripts/tests/test_openup_agent_cycle.py
- docs-eng-process/reference-driver.md
- docs/changes/T-121/plan.md
- docs/changes/T-121/design.md
- docs/roadmap.md
- docs/project-status.md
- docs/status-notes/2026-07-16-T-121.md

## Decisions

**B3 (Prose-safe box classification) — Deferred**  
Scope narrowed via fix-spec-first: `classify_box`'s match-anywhere behavior is an intended, explicitly-tested contract (`test_backticked_git_command_is_script` asserts a mid-prose command is a script step). Distinguishing run-intent from mention-intent is not mechanically possible; the `(judgment)` marker is the escape hatch. Making it prose-safe is a contract change, not a bug fix.

**B1 (grep performance)**  
grep prunes a default ignore set (.git, node_modules, vendor, build, tmp, log, storage, ...) from the tree walk and skips files > 1MB.

**B2 (exec cwd robustness)**  
exec cwd `_resolve` wrapped to return an ERROR string; dispatch also catches ToolError. No uncaught driver crash.

**B4 (parse_boxes classification)**  
parse_boxes retains a wrapped box's continuation lines in the body; extract_command reads only the FIRST line, so a continuation can't flip a judgment box to script and single-line boxes classify identically.

**B5 (complete merge conflict handling)**  
complete() merge-fail aborts the merge, checks out the branch, records pending_merge in .openup/cycle.json, returns EXIT_STEP; _retry_pending_merge runs in the recovery pre-pass (before resolve) and clears the marker on a successful retry.

**B6/B7 (truncation markers)**  
read_file whole-file truncation marker names the path; exec caps each stdout/stderr with a marker while preserving the exit= line.

## Result

- 15 new tests added (8 tools, 3 B4-classification, 4 B5-merge)
- Full suite: 649 passed
- Gates: green (check-docs, spec-scenarios 6/6 Given/When/Then, fence clean base harness-optional)
- All 6 requirements graded against the diff (see design.md)
- Success measures: n/a (internal correctness sweep; tests are the falsifiable check)

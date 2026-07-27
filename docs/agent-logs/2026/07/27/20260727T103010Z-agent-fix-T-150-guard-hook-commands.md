# Agent Run — T-150 (fix/T-150-guard-hook-commands)

- **Task**: T-150 — guard hook commands so a missing script cannot lock Bash and Write
- **Branch**: fix/T-150-guard-hook-commands · **Phase**: construction · **Iteration**: 99 · **Track**: standard (solo)
- **Start**: 2026-07-27T10:15:53Z  **End**: 2026-07-27T10:30:10Z

## Commits
- 3e91e08 docs(T-150): design decisions, verification grades, status note [T-150]
- 524aa34 fix(hooks): guard every hook command so a missing script cannot lock the repo [T-150]
- 8ef0167 docs(T-150): promote lane — author spec, board-visible [T-150]

## Files changed
- .claude/settings.json
- docs-eng-process/.claude-templates/settings.json.example
- docs-eng-process/conventions.md
- docs/agent-logs/runs/2026-07-27-T-150.jsonl
- docs/changes/T-150/design.md
- docs/changes/T-150/plan.md
- docs/status-notes/2026-07-27-T-150.md
- scripts/tests/test_hook_command_guards.py

## Decisions
- Root cause measured: python3 exits 2 on a missing file, the same code the harness reads as 'block'.
- Guard form 'if [ -f X ]; then interp X; fi' — absent=0, present=propagates status (keeps the five exit-2 gates).
- Rejected '|| true' (disarms every gate), '[ -f ] &&' (returns 1), tracked .claude/scripts/ and a run-hook.sh shim (both depend on another file existing).
- Fix is inert in its own session (harness reads main's .claude/) — verified by executing the shipped command strings directly.

## Verification
- 12 new tests; full suite 939 passed / 1 skipped / 0 failed (main baseline 928).
- Live: missing->0 silent; unguarded form reproduces the bug at rc=2; blocking hook still returns 2 through the guard.
- fence (--base origin/main) 0; check-docs 0; spec-scenarios 6/6; check-claude-sync green.

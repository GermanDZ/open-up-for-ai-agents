---
id: T-040
title: "Fix hook-test HOOKS_DIR stale path: tests point at .claude/scripts/hooks/ which no longer exists"
status: done
track: quick
priority: medium
depends-on: []
blocks: []
touches: [scripts/tests/test_t006_hooks.py, scripts/tests/test_t010_tracks.py]
claimed-by: null
---

# T-040 — Fix hook-test HOOKS_DIR stale path

## Context

Surfaced 2026-06-15 while running the full test suite during T-034…T-036 delivery.
25 tests fail and 3 error out across two files:

- `scripts/tests/test_t006_hooks.py` — 3 ERRORs + 14 FAILs
- `scripts/tests/test_t010_tracks.py` — 8 FAILs

All 28 break for the same root cause: both test files set

```python
HOOKS_DIR = REPO_ROOT / ".claude" / "scripts" / "hooks"
```

but the hooks were moved to
`docs-eng-process/.claude-templates/scripts/hooks/` in **T-022** (commit
`8e0b847`, PR #17, 2026-06-12). `.claude/scripts/hooks/` no longer exists.
The tests try to `subprocess.run` each hook from the stale path and get
`FileNotFoundError`, causing every assertion about hook behaviour to fail
immediately.

**Confirmed fix**: changing both `HOOKS_DIR` declarations to

```python
HOOKS_DIR = REPO_ROOT / "docs-eng-process" / ".claude-templates" / "scripts" / "hooks"
```

makes all 41 tests in the two files pass (verified locally by monkey-patching the
path and running the suite).

The 3 `AutoLogCommitTests` ERRORs (`agent-runs.jsonl` not found) are secondary:
the hook never runs because the path is wrong, so `docs/agent-logs/agent-runs.jsonl`
is never created, and a later assertion that tries to read it raises
`FileNotFoundError`. They resolve automatically once the path is fixed.

## Bug index

| File | Test class | Count | Symptom |
|---|---|---|---|
| `test_t006_hooks.py` | `AutoLogCommitTests` | 3 ERRORs + 2 FAILs | `FileNotFoundError` running hook; missing `agent-runs.jsonl` |
| `test_t006_hooks.py` | `OnStopTests` | 6 FAILs | Hook not found; assertions on stderr never reached |
| `test_t006_hooks.py` | `GateEditsTests` | 5 FAILs | Same |
| `test_t006_hooks.py` | `ValidateCommitTests` | 3 FAILs | Same |
| `test_t010_tracks.py` | `ActiveIterationTests` | 2 FAILs | `on-task-request.py` not found at stale path |
| `test_t010_tracks.py` | `NoActiveIterationTests` | 3 FAILs | Same |
| `test_t010_tracks.py` | `ExitCodeTests` | 2 FAILs | Same |
| `test_t010_tracks.py` | `SkillInvocationSkipTests` | 1 FAIL | Same |

## Requirements

1. `test_t006_hooks.py`: `HOOKS_DIR` resolves to
   `docs-eng-process/.claude-templates/scripts/hooks/`. All 17 tests pass.
2. `test_t010_tracks.py`: `HOOKS_DIR` (and the derived `HOOK` path for
   `on-task-request.py`) resolves to the same directory. All 8 tests pass.
3. The full suite (`python3 -m unittest discover -s scripts/tests -p 'test_*.py'`)
   shows no regressions — i.e. the pre-existing non-hook test count stays at
   172 tests passing (the baseline before this fix).
4. The fix is path-only. Hook script files are not modified.

## Approach

Two one-line changes, one per test file:

```python
# scripts/tests/test_t006_hooks.py  line ~26
HOOKS_DIR = REPO_ROOT / "docs-eng-process" / ".claude-templates" / "scripts" / "hooks"

# scripts/tests/test_t010_tracks.py  line ~25
HOOKS_DIR = REPO_ROOT / "docs-eng-process" / ".claude-templates" / "scripts" / "hooks"
```

No other changes needed; the `HOOK` variable in `test_t010_tracks.py` is derived
from `HOOKS_DIR` so it resolves automatically.

## Structure

- `scripts/tests/test_t006_hooks.py` — change `HOOKS_DIR` line
- `scripts/tests/test_t010_tracks.py` — change `HOOKS_DIR` line

## Operations

1. Edit `HOOKS_DIR` in both files (two one-line edits).
2. Run `python3 -m unittest scripts.tests.test_t006_hooks scripts.tests.test_t010_tracks`
   — expect all 41 tests to pass.
3. Run the full suite — confirm total test count increases from 172 to 193 passing
   and error/failure count drops to 0 for the affected files.
4. Commit with message `fix(tests): update HOOKS_DIR to current template path [T-040]`.

## Norms

- See `docs-eng-process/conventions.md` — test files are under `scripts/tests/`,
  one file per tested script.

## Safeguards

- Only test files change; no production script, hook, or template is touched.
- No hook scripts are moved or renamed — only the path the tests use to find them.

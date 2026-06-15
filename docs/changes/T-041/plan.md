---
id: T-041
title: "OpenUP audit remediation: 8 fixes surfaced by the es-invoices session/log audit"
status: in-progress
track: standard
priority: high
depends-on: []
blocks: []
touches: [scripts/openup-state.py, scripts/setup-agent-teams.sh, scripts/bootstrap-project.sh, scripts/README.md, scripts/tests/test_openup_state.py, scripts/tests/test_t006_hooks.py, scripts/tests/test_t010_tracks.py, docs-eng-process/script-cli-reference.md, docs-eng-process/.claude-templates]
claimed-by: null
---

# T-041 — OpenUP audit remediation (8 fixes)

## Context

An audit of the `es-invoices` project (agent logs under `docs/agent-logs/` plus
12 Claude session transcripts in `~/.claude/projects/…-es-invoices/`) was run to
check whether the OpenUP process, skills, and scripts behave as intended. The
guardrails held — enforcement hooks blocked the right things, deterministic
scripts ran without tracebacks, and there were no real process bypasses — but the
audit surfaced eight defects, the most serious being **fabricated timestamps in
the traceability log** (the audit trail the process exists to produce). All eight
are framework-level, so fixing them here propagates to every project bootstrapped
from the template. Full investigation evidence is in
[design.md](./design.md) and the program plan
[docs/plans/2026-06-15-openup-audit-remediation.md](../../plans/2026-06-15-openup-audit-remediation.md).

Two facts shaped how this iteration runs (both are themselves findings):
- It runs **in-place (`worktree: false`)** because the default worktree path
  triggers Fix 7 — the very bug under repair.
- Several touched files are **live + template pairs** (`.claude/…` and
  `docs-eng-process/.claude-templates/…`); every hook/skill edit must be mirrored
  to keep `.claude ↔ .claude-templates` parity green.

## Requirements

1. **Script-stamped event timestamps.** `scripts/openup-state.py` gains a
   `log-event` subcommand that appends one record to
   `docs/agent-logs/agent-runs.jsonl` with `ts` stamped from the system clock; the
   model never supplies a timestamp.
   - **Given** an active iteration, **When** a skill runs
     `openup-state.py log-event --event iteration_start --task-id T-041 …`,
     **Then** a JSONL line is appended whose `ts` is a real UTC ISO-8601 value
     (format `%Y-%m-%dT%H:%M:%SZ`) produced by `datetime.now(timezone.utc)`.
   - **Given** two `log-event` calls in sequence, **When** their records are read
     back, **Then** the second `ts` is `>=` the first (monotonic, non-fabricated).

2. **Skills stop hand-authoring timestamps.** `openup-start-iteration`,
   `openup-complete-task`, and `openup-log-run` brief the JSONL append via
   `log-event` and source the run-log `.md` Start/End from script-stamped values
   (`state.json.started_at` + `log-event` output), not `[ts]` placeholders.
   - **Given** the updated skills, **When** their SKILL.md is searched for the
     `agent-runs.jsonl` append, **Then** it calls `openup-state.py log-event`
     and contains no `\"ts\":\"[ts]\"` placeholder instruction.

3. **Agents installed into projects.** `scripts/setup-agent-teams.sh` copies
   `.claude-templates/agents/` into the project's `.claude/agents/`.
   - **Given** a project dir with no `.claude/agents/`, **When**
     `setup-agent-teams.sh` runs, **Then** `.claude/agents/openup-scribe.md` and
     `.claude/agents/openup-explorer.md` exist afterward.

4. **Spine artifacts excluded from quick track.** `on-task-request.py`'s
   `suggest_track()` returns `standard` (or `full`) for vision / risk-list /
   use-case / architecture / test-plan tasks, even when a quick signal matches.
   - **Given** the prompt "Fill the Vision document", **When** `suggest_track` is
     called, **Then** it returns `"standard"` (not `"quick"`).
   - **Given** the prompt "fix typo in readme", **When** `suggest_track` is
     called, **Then** it still returns `"quick"` (no regression).

5. **`/openup-next` empty-board guidance.** When the board is empty but pending
   roadmap rows exist without a `docs/changes/` folder, the exit-3 message names
   the gap and points to `/openup-create-task-spec`.
   - **Given** pending roadmap rows and an empty `docs/changes/`, **When**
     `/openup-next` hits exit 3, **Then** its printed reason recommends running
     `/openup-create-task-spec <id>` to seed a lane, while staying a no-op.

6. **CLI reference exists and is linked.** A new
   `docs-eng-process/script-cli-reference.md` documents subcommands/args for the
   key scripts and is linked from `scripts/README.md` and `.claude/CLAUDE.openup.md`.
   - **Given** the reference, **When** any documented invocation is run with
     `--help`, **Then** the command and its args match the live script.

7. **Worktree-aware edit gate.** `gate-edits.py` resolves `.openup/state.json`
   from the **edit target's** worktree root, not the harness cwd.
   - **Given** an active iteration whose state lives in worktree `W` while the
     harness cwd is the main repo, **When** an Edit targets a file inside `W`,
     **Then** the gate reads `W/.openup/state.json` and allows the edit.

8. **Plan-mode plan files exempt.** `gate-edits.py` treats the plan-mode plan
   directory as a process-state path.
   - **Given** no active iteration, **When** a Write targets the plan-mode plan
     file, **Then** the gate allows it (exit 0), like other process-state paths.

9. **No regressions.** The full suite
   (`python3 -m unittest discover -s scripts/tests -p 'test_*.py'`) passes, and
   `.claude ↔ .claude-templates` parity is green.

## Behavior Delta

- **Added**: `openup-state.py log-event` subcommand; `docs-eng-process/script-cli-reference.md`; a `SPINE_RE` branch in `on-task-request.py`; plan-mode-plan exemption in `gate-edits.py`.
- **Modified**: `gate-edits.py` state resolution (cwd → target worktree root); three skills' timestamp briefs; `setup-agent-teams.sh` copy set (+agents); `openup-next` exit-3 message; `bootstrap-project.sh` commit message; `scripts/README.md` + `CLAUDE.openup.md` (link the new reference). Each cites the audit findings above; no Ring-1 product artifact changes.
- **Removed**: model-authored `[ts]` placeholder instructions in the three skills.

## Operations

- [x] Fix 1 — `openup-state.py log-event` subcommand (+ 3 unit tests, smoke-tested)
- [x] Fix 2 — `setup-agent-teams.sh` copies `agents/` (verified end-to-end into a temp project)
- [x] Fix 3 — `on-task-request.py` spine-artifact track exclusion (+ 2 tests; both hook copies)
- [x] Fix 7 — `gate-edits.py` worktree-aware state resolution (+ test; both hook copies)
- [x] Fix 8 — `gate-edits.py` plan-mode-plan exemption (+ test; both hook copies)
- [x] Fix 4 — `openup-next` empty-board + end-of-phase guidance (synced stale live copy ← richer template)
- [x] Fix 5 — `script-cli-reference.md` + links from README & CLAUDE.openup.md (both copies)
- [x] Fix 6 — `bootstrap-project.sh` canonical commit message
- [x] Fix 1 skills (start-iteration, complete-task, log-run) rewired + mirrored to templates
- [x] Full test suite: 233 pass / 1 pre-existing env failure (docs-index `/private`-symlink); all new tests green
- [ ] `check-claude-sync`: pre-existing red (34 drifts, none mine) — see design.md DD5; out of scope

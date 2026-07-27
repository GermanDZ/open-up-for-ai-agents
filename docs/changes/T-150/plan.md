---
id: T-150
title: "A merged settings.json referencing a not-yet-synced hook script locks both Bash and Write"
status: ready
priority: critical
estimate: 0.5 session
plan: ""
depends-on: []
blocks: []
last-synced: ""
touches:
  - .claude/settings.json
  - docs-eng-process/.claude-templates/settings.json.example
  - scripts/tests/test_hook_command_guards.py
  - docs-eng-process/conventions.md
  - docs/roadmap.md
---

# T-150 — A merged `settings.json` referencing a not-yet-synced hook script locks both Bash and Write

## Story

> **As** anyone who merges a change that adds an OpenUP hook
> **I want** a hook command whose script is not on disk to be a silent no-op
> **So that** the window between "settings merged" and "templates synced" cannot leave the
> repo with no working tool call and no way to recover from inside the session.

INVEST check:
✅ Independent · ✅ Negotiable (guard shape is a choice; the invariant is not) ·
✅ Valuable (removes the only known total-lockout) · ✅ Estimable (11 command strings + a test) ·
✅ Small (half a session) · ✅ Testable (a settings file naming a missing script must not block).

## Analysis Context

- **Domain.** Hook wiring: the 11 `hooks[].command` strings in `.claude/settings.json` and
  its template `docs-eng-process/.claude-templates/settings.json.example`.
- **Scope boundaries.** Does NOT change what any hook *does*, which events they bind to,
  their order, or `sync-templates-to-claude.sh`. Does NOT make `.claude/scripts/` tracked
  (rejected below). Does NOT touch `scripts/session-start.sh`'s contents.
- **Definition of done.** A `settings.json` naming a hook script that does not exist on
  disk leaves every tool call working; a hook script that *does* exist behaves exactly as
  today, **including its blocking exit code**.

**How the lockout happens (observed live 2026-07-27, merging T-140 / PR #94).**
`.claude/settings.json` is tracked, so it merges instantly and immediately references
`stage-run-log.py`. `.claude/scripts/hooks/*` is gitignored and only materializes when
`sync-templates-to-claude.sh` runs. In that window:
- every **Bash** call died with `python3: can't open file .../stage-run-log.py`, and
- **Write** was independently blocked by `gate-edits` (no active iteration after completion).

Both recovery routes were shut simultaneously and the owner had to run the sync from their
own shell. This is not specific to T-140 — **any** future hook addition reproduces it.

**The constraint that rules out the obvious guard.** Five of the 11 hooks
(`gate-edits.py`, `on-task-request.py`, `validate-commit.py`, `on-stop.py`,
`check-unfinished-tasks.py`) deliberately `sys.exit(2)` to *block* a tool call — that is
the entire enforcement mechanism. A guard of the form `python3 X || true` would swallow
those exit codes and silently disable every gate in the framework. The guard must make a
**missing** script a no-op while leaving a **present** script's exit code fully intact.

> **Assumption:** guard each command inline as `if [ -f <path> ]; then python3 <path>; fi`
> rather than tracking `.claude/scripts/`. `if`/`fi` returns 0 when the condition is false
> and otherwise propagates the body's exit status, which is exactly the required semantics.
> Chosen over `[ -f X ] && python3 X` (returns 1 when absent, still an error) and over
> `... || true` (destroys the blocking contract). *(Vetoable at review.)*

> **Assumption:** rejected the alternative "track the hook scripts so they merge atomically
> with `settings.json`". It would work here, but the fix would then depend on *another* file
> being present — the exact failure class being removed — and it would duplicate the pack
> (`.claude/` is generated from `.claude-templates/`, and `check-claude-sync.sh` enforces
> that they match). *(Vetoable at review.)*

> **Assumption:** rejected a shared shim (`scripts/run-hook.sh <name>`) for the same reason:
> it trades 11 verbose commands for a single point of failure that must itself exist.
> Verbosity in `settings.json` is the acceptable cost of a self-sufficient guard.
> *(Vetoable at review.)*

## Requirements

1. A hook command whose script is absent is a silent no-op and blocks nothing.
   - **Given** `settings.json` binds `PreToolUse`/Bash to a hook script that does not exist
     on disk, **When** any Bash command runs, **Then** the hook command exits `0`, prints
     nothing to stderr, and the tool call proceeds.

2. A hook script that exists keeps its exit code, including the blocking `2`.
   - **Given** a guarded command pointing at a script that exits `2`, **When** the command
     runs, **Then** the guarded command's exit status is `2` (the gate still blocks).

3. A hook script that exists and succeeds still runs its side effects.
   - **Given** a guarded command pointing at a script that writes a file and exits `0`,
     **When** the command runs, **Then** the file is written and the status is `0`.

4. Hooks still receive their JSON payload on stdin through the guard.
   - **Given** a guarded command whose script echoes its stdin, **When** a payload is piped
     to it, **Then** the script receives the payload byte-for-byte.

5. Every hook entry in both settings files is guarded — no unguarded command remains.
   - **Given** `.claude/settings.json` and `settings.json.example`, **When** every
     `hooks[].command` is inspected, **Then** each one is guarded, and the two files remain
     byte-identical to each other.

6. The guard never uses a form that suppresses a non-zero exit.
   - **Given** any hook command string, **When** it is inspected, **Then** it contains no
     `|| true`, `|| :`, or `; true` suffix that would mask a blocking exit code.

## Behavior Delta

**Added** — behavior that did not exist before:
- A missing hook script is tolerated as a no-op instead of erroring.

**Modified** — behavior that changes:
- Hook invocation form — `.claude/settings.json` §`hooks` and
  `docs-eng-process/.claude-templates/settings.json.example` §`hooks` (11 command strings
  gain an existence guard). No hook's own logic, binding, or ordering changes.
- Hook-wiring convention — `docs-eng-process/conventions.md` gains the rule that a hook
  command must be guarded and must never suppress its exit code.

**Removed** — behavior that no longer holds:
- The hard interpreter error on a missing hook script. No Ring-1 product artifact describes
  it; it was emergent behavior of an unguarded command string.

## Entities

- **Hook wiring** (modified) — `.claude/settings.json` → `hooks{PreToolUse,PostToolUse,Stop,UserPromptSubmit,SessionStart}`
- **Hook wiring template** (modified) — `docs-eng-process/.claude-templates/settings.json.example`
- **Blocking hooks** (read-only, must keep working) — `gate-edits.py`, `on-task-request.py`, `validate-commit.py`, `on-stop.py`, `check-unfinished-tasks.py`
- **Sync check** (read-only) — `scripts/check-claude-sync.sh` (keeps the two settings files identical)
- **Guard test** (new) — `scripts/tests/test_hook_command_guards.py`

## Approach

Wrap each `hooks[].command` in a shell existence test — `if [ -f <path> ]; then <interpreter>
<path>; fi` — so the command is well-defined whether or not the script is on disk. `if`/`fi`
is chosen precisely for its exit semantics: false condition yields `0`, true condition yields
the body's status, so the five blocking hooks keep the `exit 2` contract that makes them
gates. The guard is inline and self-sufficient: it depends on no file existing, which is the
whole point. A test then holds the invariant structurally (every command guarded, no
exit-suppressing form, both settings files identical) and behaviourally (missing → 0,
present-and-blocking → 2, stdin passes through).

## Structure

**Add:**
- `scripts/tests/test_hook_command_guards.py` — structural checks over both settings files
  plus behavioural checks of the guard form against throwaway scripts.

**Modify:**
- `.claude/settings.json` — guard all 11 `hooks[].command` strings.
- `docs-eng-process/.claude-templates/settings.json.example` — identical change.
- `docs-eng-process/conventions.md` — record the hook-command convention and why
  `|| true` is forbidden.
- `docs/roadmap.md` — status row for T-150.

**Do not touch:**
- `.claude/scripts/hooks/*.py` — the scripts are fine; the wiring is the defect.
- `.gitignore` — tracking `.claude/scripts/` is the rejected alternative.
- `scripts/sync-templates-to-claude.sh` — the sync is not at fault; the window it leaves is.
- `scripts/check-claude-sync.sh` — must keep passing, unchanged.

## Operations

- [x] Add the existence guard to all 11 `hooks[].command` strings in `.claude/settings.json`,
      preserving each interpreter (`python3` / `bash`) and argument list exactly.
- [x] Apply the identical change to `docs-eng-process/.claude-templates/settings.json.example`
      and confirm `scripts/check-claude-sync.sh` still reports the two in sync.
- [x] Add `scripts/tests/test_hook_command_guards.py` covering: every command guarded, no
      exit-suppressing form, the two files identical, and the guard's behaviour
      (missing → 0, present → propagates 2, stdin passthrough).
- [x] Record the hook-command convention in `docs-eng-process/conventions.md`, naming the
      `|| true` hazard and the five blocking hooks it would disable.
- [x] (tester) Verify live in this session: point a guarded command at a deliberately
      absent path and confirm a Bash call still runs; confirm `gate-edits` still blocks a
      source edit with no active iteration.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, hook conventions
- `.claude/CLAUDE.openup.md` — token-efficiency protocol, legal exits
- `docs-eng-process/parallel-lanes.md` — lane-owned surfaces and the write-fence

## Safeguards

- **The blocking contract is inviolable.** All five `exit 2` hooks must still block after
  this change; a guard that masks their status is a failed implementation, not a trade-off.
- **stdin must reach the script.** Every hook reads its JSON payload from stdin; the guard
  must not consume or reorder it.
- **The two settings files stay byte-identical** — `check-claude-sync.sh` enforces it and
  must keep passing.
- **Reversibility.** The change is confined to command strings in two JSON files; reverting
  restores the previous behaviour exactly.
- **No-go zones.** Hook script contents, event bindings, hook ordering, `.gitignore`.
- **Token / size budget.** Test file ≤ ~140 lines.

## Success Measures

We expect **the number of sessions in which a hook-wiring change makes tool calls
unusable** to move **from 1 (observed 2026-07-27) to 0** within **the next 3 merges that
touch `settings.json` or `.claude/scripts/hooks/`**. Instrumentation: the guard test
(`scripts/tests/test_hook_command_guards.py`) fails the build if any command is unguarded,
so the invariant is checked on every run rather than observed after the fact; plus the
manual post-merge check "delete a hook script, run a Bash command, confirm it succeeds".
Read-back: after the third such merge, or at the next retrospective, whichever is first.
The instrumentation lives in this repo, which is where the read-back happens (T-152).

## Rollout

**Flagged? No.** Hook commands are read fresh from `settings.json` on each tool call;
the kill switch is reverting two JSON files, which is faster and safer than any flag read,
and a flag would itself have to be evaluated by the very mechanism being repaired.
Not user-facing (agent tooling), so `n/a` for environment defaults and in-flight users —
no user state exists to strand.

## Verification

- `python3 -m pytest scripts/tests/test_hook_command_guards.py -q` passes.
- `bash scripts/check-claude-sync.sh` reports the two settings files in sync.
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-150/plan.md` exits 0.
- `python3 scripts/check-docs.py` exits 0.
- Live: a guarded command pointing at an absent script leaves Bash working; `gate-edits`
  still blocks a source edit with no active iteration.
- Full suite green.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

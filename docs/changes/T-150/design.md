# T-150 — In-flight design decisions

## DD1. Root cause: `python3`'s missing-file exit code is 2, the same code that blocks

Measured during live verification: running the *unguarded* command against an absent
script exits **2** — `python3: can't open file …` uses exit code 2. The harness treats a
PreToolUse exit of 2 as "block this tool call". So a missing hook script did not degrade
to a warning; it was indistinguishable from a hook deliberately vetoing every command.

That is the whole bug in one line, and it explains why the failure was total rather than
noisy: `gate-edits` (Write) and the missing `stage-run-log` (Bash) were both returning 2,
so both tool families were vetoed at once with no recovery route from inside the session.

## DD2. `if`/`fi`, not `&&`, and never `|| true`

The guard must satisfy two opposing requirements simultaneously:

| Form | Missing script | Present script exiting 2 | Verdict |
|---|---|---|---|
| `python3 X` (today) | **2 → blocks everything** | 2 | the bug |
| `python3 X \|\| true` | 0 | **0 → gate silently disarmed** | worse than the bug |
| `[ -f X ] && python3 X` | **1 → still an error** | 2 | half a fix |
| `if [ -f X ]; then python3 X; fi` | 0 | 2 | correct |

`if`/`fi` returns 0 when the condition is false and otherwise propagates the body's status.
Five hooks (`gate-edits`, `on-task-request`, `validate-commit`, `on-stop`,
`check-unfinished-tasks`) exit 2 to block, and that exit code *is* the enforcement
mechanism — so `|| true` would not be a smaller fix, it would silently delete every gate in
the framework while appearing to work. `test_the_rejected_guard_form_would_disarm_a_blocking_hook`
asserts that trap directly so nobody "simplifies" the guard later.

## DD3. Rejected: tracking `.claude/scripts/` so it merges with `settings.json`

It would close the specific skew, but the fix would then depend on *another* file being
present — the exact failure class being removed. It also duplicates the pack (`.claude/` is
generated from `.claude-templates/`, and `check-claude-sync.sh` enforces that they match),
so the tracked copy would be a second source of truth. The inline guard depends on nothing.

## DD4. Rejected: a shared shim (`scripts/run-hook.sh <name>`)

Cleaner-looking `settings.json`, but it trades 11 self-sufficient commands for one file
that must itself exist. Same objection as DD3. Verbosity in `settings.json` is the
acceptable price of a guard that cannot itself go missing.

## DD5. This fix is inert in the session that ships it

Same property T-140 hit (its DD5): `CLAUDE_PROJECT_DIR` resolves to the **main** checkout,
so the harness reads main's `.claude/settings.json`, not this worktree's. The guard
therefore protects the *next* hook change, not this one. Verification accordingly executes
the shipped command strings directly rather than relying on harness registration.

**Consequence for whoever merges:** run `scripts/sync-templates-to-claude.sh` on main after
merging, as with any hook-wiring change. After T-150 that sync is no longer *load-bearing
for recoverability* — a forgotten sync becomes a silent no-op instead of a lockout, which
is the entire point of the task.

## Completion verification (step 1a) — graded against the diff

| # | Requirement | Verdict | Evidence |
|---|---|---|---|
| 1 | Missing script is a silent no-op | ✅ | Live: real `stage-run-log.py` command with the script moved away → rc 0, empty stderr. `test_missing_script_is_a_silent_noop` |
| 2 | Present script keeps its blocking exit 2 | ✅ | Live: real `validate-commit.py` command with a malformed message → rc 2. `test_present_script_propagates_a_blocking_exit_2` |
| 3 | Present script still runs its side effects | ✅ | `test_present_script_runs_its_side_effect_and_exits_zero`; live valid-message case → rc 0 |
| 4 | stdin payload reaches the script | ✅ | `test_stdin_payload_reaches_the_guarded_script` (byte-for-byte echo) |
| 5 | Every entry guarded in both files, files identical | ✅ | 11/11 guarded in each; `test_every_hook_command_is_guarded`, `test_settings_and_template_stay_identical`, `test_the_known_hook_entries_are_all_present`; `check-claude-sync.sh` green |
| 6 | No exit-suppressing form anywhere | ✅ | `test_no_command_suppresses_its_exit_code` scans for `\|\| true`, `\|\| :`, `; true`, `\|\| exit 0` |

## Completion verification (step 1b) — Success-Measure instrumentation

✅ **Instrumentation ships with the change and lives where the read-back happens.**
`scripts/tests/test_hook_command_guards.py` fails the suite if any hook command is
unguarded or uses an exit-suppressing form, so the invariant is checked continuously rather
than observed after an incident. This repo is also the read-back environment, satisfying
the constraint T-152 will generalize.

**Read-back: after the next 3 merges touching `settings.json` or `.claude/scripts/hooks/`,
or the next retrospective, whichever is first.** Expectation: zero sessions in which a
hook-wiring change makes tool calls unusable (baseline 1, observed 2026-07-27).

# Process Conventions

**⚠️ This file contains process conventions that should be stable across projects using this template. Changing these would mean changing how agents/teams execute the process.**

## Conventions Split

- **Process conventions** (this file): Rules that should be stable across projects using this template
- **Project conventions** (`docs/conventions.md`): Rules specific to the product/domain/architecture that may vary by project

## Commit Message Format

**This is the single source of truth for commit messages.** All skills and docs reference this format.

```
type(scope): brief description [T-XXX]

- Detail about what changed
- Why it changed (if not obvious)
```

**Types**: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

**Examples**:
- `feat(auth): add login form component [T-005]`
- `fix(api): handle timeout in retry logic [T-012]`
- `docs(readme): update setup instructions [T-003]`
- `refactor(db): extract query builder [T-008]`

## Pre-Commit Housekeeping: Run-Log Deltas Are Automatic

**Nothing to do — do not hand-sweep `docs/agent-logs/`.** A commit can never
contain its own run-log record (the record carries the commit's SHA, and the SHA
hashes the tree that would hold it), so `auto-log-commit.py` observes a commit
only after it lands. Since T-140 it queues the record to the untracked
`<main-repo-root>/.openup/run-log-pending.jsonl`; the `PreToolUse` hook
`stage-run-log.py` drains that queue into the lane shard and stages it just
before the **next** commit. A successful commit therefore leaves
`docs/agent-logs/` clean, and no lane pays a follow-up sweep commit.

The headless reference engine solves the same problem its own way —
`_sweep_run_logs` (`scripts/openup_agent/cycle.py`) folds the `docs/agent-logs/`
delta into a log-only `[openup-skip]` commit on every exit path.

## Branch Naming

```
feature/issue-{number}-{short-description}
fix/issue-{number}-{short-description}
refactor/{short-description}
docs/{description}
```

## PR Workflow

- Every PR should be focused (solves exactly one issue or task)
- PRs should be reviewable (aim for <400 lines changed)
- All tests must pass
- PRs must link to the issue/task being solved

## Documentation Standards

- Keep docs up to date when making changes
- Reference docs in PR descriptions when relevant
- Update `docs/project-status.md` after completing work
- Update phase notes in `docs/phases/{phase}/notes.md`

## Logging/Traceability Requirements

- Every agent run must create a log entry in `docs/agent-logs/`
- Logs must include: run metadata, tasks performed, commits created, decisions made
- See [the Traceability Logging SOP](sops/traceability-logging.md) for complete requirements

## Code Style (Language-Specific)

*Note: Language-specific code style rules belong in `docs/conventions.md` (project conventions), not here. This section is for process-level style requirements that apply regardless of language.*

- Prefer clarity over cleverness
- Keep functions small and focused
- Use meaningful names
- Write self-documenting code; add comments for *why*, not *what*

---

**For project-specific conventions** (naming conventions for domain, architecture patterns, API conventions, etc.), see `docs/conventions.md` (created during project development).

## Hook Commands Must Be Guarded

Every `hooks[].command` in `.claude/settings.json` (and its template
`docs-eng-process/.claude-templates/settings.json.example`) is wrapped in an existence
test:

```
if [ -f "$CLAUDE_PROJECT_DIR"/.claude/scripts/hooks/<name>.py ]; then python3 "$CLAUDE_PROJECT_DIR"/.claude/scripts/hooks/<name>.py; fi
```

**Why.** `settings.json` is tracked and merges instantly; `.claude/scripts/hooks/*` is
gitignored and only materializes when `sync-templates-to-claude.sh` runs. Between those two
moments an unguarded command is a hard interpreter error: it blocked every Bash call while
`gate-edits` independently blocked Write, leaving a session with no recovery route at all
(observed 2026-07-27 merging T-140).

**Never write `python3 <path> || true`.** Five hooks — `gate-edits.py`,
`on-task-request.py`, `validate-commit.py`, `on-stop.py`, `check-unfinished-tasks.py` —
deliberately `exit 2` to *block* a tool call, and that exit code is the entire enforcement
mechanism. `|| true` swallows it and silently disarms every gate in the framework.
`if`/`fi` is used precisely because it returns 0 when the file is absent and otherwise
propagates the script's own status.

`scripts/tests/test_hook_command_guards.py` enforces both halves — every command guarded,
and no command using an exit-suppressing form.

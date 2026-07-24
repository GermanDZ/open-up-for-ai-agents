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

## Pre-Commit Housekeeping: Sweep Hook-Appended Log Deltas

`auto-log-commit.py` (a `PostToolUse` hook) can only inspect a commit **after**
it has already landed — it appends one JSONL line to a `docs/agent-logs/`
run-log shard, leaving the tree dirty. Left unswept, this forces a
noticed-then-recommitted follow-up commit every time (a real cost measured
live: 6 avoidable round trips in one bootstrap lane).

**Before staging any commit, check for this delta and fold it in**:

```bash
git status --porcelain -- docs/agent-logs/
```

If it shows a change, `git add -- docs/agent-logs/` alongside whatever else
you're staging for this commit, rather than committing now and making a
second commit later once you notice the dirt. This mirrors the pattern the
headless reference engine already uses to solve the identical problem —
`_sweep_run_logs` (`scripts/openup_agent/cycle.py:1060-1084`) folds the whole
`docs/agent-logs/` delta into a log-only `[openup-skip]` commit on every exit
path. Applying the same discipline by hand at every commit you make keeps a
Claude-Code-driven lane's history free of avoidable follow-up commits.

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

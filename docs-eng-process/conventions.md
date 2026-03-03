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
- See [agent-workflow.md](agent-workflow.md#traceability-logging-sop) for complete requirements

## Code Style (Language-Specific)

*Note: Language-specific code style rules belong in `docs/conventions.md` (project conventions), not here. This section is for process-level style requirements that apply regardless of language.*

- Prefer clarity over cleverness
- Keep functions small and focused
- Use meaningful names
- Write self-documenting code; add comments for *why*, not *what*

---

**For project-specific conventions** (naming conventions for domain, architecture patterns, API conventions, etc.), see `docs/conventions.md` (created during project development).

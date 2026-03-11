# Commit Procedure

## Canonical Commit Format

Single source of truth: `docs-eng-process/conventions.md`

```
type(scope): brief description [T-XXX]
```

**Types**: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

## Never Commit to Trunk

Check branch before committing: `git rev-parse --abbrev-ref HEAD`. If on trunk (main/master/detected), create a feature branch first: `git checkout -b feature/<scope>-<desc>` (or `fix/` for bug fixes).

## Atomic Commits During Implementation

**Do NOT save all changes for one big commit at the end.** Commit after each meaningful unit of work (function, test suite, config change, docs update).

## Commit Ordering by Precedence

Commit in dependency order — foundational first:

1. Dependencies & config (`chore`)
2. Types, interfaces, schemas (`feat`/`refactor`)
3. Core logic & implementation (`feat`/`fix`/`refactor`)
4. Dependent features & integrations (`feat`)
5. Docs (`docs`)

Each logical unit = one commit. Verify with `git log --oneline <trunk>..HEAD`.

## Lint Before Committing

Run the project's linter/formatter before staging each commit. Fix issues first. Skip if no linter is configured.

## Test Commit Strategy

- **Features/changes**: tests go in the **same commit** as the code they test.
- **Bug fixes**: commit the **failing test first** (exposing the bug), then commit the fix separately (`reproduce → fix` history).

Use branch prefix (`fix/` vs `feature/`) and task context to pick the strategy.

## Final "Commit Remaining Changes" (at task end)

When `/openup-complete-task` runs, most work should already be committed. This step catches leftovers:

1. `git status --porcelain` — check for uncommitted changes
2. If changes exist: `git add <files>` then commit with canonical format
3. Verify clean: `git status --porcelain` must return empty

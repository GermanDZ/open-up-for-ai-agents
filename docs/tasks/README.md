# Task Specs

Each task in this directory is a **REASONS Canvas** — a structured per-task spec
that a developer-role agent consumes verbatim before generating code. Format
adopted from Martin Fowler's "Structured Prompt-Driven Development" (SPDD).

## REASONS Canvas Sections

| Section | Purpose |
|---|---|
| **Story** | INVEST-shaped user story for the task |
| **Analysis Context** | Domain notes, scope boundaries, definition of done |
| **Requirements** | What must be true when the task is done |
| **Entities** | Domain concepts / files / data the task touches |
| **Approach** | Design intent — *how* in 3–5 lines, not *what* |
| **Structure** | Concrete file/module list to add or modify |
| **Operations** | Ordered, testable execution steps |
| **Norms** | Inherited style/naming rules (point at `conventions.md`, don't duplicate) |
| **Safeguards** | Invariants, perf/security limits, what must NOT change |

## Conventions

- **IDs**: `T-XXX` zero-padded, monotonically assigned. Reference in commits as `[T-XXX]`.
- **Filename**: `T-XXX-kebab-case-summary.md`.
- **Lifecycle**: `proposed` → `ready` → `in-progress` → `done` → `verified`. Status lives in front-matter.
- **Spec-first**: behaviour changes update this file *before* code (per `.claude/CLAUDE.openup.md`).
- **Refactors**: code first, then back-propagate via `/openup-sync-spec` (skill TBD — see T-002).

## Creating a Task Spec

Run `/openup-create-task-spec` — it copies the template at
`docs-eng-process/templates/task-spec.md`, runs an analyst → architect → developer
handoff to populate the sections, and grades the result against
`.claude/rubrics/task-spec-rubric.md`. A spec must score all-✅ before its
`status` moves from `proposed` to `ready`.

For worked examples, see the existing `T-001` / `T-002` / `T-003` files in
this directory — they were authored against this format and pass the rubric.

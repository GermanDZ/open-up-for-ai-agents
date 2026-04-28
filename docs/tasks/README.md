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

> The official template and skill (`/openup-create-task-spec`) are defined by **T-001** itself.
> Until that lands, use the structure of this directory's existing files as the de facto template.

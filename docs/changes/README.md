# Changes (Ring 2)

One folder per change: `docs/changes/T-NNN/`. A *change* is a single unit of
delivery work (one roadmap task). Change folders hold the **inputs and working
state** for a task — they are *not* product truth (that lives in `docs/product/`,
Ring 1) and *not* ephemeral session state (`.openup/`, `.claude/memory/`, Ring 3).

```
docs/changes/
├── README.md            # this file
├── T-NNN/               # an active / in-progress change
│   ├── plan.md          # the REASONS Canvas spec / iteration plan for this change
│   ├── design.md        # decisions made DURING execution (living; keeps plan.md from going stale)
│   ├── inputs/          # examples, ideas, references seeding the work (optional)
│   ├── test-notes.md    # test scope / results (optional)
│   └── state.json       # archived .openup/state.json, copied here on completion
└── archive/             # completed change folders, moved here by /openup-complete-task
    └── T-NNN/
```

## Lifecycle

`proposed` → `ready` → `in-progress` → `done` → `verified` (status lives in the
`plan.md` front-matter; the live board is `docs/roadmap.md`, generated/synced via
`scripts/sync-status.py`).

Each `plan.md` also carries **coordination frontmatter** (`status`, `depends-on`,
`blocks`, `touches`, `claimed-by`, `claimed-at`, `worktree`) that `/openup-readiness`
parses into the dependency DAG. The full field set, status enum, hyphen convention, and
minimum-required fields for active vs archived tasks are documented in
[`docs-eng-process/coordination-frontmatter.md`](../../docs-eng-process/coordination-frontmatter.md).

On completion, `/openup-complete-task`:
1. merges durable outcomes into Ring 1 (`docs/product/`) — the "fix-spec-first" direction,
2. copies `.openup/state.json` into the change folder as `state.json`,
3. `git mv`s the folder into `docs/changes/archive/`.

## plan.md — the REASONS Canvas

Each `plan.md` is a **REASONS Canvas**: a structured per-task spec a developer-role
agent consumes verbatim before generating code (format from Martin Fowler's
"Structured Prompt-Driven Development").

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
- **Folder**: `docs/changes/T-XXX/`; the spec is always `plan.md` inside it.
- **Program-level plans** that span multiple tasks live in `docs/plans/`, not here — they *seed* change folders but are not themselves a single change.
- **Spec-first**: behaviour changes update `plan.md` (and `design.md` for in-flight decisions) *before* code (per `.claude/CLAUDE.openup.md`).
- **Refactors**: code first, then back-propagate via `/openup-sync-spec` (skill TBD — see [T-002](T-002/plan.md)).

## Creating a change spec

Run `/openup-create-task-spec` — it copies the template at
`docs-eng-process/templates/task-spec.md`, runs an analyst → architect → developer
handoff to populate the sections, and grades the result against
`.claude/rubrics/task-spec-rubric.md`. A spec must score all-✅ before its
`status` moves from `proposed` to `ready`.

For worked examples, see the archived [T-001](archive/T-001/plan.md) /
[T-003](archive/T-003/plan.md) and the active [T-002](T-002/plan.md) — they were
authored against this format and pass the rubric.

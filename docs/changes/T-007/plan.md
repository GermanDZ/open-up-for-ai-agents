---
id: T-007
title: Three-ring docs scoping (product / changes / archive) + context-loading updates
status: in-progress
priority: medium
estimate: 1–2 sessions
plan: docs/plans/2026-06-10-process-v2-claude-code-harness.md#ws4
depends-on: []
blocks: [T-008]
---

# T-007 — Three-ring docs scoping (Process v2 WS4)

## Story

As an OpenUP agent, I want `docs/` split into three rings — product truth (Ring 1),
per-change folders (Ring 2), and ephemeral session state (Ring 3) — so that context
loaded per unit of work is scoped, plans stop going stale, and completed work archives
cleanly instead of accumulating as flat files.

## Analysis Context

- WS4 of the Process v2 program plan. Absorbs OpenSpec ideas #3 (per-change folders) and #4 (archive-on-complete).
- **Scope boundary (decided 2026-06-11):** `docs/roadmap.md`, `docs/project-status.md`, `docs/plans/`, and `docs/agent-logs/` all **stay in place** (see `design.md`). The migration that actually moves files is limited to `docs/tasks/` → `docs/changes/`.
- Definition of done: rings exist; `docs/tasks/` migrated and removed; references to the old paths updated; skills brief specialists with "Ring 1 + one change folder"; consumer migration note shipped; templates re-synced; link integrity verified.

## Requirements

1. `docs/product/`, `docs/changes/`, `docs/changes/archive/` exist and are documented.
2. `docs/tasks/T-NNN-*.md` migrated to `docs/changes/[archive/]T-NNN/plan.md` with git history preserved (`done`/`verified` → `archive/`).
3. No dangling references to `docs/tasks/` remain in skills, scripts, hooks, or docs.
4. Skills' context-loading guidance references the rings, not "scan all of `docs/`".
5. A migration note tells consumer projects (e.g. Kaze) how to adopt the new layout.
6. `.claude/` and `docs-eng-process/.claude-templates/` stay in sync.

## Entities

- `docs/tasks/` (source, removed), `docs/changes/` (target), `docs/product/` (new Ring 1 home).
- Skills referencing `docs/tasks`: `create-task-spec` (both copies), `developer` teammate, `skills-guide.md`, `task-spec.md` template.
- Migration note: `docs-eng-process/migration-three-ring-docs.md` (new).

## Approach

Mechanical `git mv` for the moves; targeted edits for the ~10 prose references that
point at moving paths. Status/roadmap/plans/agent-logs deliberately untouched, which
keeps the 150+/50+ reference counts inert and the hook layer unchanged. Dogfood the
new structure by housing this very task's spec in `docs/changes/T-007/`.

## Structure

- NEW `docs/product/.gitkeep`, `docs/changes/`, `docs/changes/archive/`
- MOVED `docs/tasks/{T-001,T-003}` → `docs/changes/archive/{T-001,T-003}/plan.md`; `docs/tasks/T-002` → `docs/changes/T-002/plan.md`; `docs/tasks/README.md` → `docs/changes/README.md` (rewritten)
- NEW `docs/changes/T-007/{plan.md,design.md}` (dogfood)
- MOD references in `.claude/skills/.../create-task-spec/SKILL.md`, `.claude/teammates/developer.md`, `docs-eng-process/skills-guide.md`, `docs-eng-process/templates/task-spec.md` (+ template mirrors)
- NEW `docs-eng-process/migration-three-ring-docs.md`

## Operations

1. Fix-spec-first: correct WS4 wording in the program plan. ✅
2. Create rings; migrate `docs/tasks/`. ✅
3. Rewrite `docs/changes/README.md`; dogfood `docs/changes/T-007/`. ✅
4. Update the `docs/tasks/` references (create-task-spec skill, developer teammates, skills-guide, task-spec template, roadmap + spdd-evaluation links) + three-ring context-loading guidance in `CLAUDE.md`. ✅
5. Write the consumer migration note (`docs-eng-process/migration-three-ring-docs.md`); re-sync templates → `.claude/`. ✅
6. Tester lane: grepped for dangling `docs/tasks` refs (none in functional paths), verified moved links resolve, `check-claude-sync` parity holds. ✅

## Norms

Follow `.claude/CLAUDE.openup.md` (fix-spec-first, edit-artifacts-through-skill).
Commits use `type(scope): description [T-007]`.

## Safeguards

- Do **not** move `docs/agent-logs/`, `docs/plans/`, `docs/project-status.md`, `docs/roadmap.md` — moving them breaks T-006 hooks and the WS3 logging guarantee.
- Preserve git history on all moves (`git mv`, never delete+create).
- `.claude/` ↔ `.claude-templates/` parity must hold (`check-claude-sync` hook).

---
id: T-016
title: Self-briefing roles — per-role cold-start reading lists + pointer-only PM delegation
status: done   # proposed → ready → in-progress → done → verified
completed: 2026-06-12
priority: high
estimate: 1 session
plan: docs/plans/2026-06-12-clarity-self-briefing-continue-loop.md#t-016-f-self-briefing-roles-pointer-only-delegation
depends-on: [T-015]
blocks: [T-017]
touches:
  - .claude/teammates/                                      # uniform "On start, read" block in every role file (+ compact pointers)
  - docs-eng-process/.claude-templates/teammates/           # mirror of the above (parity)
  - .claude/CLAUDE.openup.md                                # briefing-from-docs principle
  - docs-eng-process/.claude-templates/CLAUDE.openup.md     # mirror
  - docs/roadmap.md                                         # mark T-016 status
claimed-by: null
claimed-at: null
worktree: null
last-synced: ""
---

# T-016 — Self-briefing roles: per-role cold-start reading lists + pointer-only PM delegation

## Story

> **As an** agent assuming a role at the start of a session
> **I want** a uniform, role-scoped "On start, read" list and a PM delegation brief that carries only *deltas* the docs don't already state
> **So that** roles self-brief from the repo instead of from a custom prose briefing — and a brief that has to spell out scope becomes a signal that the spec is incomplete (fix-spec-first), not a place to patch it.

INVEST check:
✅ Independent (only needs T-015's assumption convention) · ✅ Negotiable (block wording/placement tunable) · ✅ Valuable (kills redundant briefings + surfaces incomplete specs) · ✅ Estimable (1 session) · ✅ Small (6 role files + 6 compact + CLAUDE.openup.md + mirrors) · ✅ Testable (cold-start a role given only a task ID; confirm it loads the right ring-scoped docs)

## Analysis Context

- **Domain.** The `.claude/teammates/*.md` role definitions and the PM orchestrator's Delegation Brief Format, plus the briefing-from-docs principle in `.claude/CLAUDE.openup.md`. This is process/prose, not executable code — the "self-brief" is instructions a role agent follows, enforced by convention.
- **Scope boundaries.** Covers the six role files (analyst, architect, developer, project-manager, tester, scribe) + their `-compact` variants, and the PM delegation section. Does NOT build `/openup-next` (T-017 composes these self-briefing roles into the loop), does NOT add `docs/project-config.yaml` (T-018), and does NOT change the three-ring scoping rules themselves (T-007, already shipped) — it only points roles at those rings.
- **Definition of done.** Every role file has a uniform `## On Start, Read` section with three ring-scoped components (status · the active change folder · role-relevant guideline docs); the PM Delegation Brief Format collapses to a pointer-only form (`[ROLE]: T-NNN. Deltas: …`) and names "writing scope into a brief" as a fix-spec-first trigger; `CLAUDE.openup.md` states the briefing-from-docs principle; `.claude/` ↔ `.claude-templates/` parity holds (`check-claude-sync` passes).

**Assumption:** the cold-start block lives in a dedicated `## On Start, Read` section placed right after the role intro, and the redundant "Before starting work" line in the existing "How You Work" step is trimmed to point at it (avoids two divergent reading lists per file). *(Vetoable at review.)*
**Assumption:** `-compact.md` variants get a **one-line pointer** to the full file's block, not a verbatim copy — compact files already end with a "Full instructions: …" footer, so duplicating the list would defeat their purpose (resolves plan Open Question #3). *(Vetoable at review.)*
**Assumption:** the **scribe** is the deliberate exception — its standing rule is "read only the exact target file," so it gets a one-line cold-start note affirming that, not the three-component block (forcing it to read status would contradict its design). *(Vetoable at review.)*
**Assumption:** role guideline reading lists reference only docs that exist today and tag Ring 1 product artifacts (`docs/product/…`, currently unpopulated in this repo) as "if present," matching how the current files already phrase `architecture-notebook.md` — no forward reference to T-018's project-config. *(Vetoable at review.)*

No blocking questions: the request fully determines the deliverable; all open points above are low-cost defaults.

## Requirements

1. Each of the five reasoning role files (`analyst`, `architect`, `developer`, `project-manager`, `tester`) has a uniform `## On Start, Read` section with three ring-scoped components: **status** (`docs/project-status.md` + `docs/roadmap.md`), **the active change folder** (`docs/changes/T-NNN/plan.md`, Ring 2), and **role-relevant guideline docs**.
2. The reading list's framing names the spec as authoritative and instructs the role: if the spec doesn't answer a question, fix the spec rather than work around it (fix-spec-first).
3. The `scribe` role file carries a one-line cold-start note affirming its "read only the target file" rule instead of the three-component block (the deliberate exception).
4. Each `-compact.md` variant carries a one-line pointer to its full file's `## On Start, Read` block (no verbatim duplication).
5. The PM `### Delegation Brief Format` collapses to a pointer-only form: `[ROLE]: T-NNN. Deltas: <only what the docs don't say — usually nothing>`.
6. The PM section names "I'm writing scope/context into a brief" as a recognized fix-spec-first signal (the spec is incomplete; fix it, don't patch it with prose).
7. `.claude/CLAUDE.openup.md` states the briefing-from-docs principle (roles self-brief from the repo; a custom briefing is a symptom of an incomplete spec).
8. Every `.claude/` edit is mirrored to its `docs-eng-process/.claude-templates/` source so `check-claude-sync` passes.

## Entities

- **Role files** (modified) — `.claude/teammates/{analyst,architect,developer,project-manager,tester,scribe}.md` (+ mirrors under `docs-eng-process/.claude-templates/teammates/`)
- **Compact role files** (modified) — `.claude/teammates/{analyst,architect,developer,project-manager,tester,scribe}-compact.md` (+ mirrors)
- **OpenUP short instructions** (modified) — `.claude/CLAUDE.openup.md` (+ mirror `docs-eng-process/.claude-templates/CLAUDE.openup.md`)
- **Sync checker** (read-only) — `scripts/check-claude-sync.sh` (parity gate; `--fix-from-live` mirrors `.claude/` → templates)
- **Three-ring scoping** (read-only) — `.claude/CLAUDE.openup.md` "Context Scoping (Three Rings)" — the rings the reading lists point at

## Approach

Add one uniform `## On Start, Read` section to each reasoning role file, immediately after the role intro, built from three ring-scoped components (status · active change folder · role-relevant guidelines). The third component is the only part that varies by role, and it references existing guide docs + Ring-1 artifacts "if present" — never inventing a doc. Compact variants stay compact via a one-line pointer. The scribe keeps its single-file rule as its (deliberately different) cold-start note. In `project-manager.md`, replace the verbose Delegation Brief Format with a one-line pointer-only form and add a fix-spec-first trigger so a brief that needs prose scope is treated as a missing-spec signal. `CLAUDE.openup.md` gains a short briefing-from-docs principle that ties it together. All `.claude/` edits mirror to `.claude-templates/` via `check-claude-sync.sh --fix-from-live`.

## Structure

**Add:**
- `docs/changes/T-016/plan.md` — this spec (already created).
- A `## On Start, Read` section in each of the 5 reasoning role files; a one-line cold-start note in `scribe.md`.

**Modify:**
- `.claude/teammates/{analyst,architect,developer,project-manager,tester}.md` (+ mirrors) — cold-start block; trim the now-redundant "Before starting work" line.
- `.claude/teammates/scribe.md` (+ mirror) — one-line single-file cold-start note.
- `.claude/teammates/{...}-compact.md` (all six, + mirrors) — one-line pointer to the full block.
- `.claude/teammates/project-manager.md` (+ mirror) — pointer-only Delegation Brief Format + fix-spec-first trigger.
- `.claude/CLAUDE.openup.md` (+ mirror) — briefing-from-docs principle.

**Do not touch:**
- `.claude/skills/openup-workflow/next/` — that is T-017; this task only makes roles self-briefing, it does not compose the loop.
- The "Context Scoping (Three Rings)" rules themselves — reading lists *point at* the rings; the rings are unchanged (T-007).
- `docs/product/` artifacts — out of scope; reference them "if present," do not author them.

## Operations

1. Draft the uniform `## On Start, Read` block (3 components; role-varying third bullet) and add it to `analyst.md`, `architect.md`, `developer.md`, `tester.md`, and `project-manager.md`, trimming each file's redundant "Before starting work" reading line to point at the new section.
2. Add the one-line cold-start note to `scribe.md` (affirm "read only the target file") and a one-line pointer to all six `-compact.md` variants.
3. Replace the PM `### Delegation Brief Format` body with the pointer-only form (`[ROLE]: T-NNN. Deltas: …`) and add the "writing scope into a brief = fix-spec-first signal" trigger; mirror the same compaction into `project-manager-compact.md` if it carries the brief format.
4. Add the briefing-from-docs principle to `.claude/CLAUDE.openup.md`.
5. Run `scripts/check-claude-sync.sh --fix-from-live` to mirror all `.claude/` edits into `docs-eng-process/.claude-templates/`; then run `scripts/check-claude-sync.sh` (check mode) and confirm it passes (full-tree parity).
6. Verify behavior: simulate a cold-start developer-role session given only `task_id: T-016` — confirm the `## On Start, Read` block names exactly the ring-scoped docs to load and no extra briefing is needed; confirm the PM brief format no longer carries scope/context/done-when prose.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, process conventions.
- `.claude/CLAUDE.openup.md` — fix-spec-first, edit-artifacts-through-their-skill, three-ring scoping, `.claude/` ↔ `.claude-templates/` parity.

## Safeguards

- **Token / size budget.** Each reasoning role file gains ≤ ~12 lines; each compact gains 1 line; PM brief format shrinks; `CLAUDE.openup.md` gains ≤ ~6 lines.
- **Reversibility.** Pure additive/replacement prose edits; revert by removing the added sections and restoring the old brief format. No script, state, or schema changes.
- **No-go zones.** Do not add an executable hook or change any `.py` enforcement — self-briefing stays prose/convention for T-016. Do not build `/openup-next`. Do not reference T-018's `project-config.yaml` (not yet built).
- **Invariant.** `.claude/` and `docs-eng-process/.claude-templates/` must be byte-identical after the change (`check-claude-sync` green).

## Verification

- Each of the 5 reasoning role files contains a `## On Start, Read` section with the three ring-scoped components; `scribe.md` has its single-file cold-start note; all 6 compacts carry the one-line pointer.
- The PM Delegation Brief Format is the pointer-only form and names the fix-spec-first trigger.
- `CLAUDE.openup.md` states the briefing-from-docs principle.
- `scripts/check-claude-sync.sh` exits 0 (parity holds across the full tree).
- A cold-start developer-role dry-run, given only `T-016`, loads exactly the ring-scoped docs from its block and needs no extra briefing.
- Grade this spec against `.claude/rubrics/task-spec-rubric.md` — all criteria ✅.

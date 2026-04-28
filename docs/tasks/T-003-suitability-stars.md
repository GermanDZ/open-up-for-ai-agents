---
id: T-003
title: Suitability "fit" metadata in workflow skill front-matter
status: done
priority: low
estimate: 0.5 session
plan: docs/plans/2026-04-28-spdd-ideas-worth-adopting-in-openup.md#4
depends-on: []
blocks: []
completed: 2026-04-28
---

# T-003 — Suitability "fit" metadata in workflow skill front-matter

## Story

> **As a** new OpenUP user (human or agent)
> **I want** each workflow skill to declare what it's good and bad for
> **So that** I pick `quick-task` vs `start-iteration` vs `orchestrate`
>   correctly without guessing.

INVEST: ✅ all dimensions; trivially small.

## Analysis Context

SPDD rates itself 5★ for standardised delivery and 1–2★ for hotfixes /
spikes / one-off scripts — explicit about its bad-fit cases. OpenUP's
workflow skills carry no such guidance; users guess between
`quick-task` / `start-iteration` / `orchestrate`. The boundary is
under-documented in `QUICK-REFERENCE.md`.

**Definition of done:** every workflow skill declares fit; fit-matrix
appears in `QUICK-REFERENCE.md`; the `/openup-init` flow surfaces it.

## Requirements

1. Each workflow skill carries a `fit:` front-matter block with three
   categories: `great`, `ok`, `poor`.
2. `QUICK-REFERENCE.md` carries a fit-matrix table summarising all
   workflow skills.
3. `/openup-init` references the fit-matrix when introducing the
   workflow commands.

## Entities

- Workflow skills (modified):
  - `.claude/skills/openup-workflow/openup-start-iteration/SKILL.md`
  - `.claude/skills/openup-workflow/openup-quick-task/SKILL.md`
  - `.claude/skills/openup-workflow/openup-orchestrate/SKILL.md`
  - `.claude/skills/openup-workflow/openup-complete-task/SKILL.md`
  - (and any sibling workflow skills)
- `docs-eng-process/QUICK-REFERENCE.md` (modified)
- `.claude/skills/openup-init/SKILL.md` (modified — single line reference)

## Approach

Add a YAML `fit:` block to each workflow skill's existing front-matter.
Use plain English in arrays — no star ratings. Surface in QUICK-REFERENCE
as a four-column table (skill | great | ok | poor).

## Structure

**Modify:**
- Each `.claude/skills/openup-workflow/*/SKILL.md` — front-matter only.
- `docs-eng-process/QUICK-REFERENCE.md` — add fit-matrix table.
- `.claude/skills/openup-init/SKILL.md` — one-line reference to the matrix.

**Do not modify:**
- Skill bodies (front-matter only).
- Phase or artifact skills (out of scope for this task).

## Operations

1. Read each workflow skill; for each, draft a `fit:` block reflecting its
   actual sweet spot per `skills-guide.md` and `QUICKSTART.md`.
2. Apply edits in one batch; verify the YAML still parses.
3. Build the fit-matrix table in `QUICK-REFERENCE.md`.
4. Add the one-line reference in `/openup-init`.
5. Smoke test by reading `QUICK-REFERENCE.md` end-to-end.

## Norms

- Inherits from `docs-eng-process/conventions.md`.
- YAML front-matter style matches existing skill files.
- Plain English in `fit:` arrays — no ratings, no jargon.

## Safeguards

- **Front-matter only.** Do not change skill behaviour.
- **No new skills.** Do not introduce phase/artifact `fit:` blocks in
  this task — out of scope; reduces blast radius.
- **Reversibility.** Each edit is independent; revert per-file is trivial.

## Verification

- Read `QUICK-REFERENCE.md` cold, decide which skill to use for: (a) a
  one-line typo fix, (b) a new feature, (c) a multi-role refactor. The
  matrix should make the choice obvious.
- `grep -L "^fit:" .claude/skills/openup-workflow/*/SKILL.md` returns no
  output (every workflow skill has `fit:`).

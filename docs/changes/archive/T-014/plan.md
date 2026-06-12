---
id: T-014
title: "Edit artifacts through their skill, not by hand (SPDD item #5)"
status: done
priority: low
estimate: 0.25 session
plan: docs/plans/2026-04-28-spdd-ideas-worth-adopting-in-openup.md#5
depends-on: []
blocks: []
completed: 2026-04-28
note: implemented out-of-band before formal task tracking; backfilled 2026-06-12
---

# T-014 — Edit artifacts through their skill, not by hand

## Story

> **As an** OpenUP agent (any role)
> **I want** an explicit prohibition on hand-editing structured artifacts
> **So that** rubric criteria are never silently bypassed by ad-hoc edits.

INVEST: ✅ Independent, ✅ Negotiable (phrasing), ✅ Valuable (enforces rubric
discipline), ✅ Estimable (< 30 min), ✅ Small (one-bullet addition to one file),
✅ Testable (grep rule + cold read).

## Analysis Context

SPDD warns that manually editing structured prompts breaks internal consistency
because rubric criteria are silently violated. OpenUP artifacts (use cases,
architecture notebook, iteration plans) carry the same risk: hand-edits bypass
the rubric re-application that the `/openup-create-*` and `/openup-detail-*`
skills perform automatically.

**Gap:** No rule prevented direct hand-edits to artifact files. Silent rubric
violations could accumulate undetected.

**Definition of done:** `CLAUDE.openup.md` prohibits hand-edits to structured
artifacts except for trivial typos, directing changes through the relevant skill.

## Requirements

1. `CLAUDE.openup.md` under "Critical Rules" states that artifact changes
   (use cases, iteration plans, architecture notebook, vision, test plan) must go
   through the relevant `/openup-create-*` or `/openup-detail-*` skill.
2. The rule explicitly names the exception: typo-level fixes.

## Entities

- `.claude/CLAUDE.openup.md` (modified — Critical Rules section)

## Approach

Add one paragraph under Critical Rules: "Edit artifacts through their skill,
not by hand." Name the covered artifact types. Name the exception (typos).
Explain why: hand-edits bypass rubric criteria.

## Structure

No new files. Single prose addition to `CLAUDE.openup.md`.

## Operations

1. Add ~3 lines under Critical Rules in `CLAUDE.openup.md`.
2. Sanity-read end-to-end; confirm the exception is unambiguous.

## Norms

- Inherits from `docs-eng-process/conventions.md`.
- Rule phrasing in OpenUP idiom.

## Safeguards

- **Doc-only.** No code, no skill, no hook changes.
- **Size budget.** Rule adds < 4 lines.

## Verification

- `grep "Edit artifacts through their skill" .claude/CLAUDE.openup.md` returns a match.
- Read cold: the exception (typos) is clearly stated and the covered artifact types are listed.

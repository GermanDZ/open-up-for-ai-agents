---
id: T-013
title: "Fix-spec-first rule for behavior changes (SPDD item #2)"
status: done
priority: high
estimate: 0.5 session
plan: docs/plans/2026-04-28-spdd-ideas-worth-adopting-in-openup.md#2
depends-on: []
blocks: []
completed: 2026-04-28
note: implemented out-of-band before formal task tracking; backfilled 2026-06-12
---

# T-013 — Fix-spec-first rule for behavior changes

## Story

> **As an** OpenUP developer-role agent
> **I want** an explicit rule about which comes first — spec update or code change
> **So that** use cases, iteration plans, and code never silently diverge.

INVEST: ✅ Independent (pure doc change, no dependencies), ✅ Negotiable (phrasing),
✅ Valuable (closes silent-drift failure mode SPDD calls out), ✅ Estimable (< 1 hr),
✅ Small (CLAUDE.openup.md + 4 teammate files), ✅ Testable (grep rule + read cold).

## Analysis Context

SPDD identifies silent drift between structured prompts and code as the primary
failure mode of prompt-driven development. OpenUP had artifact-level specs but
no codified rule about update ordering when implementation reveals a divergence.

**Gap:** When a developer-agent finds implementation should differ from the spec,
there was no rule. Risk: specs and code diverge silently, defeating the artifact
discipline OpenUP enforces via rubrics.

**Definition of done:** `CLAUDE.openup.md` contains the bifurcated rule under
Critical Rules; `developer.md`, `developer-compact.md`, `architect.md`,
`architect-compact.md` each carry a one-bullet reminder.

## Requirements

1. `CLAUDE.openup.md` under "Critical Rules" states: behavior changes → spec first;
   refactors → code first, then back-propagate via `/openup-sync-spec`.
2. `developer.md` and `developer-compact.md` reference this rule with one bullet.
3. `architect.md` and `architect-compact.md` reference this rule with one bullet.

## Entities

- `.claude/CLAUDE.openup.md` (modified — Critical Rules section)
- `.claude/teammates/developer.md` (modified — one bullet)
- `.claude/teammates/developer-compact.md` (modified — one bullet)
- `.claude/teammates/architect.md` (modified — one bullet)
- `.claude/teammates/architect-compact.md` (modified — one bullet)

## Approach

Add a short "Fix the spec first" section to the Critical Rules block in
`CLAUDE.openup.md`. Bifurcate on behavior-change vs refactor-only. Add one-bullet
reminders to developer and architect teammate prompts referencing this rule.

## Structure

No new files. Edits are front-matter and prose additions only.

## Operations

1. Add ~6 lines under Critical Rules in `CLAUDE.openup.md`.
2. Add one bullet to `developer.md` and `developer-compact.md`.
3. Add one bullet to `architect.md` and `architect-compact.md`.
4. Sanity-read `CLAUDE.openup.md` end-to-end; confirm size budget respected.

## Norms

- Inherits from `docs-eng-process/conventions.md`.
- Rule phrasing in OpenUP idiom (not SPDD terminology).

## Safeguards

- **Doc-only.** No code, no skill, no hook changes in this task.
- **Size budget.** `CLAUDE.openup.md` must remain quick-loadable; rule adds < 6 lines.

## Verification

- `grep "Fix the spec first" .claude/CLAUDE.openup.md` returns a match.
- `grep "spec.first\|Spec-first" .claude/teammates/developer.md` returns a match.
- `grep "spec.first\|Architecture Notebook first" .claude/teammates/architect.md` returns a match.
- Read `CLAUDE.openup.md` cold; the ordering rule is unambiguous.

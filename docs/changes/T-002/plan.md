---
id: T-002
title: /openup-sync-spec — back-propagate refactors to artifacts
status: deferred
priority: medium
estimate: 1 session
plan: docs/plans/2026-04-28-spdd-ideas-worth-adopting-in-openup.md#3
depends-on: [T-001]
blocks: []
touches:
  - .claude/skills/openup-workflow/
  - docs-eng-process/templates/
defer-until: "drift observed in practice after T-001 lands"
claimed-by: null
claimed-at: null
worktree: null
---

# T-002 — `/openup-sync-spec`: refactor → artifact back-propagation

## Story

> **As an** OpenUP architect/developer agent
> **I want** a one-shot skill that detects and proposes targeted edits to
>   stale artifacts after a refactor
> **So that** code-side cleanups don't silently invalidate the use case,
>   architecture notebook, or task spec.

INVEST: ✅ all dimensions; small enough to ship in one session once needed.

## Analysis Context

**Status: DEFERRED.** The plan recommends shipping T-001 and the spec-first
rule first, then evaluating whether real drift occurs. If specs and code
stay aligned because the spec-first rule is sufficient, this task is
**YAGNI** and should be closed without implementation.

**Trigger to un-defer.** Any of:
- Two or more refactors land without artifact updates (caught in retro).
- A bug is traced to outdated architecture notebook content.
- An iteration retrospective explicitly asks for the skill.

## Requirements

1. Skill diffs current code state against an artifact's `last-synced` git ref.
2. Identifies which artifact sections are likely stale (heuristic: sections
   that name files / symbols changed in the diff).
3. Proposes targeted edits — does NOT regenerate whole documents.
4. Updates `last-synced: <sha>` front-matter on each touched artifact.
5. Refuses to run for behaviour-changing diffs (those go spec-first; the
   skill should detect and direct the user back to the originating
   `/openup-create-*` skill).

## Entities

- New skill: `.claude/skills/openup-workflow/openup-sync-spec/SKILL.md`
- Modified front-matter: every artifact template gains optional
  `last-synced` field (`use-case-specification.md`, `architecture-notebook.md`,
  `iteration-plan.md`, `task-spec.md`).
- Heuristic: read `architect` + `developer` teammates for sync-vs-spec
  classification rules.

## Approach

A read-only diff tool wrapped in an architect-led skill. Architect classifies
the diff (refactor vs behaviour) and refuses non-refactor diffs. For
qualifying diffs, scribe role drafts targeted edits per artifact, presented
as a unified review for the user before write.

## Structure

**Add:**
- `.claude/skills/openup-workflow/openup-sync-spec/SKILL.md`

**Modify:**
- Each artifact template — add optional `last-synced` field.
- `docs-eng-process/skills-guide.md` — register skill.
- `.claude/CLAUDE.openup.md` — replace "(when available)" with concrete reference once shipped.

## Operations

1. Define the `last-synced` front-matter conventions; update existing artifact templates.
2. Implement skill: input is a git ref or "since last commit"; output is a diff classification + per-artifact proposed edits.
3. Add behaviour-change detection guard: if diff touches public APIs, business logic, or acceptance criteria, refuse and point user at the spec-first path.
4. Register in skills guide; update CLAUDE.openup.md cross-reference.
5. Verify on a synthetic refactor: rename a function, run the skill, confirm only naming-affected sections are flagged.

## Norms

- Inherits from `docs-eng-process/conventions.md`.
- Skill structure matches `.claude/skills/openup-workflow/` siblings.
- Diff classification heuristic must be documented in the skill itself for transparency.

## Safeguards

- **Read-only by default.** The skill proposes edits; the user (or a
  follow-up Edit tool call) applies them. Never auto-write artifacts.
- **No false-positive silencing.** When in doubt, classify as
  behaviour-changing and refuse — the cost of refusing a true refactor is
  small; the cost of silently letting a behaviour change slip is exactly
  what SPDD warns against.
- **Bounded scope.** Skill only handles existing artifact types; new types
  must add explicit support.

## Verification

- Synthetic refactor test (rename, extract method, move file).
- Synthetic behaviour-change test — must refuse with a clear message
  pointing at the right `/openup-create-*` skill.
- Audit one real iteration's diff against the skill output for sanity.

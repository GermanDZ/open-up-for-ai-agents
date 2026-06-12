---
id: T-015
title: Mandatory ambiguity gate in spec authoring
status: done   # proposed → ready → in-progress → done → verified
priority: high
estimate: 1 session
plan: docs/plans/2026-06-12-clarity-self-briefing-continue-loop.md#t-015-c-mandatory-ambiguity-gate-in-spec-authoring
depends-on: []
blocks: [T-016, T-017]
last-synced: ""
---

# T-015 — Mandatory ambiguity gate in spec authoring

## Story

> **As an** agent authoring a task spec or feature plan
> **I want** a required step that surfaces open questions and classifies each as blocking or non-blocking
> **So that** silent wrong guesses become either a stop-and-ask or a visible, vetoable assumption — instead of waste discovered after code is written.

INVEST check:
✅ Independent (no deps) · ✅ Negotiable (gate wording is tunable) · ✅ Valuable (cuts rework from misread intent) · ✅ Estimable (1 session) · ✅ Small (4 files + mirrors) · ✅ Testable (author from an ambiguous request, observe routing)

## Analysis Context

- **Domain.** Spec-authoring skills (`create-task-spec`, `plan-feature`) and the artifacts they produce. The gate is a prose step in those skills plus a template convention and a rubric criterion — no executable hook.
- **Scope boundaries.** Covers `create-task-spec` and `plan-feature` only. Does NOT touch `openup-quick-task` (the quick path deliberately skips ceremony) or the other `create-*` artifact skills (use-case, vision, etc.) — those can adopt the same pattern later if it proves out.
- **Definition of done.** Authoring a spec from a deliberately ambiguous request produces (a) a stop + `/openup-request-input` for a blocking question, or (b) `**Assumption:**` lines in Analysis Context for non-blocking ones; the rubric flags a spec that did neither.

**Assumption:** non-blocking assumptions are recorded as `**Assumption:**` lines inside the existing **Analysis Context** section (not a new top-level section) — keeps the template stable. *(Vetoable at review.)*
**Assumption:** the rubric gains one new criterion (#9 "Ambiguity Resolution") rather than overloading an existing one — keeps grading auditable. *(Vetoable at review.)*
**Assumption:** the gate is a prose step, not a script/hook — consistent with "skills are the layer that held up" in the Kaze audit; deterministic enforcement is out of scope for T-015. *(Vetoable at review.)*

## Requirements

1. `create-task-spec` SKILL.md has a process step, before Round 1 drafting, that lists open questions and classifies each as **blocking** or **non-blocking**.
2. The step routes **blocking** questions to `/openup-request-input` and instructs the author to stop until answered.
3. The step records **non-blocking** questions as `**Assumption:**` lines in the spec's Analysis Context.
4. `plan-feature` SKILL.md has an equivalent classification step before it generates the iteration plan.
5. `docs-eng-process/templates/task-spec.md` documents the `**Assumption:**` convention within the Analysis Context section.
6. `task-spec-rubric.md` has a criterion that grades whether open questions were classified (blocking routed, non-blocking recorded as assumptions).
7. Every `.claude/` edit is mirrored to its `docs-eng-process/.claude-templates/` source so `check-claude-sync` passes.

## Entities

- **create-task-spec skill** (modified) — `.claude/skills/openup-artifacts/create-task-spec/SKILL.md` (+ mirror `docs-eng-process/.claude-templates/skills/openup-create-task-spec/SKILL.md`)
- **plan-feature skill** (modified) — `.claude/skills/openup-plan-feature/SKILL.md` (+ mirror)
- **task-spec template** (modified) — `docs-eng-process/templates/task-spec.md`
- **task-spec rubric** (modified) — `.claude/rubrics/task-spec-rubric.md` (+ mirror `docs-eng-process/.claude-templates/rubrics/task-spec-rubric.md`)
- **request-input skill** (read-only) — `.claude/skills/openup-workflow/request-input/SKILL.md` (the blocking-question destination)

## Approach

Add a single, uniform "Ambiguity Gate" step to the two authoring skills that
mirrors the existing fix-spec-first idiom: classify, then either stop-and-ask
(blocking) or record-and-proceed (non-blocking). The template carries the
`**Assumption:**` convention so the output has a stable home for vetoable
guesses, and the rubric adds one criterion so a spec that skipped the gate is
caught at grading. No new artifact, no script — the gate lives where authoring
already lives.

## Structure

**Add:**
- `docs/changes/T-015/plan.md` — this spec (already created).

**Modify:**
- `.claude/skills/openup-artifacts/create-task-spec/SKILL.md` (+ template mirror) — new "Ambiguity Gate" step before Round 1.
- `.claude/skills/openup-plan-feature/SKILL.md` (+ template mirror) — classification step before plan generation.
- `docs-eng-process/templates/task-spec.md` — `**Assumption:**` convention note in Analysis Context.
- `.claude/rubrics/task-spec-rubric.md` (+ template mirror) — criterion 9 "Ambiguity Resolution".

**Do not touch:**
- `.claude/skills/openup-quick-task/` — the quick path intentionally skips ceremony; gating it would defeat its purpose.
- other `create-*` artifact skills — out of scope; adopt later if the pattern proves out.

## Operations

1. Add the `**Assumption:**` convention to the Analysis Context section of `docs-eng-process/templates/task-spec.md`; confirm the template still reads cleanly.
2. Insert an "Ambiguity Gate" step into `create-task-spec` SKILL.md (after Read Context, before Round 1); mirror to `.claude-templates`. Verify both copies are identical.
3. Insert an equivalent classification step into `plan-feature` SKILL.md (after codebase exploration, before plan generation); mirror. Verify identical.
4. Add criterion 9 "Ambiguity Resolution" to `task-spec-rubric.md`; mirror. Verify identical.
5. Stage all and confirm `check-claude-sync` passes on commit (61-file parity).
6. Verify behavior: dry-run author a spec from an ambiguous one-line request — confirm a blocking question yields a `/openup-request-input` instruction and a non-blocking one yields an `**Assumption:**` line; grade against the new rubric criterion.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, process conventions.
- `.claude/CLAUDE.openup.md` — fix-spec-first, edit-artifacts-through-their-skill, `.claude/` ↔ `.claude-templates/` parity.

## Safeguards

- **Token / size budget.** Each skill gains ≤ ~20 lines; rubric gains one criterion; template gains ≤ 5 lines.
- **Reversibility.** Pure additive prose edits; revert by removing the added step/criterion. No script or state changes.
- **No-go zones.** Do not add a blocking hook or change `gate-edits.py` — the gate stays advisory/prose for T-015. Do not gate the quick track.

## Verification

- Both skill files and the rubric are byte-identical to their `.claude-templates` mirrors (`diff -q`); `check-claude-sync` passes.
- A spec authored from an ambiguous request routes a blocking question to `/openup-request-input` and records a non-blocking one as an `**Assumption:**` line.
- The new rubric criterion flags a spec that did neither.
- Grade this spec against `.claude/rubrics/task-spec-rubric.md` — all criteria ✅.

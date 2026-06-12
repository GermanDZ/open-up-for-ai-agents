---
id: T-021
title: Implementation-vs-spec verify step in /openup-complete-task
status: done   # proposed → ready → in-progress → done → verified
completed: 2026-06-12
priority: medium
estimate: 0.5 session
plan: docs/plans/2026-06-12-clarity-self-briefing-continue-loop.md#t-021-e-implementation-vs-spec-verify-step-in-openup-complete-task
depends-on: [T-020]
blocks: []
track: standard
touches:
  - docs-eng-process/.claude-templates/skills/openup-complete-task/SKILL.md   # new verify step + blocking gate
  - docs/roadmap.md                                                          # T-021 status
claimed-by: null
claimed-at: null
worktree: null
last-synced: ""
---

# T-021 — Implementation-vs-spec verify step in /openup-complete-task

## Story

> **As a** developer-role agent closing a task with `/openup-complete-task`
> **I want** a blocking step that grades each spec requirement ✅/❌ against the actual diff (and its scenarios, if present) before anything is committed
> **So that** a task cannot be marked "done" while a requirement is silently unmet — the completion-time counterpart to the spec's `## Verification` section.

INVEST check:
✅ Independent (the step degrades gracefully without T-020 — scenarios are graded only if present) · ✅ Negotiable (grading idiom mirrors the rubrics) · ✅ Valuable (closes the "done but a requirement is missing" gap) · ✅ Estimable (one skill file) · ✅ Small (skill-only edit, no code) · ✅ Testable (a diff omitting a requirement must flag ❌ and block done)

## Analysis Context

- **Domain.** The task-completion workflow — `/openup-complete-task`, the single legal "work
  done" exit. OpenSpec's `/opsx:verify` is the analogue being grafted on.
- **Scope boundaries.** This task sharpens the *execution* of completion-time verification
  (grade requirements against the diff); it does NOT add a new artifact, does NOT automate the
  grade (the agent reads the diff — the deterministic scenario *structure* check is T-020's
  authoring-time job), and does NOT change the gate set in `openup-state.py`.
- **Definition of done.** `complete-task` carries a BLOCKING "Verify Implementation Against
  Spec" step before commit that grades each requirement ✅/❌ against `git diff`, grades
  scenarios when present, blocks completion on any ❌, and records the grade in `design.md`;
  the Success Criteria list it as blocking.

**Assumption:** The verify step lands as `### 1a.` immediately after "Verify Task Completion"
and before "Commit Remaining Changes" — verification gates the commit, so it must precede it.
*(Vetoable at review.)*

**Assumption:** When a requirement carries no scenarios (e.g. a pre-T-020 or quick-track
spec), the step grades the requirement text alone — scenario grading is additive, not
required. *(Vetoable at review.)*

## Requirements

1. `.claude/skills/openup-complete-task/SKILL.md` contains a BLOCKING "Verify Implementation
   Against Spec" step that grades **each** `## Requirements` entry ✅/❌ against the actual
   diff (`git diff <trunk>...HEAD`) before the commit step.
   - **Given** the complete-task skill **When** a reader reaches the step before "Commit
     Remaining Changes" **Then** it instructs grading every requirement against the diff with
     ✅/❌ and a pointer to where the diff satisfies it.
2. Any ❌ blocks completion — no commit, roadmap update, or archive proceeds.
   - **Given** a task whose diff omits a requirement **When** the verify step runs **Then** it
     grades that requirement ❌ and the skill halts completion rather than committing.
3. When a requirement carries `Given / When / Then` scenarios (T-020), the step grades each
   scenario's **Then** as the observable check, running it where mechanically checkable.
   - **Given** a requirement with a scenario whose **Then** is a runnable check **When** the
     verify step runs **Then** it executes/inspects that check and grades on the result;
     **Given** a requirement with no scenario **When** the step runs **Then** it grades the
     requirement text alone without error.
4. The grade is recorded in `docs/changes/{task_id}/design.md` (persisted, not
   conversation-only).
   - **Given** the verify step completes **When** the grade is produced **Then** the skill
     directs writing it to the change folder's `design.md`.
5. The skill's Success Criteria list the verify step as a BLOCKING item.
   - **Given** the complete-task Success Criteria **When** a reader scans them **Then** the
     first item is the blocking per-requirement verification.

## Behavior Delta

How this task changes **existing product behavior** (Ring 1: `docs/product/`).

**n/a — all Added.** T-021 changes the completion *workflow skill*, not Ring-1 *product*
behavior. No use case, vision, or architecture statement changes.

## Entities

- **complete-task skill** (modified) — `.claude/skills/openup-complete-task/SKILL.md` (+ `.claude-templates/` mirror)
- **scenario validator** (read-only) — `scripts/openup-spec-scenarios.py` (T-020; referenced for scenario grading)
- **task-spec** (read-only) — `docs/changes/{task_id}/plan.md` (source of requirements graded)

## Approach

A single skill edit: insert a BLOCKING verify step that reuses the rubrics' per-criterion
✅/❌ idiom, but applied to the spec's *requirements* against the *diff* rather than to the
spec's own quality. Degrade gracefully — scenarios sharpen the grade when present (T-020) but
are not required for the step to function. The grade is persisted to `design.md` to honour the
no-conversation-only-state rule, and any ❌ routes back to either finishing the work or
fixing the spec (fix-spec-first), never to committing anyway.

## Structure

**Add:**
- (none — no new files)

**Modify:**
- `.claude/skills/openup-complete-task/SKILL.md` (+ `.claude-templates/` mirror) — step 1a + Success Criteria item
- `docs/roadmap.md` — T-021 row → ready → done

**Do not touch:**
- `scripts/openup-state.py` — the gate set is unchanged; verification is a skill discipline,
  not a new machine gate (tempting to add a `spec_verified` gate, but out of scope here).
- `scripts/openup-spec-scenarios.py` — consumed read-only; not modified.

## Operations

- [x] Add the BLOCKING "Verify Implementation Against Spec" step (`### 1a.`) to
      `.claude/skills/openup-complete-task/SKILL.md`, before "Commit Remaining Changes".
- [x] Add the blocking per-requirement verification to the skill's Success Criteria.
- [x] Mirror live ↔ templates (`check-claude-sync.sh` exit 0).
- [x] (tester) Confirm the step reads as blocking, grades against the diff, grades scenarios
      when present, and records the grade in `design.md`.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.)
- The rubrics' per-criterion ✅/❌ grading idiom this step mirrors.

## Safeguards

- **Token / size budget.** Step ≤ ~30 lines; Success-Criteria addition is one line. Additive.
- **Reversibility.** Delete the step + the Success-Criteria line; no code, no migrations.
- **No-go zones.** Do not weaken the existing gate set; do not turn verification into a
  non-blocking suggestion; do not add a new artifact.
- **Parity invariant.** `scripts/check-claude-sync.sh` exits 0 before complete-task.

## Verification

- `grep -n "Verify Implementation Against Spec" .claude/skills/openup-complete-task/SKILL.md`
  shows the step, positioned before "Commit Remaining Changes".
- The Success Criteria list the blocking verification as the first item.
- `scripts/check-claude-sync.sh` exits 0.
- Grade the final artifact against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

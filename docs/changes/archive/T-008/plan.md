---
id: T-008
title: Coordination frontmatter + /openup-readiness DAG skill
status: done
completed: 2026-06-11
priority: medium
estimate: 1 session
plan: docs/plans/2026-06-10-process-v2-claude-code-harness.md#ws5
depends-on: [T-007]
blocks: [T-009]
touches:
  - docs/changes/
  - .claude/skills/openup-workflow/
  - docs-eng-process/
claimed-by: null
claimed-at: null
worktree: null
---

# T-008 — Coordination frontmatter + `/openup-readiness` DAG (Process v2 WS5a + WS5b)

## Story

> **As an** OpenUP PM/orchestrator agent
> **I want** every change folder's `plan.md` to declare machine-readable coordination
>   fields (status, dependencies, collision surface, claim) **and** a `/openup-readiness`
>   skill that computes the dependency DAG
> **So that** PM intake becomes a deterministic query — "what is READY to start, what is
>   BLOCKED and why, and which READY tasks would collide" — instead of a manual reading of
>   prose roadmap notes.

INVEST: ✅ small, independent (T-007 landed the change folders it annotates), testable
(readiness output is deterministic from frontmatter), valuable (un-defers T-002 and is the
precondition for T-009 worktree claims).

## Analysis Context

- WS5a + WS5b of the Process v2 program plan. Absorbs OpenSpec idea #1 (readiness DAG).
- WS5c (worktree-per-task + live lease claims) is **T-009**, out of scope here. T-008 defines
  the `claimed-by` / `claimed-at` / `worktree` fields so the schema is stable, but does not
  write or enforce claims — readiness only *reads* them.
- This task is the precondition that un-defers T-002 (`/openup-sync-spec`).

## Design Decisions

1. **Key naming — hyphens, not underscores.** Existing change files (`T-002`, archived
   `T-007`) use `depends-on` and `blocks`. The program-plan sketch (WS5a) used `depends_on`,
   but that was illustrative. We standardize on **hyphenated keys** to match what already
   ships and avoid a migration churn: `depends-on`, `claimed-by`, `claimed-at`. New fields
   `touches` and `worktree` are single words (no separator needed).

2. **Status enum.** `proposed | ready | blocked | in-progress | done | verified`.
   Existing files use `deferred` (T-002) and `done` (T-007) — both are tolerated by the
   reader; `deferred` is reported as a distinct non-actionable state, not an error.

3. **Readiness is read-only and stateless.** `/openup-readiness` parses frontmatter across
   `docs/changes/**/plan.md` (including `archive/`) and prints a report. It writes nothing,
   claims nothing. `model: haiku` (coordination tier per `model-tiers.md`).

4. **READY / BLOCKED computation.** A task is **READY** iff `status` ∈ {proposed, ready}
   **and** every id in `depends-on` resolves to a task with `status` ∈ {done, verified}.
   Otherwise **BLOCKED**, with the specific unmet dependency ids named. `in-progress`,
   `done`, `verified`, `deferred` are reported in their own sections, not as READY/BLOCKED.

5. **Collision flagging.** Among READY tasks (and any `in-progress` task), if two tasks'
   `touches` lists share a path prefix, flag the overlap. If a task carries a non-null
   `claimed-by`, surface the claim so the PM knows it is owned. (Live `.git/openup/claims/`
   lease reading is T-009; T-008 reads only the frontmatter claim field.)

## Requirements

1. **Schema documented.** The coordination frontmatter (all WS5a fields, the status enum,
   hyphen convention) is documented — extend `docs-eng-process/` (a new
   `coordination-frontmatter.md` or a section in an existing process doc).
2. **Existing change files migrated.** `docs/changes/T-002/plan.md` and the archived
   `T-001/T-003/T-007` plans gain the new fields where sensible (`touches`, claim fields =
   null). Archived/done tasks need not carry claim fields if that adds noise — document the
   minimum required set.
3. **`/openup-readiness` skill exists** under `.claude/skills/openup-workflow/readiness/`
   with `SKILL.md` (`model: haiku`), declaring its inputs (the change-folder tree) and the
   exact report format (READY / BLOCKED-with-reasons / IN-PROGRESS / collisions).
4. **DAG computation is deterministic and demonstrated.** Running the skill against the
   current change folders produces a correct report: T-002 deferred, T-009/T-010/T-011 not
   yet having change folders are sourced from the roadmap table (or documented as out of
   scope until they get folders). Decide and document the source of truth: change-folder
   `plan.md` frontmatter is authoritative; the roadmap table is the human view.
5. **Templates re-synced.** Mirror any `.claude/` changes into
   `docs-eng-process/.claude-templates/` (the template-sync hook covers this, but verify).

## Definition of Done

- [ ] Coordination frontmatter schema documented in `docs-eng-process/`.
- [ ] `/openup-readiness` skill created (`model: haiku`), with a precise report-format spec.
- [ ] Skill produces a correct READY/BLOCKED/collision report against the live change folders.
- [ ] Existing change `plan.md` files carry the agreed minimum coordination fields.
- [ ] Templates re-synced; link integrity intact.
- [ ] Verified by the tester against the acceptance check below.

## Acceptance Check (from program plan)

> `/openup-readiness` lists READY/BLOCKED with dependency reasons.

Concretely, against the current state: with T-007 `done`, T-008 should report as the
actionable in-progress task; T-009 BLOCKED on T-008; T-010 BLOCKED on T-005,T-006 (both
done → actually READY once it has a folder); T-011 READY (depends on T-005 ✅). The tester
confirms the dependency reasoning matches the roadmap DAG.

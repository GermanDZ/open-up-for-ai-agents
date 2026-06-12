# Exploration: OpenSpec ideas for reducing waste from unclear objectives

**Started:** 2026-06-12
**Question:** Which OpenSpec primitives, not yet adopted by OpenUP, would reduce
development waste caused by unclear objectives and misunderstandings between
the requester and the implementing agent?

## Context

This is a follow-up to [2026-05-13-openspec-ideas-for-openup.md](../plans/2026-05-13-openspec-ideas-for-openup.md),
re-focused on a single goal: **waste reduction from intent ambiguity**. Since
that plan was written, Process v2 (T-004…T-011) absorbed most of it:

| 2026-05-13 item | Status today |
|---|---|
| #1 Readiness DAG | ✅ done — T-008, `/openup-readiness` + coordination frontmatter |
| #2 `project-config.yaml` context/rules injection | ❌ **not implemented** — no references anywhere in skills or docs-eng-process |
| #3 Per-change folders | ✅ done — T-007, `docs/changes/T-NNN/` (Ring 2) |
| #4 Archive flow | ✅ done — `docs/changes/archive/` |
| #5 Explore mode | ✅ done — this file is written through it |
| (related) T-002 `/openup-sync-spec` | ✅ done — 2026-06-11 |

So the question is no longer "what should we borrow" wholesale — it's what
remains in OpenSpec (including its current OPSX iteration: `/opsx:propose`,
`/opsx:verify`, delta-specs, structural validation) that targets the two
moments where ambiguity waste actually occurs:

1. **Before work starts** — intent never pinned down; the agent builds a
   plausible-but-wrong thing.
2. **During/after work** — ambiguity discovered mid-flight is resolved
   silently by the agent; spec and code drift without anyone deciding.

## Notes

### Where OpenUP already stands on clarity

- **Task spec (REASONS canvas)** is strong on *scope* alignment: Story +
  INVEST, "Scope boundaries", "Do not touch" (explicit anti-scope), Safeguards
  with no-go zones. This is better than OpenSpec's proposal at preventing
  scope creep.
- **Use-case rubric** enforces flows, alternates, exceptions — good behavioral
  coverage at the *use-case* level.
- **Weak point 1:** task-spec `## Requirements` are "numbered, testable
  assertions" — testability is *asserted*, never *demonstrated*. Nothing forces
  a requirement to be concrete enough that two readers parse it identically.
- **Weak point 2:** requirements are written fresh, not as a **delta against
  Ring 1 product truth**. A reviewer can't see "this changes existing behavior
  X" vs "this adds new behavior Y" without doing the diff in their head — which
  is exactly where misunderstandings hide ("I thought we were keeping X").
- **Weak point 3:** `/openup-request-input` exists (and its `fit.great`
  includes "ambiguous requirements"), but **no authoring skill is required to
  use it**. Neither `create-task-spec` nor `plan-feature` mention ambiguity,
  clarification, or request-input. An agent that guesses wrong never hits a
  gate.

### What OpenSpec does at those two moments

- **Pre-work:** proposal = "Why / What changes / Impact" reviewed by the human
  *before* any artifact is built; requirements written as **deltas**
  (`ADDED` / `MODIFIED` / `REMOVED` against living specs); every requirement
  must carry ≥1 `#### Scenario:` in Given/When/Then; `openspec validate`
  checks this structure deterministically; agent instructions say "ask
  clarifying questions when the request is ambiguous" rather than guess.
- **Post-work:** `/opsx:verify` checks the implementation against the
  artifacts; archive folds deltas back into the living `specs/` truth.

## Options Considered

Five candidate adoptions, graded for the stated goal:

- **Option A — Behavior-delta section in the task spec** (HIGH value / MED effort).
  Add a `## Behavior Delta` section to `docs-eng-process/templates/task-spec.md`:
  requirements grouped **Added / Modified / Removed**, each Modified/Removed
  entry naming the Ring 1 artifact + section it changes
  (`docs/product/use-cases/UC-3 §main-flow`). Pro: misunderstandings about
  *existing* behavior become visible at review time; gives `/openup-sync-spec`
  an exact list of Ring-1 artifacts to update instead of inferring. Con: only
  pays off when Ring 1 is populated; meaningless for greenfield tasks (make the
  section "n/a — all Added" in that case). Mirrors the existing
  Add/Modify/Do-not-touch idiom the Structure section already uses for *files*.

- **Option B — Scenario-per-requirement + deterministic validation** (HIGH value / MED effort).
  Every entry in `## Requirements` must carry at least one
  `Given / When / Then` scenario; a small script (extend
  `/openup-readiness` or a `.claude/scripts/` check invoked by
  `/openup-assess-completeness`) validates the structure deterministically —
  Process v2's own principle: "if a step is deterministic, the harness does
  it." Pro: writing the scenario is where vague requirements break down
  ("When the user does X — *which* X?"); the misunderstanding surfaces before
  code. Con: ceremony for quick-track tasks — apply on standard/full tracks
  only.

- **Option C — Mandatory ambiguity gate in spec authoring** (HIGH value / LOW effort).
  Add a numbered step to `create-task-spec` and `plan-feature`: before
  drafting, list open questions; classify each as *blocking* (answer changes
  scope/requirements) or *non-blocking* (note the assumption inline). Blocking
  → invoke `/openup-request-input` and stop; non-blocking → record as
  `**Assumption:**` lines in Analysis Context so the requester can veto them at
  review. Pro: cheapest item; directly converts silent guesses into visible,
  vetoable assumptions. Con: relies on prose instruction (no hook) — but it
  lives inside a skill, the layer that held up in the Kaze audit.

- **Option D — `docs/project-config.yaml`** (MED value / LOW effort).
  The one surviving item from the 2026-05-13 plan, already fully specified
  there (item #2). A canonical home for project facts (stack, domain,
  compliance) injected as `<project-context>` / `<project-rules>` into every
  `/openup-create-*` prompt. Pro: removes a whole class of misunderstanding —
  "the agent didn't know a fact that's true here but not everywhere." Con:
  none new; it was rated MED/LOW then and nothing changed.

- **Option E — Implementation-vs-spec verify step in `/openup-complete-task`** (MED value / LOW effort).
  OpenSpec's `/opsx:verify` equivalent: before marking done, grade each
  requirement (and its scenarios, if Option B lands) ✅/❌ against the actual
  diff — same per-criterion idiom as the rubrics. Pro: catches "built the
  wrong thing" before it's archived as done. Con: partially overlaps the
  task-spec's own `## Verification` section; implement as a sharpening of
  that section's execution, not a new artifact.

**Ruled out** (unchanged from 2026-05-13, still correct): OpenSpec artifact
names, forkable schemas, npm CLI, tool-portability. Also ruled out from the
current OPSX set: `/opsx:ff` (covered by `/openup-start-iteration` +
plan-feature) and `/opsx:onboard` (covered by `/openup-init`).

### Suggested sequencing

C (one session, immediate) → D (one session, already specified) →
A (feeds sync-spec; do before B) → B (validation builds on A's structure) →
E (half session, folds into complete-task).

C+D+A together address "objectives not clear before work"; B+E address
"misunderstanding not caught during/after work."

## Open Questions

- Should Option B's scenario requirement apply to `standard` track or only
  `full`? (Lean: standard+full, skip quick.)
- Does Option A's Behavior Delta live in `plan.md` (Ring 2) or in the task
  spec template — or are those now the same file under `docs/changes/T-NNN/`?
  Needs a look at how T-007 reconciled `task-spec.md` with `plan.md`.
- Option E vs the existing rubric pass in `/openup-complete-task` (full
  track) — extension or duplication? Check complete-task's current steps
  before scoping.

## Where this goes next

→ iteration — promote to a roadmap entry "OpenSpec clarity mechanisms
(reduce ambiguity waste)" with five candidate tasks (C, D, A, B, E in that
order); C and D are each ~1 session and can start immediately.

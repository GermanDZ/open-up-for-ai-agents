---
id: T-XXX
title: <one-line task summary>
status: proposed   # proposed → ready → in-progress → done → verified
priority: medium   # critical | high | medium | low
estimate: 1 session   # rough size (e.g. "0.5 session", "1–2 sessions")
plan: docs/plans/<plan-file>.md#<section>   # link to originating plan, if any
depends-on: []     # list of task IDs that must finish first
blocks: []         # list of task IDs that wait on this one
last-synced: ""    # full git SHA of last code↔spec sync (set by /openup-sync-spec)
---

# T-XXX — <Title>

## Story

> **As a** <role>
> **I want** <capability>
> **So that** <outcome / why>

INVEST check — keep it brief; one line per dimension is fine:
✅ Independent · ✅ Negotiable · ✅ Valuable · ✅ Estimable · ✅ Small · ✅ Testable

## Analysis Context

State the *why* the spec needs but the code can't show:
- **Domain.** What part of the system / problem space this touches.
- **Scope boundaries.** What this task does NOT cover (cuts the long tail).
- **Definition of done.** Concrete, observable end state.

Record any **non-blocking** open questions resolved by a default choice as
`**Assumption:**` lines here — one per line, each stating the choice and (in
parens) that it is vetoable at review. This makes a silent guess a visible,
overridable decision. *Blocking* questions (whose answer would change scope or
requirements) do not belong here — raise them via `/openup-request-input` before
drafting. See the Ambiguity Gate step in the authoring skill.

> **Assumption:** <the default chosen>. *(Vetoable at review.)*

## Requirements

Numbered, testable assertions. Each one should be checkable post-implementation.
1. <requirement>
2. <requirement>

## Entities

Domain concepts, files, and types the task touches. Not exhaustive — load-bearing only.
- **<Entity>** (new | modified | read-only) — `<path-or-symbol>`

## Approach

3–5 lines describing the *design intent*. Resist the urge to describe operations
here; that's the next section. State the shape of the solution, not the steps.

## Structure

Concrete file/module list. Group by **Add** / **Modify** / **Do not touch**.
Out-of-scope items in "Do not touch" are explicit alignment, not defensive
padding — only list items a reasonable reader might think belong in scope.

**Add:**
- <path>

**Modify:**
- <path> — <what changes>

**Do not touch:**
- <path> — <why it's tempting but out of scope>

## Operations

Ordered steps a developer-role agent can execute. Each step should be testable
on its own. Use 3–8 steps; if you need more, the task is probably too big.

1. <step>
2. <step>

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.)
- `docs/conventions.md` (if exists) — project conventions
- <other inherited rule sources, file paths only — DO NOT inline rules>

> **Anti-pattern**: pasting rules from `conventions.md` here. Reference, don't copy.

## Safeguards

Invariants and limits that must hold:
- **Token / size budget.** <e.g. "template body ≤ 120 lines">
- **Reversibility.** <how to back out if needed>
- **No-go zones.** <what behavior must not change>
- <other invariants>

> **Anti-pattern**: pasting safeguards from the architecture notebook here.
> Reference the notebook section, don't restate.

## Verification

How a reviewer (human or agent) confirms the task is done:
- <test command, file existence check, manual review step>
- Grade the final artifact against `.claude/rubrics/task-spec-rubric.md` —
  every criterion must be ✅ or have a clear gap call-out.

---

<!--
Worked example: see docs/changes/archive/T-001/plan.md for a real
spec produced from this template. The task that introduced this template
is itself written in the format — meta but useful as a reference.
-->

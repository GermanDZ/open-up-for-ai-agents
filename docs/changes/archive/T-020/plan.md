---
id: T-020
title: Scenario-per-requirement + deterministic validation in the task spec
status: done   # proposed → ready → in-progress → done → verified
completed: 2026-06-12
priority: high
estimate: 1 session
plan: docs/plans/2026-06-12-clarity-self-briefing-continue-loop.md#t-020-b-scenario-per-requirement-deterministic-validation
depends-on: [T-019]
blocks: [T-021]
track: standard
touches:
  - docs-eng-process/templates/task-spec.md                                       # scenario-per-requirement convention
  - scripts/openup-spec-scenarios.py                                              # new deterministic validator
  - scripts/tests/test_openup_spec_scenarios.py                                   # validator tests
  - docs-eng-process/.claude-templates/rubrics/task-spec-rubric.md               # criterion 11
  - docs-eng-process/.claude-templates/skills/openup-create-task-spec/SKILL.md   # author scenarios + run check
  - docs-eng-process/.claude-templates/skills/openup-assess-completeness/SKILL.md # wire the validator
  - docs/roadmap.md                                                              # T-020 status
claimed-by: null
claimed-at: null
worktree: null
last-synced: ""
---

# T-020 — Scenario-per-requirement + deterministic validation

## Story

> **As a** reviewer (or `/openup-assess-completeness`) gating a task spec before implementation
> **I want** every requirement to carry a concrete `Given / When / Then` scenario, validated by a deterministic script
> **So that** a vague requirement fails mechanically at authoring time instead of being argued over (or silently misread) at review.

INVEST check:
✅ Independent (depends only on T-019, done) · ✅ Negotiable (scenario marker syntax is conventional) · ✅ Valuable (closes "specs assert testability but never demonstrate it") · ✅ Estimable (template + 1 script + tests + skill/rubric wiring) · ✅ Small (additive; one new stdlib script) · ✅ Testable (the validator is itself unit-tested, and this spec dog-foods the convention)

## Analysis Context

- **Domain.** Spec-authoring machinery — the REASONS-Canvas task-spec template, its rubric,
  its authoring skill, and the readiness/assessment path. Same surface T-015 (ambiguity gate)
  and T-019 (Behavior Delta) extended.
- **Scope boundaries.** This task validates **structure** (every requirement has a
  Given/When/Then scenario), not scenario *quality* or semantic correctness — judging whether
  a scenario is meaningful stays a human/rubric call. It does NOT retrofit scenarios into
  archived specs, and does NOT change the `quick` track (exempt).
- **Definition of done.** The template requires a scenario per requirement; a deterministic
  `scripts/openup-spec-scenarios.py` validates it (exit 0/1/2) and is unit-tested; rubric
  criterion 11 grades it; `create-task-spec` authors the scenarios and `assess-completeness`
  runs the validator; `.claude/` ↔ `.claude-templates/` parity holds.

**Assumption:** A scenario is recognised by the bold markers `**Given**` / `**When**` /
`**Then**` (all three present in a requirement's block). The bold form never appears in
ordinary prose, so the check has no false positives. *(Vetoable at review.)*

**Assumption:** The validator is a standalone `scripts/` peer of `openup-board.py` /
`openup-claims.py` (not a new subcommand on the board), invoked by `assess-completeness` —
keeps the board's job (queue derivation) and this job (spec structure) separate.
*(Vetoable at review.)*

**Assumption:** Track scope is `standard` + `full`; `quick` is exempt, per plan Open
Question #4. *(Vetoable at review.)*

## Requirements

1. `docs-eng-process/templates/task-spec.md` `## Requirements` section states that every
   requirement carries ≥1 `Given / When / Then` scenario (bold markers) and points at the
   validator.
   - **Given** the task-spec template **When** a reader opens `## Requirements` **Then** they
     see the scenario requirement and an example `- **Given** … **When** … **Then** …` line.
2. A deterministic `scripts/openup-spec-scenarios.py check <plan>` exits 0 when every
   requirement carries a scenario, 1 when one or more do not (naming them), and 2 on a
   malformed/missing spec.
   - **Given** a spec where each requirement has a scenario **When** `check` runs **Then** it
     exits 0; **Given** a spec with one scenario-less requirement **When** `check` runs
     **Then** it exits 1 and prints that requirement's number.
3. The validator is exempt on the `quick` track (frontmatter `track:` or `--track`),
   enforced on `standard`/`full`, defaulting to `standard` when no track is given.
   - **Given** a spec with `track: quick` **When** `check` runs **Then** it exits 0 without
     grading; **Given** no track at all **When** `check` runs **Then** it enforces (standard).
4. `.claude/rubrics/task-spec-rubric.md` gains criterion 11 (Scenario Coverage) and the
   skill's "10 criteria" references become "11".
   - **Given** the updated rubric **When** a grader counts criteria **Then** there are 11, the
     last being Scenario Coverage; **And** `create-task-spec` reads "11 criteria".
5. `create-task-spec` instructs the analyst to author scenarios and its grading step runs the
   validator; `assess-completeness` runs the validator for `task-spec` artifacts.
   - **Given** the create-task-spec skill **When** a reader reaches Round 1 and Step 5
     **Then** both name the scenario authoring and the `openup-spec-scenarios.py` check;
     **And** assess-completeness documents running it with track awareness.
6. The validator has hermetic unit tests covering pass, fail (with naming), quick-skip,
   multi-line scenarios, boundary non-leak, and malformed input.
   - **Given** `scripts/tests/test_openup_spec_scenarios.py` **When** the suite runs **Then**
     every case passes and the module is discovered by `unittest discover -s scripts/tests`.
7. `scripts/check-claude-sync.sh` exits 0 (rubric + skills mirrored live ↔ templates).
   - **Given** the completed edits **When** `check-claude-sync.sh` runs **Then** it exits 0.

## Behavior Delta

How this task changes **existing product behavior** (Ring 1: `docs/product/`).

**n/a — all Added.** T-020 changes process tooling (the task-spec template, its rubric and
authoring/assessment skills, and a new validator script), not Ring-1 *product* behavior. No
use case, vision, or architecture statement changes. This spec is the first dog-fooding
instance of the scenario convention it introduces.

## Entities

- **task-spec template** (modified) — `docs-eng-process/templates/task-spec.md`
- **scenario validator** (new) — `scripts/openup-spec-scenarios.py`
- **validator tests** (new) — `scripts/tests/test_openup_spec_scenarios.py`
- **task-spec rubric** (modified) — `.claude/rubrics/task-spec-rubric.md` (+ `.claude-templates/` mirror)
- **create-task-spec skill** (modified) — `.claude/skills/openup-create-task-spec/SKILL.md` (+ mirror)
- **assess-completeness skill** (modified) — `.claude/skills/openup-assess-completeness/SKILL.md` (+ mirror)
- **claims helper** (read-only) — `scripts/openup-claims.py` (imported for `parse_frontmatter`)

## Approach

Mirror the T-015/T-019 pattern: a new template *convention* (scenario per requirement), a
rubric *criterion* (11) that grades it, and skill *steps* that author + enforce it — plus,
new here, a deterministic *validator* so the grade is mechanical, not judgement. The
validator is a stdlib-only `scripts/` peer of `openup-board.py`, importing
`openup-claims.py`'s `parse_frontmatter` so "track" agrees across the toolchain. It scans the
`## Requirements` section, splits top-level numbered items into blocks, and checks each block
for the three bold markers — deterministic in, deterministic out.

## Structure

**Add:**
- `scripts/openup-spec-scenarios.py` — the validator
- `scripts/tests/test_openup_spec_scenarios.py` — its tests

**Modify:**
- `docs-eng-process/templates/task-spec.md` — scenario convention in `## Requirements`
- `.claude/rubrics/task-spec-rubric.md` (+ `.claude-templates/` mirror) — criterion 11
- `.claude/skills/openup-create-task-spec/SKILL.md` (+ mirror) — author + grade
- `.claude/skills/openup-assess-completeness/SKILL.md` (+ mirror) — run the validator
- `docs/roadmap.md` — T-020 row → ready → done

**Do not touch:**
- `scripts/openup-board.py` — the validator is a separate concern (queue vs spec structure);
  tempting to bolt on as a subcommand, but it would conflate two jobs.
- `docs/changes/archive/*/plan.md` — completed specs are not retrofitted.

## Operations

- [x] Add `scripts/openup-spec-scenarios.py` (stdlib-only, imports `openup-claims.py`;
      `check` subcommand; exit 0/1/2; `--track` override; quick-exempt).
- [x] Add `scripts/tests/test_openup_spec_scenarios.py` and confirm it is green under
      `python3 -m unittest discover -s scripts/tests`.
- [x] Add the scenario-per-requirement convention to `docs-eng-process/templates/task-spec.md`.
- [x] Add rubric criterion 11 (Scenario Coverage); bump "10 criteria" → "11" in create-task-spec.
- [x] Wire `create-task-spec` (author + grade) and `assess-completeness` (run validator).
- [x] (tester) Mirror live ↔ templates (`check-claude-sync.sh` exit 0), run the validator
      against this very spec (exit 0), and re-grade against the 11-criterion rubric.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.)
- The existing task-spec template + rubric + the `openup-board.py`/`openup-claims.py`
  script idiom this validator mirrors.

## Safeguards

- **Token / size budget.** Validator ≤ ~200 lines; template addition ≤ ~12 lines; rubric
  criterion ≤ ~12 lines. Additive only.
- **Determinism invariant.** Validator uses the standard library only, never a model, and is
  byte-stable for a given input.
- **Reversibility.** Delete the script + tests + the template/rubric/skill additions; no
  migrations, no code-path coupling.
- **No-go zones.** Do not change `quick`-track ceremony; do not gate the board on scenarios;
  do not retrofit archived specs.
- **Parity invariant.** `scripts/check-claude-sync.sh` exits 0 before complete-task.

## Verification

- `python3 -m unittest scripts.tests.test_openup_spec_scenarios` — all green.
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-020/plan.md` exits 0
  (this spec satisfies its own convention).
- `scripts/check-claude-sync.sh` exits 0.
- Rubric contains criterion 11; create-task-spec reads "11 criteria".
- Grade the final artifact against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

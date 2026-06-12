---
id: T-018
title: docs/project-config.yaml context/rules injection into /openup-create-* skills
status: done   # proposed → ready → in-progress → done → verified
completed: 2026-06-12
priority: medium
estimate: 1 session
plan: docs/plans/2026-06-12-clarity-self-briefing-continue-loop.md#t-018-d-docs-project-config-yaml-context-rules-injection
depends-on: []
blocks: []
track: standard
touches:
  - docs-eng-process/templates/project-config.example.yaml          # new — starter config
  - docs-eng-process/project-config.md                              # new — mechanism + precedence doc
  - docs-eng-process/.claude-templates/skills/openup-create-vision/SKILL.md
  - docs-eng-process/.claude-templates/skills/openup-create-use-case/SKILL.md
  - docs-eng-process/.claude-templates/skills/openup-create-architecture-notebook/SKILL.md
  - docs-eng-process/.claude-templates/skills/openup-create-iteration-plan/SKILL.md
  - docs-eng-process/.claude-templates/skills/openup-create-task-spec/SKILL.md
  - docs-eng-process/.claude-templates/skills/openup-create-test-plan/SKILL.md
  - docs-eng-process/.claude-templates/skills/openup-create-risk-list/SKILL.md
  - docs-eng-process/.claude-templates/skills/openup-init/SKILL.md   # emit starter config
  - docs-eng-process/.claude-templates/CLAUDE.md                     # precedence rule
  - docs/roadmap.md                                                  # T-018 status
claimed-by: null
claimed-at: null
worktree: null
last-synced: ""
---

# T-018 — `docs/project-config.yaml` context/rules injection

## Story

> **As a** team running OpenUP on a real project with its own stack, domain, and standards
> **I want** one project-owned file whose `context:` and per-artifact `rules:` are injected as `<project-context>` / `<project-rules>` into every `/openup-create-*` prompt
> **So that** project-specific facts and criteria are applied uniformly — instead of leaking into `CLAUDE.md` or being re-typed in every prompt — while the framework rubrics stay framework-owned.

INVEST check:
✅ Independent (no dependency on other clarity-plan tasks) · ✅ Negotiable (injection is additive, opt-in via file presence) · ✅ Valuable (single home for "true here, not everywhere" facts — the most-edited content in derived `CLAUDE.md`s) · ✅ Estimable (one example file, one doc, small edits to 9 skills + CLAUDE.md) · ✅ Small (no code; markdown + yaml only) · ✅ Testable (a `rules.use-case` entry must be injected and satisfied; absence must revert behavior)

## Analysis Context

- **Domain.** The artifact-authoring skills (`/openup-create-*`) and project-level
  configuration. This is the one un-implemented item (#2) of the 2026-05-13 OpenSpec
  plan, absorbed into the Clarity plan as T-018.
- **Scope boundaries.** This task adds a *project-owned* layer that is **additive** to the
  framework rubrics; it does NOT modify any `.claude/rubrics/*-rubric.md` (those stay
  framework-owned), does NOT add a YAML schema / linter (start unvalidated — explicitly
  out of scope per the source plan), and does NOT inject into non-artifact skills
  (`create-pr`, `create-handoff`, `create-documentation` produce outputs, not project
  specs). Injection covers the seven artifact create skills that have a rubric/work-product:
  vision, use-case, architecture-notebook, iteration-plan, task-spec, test-plan, risk-list.
- **Definition of done.** A project can drop a `docs/project-config.yaml`; every artifact
  create skill reads it, injects `<project-context>` and its own `rules.<artifact-type>`
  block as `<project-rules>`, and applies them additively under a documented precedence;
  removing the file reverts to framework-default behavior with no edits.

**Assumption:** The `rules:` map is keyed by **artifact type = the `/openup-create-<type>`
skill suffix** (`use-case`, `task-spec`, `architecture-notebook`, …), so a reader maps a
rule block to its skill by name. *(Vetoable at review.)*

**Assumption:** The per-skill injection instructions are single-sourced into one shared
doc (`docs-eng-process/project-config.md`); each skill carries a compact step that points
to it plus its own artifact-type key, rather than duplicating the full mechanism nine
times. *(Vetoable at review.)*

**Assumption:** This framework repo does **not** commit a live `docs/project-config.yaml`
(it has no project-specific stack/domain to inject); the example template + `/openup-init`
emitter are the deliverables, and the injection is exercised by a temporary fixture at
verification time. *(Vetoable at review.)*

## Requirements

1. `docs-eng-process/templates/project-config.example.yaml` exists, is valid YAML, and has
   a top-level `context:` block plus a `rules:` map keyed by artifact type (the
   `/openup-create-<type>` suffix: `vision`, `use-case`, `architecture-notebook`,
   `iteration-plan`, `task-spec`, `test-plan`, `risk-list`).
   - **Given** the example template **When** it is parsed as YAML **Then** parsing
     succeeds and the result has a `context` key and a `rules` mapping whose keys are a
     subset of the seven artifact types.
2. `docs-eng-process/project-config.md` documents the mechanism: file location, the two
   top-level keys, the artifact-type key convention, the `<project-context>` /
   `<project-rules>` injection wrappers, the precedence **framework rubric → project rules
   → task-spec safeguards**, and the list of consuming skills.
   - **Given** the mechanism doc **When** a reader looks for how rules are applied **Then**
     it states the injection wrappers, names the precedence order, and says project rules
     are additive (may add a criterion, may not waive a framework one).
3. Each of the seven artifact create skills carries a "Load Project Config" step that reads
   `docs/project-config.yaml`, injects `context:` as `<project-context>` and its own
   `rules.<artifact-type>` as `<project-rules>`, and treats the rules as additive.
   - **Given** any of the seven `openup-create-*/SKILL.md` files **When** the Process
     section is read **Then** it contains a step naming `docs/project-config.yaml`, the
     `<project-context>`/`<project-rules>` wrappers, and that skill's own artifact-type key.
4. The injection is **absence-safe**: when `docs/project-config.yaml` is missing, the step
   is skipped and framework-default behavior is unchanged.
   - **Given** a repo with no `docs/project-config.yaml` **When** a create skill runs the
     Load Project Config step **Then** the step instructs skipping it with no error and no
     change to the artifact the skill would otherwise produce.
5. `/openup-init` emits a starter `docs/project-config.yaml` (seeded from the example
   template) as part of project setup.
   - **Given** the `openup-init` skill **When** its process / generated-documents section
     is read **Then** it directs writing a starter `docs/project-config.yaml` from
     `docs-eng-process/templates/project-config.example.yaml`.
6. `CLAUDE.md` (the short agent instructions) documents the project-config precedence and
   points to `docs-eng-process/project-config.md`.
   - **Given** the templates `CLAUDE.md` **When** a reader scans the quality/rubric area
     **Then** it states the framework-rubric → project-rules → safeguards precedence and
     links the mechanism doc.

## Behavior Delta

How this task changes **existing product behavior** (Ring 1: `docs/product/`).

**n/a — all Added.** T-018 adds a project-config layer to the *framework workflow skills*
and templates; it changes no Ring-1 *product* artifact (`docs/product/` is unpopulated in
this framework repo). All behavior is new: a previously-absent config file and the skills'
new opt-in step to consume it.

**Added** — behavior that did not exist before:
- A project-owned `docs/project-config.yaml` whose `context:`/`rules:` are injected into
  every `/openup-create-*` artifact prompt.
- A "Load Project Config" step in the seven artifact create skills.
- `/openup-init` emitting a starter config.

## Entities

- **project-config example** (new) — `docs-eng-process/templates/project-config.example.yaml`
- **mechanism doc** (new) — `docs-eng-process/project-config.md`
- **artifact create skills** (modified, ×7) — `…/skills/openup-create-{vision,use-case,architecture-notebook,iteration-plan,task-spec,test-plan,risk-list}/SKILL.md`
- **init skill** (modified) — `…/skills/openup-init/SKILL.md`
- **agent instructions** (modified) — `docs-eng-process/.claude-templates/CLAUDE.md`
- **framework rubrics** (read-only) — `…/rubrics/*-rubric.md` (stay framework-owned; project rules layer on top, never edited here)

## Approach

Single-source the mechanism in one new `docs-eng-process/project-config.md` (location,
schema, artifact-type keys, the `<project-context>`/`<project-rules>` wrappers, precedence).
Each artifact create skill then gets a compact, uniform "Load Project Config" step that
points at that doc and names only its own artifact-type key — keeping nine edits small and
drift-resistant rather than pasting the full mechanism into each. The config is project-owned
and injection is gated on file presence, so the framework default is unchanged when the file
is absent. Framework rubrics are untouched; project rules are explicitly additive under a
documented precedence (`framework rubric → project rules → task-spec safeguards`).

## Structure

**Add:**
- `docs-eng-process/templates/project-config.example.yaml`
- `docs-eng-process/project-config.md`

**Modify:**
- `docs-eng-process/.claude-templates/skills/openup-create-vision/SKILL.md` — Load Project Config step (`rules.vision`)
- `docs-eng-process/.claude-templates/skills/openup-create-use-case/SKILL.md` — step (`rules.use-case`)
- `docs-eng-process/.claude-templates/skills/openup-create-architecture-notebook/SKILL.md` — step (`rules.architecture-notebook`)
- `docs-eng-process/.claude-templates/skills/openup-create-iteration-plan/SKILL.md` — step (`rules.iteration-plan`)
- `docs-eng-process/.claude-templates/skills/openup-create-task-spec/SKILL.md` — step (`rules.task-spec`)
- `docs-eng-process/.claude-templates/skills/openup-create-test-plan/SKILL.md` — step (`rules.test-plan`)
- `docs-eng-process/.claude-templates/skills/openup-create-risk-list/SKILL.md` — step (`rules.risk-list`)
- `docs-eng-process/.claude-templates/skills/openup-init/SKILL.md` — emit starter `docs/project-config.yaml`
- `docs-eng-process/.claude-templates/CLAUDE.md` — precedence rule + pointer
- `docs/roadmap.md` — T-018 row → done

**Do not touch:**
- `.claude/rubrics/*-rubric.md` — framework-owned; project rules layer on top, never edited here.
- `…/skills/openup-create-{pr,handoff,documentation}/SKILL.md` — these emit workflow outputs, not project specs; out of scope for project-rule injection.
- `scripts/` — no schema/linter for the YAML (explicitly out of scope per the source plan).

## Operations

- [x] Add `docs-eng-process/templates/project-config.example.yaml` (valid YAML: `context:` + `rules:` keyed by the seven artifact types).
- [x] Add `docs-eng-process/project-config.md` (mechanism + precedence + consuming-skill list).
- [x] Add a uniform "Load Project Config" step to each of the seven artifact create skills, each naming its own `rules.<type>` key.
- [x] Update `openup-init` to emit a starter `docs/project-config.yaml` from the example.
- [x] Add the precedence rule + pointer to `docs-eng-process/.claude-templates/CLAUDE.md`.
- [x] (tester) Verify: example parses as YAML; a temporary `rules.use-case` fixture is named by the injection step and removing the file reverts behavior; `openup-spec-scenarios.py check` on this plan exits 0; roadmap synced.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.).
- The existing `/openup-create-*` SKILL.md structure (`## Process` + numbered steps) — the new step matches that shape.
- The rubric ✅/❌ idiom — project rules are graded the same way, additively.

## Safeguards

- **Token / size budget.** Example yaml ≤ ~40 lines; mechanism doc ≤ ~120 lines; per-skill
  step ≤ ~15 lines. Additive only.
- **Reversibility.** Delete the two new files + the per-skill steps; no code, no migrations,
  no rubric edits. A consuming project reverts by deleting its `docs/project-config.yaml`.
- **No-go zones.** Do NOT edit `.claude/rubrics/*`; do NOT let a project rule waive a
  framework rubric criterion or a task-spec safeguard (precedence is additive-only); do NOT
  add a schema/validator for the YAML.
- **Parity invariant.** Template edits are the tracked source of truth (`.claude/` is
  gitignored/absent in this container); keep the seven skills' steps uniform.

## Verification

- `python3 -c "import yaml,sys; d=yaml.safe_load(open('docs-eng-process/templates/project-config.example.yaml')); assert 'context' in d and 'rules' in d"` exits 0.
- `grep -l project-config.yaml docs-eng-process/.claude-templates/skills/openup-create-*/SKILL.md` lists the seven artifact skills (+ init).
- Temporary fixture: write `docs/project-config.yaml` with `rules: {use-case: ["Must reference a stakeholder by name"]}`; confirm `openup-create-use-case`'s step names `rules.use-case` for injection; delete the fixture and confirm no tracked change remains (revert).
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-018/plan.md` exits 0.
- Grade the final artifact against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

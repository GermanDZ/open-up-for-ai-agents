---
id: T-114
title: "`/openup-init` template completeness — project-status/roadmap templates + input-request reference"
status: ready
priority: medium
estimate: 1 session
plan: docs/iteration-plans/2026-07-14-bootstrap-overhead-fixes.md
depends-on: []
blocks: []
touches:
  - docs-eng-process/templates/project-status.md
  - docs-eng-process/templates/roadmap.md
  - docs-eng-process/procedures/openup-init.md
  - docs-eng-process/.claude-templates/skills/openup-init/SKILL.md
last-synced: ""
---

# T-114 — `/openup-init` template completeness — project-status/roadmap templates + input-request reference

## Story

> **As an** agent bootstrapping a fresh project via `/openup-init`
> **I want** `docs/project-status.md`, `docs/roadmap.md`, and the
> stakeholder-brief file authored from committed templates the same way
> `docs/project-config.yaml` already is
> **So that** a fresh bootstrap stops freehand-authoring three files from
> scratch and stops live-hunting for the input-request convention — observed
> in a live session that never referenced the existing, ready
> `docs-eng-process/templates/input-request.md`

INVEST check:
✅ Independent (new templates + one procedure edit, no dependency) ·
✅ Negotiable (exact template wording/placeholders) · ✅ Valuable (closes a
concrete, evidenced gap in the framework's stated "one-command
initialization" promise) · ✅ Estimable (2 new small files + 1 procedure
edit) · ✅ Small · ✅ Testable (the templates' rendered output must match what
`/openup-init` already freehands today — a diffable equivalence, not new
content)

## Analysis Context

- **Domain.** `docs-eng-process/templates/` (the framework's template
  library) and `docs-eng-process/procedures/openup-init.md` (the skill that
  consumes them at bootstrap time).
- **Scope boundaries.** Does not redesign the *content* of
  `project-status.md`/`roadmap.md` — the new templates are a byte-equivalent
  lift of what `openup-init.md` §3 already freehands inline today (same
  fields, same placeholders), not a new schema. Does not touch
  `docs/project-config.yaml`'s existing template flow (already correct,
  serves as the pattern this task extends to the other two files). Does not
  touch any other skill.
- **Definition of done.** `/openup-init` copies three templates
  (`project-status.md`, `roadmap.md`, `input-request.md`) plus the existing
  `project-config.example.yaml`, instead of freehanding two of them and never
  referencing the third.

No open questions — the fix is a direct, unambiguous lift of already-decided
content into template files; nothing here changes what a fresh bootstrap
*produces*, only how it's produced.

## Requirements

1. `docs-eng-process/templates/project-status.md` exists and matches the
   structure `openup-init.md` §3 currently freehands, with the same
   `[PLACEHOLDER]` bracket convention the skill's other templates use.
   - **Given** the new template file, **When** its fields are compared to
     `openup-init.md`'s current inline `docs/project-status.md` markdown,
     **Then** every field present today (`Project`, `Phase`, `Iteration`,
     `Iteration Goal`, `Status`, `Current Task`, `Started`, `Last Updated`,
     `Updated By`) is present in the template, unchanged in meaning.

2. `docs-eng-process/templates/roadmap.md` exists and matches the structure
   `openup-init.md` §3 currently freehands.
   - **Given** the new template file, **When** compared to `openup-init.md`'s
     current inline `docs/roadmap.md` markdown, **Then** the same T-001/T-002
     placeholder-row shape is present, unchanged in meaning.

3. `openup-init.md` copies all three templates (project-status, roadmap,
   input-request) the same way it already copies `project-config.example.yaml`.
   - **Given** a fresh bootstrap run, **When** `/openup-init` reaches its
     "Generate Initial Documents" step, **Then** its instructions say to copy
     `docs-eng-process/templates/project-status.md` and
     `docs-eng-process/templates/roadmap.md` (filling the bracket
     placeholders) instead of freehanding the markdown inline, and to copy
     `docs-eng-process/templates/input-request.md` into
     `docs/input-requests/` for the stakeholder-brief step instead of only
     `mkdir -p`ing the directory.

4. The rendered output is unchanged — this is a mechanism change, not a
   content change.
   - **Given** the new copy-and-fill instructions, **When** `/openup-init`
     runs end to end, **Then** the resulting `docs/project-status.md` and
     `docs/roadmap.md` are structurally identical to what the pre-T-114
     freehand instructions would have produced (same fields, same shape).

## Behavior Delta

`n/a — all Added`. This changes *how* `/openup-init` produces its bootstrap
files (mechanism), not *what* it produces (content) — Requirement 4 makes
that explicit and checkable. No existing documented product behavior changes
observably.

## Entities

- **`docs-eng-process/templates/project-status.md`** (new)
- **`docs-eng-process/templates/roadmap.md`** (new)
- **`docs-eng-process/procedures/openup-init.md`** (modified) — §3 "Generate Initial Documents"
- **`docs-eng-process/templates/input-request.md`** (read-only, pre-existing — now referenced)
- **`docs-eng-process/templates/project-config.example.yaml`** (read-only reference — the pattern being extended)

## Approach

Lift the exact markdown `openup-init.md` §3 already freehands for
`project-status.md` and `roadmap.md` into two new template files (same
bracket-placeholder convention the skill already uses for
`[PROJECT_NAME]`/`[DATE]`/etc.), then rewrite §3's instructions to `cp` and
fill those templates the same way it already handles
`project-config.example.yaml` — a "lift what's already decided into a file,"
not a redesign. Add one line pointing the stakeholder-brief step at the
existing `input-request.md` template instead of only creating an empty
directory.

## Structure

**Add:**
- `docs-eng-process/templates/project-status.md`
- `docs-eng-process/templates/roadmap.md`

**Modify:**
- `docs-eng-process/procedures/openup-init.md` — §3 copies all three
  templates instead of freehanding two and ignoring the third
- `docs-eng-process/.claude-templates/skills/openup-init/SKILL.md` —
  regenerated mirror

**Do not touch:**
- `docs-eng-process/templates/project-config.example.yaml` — already correct,
  the pattern this task extends
- Any other procedure file

## Operations

- [ ] (developer) Create `docs-eng-process/templates/project-status.md`, lifting the exact structure from `openup-init.md`'s current §3 inline markdown.
- [ ] (developer) Create `docs-eng-process/templates/roadmap.md`, lifting the exact structure from `openup-init.md`'s current §3 inline markdown.
- [ ] (developer) Rewrite `openup-init.md` §3 to copy+fill all three templates (project-status, roadmap, input-request) alongside the existing project-config.example.yaml copy step.
- [ ] `python3 scripts/render-skills-mirror.py --write && scripts/sync-templates-to-claude.sh && python3 scripts/check-skills-guide.py --write && python3 scripts/check-model-tiers.py --write`
- [ ] `git diff harness-optional -- docs-eng-process/procedures/openup-next.md`
- [ ] `python3 scripts/render-skills-mirror.py --check && python3 scripts/check-skills-guide.py --check && python3 scripts/check-model-tiers.py --check && python3 scripts/check-docs.py`

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format
- `docs-eng-process/project-config.md` — the copy-a-template pattern this task extends from `project-config.example.yaml` to the other two files

## Safeguards

- **Token / size budget.** Two small new template files (a few dozen lines
  each) + one procedure section rewrite — no other file touched.
- **Reversibility.** Revert the two new template files and the `openup-init.md`
  §3 edit; nothing else depends on this.
- **No-go zones.** The templates must remain byte-equivalent in *meaning* to
  what `openup-init.md` currently freehands (Requirement 4) — this is a
  mechanism change, not a chance to redesign the bootstrap file shapes.
  `openup-init.md`'s "Gate awareness — scaffold with Bash, not Write/Edit"
  section stays true: the new copy commands must still run via Bash (`cp` is
  already gate-exempt, same as the existing `project-config.example.yaml`
  copy), never `Write`/`Edit`.

## Verification

- `python3 scripts/render-skills-mirror.py --check`
- `python3 scripts/check-skills-guide.py --check`
- `python3 scripts/check-model-tiers.py --check`
- `python3 scripts/check-docs.py`
- `git diff harness-optional -- docs-eng-process/procedures/openup-next.md` — must be empty
- Manual structural comparison: the new templates' fields vs. `openup-init.md`'s
  pre-edit inline markdown (Requirement 4)

## Success Measures

We expect the next real `/openup-init` bootstrap run to show **zero** freehand
heredoc authoring of `docs/project-status.md`/`docs/roadmap.md` and **zero**
live searches for the input-request convention (a magnitude of exactly 0
occurrences of either pattern, vs. both observed in the live T-002 bootstrap
transcript this task is fixing). Instrumentation: a re-read of that next
bootstrap session's transcript (tool-call descriptions), the same method used
to find the original gap. Read-back: after the next real fresh-project
bootstrap, whenever that occurs (this repo's own delivery loop is the only
consumer).

## Rollout

**Flagged?** No — a procedure-wording + template-file change with no runtime
toggle; the only "rollout" is the next `/openup-init` invocation reading the
updated instructions. Not applicable in the feature-flag sense.

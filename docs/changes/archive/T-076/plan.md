---
id: T-076
title: Development Case config (`process:` section + archetypes)
status: done
priority: high   # critical | high | medium | low
estimate: 1 session
plan: docs/explorations/2026-07-13-phase-aware-loop-redesign.md
depends-on: []
blocks: [T-077]
touches:
  - scripts/
  - docs/changes/
  - docs-eng-process/
  - .claude/
  - tests/
last-synced: ""
---

# T-076 — Development Case config (`process:` section + archetypes)

## Story

> **As a** project maintainer adopting OpenUP for a specific project
> **I want** to tailor the whole delivery lifecycle from one config block —
> declaring an archetype (quick | mvp | product) that sets per-phase defaults
> (iteration budgets, required artifacts, exit criteria, milestone formality)
> **So that** ceremony matches scope by data rather than being one-size-fits-all,
> and the same phase-aware engine (T-077+) runs a throwaway script, an MVP, or a
> full product without code changes — with the `quick` archetype degenerating to
> today's `/openup-quick-task` cost so the design passes its own efficiency bar.

INVEST — ✅ Independent · ✅ Negotiable · ✅ Valuable · ✅ Estimable · ✅ Small · ✅ Testable

## Analysis Context

- **Domain.** OpenUP's **Development Case** — the project's own tailoring of the
  method (`project_process_tailoring/guidances/concepts/development-case.md`).
  This task makes it *machine-readable*: a `process:` section in the already-
  existing project-owned config `docs/project-config.yaml` (the project-rules
  home from T-018). It is the second slice of the phase-aware program (§3.2 /
  §5.2 of the redesign exploration) and the data that T-077's plan-iteration and
  T-078's milestone-review will read.
- **Config layer, not framework layer.** `docs/project-config.yaml` is
  **project-owned** (a consuming project authors it); the framework ships only a
  commented **example** (`docs-eng-process/templates/project-config.example.yaml`)
  and the starter block `/openup-init` emits. This task adds the schema + example
  + validation + docs — it does **not** hand a live `process:` block to any
  particular project except this repo's own dogfood copy.
- **Archetype = defaults, explicit keys = overrides.** `archetype` (quick | mvp |
  product) selects a per-phase default set; any explicitly-written phase key
  overrides that default. This mirrors the existing `rules:` precedence
  (framework rubric → project rules → task-spec safeguards) already documented in
  `docs-eng-process/project-config.md` — the `process:` section extends the same
  chain and never *waives* a framework rubric criterion or a safeguard, only
  sets ceremony levels.
- **Read side is validation-only here.** No loop consumes `process:` yet — T-077
  (plan-iteration) and T-078 (milestone-review) are the consumers. This task is
  bounded to: (1) define the section + archetype defaults, (2) validate it, (3)
  document the Development Case mapping + precedence, (4) emit a starter. It does
  **not** change `openup-next` resolve order, does **not** generate lanes, does
  **not** wire milestone reviews.
- **Honest validation scope.** `check-docs.py` validates the `process:` section
  **structurally** (known archetype, known phase keys, well-typed values, no
  waiving of a safeguard) — it does not assert the archetype is *appropriate* for
  the project (a human judgment). Absence of a `process:` section is **not** an
  error (backward-compatible — existing projects keep working); a present-but-
  malformed section **is**.
- **Quick archetype is the efficiency guardrail.** The redesign's headline risk
  is ceremony creep. The `quick` archetype must set defaults that degenerate to
  ~today's `/openup-quick-task` behavior (near-empty Inception, Elaboration
  skipped, one Construction iteration, `milestone_review: auto-assess`). This is
  asserted as a defaults-mapping requirement, testable against the documented
  archetype table.

## Requirements

1. **`process:` section + archetype defaults in the config schema.**
`docs/project-config.yaml` gains a `process:` section: an `archetype`
(`quick | mvp | product`) that sets per-phase defaults, a `phases:` map
(inception/elaboration/construction/transition, each with `iterations`,
`artifacts`, `exit`, `parallel` as applicable), and a `milestone_review`
(`human | auto-assess`). The framework example
(`docs-eng-process/templates/project-config.example.yaml`) documents the full
shape as commented YAML; the three archetype default sets are documented in
`docs-eng-process/project-config.md`.

> **Given** a `docs/project-config.yaml` whose `process:` block sets
> `archetype: mvp` and overrides `construction: { iterations: many }`,
> **When** validation runs,
> **Then** the section is accepted, the `mvp` defaults apply to every phase key
> not explicitly written, and the explicit `construction` override wins over the
> `mvp` default for that phase.

2. **`quick` archetype degenerates to today's quick-task ceremony.**
The documented `quick` archetype default set encodes: Inception near-empty,
Elaboration skipped, a single Construction iteration, and
`milestone_review: auto-assess` — so a `quick` project incurs ~today's
`/openup-quick-task` cost (the efficiency guardrail from the exploration's
risks).

> **Given** `process: { archetype: quick }` with no phase overrides,
> **When** the archetype defaults are resolved,
> **Then** Elaboration resolves to skipped, Construction to a single iteration,
> and `milestone_review` to `auto-assess` — matching the documented `quick`
> default table (no `human` milestone gate introduced for quick work).

3. **`check-docs.py` validates the `process:` section structurally.**
`check-docs.py` gains a validator for `process:`: unknown archetype, unknown
phase key, mis-typed value (e.g. `iterations` not int/`auto`/`many`), or an
invalid `milestone_review` value is a **blocking** error naming the offending
key; a well-formed section — or an **absent** section — passes. A `process:`
section may not carry a key that would waive a framework rubric criterion or a
safeguard (precedence is additive only).

> **Given** a `process:` block with `archetype: enterprise` (not one of
> quick/mvp/product),
> **When** `python3 scripts/check-docs.py` runs,
> **Then** it exits non-zero with an error naming `archetype` and the offending
> value; **and** a config with **no** `process:` section exits 0 (backward-
> compatible).

4. **`openup-doctor` surfaces `process:` status as a read-only, process-specific signal.**
`openup-doctor.py` gains a read-only `process-config` check reporting the
Development Case status: `INFO` when the section is absent (framework defaults
apply) or valid (`archetype=<x>`), and a `WARNING` naming the offending key and
pointing at `scripts/check-docs.py` when the `process:` section is structurally
invalid. This check **never writes** and **never raises `ERROR` itself** — it
adds a targeted, actionable message (mirroring the existing
`check_section_status_drift` warning). Doctor's overall exit code is governed by
its normal `ERROR` rule; a malformed config still fails the run because the
existing aggregate already runs `check-docs.py` (R3), which is the escalation
path — the dedicated check is the human-readable pointer, not a second gate.

> **Given** a `docs/project-config.yaml` with a malformed `process:` section,
> **When** the `process-config` check runs (`check_process_config(repo)`),
> **Then** it returns a `WARNING`-severity finding naming the offending key and
> referencing `check-docs.py` (never `ERROR`); **and** for a valid or absent
> section it returns only an `INFO` finding (`archetype=<x>` or "no Development
> Case configured").

5. **Development Case mapping + precedence documented; `/openup-init` emits a starter.**
`docs-eng-process/project-config.md` documents the `process:` section as OpenUP's
Development Case made machine-readable — the three archetype default tables and
the precedence extension — and `/openup-init` appends a **commented** `process:`
starter block to a newly-created `docs/project-config.yaml` (opt-in, following
the existing commented-starter convention for `environments:`).

> **Given** a fresh project running `/openup-init`,
> **When** the config starter is emitted,
> **Then** `docs/project-config.yaml` contains a commented `process:` starter
> naming the three archetypes; **and** `docs-eng-process/project-config.md`
> carries the Development Case mapping + archetype default tables + precedence
> note.

## Behavior Delta

- **Added.** `process:` section schema + three archetype default sets;
  `check-docs.py` structural validator for `process:`; `openup-doctor.py`
  `process:`-drift warning; Development Case section in
  `docs-eng-process/project-config.md`; commented starter in
  `docs-eng-process/templates/project-config.example.yaml` + `/openup-init`
  emission; hermetic tests.
- **Modified.** `docs/project-config.yaml` gains an optional `process:` section
  (absent = unchanged behavior). `check-docs.py` / `openup-doctor.py` gain one
  new check each; existing checks unchanged. No loop behavior changes (T-077/T-078
  are the consumers).
- **Removed.** n/a.

## Definition of Done

- [ ] `process:` section defined: archetype (quick|mvp|product) + per-phase
      defaults + `milestone_review`; documented in the example + project-config.md (R1).
- [ ] `quick` archetype default table degenerates to today's quick-task ceremony (R2).
- [ ] `check-docs.py` structural validator: malformed blocks, absent passes,
      no-waiving-safeguards enforced (R3).
- [ ] `openup-doctor.py` read-only `process-config` check: WARNING on invalid,
      INFO on valid/absent; never writes, never raises ERROR itself (R4).
- [ ] Development Case mapping + precedence in `project-config.md`;
      `/openup-init` commented starter (R5).
- [ ] Hermetic tests cover: archetype default resolution + override, quick
      degeneration, invalid archetype/phase/value errors, absent-section pass,
      doctor warning.
- [ ] `check-docs.py` + fence green (`--base harness-optional`); `.claude/` re-synced
      if the `openup-init` procedure changed.

## Operations

- [x] (developer) Define the `process:` schema + three archetype default sets (R1, R2)
- [x] (developer) Add the `check-docs.py` structural validator for `process:` (R3)
- [x] (developer) Add the `openup-doctor.py` `process:`-drift warning (R4)
- [x] (developer) Document Development Case mapping + precedence in `project-config.md`; add commented starter to the example + `/openup-init` (R5)
- [x] (tester) Hermetic tests for R1–R4
- [x] (developer) Run check-docs + fence (`--base harness-optional`); sync `.claude/` if the openup-init procedure changed

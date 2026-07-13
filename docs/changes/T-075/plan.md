---
id: T-075
title: openup-lifecycle.py status + milestone decision records (derived phase view)
status: in-progress
priority: high   # critical | high | medium | low
estimate: 1 session
plan: docs/explorations/2026-07-13-phase-aware-loop-redesign.md
depends-on: []
blocks: [T-077, T-078]
touches:
  - scripts/
  - docs/changes/
  - docs/product/
  - docs-eng-process/
  - tests/
last-synced: ""
---

# T-075 — openup-lifecycle.py status + milestone decision records

## Story

> **As a** maintainer (or automated loop) driving OpenUP delivery
> **I want** a deterministic, read-only answer to "what phase are we in and what
> does this milestone still need", derived from repo facts plus recorded human
> go/no-go decisions — not a hand-set label in `project-status.md`
> **So that** every later slice of the phase-aware program (T-076…T-079) reads
> lifecycle state from one honest source, and this first step ships zero risk
> (advisory only — no loop behavior change).

INVEST — ✅ Independent · ✅ Negotiable · ✅ Valuable · ✅ Estimable · ✅ Small · ✅ Testable

## Analysis Context

- **Domain.** The OpenUP three-layer state machine (project lifecycle →
  iteration → micro-increment). Today only the inner micro-increment layer is
  mechanized (board/lease/fence); the phase is a hand-set string in
  `docs/project-status.md` / `.openup/state.json`. This task adds the *read side*
  of the outer project-lifecycle layer — a derived view, sibling to
  `openup-board.py`.
- **Source of truth split.** Two inputs decide "current phase":
  1. **Milestone decision records** — `docs/product/milestones/<phase>-<cycle>.md`,
     each recording a human go/no-go at a phase boundary (LCO/LCA/IOC/Product
     Release). The *record* is authoritative for "phase advanced" — the script
     only reads it. A `cycle` counter supports OpenUP's "start another
     development cycle" (return to Construction after partial Transition).
  2. **Work-product instances + roadmap facts** — used only to compute
     *per-milestone criteria state* (what the current milestone still needs),
     never to decide the phase. Criteria detection is honest about what a script
     can mechanically verify (artifact exists + `status:` frontmatter from T-038
     typed traceability) vs. what only a human can judge (e.g. "architecture
     validated" = a tested skeleton, not a notebook) — the latter is carried by
     the milestone record, not asserted by the script.
- **No fabricated history.** When no milestone record exists yet, `status`
  falls back to the phase already recorded in `.openup/state.json` (currently
  `construction`) — it does NOT invent retroactive go/no-go records. Milestone
  records are authoritative *going forward*; the fallback keeps the derived view
  honest for a project (like this one) that predates the records.
- **Phase becomes a derived cache.** `phase` in `.openup/state.json` stops being
  hand-set via `project-status.md` and becomes a cache stamped from
  `openup-lifecycle.py status`. A `stamp-phase` verb writes it idempotently; no
  loop consumes the new value differently yet (advisory).
- **Scope boundaries.** This task is READ-ONLY with respect to the loop: it adds
  a derived view + a data format + a manifest/CLI-ref entry + an idempotent
  phase-cache stamp. It does NOT change `openup-next` resolve order, does NOT add
  plan-iteration/assess-iteration/milestone-review paths (T-077/T-078), does NOT
  wire `/openup-phase-review` into the automated loop (T-078), does NOT add the
  Development Case `process:` config (T-076). The milestone-record *format* and
  directory are defined here; automated *writing* of records via the loop is
  T-078 (a human may author one by hand meanwhile, following the documented
  format).
- **Never-hand-edit rule.** `openup-lifecycle.py status` output (and any file it
  derives) follows the same rule as `openup-board.py` / `docs/roadmap.md`: it is
  regenerated, never hand-edited. Milestone *records* ARE hand-authored (they
  encode a human decision) — that is the deliberate exception, exactly like a
  ticked Operations checkbox is sanctioned hand state.

## Requirements

1. **`openup-lifecycle.py status` derives the current phase (read-only).**
`scripts/openup-lifecycle.py status` prints the current phase, cycle, and
per-milestone criteria state, computed from milestone records (authoritative for
phase) with a fallback to the recorded state phase. Read-only; supports `--json`.

> **Given** a repo whose latest milestone record is `elaboration-1.md` with
> decision `GO` (resulting phase `construction`),
> **When** I run `python3 scripts/openup-lifecycle.py status --json`,
> **Then** it exits 0 and reports `phase: construction`, `cycle: 1`, and a
> `milestones` object listing the current (Construction/IOC) milestone's
> criteria — without writing any file.

> **Given** a repo with **no** `docs/product/milestones/` records,
> **When** I run `python3 scripts/openup-lifecycle.py status --json`,
> **Then** it falls back to the `phase` in `.openup/state.json` (e.g.
> `construction`), reports it, and flags `source: state-fallback` so the caller
> knows the phase is not yet milestone-anchored.

2. **Per-milestone criteria are computed mechanically and honestly.**
For the current phase, `status` reports each milestone-exit criterion as
`met | unmet | human-judgment` — deriving `met/unmet` only from facts a script
can verify (artifact instance present + its `status:` frontmatter), and marking
criteria that require human judgment as `human-judgment` rather than guessing.

> **Given** the current phase is `inception` and a `vision` instance exists with
> `status: implemented` but no `risk-list` instance exists,
> **When** I run `status --json`,
> **Then** the Inception/LCO criteria show the vision criterion `met` and the
> risk-list criterion `unmet`, and any "stakeholder concurrence" criterion is
> reported `human-judgment` (never auto-`met`).

3. **Milestone decision records: defined format + directory.**
`docs/product/milestones/<phase>-<cycle>.md` is defined with a documented
frontmatter schema (phase, cycle, milestone name, decision `GO|NO-GO|CONDITIONAL`,
date, decided-by, evidence links) plus a `README.md` describing the format.
`openup-lifecycle.py` reads these records to determine the authoritative phase.

> **Given** a well-formed `docs/product/milestones/inception-1.md` with
> `decision: GO`,
> **When** `openup-lifecycle.py status` runs,
> **Then** it treats Inception as passed and reports the resulting phase
> (`elaboration`) as current; **and** a malformed record (missing `decision`)
> causes a clear non-zero error naming the offending file, not a silent wrong
> phase.

4. **`phase` in state becomes a derived cache (`stamp-phase`).**
`openup-lifecycle.py stamp-phase` writes the derived phase into
`.openup/state.json` idempotently, so `phase` is sourced from the derived view
rather than hand-set. Running it twice makes no second change.

> **Given** `.openup/state.json` has `phase: elaboration` but the milestone
> records resolve the current phase to `construction`,
> **When** I run `python3 scripts/openup-lifecycle.py stamp-phase`,
> **Then** state's `phase` becomes `construction`; **and** running the same
> command again leaves the file byte-identical (idempotent).

5. **Distribution: manifest + CLI reference.**
`scripts/openup-lifecycle.py` is registered in `scripts/process-manifest.txt`
and documented in `docs-eng-process/script-cli-reference.md`, so every
install/update path ships it and agents can invoke it without a `--help`
round-trip.

> **Given** a fresh consuming project synced from the framework,
> **When** the manifest-driven install runs,
> **Then** `scripts/openup-lifecycle.py` is present and its `status` /
> `stamp-phase` signatures are listed in `script-cli-reference.md`.

## Behavior Delta

- **Added.** `scripts/openup-lifecycle.py` (`status`, `stamp-phase`);
  `docs/product/milestones/` directory + record format + `README.md`; manifest +
  CLI-reference entries; a hermetic test module.
- **Modified.** `phase` in `.openup/state.json` is now *derivable* via
  `stamp-phase` (previously only hand-set through `project-status.md`). No
  existing consumer's behavior changes — the value is stamped from the same
  phase it already held unless a milestone record moves it.
- **Removed.** n/a.

## Definition of Done

- [ ] `scripts/openup-lifecycle.py status [--json]` — read-only, derives phase +
      cycle + per-milestone criteria (R1, R2); state-fallback flagged.
- [ ] `docs/product/milestones/` format + `README.md`; records parsed as the
      authoritative phase source; malformed record → clear error (R3).
- [ ] `openup-lifecycle.py stamp-phase` — idempotent phase-cache write (R4).
- [ ] Registered in `process-manifest.txt` + `docs-eng-process/script-cli-reference.md` (R5).
- [ ] Hermetic tests in `tests/` cover: milestone-anchored phase, state-fallback,
      criteria met/unmet/human-judgment, malformed record error, stamp idempotency.
- [ ] `check-docs.py` + fence green; no hand-edit of `roadmap.md` / `project-status.md`.

## Operations

- [ ] (developer) Implement `scripts/openup-lifecycle.py` (`status`, `stamp-phase`)
- [ ] (developer) Define `docs/product/milestones/` format + `README.md`
- [ ] (developer) Register in `process-manifest.txt` + `script-cli-reference.md`
- [ ] (tester) Hermetic tests for R1–R4
- [ ] (developer) Run check-docs + fence; sync `.claude/` if any skill/template touched

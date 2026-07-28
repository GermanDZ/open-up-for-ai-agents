---
id: T-161
title: "Phase resolves to `inception` whenever no lane is active, routing mature projects into a fresh-Inception plan"
status: ready
priority: high
estimate: 1 session
plan: ""
depends-on: []
blocks: []
last-synced: ""
touches:
  - scripts/openup-lifecycle.py
  - tests/test_lifecycle.py
  - docs-eng-process/script-cli-reference.md
  - docs/roadmap.md
---

# T-161 — Phase resolves to `inception` whenever no lane is active, routing mature projects into a fresh-Inception plan

## Story

> **As a** maintainer running `/openup-next` (or an unattended `/loop`) with no lane in flight
> **I want** the derived phase to reflect the project's actual phase
> **So that** a drained roadmap stops the loop cleanly instead of sending it to author a fresh Vision and use-case set in a project that finished Inception a hundred tasks ago

INVEST check:
✅ Independent — one function's fallback chain plus its tests · ✅ Negotiable — the fallback's precedence and source label are open · ✅ Valuable — removes a wrong-work hazard from every unattended loop · ✅ Estimable — one reader + one tier · ✅ Small · ✅ Testable — reproduces deterministically with no state file

## Analysis Context

- **Domain.** Phase derivation in `scripts/openup-lifecycle.py` (`compute_status` → `resolve_phase`), consumed by `openup-board.py resolve` to choose the cycle's path.
- **Scope boundaries.** This does NOT change `resolve`'s precedence (it is correct — see below), does NOT change which phases may plan-fresh, does NOT touch milestone records, and does NOT make the phase writable by hand.
- **Definition of done.** With no `.openup/state.json` and no milestone records, the derived phase equals the phase recorded in `docs/project-status.md`, and a drained roadmap in Construction resolves to `noop` rather than `plan-iteration`.

**Root cause (verified before drafting).** `resolve_phase(records, state_phase)` falls back to `(state_phase or "inception")` (`scripts/openup-lifecycle.py:193`), and `compute_status` supplies `state_phase` from **live state only** — `state.get("phase") if state else None` (`:327`). With no lane active there is no `.openup/state.json`, so `state_phase` is `None` and the phase becomes **`inception`**, regardless of project maturity. Demonstrated directly: `resolve_phase([], None)` → `('inception', 1, 'state-fallback')`, while `resolve_phase([], 'construction')` → `('construction', 1, 'state-fallback')`. The function is correct; **the caller has nothing to pass**, and it never consults `docs/project-status.md`, whose `**Phase**: construction` is the durable record `sync-status.py` maintains.

**Why that is harmful, not cosmetic.** `openup-board.py`'s §1c-plan-fresh branch (`:892-899`) fires when nothing is promotable, the phase is in `_AUTHORING_PHASES` (`inception`/`elaboration`), and phase criteria are unmet. Its own comment states the intent plainly: *"Construction/transition are excluded, so their drained-roadmap case still falls through to noop."* With the phase mis-derived as `inception`, that exclusion is bypassed and a mature Construction project with a drained roadmap is routed to **plan a fresh Inception iteration from the process map** — authoring Vision, use cases and a risk list. Under an unattended `/loop` that is real damage before anyone looks.

**Corrected diagnosis.** An earlier reading of this defect blamed `resolve`'s precedence for conflating "no promotable entries" with "no roadmap". That was wrong: the precedence and the plan-fresh gating are both correct by design. The single fault is the phase fallback chain. Recorded here because the wrong diagnosis would have produced a much larger and worse change.

**Trigger is general, not deferral-specific.** T-073 and T-156 being deferred is merely what drained the roadmap today. The same misfire occurs on any repo whose roadmap is fully delivered while no lane is active — the ordinary end state of a completed backlog.

> **Assumption:** the new tier reads `docs/project-status.md`'s `**Phase**:` field, which `sync-status.py` writes from state at every completion, making it the durable record of the last known phase. It is preferred over scanning archived states (ordering is ambiguous and the archives are large). *(Vetoable at review.)*

> **Assumption:** the fallback is reported as a **distinct source**, `project-status-fallback`, not silently as `state-fallback`. Provenance is the whole point of that field, and conflating two different fallbacks would hide exactly the confusion this task fixes. Existing `state-fallback` behaviour, when live state *is* present, is unchanged. *(Vetoable at review.)*

> **Assumption:** precedence remains **milestone records → live state → project-status → `inception`**. Live state wins over project-status because an active lane is more current than the last synced view; `inception` remains the final default for a genuinely fresh project with neither. *(Vetoable at review.)*

## Requirements

1. With no live state and no milestone records, the derived phase comes from `docs/project-status.md`.
   - **Given** a repo with no `.openup/state.json`, no milestone records, and `**Phase**: construction` in `docs/project-status.md`, **When** `openup-lifecycle.py status --json` runs, **Then** `phase` is `construction`, not `inception`.
2. That fallback is reported as a distinct source.
   - **Given** the same repo, **When** status is computed, **Then** `source` is `project-status-fallback`, distinguishable from `state-fallback`.
3. Live state still wins over the project-status view.
   - **Given** `.openup/state.json` recording `phase: elaboration` **and** `docs/project-status.md` recording `construction`, **When** status is computed, **Then** `phase` is `elaboration` and `source` is `state-fallback` — unchanged from today.
4. A genuinely fresh project still defaults to `inception`.
   - **Given** no state, no milestone records, and **no** `docs/project-status.md` (or one with no `**Phase**:` line), **When** status is computed, **Then** `phase` is `inception` and the existing default behaviour is preserved.
5. An unparseable or invalid phase value is rejected rather than propagated.
   - **Given** `docs/project-status.md` containing `**Phase**: banana`, **When** status is computed, **Then** the value is discarded and `phase` falls through to `inception` — the same validation `resolve_phase` already applies to state values.
6. Milestone records still take precedence over everything.
   - **Given** a milestone record for `construction` cycle 2 and a `docs/project-status.md` saying `inception`, **When** status is computed, **Then** the record wins and `source` is not a fallback.
7. A drained roadmap in Construction resolves to `noop`, not `plan-iteration`.
   - **Given** this repo's current state — no active lane, no promotable roadmap entry, `**Phase**: construction` — **When** `openup-board.py resolve` runs, **Then** `path` is `noop` and the reason names the exhausted roadmap rather than a fresh-Inception plan.
8. The `source` field's documented values stay accurate.
   - **Given** `docs-eng-process/script-cli-reference.md:332` documents `state-fallback`, **When** a new source value exists, **Then** that line names it too.
9. Both changes are additive: every existing test passes unmodified.
   - **Given** `tests/test_lifecycle.py` (13 tests, including one asserting `source == "state-fallback"`), **When** the suite runs, **Then** all pass with no assertion edited, and `scripts/run-tests.sh` reports both directories green.

## Behavior Delta

**Added:**
- A `project-status-fallback` tier in phase derivation, and its source label.

**Modified** — cited artifact + section:
- Phase derivation precedence — `docs-eng-process/script-cli-reference.md §openup-lifecycle.py` (the line documenting `state-fallback`).
- `openup-board.py resolve`'s *observed* output for a drained roadmap in a non-authoring phase: `plan-iteration` → `noop`. **No change to `openup-board.py` itself** — its gating was always correct; it now receives the right phase.

**Removed** — none. No existing source value, exit code, or default is removed.

## Entities

- **`compute_status`** (modified) — `scripts/openup-lifecycle.py:325`; supplies the new tier.
- **`resolve_phase`** (modified) — `scripts/openup-lifecycle.py:186`; gains the source label; its validation is reused for the new input.
- **Project-status reader** (new) — a small helper in `scripts/openup-lifecycle.py` parsing `**Phase**:`.
- **`_lifecycle_status` / plan-fresh branch** (read-only) — `scripts/openup-board.py:828,892`; deliberately unchanged, and requirement 7 asserts the corrected outcome through them.
- **Lifecycle tests** (modified) — `tests/test_lifecycle.py`.

## Approach

Fix the fallback chain, not the consumer. `openup-board.py`'s plan-fresh gating already excludes Construction by design, so the only defect is that it is handed the wrong phase; changing the board would have been the wrong repair, and a wrong diagnosis nearly produced one. `compute_status` gains one tier between live state and the hard-coded default: read `**Phase**:` from `docs/project-status.md`, the durable record `sync-status.py` maintains, and reuse `resolve_phase`'s existing validation so a malformed value is discarded rather than propagated. The new tier reports its own `source`, because provenance is that field's entire purpose. Deliberately deferred: reconstructing phase history from archived states, and any change to which phases may plan-fresh.

## Structure

**Add:**
- `read_project_status_phase(root) -> str | None` in `scripts/openup-lifecycle.py`.

**Modify:**
- `scripts/openup-lifecycle.py` — `compute_status` consults the new reader when live state has no phase; `resolve_phase` reports `project-status-fallback` for that input.
- `tests/test_lifecycle.py` — cases for requirements 1–6.
- `docs-eng-process/script-cli-reference.md` — the documented `source` values (req. 8).
- `docs/roadmap.md` — this task's own entry. *Listed up front: three lanes in a row omitted it, and T-159 was caught only by its own C3 warning.*

**Do not touch:**
- `scripts/openup-board.py` — the tempting target, and the wrong one. Its `_AUTHORING_PHASES` gating and `resolve` precedence are correct; requirement 7 proves the fix reaches it without an edit.
- Milestone-record reading — the authoritative source, unaffected.
- `sync-status.py` — it already writes the `**Phase**:` field this fix reads.
- `tests/test_lifecycle.py`'s existing `state-fallback` assertion — it must keep passing unmodified (req. 3 covers the same path); if it fails, the fix overreached into live-state behaviour.

## Operations

- [ ] Reproduce first: in a fixture with no state, no milestone records, and `**Phase**: construction`, confirm `status --json` reports `inception` — and confirm `openup-board.py resolve` returns `plan-iteration` with the fresh-Inception reason.
- [ ] Write the failing cases for requirements 1–6 in `tests/test_lifecycle.py`; confirm each fails for the stated reason, not an import error.
- [ ] Add `read_project_status_phase()` and wire it into `compute_status`, reusing `resolve_phase`'s validation; report `project-status-fallback`. Confirm reqs 1–6 pass.
- [ ] Verify requirement 7 end-to-end in **this** repo: `openup-board.py resolve` returns `noop` with an exhausted-roadmap reason, with no edit to `openup-board.py`.
- [ ] Update the documented `source` values in `script-cli-reference.md` (req. 8).
- [ ] (tester) Run `scripts/run-tests.sh` and confirm both directories green with the pre-existing counts unchanged (req. 9).

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process + script conventions.
- `docs-eng-process/state-file.md` — state and phase semantics.
- `docs-eng-process/tracks.md` — track ceremony.

## Safeguards

- **Do not edit `openup-board.py`.** Its gating is correct; requirement 7 verifies the fix arrives through it untouched. Editing it would re-introduce the wrong diagnosis.
- **Live state must keep winning.** An active lane is more current than the last synced view; requirement 3 pins it.
- **A fresh project must still start at `inception`.** Requirement 4 pins the default so the fix cannot break bootstrap.
- **Validate, never propagate.** A malformed `**Phase**:` is discarded (req. 5) using the existing validation, not a second copy of it.
- **Honest provenance.** The new tier gets its own `source`; reusing `state-fallback` would hide the distinction this task exists to make.
- **Reversibility.** One function plus one tier; revert the commit. No data format changes, so nothing needs migrating.
- **Size budget.** ≤ ~25 LOC of implementation. More means the chain was misread.

## Success Measures

We expect **the number of `openup-board.py resolve` calls that return `plan-iteration` with a fresh-phase reason while `docs/project-status.md` records a non-authoring phase** to be **0**, from **1 of 1** today (reproduced 2026-07-28 in this repo). Instrumentation, committed by this task: the requirement-7 test asserting `resolve` returns `noop` for exactly this configuration, plus the `source` field itself — a status output reading `project-status-fallback` is direct evidence the tier is being used, and one reading `inception` with a mature `project-status.md` is the defect recurring. Read-back environment: **this repo** — both the board and the lifecycle script run here, and the repo is currently in the triggering state. Read-back: **the second retrospective after landing** (absolute backstop **2026-11-30**).

The measure is checkable on demand rather than only at read-back: `openup-lifecycle.py status --json` with no lane active answers it in one call, so a `0` never depends on a lane having run.

## Rollout

`n/a — not user-facing.` Internal tooling; no flag. The change is additive — a new fallback tier and a new `source` value — and every existing invocation with live state behaves identically, so there is nothing to toggle and no migration. Reaches agents on merge and downstream consumers via `sync-from-framework.sh`. No flag-removal follow-up is owed.

## Verification

- `asdf exec python3 -m pytest tests/test_lifecycle.py -q` — 13 pre-existing + new cases green.
- `bash scripts/run-tests.sh` — both directories green, pre-existing counts unchanged.
- Live: `python3 scripts/openup-lifecycle.py status --json` reports `construction` / `project-status-fallback` with no lane active.
- Live: `python3 scripts/openup-board.py resolve` returns `noop` with an exhausted-roadmap reason.
- `git diff --stat` shows **no** change to `scripts/openup-board.py`.
- `python3 scripts/check-docs.py` and `python3 scripts/openup-fence.py check` clean.
- Grade against `.claude/rubrics/task-spec-rubric.md`.

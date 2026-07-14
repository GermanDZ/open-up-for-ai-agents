---
id: T-103
title: Delete the hardcoded bootstrap + retire the per-cycle LLM navigator
status: ready   # proposed → ready → in-progress → done → verified
priority: high   # critical | high | medium | low
estimate: 1 session
plan: docs/iteration-plans/2026-07-14-deterministic-process-map-navigation.md
depends-on: [T-101]
blocks: []
touches:
  - scripts/openup_agent/navigator.py
  - scripts/openup_agent/cycle.py
  - scripts/openup-agent.py
  - scripts/process-manifest.txt
  - scripts/tests/test_openup_agent_navigator.py
  - scripts/tests/test_openup_agent_cycle.py
  - docs-eng-process/reference-driver.md
  - docs-eng-process/script-cli-reference.md
last-synced: ""
---

# T-103 — Delete the bootstrap + retire the per-cycle navigator

## Story

> **As** the maintainer of the reference driver,
> **I want** the per-cycle LLM navigator (T-096) and the hardcoded Inception
>   bootstrap (T-097/T-098) **removed**, now that navigation is deterministic
>   (T-101 fires Plan Iteration on a fresh project; declared inputs scaffold from
>   the map),
> **So that** the program's falsifiable win lands: **zero per-cycle navigator LLM
>   calls, the `navigator.py` decision code gone** — the flaky per-cycle-LLM
>   failure mode that produced T-096→T-099 is deleted, not carried.

INVEST — ✅ Independent (deletion of now-dead code) · ✅ Negotiable (noop message) · ✅ Valuable (the program's headline measure) · ✅ Estimable · ✅ Small (net-negative) · ✅ Testable (fresh scenario never enters a navigator; module gone)

## Analysis Context

- **Domain.** `cycle.py` wires the navigator on the `noop` path
  (`run_cycle(navigate=...)` → `_run_navigator` → `navigator.run_navigator`).
  Since **T-101**, a fresh authoring phase resolves to `plan-iteration` (not
  `noop`), so the navigator is **dead code on the fresh path**; a genuine `noop`
  (drained, complete) is handled by the T-094 replenish / DONE. Nothing but
  `cycle.py` imports `navigator`.
- **What goes.** `scripts/openup_agent/navigator.py` (the whole decision-file flow,
  `_bootstrap_step`, brief-specific scaffold, `run_navigator`); `cycle.py`'s
  `navigate` param + `_navigator` seam + `_run_navigator`; the `--no-navigate` CLI
  flag; the navigator from `process-manifest.txt`; `test_openup_agent_navigator.py`;
  the `NavigatorDispatchTest` + the `navigate=False` switches added to pre-existing
  cycle noop tests (they revert to plain DONE assertions).
- **What stays.** The deterministic path (resolve→plan-iteration→map-driven
  scaffold/execution, T-101); the T-099 ADVANCED-reporting lives in the
  plan-iteration `run_procedure` capture (cycle), not the navigator.
- **Definition of done.** `navigator.py` deleted; `cycle.py`'s `noop` branch prints
  `DONE` (no navigate); `--no-navigate` removed; the driver imports cleanly with no
  `navigator` reference; a fresh project drives via `plan-iteration` with **no
  navigator call**; full suite green; docs updated.

> **Assumption:** a genuine `noop` (nothing pickable, nothing promotable, phase
> exit-ready or non-authoring) → `DONE` (or T-094 replenish in the recover path),
> which already holds; the navigator added nothing there. *(Vetoable.)*

## Requirements

1. **`navigator.py` is deleted and nothing imports it.**
   - **Given** the driver, **When** `openup_agent` is imported and the test suite
     runs, **Then** there is no `scripts/openup_agent/navigator.py`, no `import
     navigator`, and the package imports cleanly.

2. **`cycle` has no per-cycle navigator path.**
   - **Given** `run_cycle`, **When** inspected, **Then** the `navigate` param,
     `_navigator` seam, and `_run_navigator` are gone; a `noop` decision prints
     `OPENUP-NEXT: DONE — <reason>` and returns 0 (no LLM).

3. **`--no-navigate` is removed from the CLI.**
   - **Given** `openup-agent.py cycle --help`, **When** read, **Then** there is no
     `--no-navigate` flag; `cycle` runs without it.

4. **A fresh project drives deterministically with no navigator call.**
   - **Given** a fresh authoring-phase project, **When** `cycle` runs, **Then**
     `resolve` returns `plan-iteration` and the run reaches Plan Iteration with
     **zero** navigator involvement (there is no navigator to involve).

5. **The manifest + tests no longer reference the navigator.**
   - **Given** `process-manifest.txt`, **When** read, **Then**
     `openup_agent/navigator.py` is absent; `test_openup_agent_navigator.py` is
     deleted and `test_openup_agent_cycle.py` has no `NavigatorDispatchTest` /
     `navigate=` usage.

## Behavior Delta

Ring-1 truth for the driver lives in `docs-eng-process/`.

**Removed:**
- The per-cycle LLM navigator (T-096) + hardcoded bootstrap (T-097/T-098):
  `navigator.py`, `cycle` `navigate`/`_run_navigator`, `--no-navigate` —
  `docs-eng-process/reference-driver.md` + `script-cli-reference.md` (the navigator
  sections are replaced by "navigation is deterministic").

**Modified:**
- `cycle` `noop` handling — prints `DONE` (no navigate).

**Added:** none (net-negative).

## Entities

- **navigator** (deleted) — `scripts/openup_agent/navigator.py`
- **cycle** (modified) — `scripts/openup_agent/cycle.py`
- **CLI** (modified) — `scripts/openup-agent.py`
- **manifest / tests / docs** (modified/deleted)

## Approach

Delete `navigator.py`. In `cycle.py`: drop the `navigator` import, `_run_navigator`,
the `navigate` param + `_navigator` seam; the `noop` branch becomes a plain `DONE`
print (keep the reason; the no-roadmap Inception hint is now unreachable for
authoring phases but harmless as a fallback message — trimmed). Remove
`--no-navigate` + the `navigate=` wire from `openup-agent.py`. Remove the navigator
line from `process-manifest.txt`. Delete `test_openup_agent_navigator.py`; remove
`NavigatorDispatchTest` and revert the `navigate=False` switches in the pre-existing
cycle noop tests to plain DONE assertions. Update the two docs.

## Structure

**Delete:**
- `scripts/openup_agent/navigator.py`
- `scripts/tests/test_openup_agent_navigator.py`

**Modify:**
- `scripts/openup_agent/cycle.py` — remove navigator import / `_run_navigator` /
  `navigate` param / `_navigator` seam; `noop` → `DONE`.
- `scripts/openup-agent.py` — remove `--no-navigate` + `navigate=`.
- `scripts/process-manifest.txt` — remove `openup_agent/navigator.py`.
- `scripts/tests/test_openup_agent_cycle.py` — remove `NavigatorDispatchTest`;
  revert `navigate=False` in the noop tests.
- `docs-eng-process/reference-driver.md`, `script-cli-reference.md` — replace the
  navigator sections with the deterministic-navigation note.

**Do not touch:**
- `plan_iteration.py` / `resolve` / assess / milestone — the deterministic path is
  the replacement, unchanged here.

## Operations

- [ ] Delete `scripts/openup_agent/navigator.py` + remove it from
  `scripts/process-manifest.txt`.
- [ ] `cycle.py`: remove the `navigator` import, `_run_navigator`, the `navigate`
  param + `_navigator` seam; make the `noop` branch print `DONE` (no navigate).
- [ ] `openup-agent.py`: remove `--no-navigate` and the `navigate=` argument.
- [ ] (tester) Delete `test_openup_agent_navigator.py`; remove
  `NavigatorDispatchTest` and revert the `navigate=False` switches (plain DONE) in
  `test_openup_agent_cycle.py`; add a fresh-project assertion that no navigator is
  involved.
- [ ] Update `reference-driver.md` + `script-cli-reference.md` (deterministic
  navigation; navigator removed).
- [ ] (tester) Full driver+board suite green; `check-docs`, `spec-scenarios`,
  `process-map validate`, fence (`--base harness-optional`) green; `openup_agent`
  imports with no navigator.

## Norms

Inherits from:
- `docs-eng-process/conventions.md`
- `docs-eng-process/reference-driver.md` — the driver contract
- `docs/iteration-plans/2026-07-14-deterministic-process-map-navigation.md`

## Safeguards

- **No uncovered `resolve` path (self-critique, from the plan).** Before deleting,
  confirm every `resolve` outcome is handled without the navigator: pick/resume
  (executor), plan-iteration (T-090/T-101), assess/milestone (T-091), noop
  (DONE / T-094 replenish). The navigator was only ever reached on `noop`, now
  covered.
- **Reversibility.** Pure deletion of now-dead code; git-revertible.
- **Stdlib-only** (unchanged).

## Success Measures

n/a — internal. **This task realizes the P1 program measure**: a fresh
Inception-through-delivery run completes with **zero per-cycle navigator LLM
calls** and the `navigator.py` decision code **deleted** — verified by the suite
(no navigator module/import) + a fresh-project test that reaches `plan-iteration`
with no navigator. Live token/reliability is the T-080 owner batch.

## Rollout

`n/a — not user-facing`: reference-driver internals; no flag. Backout is a version
pin.

## Verification

- `python3 -c "import sys; sys.path.insert(0,'scripts'); import openup_agent.cycle"`
  imports with no `navigator`; `ls scripts/openup_agent/navigator.py` → absent.
- `python3 -m pytest scripts/tests/ -q` — green (minus the two known-stale, one of
  which T-101 already fixed).
- `openup-agent.py cycle --help` has no `--no-navigate`.
- Fresh project → `resolve` = `plan-iteration`; `cycle` drives it, no navigator.
- `openup-spec-scenarios.py check docs/changes/T-103/plan.md` → 0; `check-docs.py`
  → 0; `openup-fence.py check --base harness-optional` → clean.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

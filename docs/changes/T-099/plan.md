---
id: T-099
title: Navigator reports ADVANCED after a successful procedure run (not the procedure's DONE)
status: ready   # proposed → ready → in-progress → done → verified
priority: medium   # critical | high | medium | low
estimate: 1 session
plan: docs/changes/archive/T-098/plan.md
depends-on: [T-096, T-098]
blocks: []
touches:
  - scripts/openup_agent/navigator.py
  - scripts/openup_agent/cycle.py
  - scripts/tests/test_openup_agent_navigator.py
  - scripts/tests/test_openup_agent_cycle.py
  - docs-eng-process/reference-driver.md
last-synced: ""
---

# T-099 — Navigator: a procedure run is an ADVANCE, not a DONE

## Story

> **As an** operator running `./scripts/next-cycle`,
> **I want** the guidance after the navigator authors an artifact (e.g. the
>   Inception vision) to say **progress — run again**, not "nothing to do",
> **So that** I keep driving the loop instead of stopping, since a bootstrap
>   authoring step advances the project rather than ending it.

INVEST — ✅ Independent (navigator sentinel) · ✅ Negotiable (message text) · ✅ Valuable (fixes misleading "nothing to do" after real progress) · ✅ Estimable · ✅ Small · ✅ Testable (hermetic seams)

## Analysis Context

- **Domain.** The navigator (`navigator.py`) runs a procedure in two cases: the
  T-098 deterministic bootstrap (`openup-create-vision` on a filled brief) and a
  T-096 LLM-navigator decision that names a process-artifact procedure. In both it
  calls the injected `run_procedure`, which runs `loop.run` — and the procedure
  prints **its own** completion sentinel `OPENUP-NEXT: DONE — <what it authored>`.
- **The bug (live, my-product, 2026-07-14).** After the fast-path authored a
  vision + roadmap, the run ended `OPENUP-NEXT: DONE — Vision … created` and
  `./scripts/next-cycle` printed **"nothing to do right now"** — because its
  guidance keys on the sentinel (`ADVANCED` ⇒ "run again", else ⇒ "nothing to
  do"). But real progress was made and **re-running continues** (it plans the
  Inception iteration off the new roadmap). A procedure's "DONE" (I finished
  authoring) is not the loop's "DONE" (nothing left to do).
- **The fix.** When the navigator successfully runs a procedure, it emits the
  **cycle-level `ADVANCED`** sentinel (progress; re-run to continue) and suppresses
  the sub-procedure's own `DONE` so only one, correct sentinel reaches stdout. On
  failure the procedure's output is surfaced for diagnosis and the failing code
  propagates.
- **Scope boundaries.** Navigator + the cycle's `run_procedure` wiring only. No
  change to the deterministic engine, resolve, other decision paths, or the
  procedures themselves (their standalone `DONE` is correct when run via
  `openup-agent.py run`).
- **Definition of done.** A successful navigator procedure run ends
  `OPENUP-NEXT: ADVANCED — …` (so `next-cycle` says "progress, run again"); the
  sub-procedure's `DONE` does not leak; a failed run still surfaces its output and
  returns the failing code.

> **Assumption:** the ADVANCED message names the procedure, e.g.
> `OPENUP-NEXT: ADVANCED — authored via openup-create-vision; re-run to continue`.
> *(Vetoable at review.)*

## Requirements

1. **A successful navigator procedure run reports ADVANCED.**
   - **Given** the navigator runs a procedure (bootstrap or LLM-decided) that
     exits 0, **When** `run_navigator` returns, **Then** it prints exactly one
     `OPENUP-NEXT: ADVANCED — …` sentinel on stdout and returns 0.

2. **The sub-procedure's own sentinel does not leak.**
   - **Given** the run procedure printed `OPENUP-NEXT: DONE — …`, **When** the
     navigator wraps it, **Then** that `DONE` line is not present on the cycle's
     stdout (only the single `ADVANCED` sentinel is).

3. **`next-cycle` then guides "run again".**
   - **Given** a successful bootstrap create-vision via `cycle`, **When**
     `./scripts/next-cycle` prints its guidance, **Then** it is the progress line
     ("run … again to continue"), not "nothing to do".

4. **A failed procedure run still surfaces its output and propagates.**
   - **Given** the run procedure exits non-zero, **When** the navigator wraps it,
     **Then** the procedure's captured stdout is re-emitted (for diagnosis), no
     ADVANCED sentinel is printed, and the failing exit code is returned.

## Behavior Delta

Ring-1 truth for the driver lives in `docs-eng-process/`.

**Modified:**
- The navigator's sentinel after a procedure run —
  `docs-eng-process/reference-driver.md` (navigator section): a successful
  authoring run reports `ADVANCED` (progress), not the procedure's `DONE`.

**Removed:** the misleading `DONE`/"nothing to do" outcome after a navigator
authoring run.

## Entities

- **navigator** (modified) — `scripts/openup_agent/navigator.py`
  (`run_navigator` procedure-run reporting)
- **cycle wiring** (modified) — `scripts/openup_agent/cycle.py`
  (`_run_navigator`'s `run_procedure` captures the sub-procedure stdout)

## Approach

Make the cycle's injected `run_procedure` **capture** the sub-procedure's stdout
(the sentinel) rather than letting it pass through, returning `(rc, captured)`.
In `run_navigator`, route both procedure-run sites through one helper: on success
print the cycle `ADVANCED` sentinel; on failure re-emit the captured output and
return the code. Progress/log lines (stderr) are unaffected.

## Structure

**Modify:**
- `scripts/openup_agent/cycle.py` — `_run_navigator`'s `run_procedure` captures
  stdout and returns `(rc, out)` (or the navigator helper captures via the
  callable contract).
- `scripts/openup_agent/navigator.py` — a `_run_procedure_reporting(...)` helper
  used by the bootstrap and LLM-decided procedure paths; emits `ADVANCED` on
  success, re-emits captured output on failure.
- `scripts/tests/test_openup_agent_navigator.py` — success → ADVANCED + no DONE
  leak; failure → output surfaced + code propagates.
- `scripts/tests/test_openup_agent_cycle.py` — the wiring still returns 0 and the
  stdout carries ADVANCED (guarding the `run_procedure` capture).
- `docs-eng-process/reference-driver.md` — the ADVANCED-after-authoring note.

**Do not touch:**
- The procedures themselves (their standalone `DONE` is correct for
  `openup-agent.py run`).
- The deterministic engine / resolve / other decision paths.

## Operations

- [ ] Change `run_procedure` (navigator contract) to return `(rc, captured_stdout)`
  and update `cycle.py` `_run_navigator` to capture the sub-procedure stdout.
- [ ] Add `_run_procedure_reporting` in `navigator.py` (ADVANCED on success;
  re-emit captured output + propagate on failure) and route the bootstrap +
  LLM-decided procedure paths through it.
- [ ] (tester) Navigator tests (success → single ADVANCED, no DONE leak; failure
  → output surfaced + code) + a cycle wiring assertion.
- [ ] Update the navigator section of `docs-eng-process/reference-driver.md`.
- [ ] (tester) Full driver+navigator+cycle+next-cycle suite green; `check-docs`,
  `openup-spec-scenarios`, `openup-fence.py check --base harness-optional` green.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format
- `docs-eng-process/reference-driver.md` — sentinel contract (ADVANCED vs DONE)
- `docs/changes/archive/T-098/plan.md` — the bootstrap this refines

## Safeguards

- **Reversibility.** Navigator-local; a failed run still surfaces the
  sub-procedure output. No procedure or engine change.
- **Protocol cleanliness.** Exactly one sentinel reaches stdout per navigator run.
- **No-go zones.** No change to the engine, resolve, or the procedures.
- **Stdlib-only.**

## Success Measures

n/a — internal UX fix. Falsifiable acceptance = the hermetic tests (Req 1–4) plus
the owner re-running `next-cycle` on my-product (guidance reads "run again" after
the vision is authored, and re-running plans the Inception iteration).

## Rollout

`n/a — not user-facing`: reference-driver developer tooling; no flag. Backout is a
version pin.

## Verification

- `python3 -m pytest scripts/tests/test_openup_agent_navigator.py
  scripts/tests/test_openup_agent_cycle.py -q` — green.
- Scripted bootstrap create-vision → stdout ends `OPENUP-NEXT: ADVANCED — …`, no
  `DONE` line; a failing run re-emits output + returns the code.
- `openup-spec-scenarios.py check docs/changes/T-099/plan.md` → 0; `check-docs.py`
  → 0; `openup-fence.py check --base harness-optional` → clean.

---
id: T-117
title: "openup-doctor --fix: apply auto-heal-class findings"
status: done
priority: medium
estimate: 1 session
plan: docs/explorations/2026-07-15-self-healing-interrupted-process-state.md
depends-on: []
blocks: []
last-synced: ""
touches:
  - scripts/openup-doctor.py
  - tests/test_openup_doctor_fix.py
---

# T-117 — openup-doctor `--fix`: apply auto-heal-class findings

## Story

> **As a** maintainer of an OpenUP project whose tree drifted after an interrupted run
> **I want** `openup-doctor --fix` to repair the auto-heal-class findings by invoking their owning scripts
> **So that** derivable state (stale views, single-valued unset gates) heals without me diagnosing each papercut by hand

INVEST — ✅ Independent · ✅ Negotiable · ✅ Valuable · ✅ Estimable · ✅ Small · ✅ Testable

## Analysis Context

- **Domain.** Process-state self-healing. Doctor already owns read-only detection and emits remediation strings; the missing half is an *applier* that turns a remediable finding into its fix.
- **Scope boundaries.** Only **auto-heal-class** findings are applied non-interactively: derived/mirror-view drift (re-run the generator) and a single-valued unset `plan_persisted` gate (a lookup, not a judgment). **Confirm-class** findings (clobbered state re-init, wrongly-`completed` cell, stranded spec) are printed as proposals and applied only under `--fix --confirm`. **Human-only** findings (corrupt `state.json` with no recoverable intent; the roadmap-drained no-op) are never touched. `settings.json` no-op reorder is **out of scope** — doctor does not currently detect it and no canonical serializer exists yet (deferred to a follow-up).
- **Definition of done.** `openup-doctor --fix` invokes owning scripts for auto-heal-class findings, re-runs detection, and reaches an error-free (green) report non-interactively; confirm/human findings are untouched without `--confirm`; a test corrupts one state per class and asserts fix-then-clean and boundary-respect.

> **Assumption:** the auto-heal set for this task is derived-view drift + unset `plan_persisted` gate only; `settings.json` reorder is deferred. *(Vetoable at review.)*
> **Assumption:** `--fix` delegates to each owning script (DD1: invoke, never reimplement) rather than editing files itself, except gate-set which is itself an owning-script call (`openup-state.py set-gate`). *(Vetoable at review.)*

## Requirements

1. Each auto-heal-class finding carries a machine-readable fix: an owning-script command plus a `fix_class` of `auto`.
   - **Given** doctor detects derived-view drift (e.g. `docs-index.py --check` fails) **When** the finding is built **Then** it records `fix_class="auto"` and the owning command (`docs-index.py`).
2. `openup-doctor --fix` invokes the owning script for every `auto`-class finding, then re-runs detection and reports the post-fix state.
   - **Given** a repo with a stale `INDEX.md` **When** `openup-doctor --fix` runs **Then** the generator is invoked, the drift finding is gone on re-detect, and the exit code is 0.
3. `--fix` heals a single-valued unset `plan_persisted` gate when `docs/changes/<id>/plan.md` exists for the active lane.
   - **Given** an active lane whose `plan_persisted` gate is unset but whose `plan.md` exists **When** `openup-doctor --fix` runs **Then** `openup-state.py set-gate plan_persisted <path>` is invoked and the gate is set.
4. `--fix` never applies confirm-class or human-class findings; confirm-class fixes are applied only under `--fix --confirm`.
   - **Given** a confirm-class finding is present **When** `openup-doctor --fix` runs without `--confirm` **Then** the fix is printed as a proposal, not applied, and the underlying state is unchanged.
5. Default (no `--fix`) behavior is unchanged: doctor stays strictly read-only.
   - **Given** `openup-doctor` is run without `--fix` **When** it completes **Then** no file is written and output matches the pre-T-117 report shape.

## Behavior Delta

**Added** — new `openup-doctor --fix` / `--fix --confirm` write mode invoking owning scripts for auto-heal-class findings; default run stays read-only.

**Modified** — n/a (default read-only report shape preserved).

**Removed** — n/a.

## Entities

- **Doctor CLI** (modified) — `scripts/openup-doctor.py`
- **Finding** (modified) — gains `fix_class` + `fix_cmd` fields — `scripts/openup-doctor.py`
- **Owning fix-scripts** (read-only, invoked) — `docs-index.py`, `render-skills-mirror.py`, `sync-status.py --reconcile`, `check-claude-sync`/`sync-templates-to-claude.sh`, `openup-state.py set-gate`
- **Test** (new) — `tests/test_openup_doctor_fix.py`

## Approach

Give `Finding` two optional fields: `fix_class` (`auto` | `confirm` | `human` | `None`) and `fix_cmd` (argv relative to `scripts/`). Detection checks that already know their owning script tag the findings they emit. A new `apply_fixes(findings, repo, confirm)` routine runs each `auto` fix (and `confirm` fixes only when `confirm=True`), then re-runs the full detection pass and returns the post-fix findings. `--fix` in `main()` wires this in; the exit code reflects the post-fix state. No detection logic is duplicated and no file is written by doctor itself (DD1) — every fix is an owning-script subprocess call.

## Structure

**Add:**
- `tests/test_openup_doctor_fix.py` — one corrupted-state fixture per class; asserts fix-then-clean + boundary.

**Modify:**
- `scripts/openup-doctor.py` — `Finding` fields, tag auto-heal findings, `apply_fixes()`, `--fix`/`--confirm` args, exit-code wiring.

**Do not touch:**
- The owning fix-scripts — invoked, never reimplemented (DD1).
- Default report path — must stay byte-compatible when `--fix` absent.

## Operations

- [x] Add `fix_class` + `fix_cmd` to `Finding` (default `None`); include in `as_dict()`.
- [x] Tag auto-heal findings at their source: derived-view drift (aggregate + roadmap-status-drift) → `fix_class="auto"` with the generator command; unset `plan_persisted` gate detection (new, or extend state check) → `auto` with `set-gate` command.
- [x] Add a confirm-class example finding path so the boundary is testable (proposal-only unless `--confirm`).
- [x] Implement `apply_fixes(findings, repo, confirm)`: run auto (and confirm-if-flagged) `fix_cmd`s via `run()`, then re-detect and return post-fix findings.
- [x] Wire `--fix` / `--confirm` argparse flags into `main()`; exit code reflects post-fix findings; default run stays read-only.
- [x] (tester) Write `tests/test_openup_doctor_fix.py`: corrupt one state per class, assert `--fix` reaches green, confirm/human untouched without `--confirm`.
- [x] Update the module docstring to note `--fix` is opt-in and default stays read-only.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions
- `docs/changes/T-053/design.md` — DD1 (invoke owning scripts, never reimplement detection)

## Safeguards

- **Reversibility.** Every applied fix is an owning-script re-run of a derivable view, or an idempotent gate-set; re-running `--fix` is safe.
- **No-go zones.** Default (no `--fix`) run must write nothing. `--fix` must never apply confirm/human-class findings without `--confirm`; must never fabricate product intent (the roadmap-drained no-op is the defining negative boundary).
- **DD1.** Doctor invokes owning scripts; it does not reimplement any detection or fix logic.
- **Token budget.** Net addition to `openup-doctor.py` ≤ ~120 lines.

## Verification

- `asdf exec python3 -m pytest tests/test_openup_doctor_fix.py -q` passes.
- `python3 scripts/openup-doctor.py` (no `--fix`) writes nothing and matches prior report shape.
- Grade against `.claude/rubrics/task-spec-rubric.md`.

## Success Measures

n/a — internal tooling; the falsifiable outcome is the boundary test (fix-then-clean for auto-heal classes, untouched confirm/human classes), not a usage metric.

## Rollout

n/a — internal CLI tooling, no user-facing runtime surface; `--fix` is opt-in by flag (adds no safety needing a feature flag).

---
id: T-097
title: Navigator scaffolds a fillable artifact instead of an unanswerable input-request
status: ready   # proposed → ready → in-progress → done → verified
priority: high   # critical | high | medium | low
estimate: 1 session
plan: docs/changes/archive/T-096/plan.md
depends-on: [T-096]
blocks: []
touches:
  - scripts/openup_agent/navigator.py
  - scripts/next-cycle
  - scripts/tests/test_openup_agent_navigator.py
  - scripts/tests/test_next_cycle.py
  - docs-eng-process/reference-driver.md
last-synced: ""
---

# T-097 — Navigator: scaffold a fillable artifact, don't raise an unanswerable request

## Story

> **As an** operator running `./scripts/next-cycle` on a fresh project,
> **I want** the navigator, when it needs a human-authored artifact (a stakeholder
>   brief), to hand me a fillable template and detect when I've filled it,
> **So that** the loop **converges** — instead of re-raising an input-request whose
>   `**Answer**:` field cannot produce the artifact, so every re-run re-suspends.

INVEST — ✅ Independent (navigator-local) · ✅ Negotiable (template content, default path) · ✅ Valuable (fixes a live non-converging loop) · ✅ Estimable · ✅ Small (one affordance swap + marker-aware survey) · ✅ Testable (hermetic seams)

## Analysis Context

- **Domain.** The T-096 process navigator (`scripts/openup_agent/navigator.py`).
  On a fresh project (`noop`, `phase: inception`, no vision/roadmap/brief) it
  correctly decides "the `openup-create-vision` procedure needs a vision or a
  stakeholder brief, neither exists" and returns `missing_inputs`. The driver then
  raises a **T-074 input-request** and suspends.
- **The bug (observed live, my-product / qwen local model, 2026-07-13).** An
  input-request is answered by filling a `**Answer**:` text line — but that does
  **not** create a stakeholder brief. So the next `cycle` re-runs the navigator,
  re-detects the missing brief, and re-suspends on the same request. The loop
  **never converges**; the human has no affordance that satisfies the need.
- **The fix.** A missing human **artifact** needs an *artifact* affordance, not a
  question: scaffold a **marker-guarded template** at the artifact's path, tell
  the human to fill it and re-run, and treat a still-templated file as *absent* in
  the Ring-1 survey so a filled brief (marker removed) is what advances the loop.
  This restores the T-095 brief affordance, now **driven by the navigator's
  process-agnostic decision** (the navigator names the path; the driver scaffolds)
  rather than hardcoded in the wrapper. The input-request path stays for genuine
  short-answer questions.
- **Scope boundaries.** Only the navigator's missing-input handling +
  Ring-1-survey marker-awareness + the wrapper's exit-5 guidance. Does not touch
  the deterministic engine, `resolve`, or the assess/milestone/plan-iteration
  paths.
- **Definition of done.** A fresh project's `next-cycle` scaffolds
  `docs/inputs/stakeholder-brief.md` (marker-guarded, never overwriting a filled
  one), guides the human, and suspends; once the human fills it (marker removed),
  the next run's navigator returns `openup-create-vision` and runs it. A genuine
  question with no artifact path still uses an input-request.

> **Assumption:** the navigator decision gains an optional `input_path`; the LLM
> sets it for an artifact need (e.g. `docs/inputs/stakeholder-brief.md`). The
> driver also **defaults** to that path when the phase is `inception`, no brief
> exists, and the LLM omitted it — so convergence does not depend on a weak local
> model emitting the field. *(Vetoable at review.)*
> **Assumption:** the scaffold uses a template marker (`<!-- template: … -->`);
> the Ring-1 `stakeholder_brief` survey counts the file present only when it
> exists AND lacks the marker. *(Vetoable.)*

## Requirements

1. **A missing human artifact scaffolds a fillable template, not an input-request.**
   - **Given** a fresh project whose navigator returns `missing_inputs` with an
     `input_path` (or the inception-brief default) and no such file exists,
     **When** the navigator runs, **Then** it writes a marker-guarded template at
     that path, prints guidance naming the file to fill, and suspends (exit 5) —
     and creates **no** input-request.

2. **A filled artifact converges the loop.**
   - **Given** the scaffolded brief has been filled (template marker removed),
     **When** the navigator runs, **Then** the Ring-1 survey reports the brief
     present, the navigator returns `procedure: openup-create-vision`, and the
     driver runs it (no re-scaffold, no suspend).

3. **The scaffold never clobbers a human's file.**
   - **Given** `docs/inputs/stakeholder-brief.md` already exists **with** the
     template marker (a partially-filled scaffold), **When** the navigator runs,
     **Then** it does not overwrite the file; it re-guides and suspends.

4. **A genuine question (no artifact path) still uses an input-request.**
   - **Given** the navigator returns `missing_inputs` with no `input_path` and no
     default artifact applies, **When** it runs, **Then** it creates a T-074
     input-request and suspends (the prior behavior), remembered so a re-run does
     not duplicate it.

5. **The wrapper's exit-5 guidance covers both affordances.**
   - **Given** any suspend (exit 5), **When** `./scripts/next-cycle` prints its
     guidance, **Then** it names both paths to resolution — fill the template file
     **or** answer the input-request named above — then re-run.

## Behavior Delta

Ring-1 truth for the driver lives in `docs-eng-process/`.

**Modified:**
- The navigator's missing-input affordance — `docs-eng-process/reference-driver.md`
  (navigator section): a missing human *artifact* scaffolds a fillable template
  and detects its filling (marker-aware survey); the input-request is reserved for
  genuine questions.
- `scripts/next-cycle` exit-5 guidance — now names the template-fill path too.

**Removed:** the non-converging "input-request for a missing artifact" behavior
from T-096 (archived T-096 spec Req 4/5 — superseded for the artifact case).

## Entities

- **navigator** (modified) — `scripts/openup_agent/navigator.py`
  (`RING1_ARTIFACTS`/`_ring1_survey` marker-awareness, decision `input_path`,
  `_scaffold_input`, `run_navigator` missing-input branch)
- **next-cycle** (modified) — `scripts/next-cycle` (exit-5 guidance)

## Approach

Add a template marker + a generic scaffold writer to `navigator.py`. In
`run_navigator`'s missing-input branch, resolve an artifact path (the decision's
`input_path`, else the inception-brief default); if resolvable, scaffold a
marker-guarded template there (skip if the file exists without the marker — a
filled artifact — or with it — a partial edit to preserve), print guidance, and
suspend. Make `_ring1_survey` mark the brief present only when it exists without
the marker, so a scaffolded-but-unfilled brief reads as absent and a filled one
advances the loop. Keep the input-request path for `missing_inputs` with no
artifact path. Generalize the wrapper's exit-5 line.

## Structure

**Modify:**
- `scripts/openup_agent/navigator.py` — `TEMPLATE_MARKER`, `BRIEF_TEMPLATE`,
  `DEFAULT_INPUT_PATH`, `_scaffold_input`, marker-aware `_ring1_survey`,
  `input_path` in the schema + `read_navigator_decision`, the missing-input branch
  in `run_navigator`, and a system-prompt line about `input_path`.
- `scripts/next-cycle` — exit-5 guidance names the template-fill path.
- `scripts/tests/test_openup_agent_navigator.py` — scaffold-on-missing-artifact,
  filled-brief-converges, no-clobber, genuine-question-still-requests.
- `scripts/tests/test_next_cycle.py` — exit-5 guidance mentions filling a file.
- `docs-eng-process/reference-driver.md` — navigator affordance note.

**Do not touch:**
- The deterministic engine / `resolve` / assess / milestone / plan-iteration.
- The input-request machinery (reused unchanged for genuine questions).

## Operations

- [x] Add to `navigator.py`: `TEMPLATE_MARKER`, `BRIEF_TEMPLATE`,
  `DEFAULT_INPUT_PATH`, `_scaffold_input(root, path, guidance)`, and make
  `_ring1_survey` treat a marker-containing artifact as absent.
- [x] Add `input_path` to the decision schema (`read_navigator_decision` +
  system-prompt guidance) and rewrite `run_navigator`'s missing-input branch:
  resolve a path (decision `input_path` → inception-brief default), scaffold +
  guide + suspend when resolvable; else fall back to the input-request.
- [x] Generalize `scripts/next-cycle` exit-5 guidance to name the template-fill
  path as well as the input-request.
- [x] (tester) Add navigator tests (scaffold, converge-on-filled, no-clobber,
  genuine-question-requests) + a next-cycle guidance test.
- [x] Update the navigator section of `docs-eng-process/reference-driver.md`.
- [x] (tester) Full driver+navigator+next-cycle suite green; `check-docs`,
  `openup-spec-scenarios`, `openup-fence.py check --base harness-optional` green.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format
- `docs-eng-process/reference-driver.md` — driver contract (sentinels, exits)
- `docs/changes/archive/T-096/plan.md` — the navigator design this refines

## Safeguards

- **Reversibility.** Additive to the navigator; the input-request path is retained
  for questions. A filled brief is never overwritten (marker guard).
- **No-go zones.** No change to the engine, resolve, or the other decision paths.
- **Convergence guarantee.** The default brief path makes a fresh inception
  project converge even if a weak model omits `input_path`.
- **Stdlib-only.**

## Success Measures

n/a — internal tooling / bug fix. Falsifiable acceptance = the hermetic tests
(Req 1–5), especially the scaffold→fill→create-vision convergence. Live
confirmation is the owner re-running `next-cycle` on my-product after re-sync.

## Rollout

`n/a — not user-facing`: reference-driver developer tooling; no flag. Backout is a
version pin.

## Verification

- `python3 -m pytest scripts/tests/test_openup_agent_navigator.py
  scripts/tests/test_next_cycle.py -q` — green.
- Scripted fresh project: navigator scaffolds the brief + suspends; with the brief
  filled, it returns `openup-create-vision`; a marker-only file is not clobbered;
  a no-path question still creates an input-request.
- `grep 'template' scripts/next-cycle` guidance covers the fill path.
- `openup-spec-scenarios.py check docs/changes/T-097/plan.md` → 0; `check-docs.py`
  → 0; `openup-fence.py check --base harness-optional` → clean.

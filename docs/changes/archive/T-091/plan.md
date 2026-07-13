---
id: T-091
title: Cycle engine — assess + milestone paths; pack ceremony/judgment split
status: done
priority: medium   # critical | high | medium | low
estimate: 1–2 sessions
plan: docs/explorations/2026-07-13-deterministic-cycle-engine.md
depends-on: [T-089, T-090]
blocks: []
touches:
  - scripts/openup_agent/assess.py
  - scripts/openup_agent/cycle.py
  - scripts/process-manifest.txt
  - scripts/tests/test_openup_agent_assess.py
  - scripts/tests/test_openup_agent_cycle.py
  - docs-eng-process/reference-driver.md
  - docs-eng-process/script-cli-reference.md
  - docs-eng-process/procedures/openup-assess-iteration.md
  - docs-eng-process/procedures/openup-phase-review.md
  - docs-eng-process/.claude-templates/skills/openup-assess-iteration/SKILL.md
  - docs-eng-process/.claude-templates/skills/openup-phase-review/SKILL.md
last-synced: ""
---

# T-091 — Cycle engine: assess + milestone paths; pack ceremony/judgment split

## Story

> **As an** operator driving OpenUP with the reference-driver `cycle` engine,
> **I want** `cycle` to handle the last two decision paths — `assess-iteration`
>   (grade the iteration, record `## Assessment`) and `milestone-review` (prepare
>   evidence and pause for the human go/no-go) — with the same sentinels and human
>   gates as `/openup-next`,
> **So that** the engine reaches **full `/openup-next` parity**, a phase-aware
>   iteration *converges* (assess → milestone) end-to-end through `cycle`, and the
>   prose–code drift risk closes as the pack's ceremony sections defer to the
>   engine.

INVEST — ✅ Independent (composes existing scripts + the T-090 iteration-plan instance) · ✅ Negotiable (assessment format, feedback boundary) · ✅ Valuable (parity + convergence; closes the program) · ✅ Estimable · ✅ Small-ish (two handlers: assess = 1 grading sub-run + deterministic append; milestone = zero-LLM pause) · ✅ Testable (hermetic seams + fixtures)

## Analysis Context

- **Domain.** The `cycle` engine (`scripts/openup_agent/cycle.py`). Two decision
  paths still land in `UNSUPPORTED_PATHS` → exit 7: `assess-iteration` (§1c-assess,
  fired by `openup-board.py` when a T-090-planned iteration's committed lanes are
  all done and its instance has no `## Assessment`) and `milestone-review`
  (§1c-milestone, fired when the roadmap is drained + phase exit criteria met +
  no milestone record). T-090 made these reachable by producing recognizable
  iteration-plan instances; T-091 makes `cycle` handle them.
- **Assess = derive-in-code + one grading sub-run + deterministic append.**
  Done-ness of committed lanes is already code (`_work_item_done` — it is what
  fired the decision). The genuine judgment is grading the **non-derivable**
  evaluation criteria (objectives met? demo verdict) against repo evidence — ONE
  bounded sub-run whose structured output the engine appends as an `## Assessment`
  section to the iteration-plan instance (the assessed marker `resolve` reads).
  Appending `## Assessment` is sanctioned record state (like ticking a box).
- **Milestone = zero LLM.** The engine prepares evidence (phase, cycle,
  criteria) and raises the human go/no-go as a T-074 input-request, suspending
  (exit 5) — it **records evidence and pauses; it never advances the phase** (the
  human decision + lifecycle stamp does, exactly as `/openup-phase-review`).
- **Pack ceremony/judgment split (§5).** The affected procedures
  (`openup-assess-iteration.md`, `openup-phase-review.md`) gain a short note that
  the `cycle` engine is the **ceremony authority** for these paths; their prose
  describes the judgment content (what a good assessment / a go/no-go needs), the
  Claude Code path is unchanged. No aggressive rewrite — the pack still works
  in-context for the Claude Code harness.
- **Scope boundaries.** (1) Assess does **not** auto-enqueue discovered work as
  roadmap rows — that is product scope behind the T-094 consent gate; the
  `## Assessment` *records* discovered work + excluded-from-demo items as notes,
  and naming them is the human's follow-up. (2) Milestone does **not** advance the
  phase or write the milestone record — it pauses; the human go/no-go +
  `openup-lifecycle.py` own that. (3) Does **not** change `openup-board.py`
  resolve or the lifecycle readers.
- **Definition of done.** `cycle` handles both paths (removed from
  `UNSUPPORTED_PATHS`): assess grades + writes `## Assessment` + commits + emits
  the `ADVANCED` sentinel; milestone prepares evidence + suspends on an
  input-request (no dup on re-run) with the `SUSPEND` sentinel. A hermetic
  end-to-end proves a planned+delivered iteration assesses, and a drained phase
  pauses for milestone.

> **Assumption:** the grading sub-run writes structured output to
> `.openup/assessment.json` (criteria grades + demo scope + verdict + discovered
> notes), the T-072 pattern; the engine renders the `## Assessment` section
> deterministically from it. *(Vetoable at review.)*
> **Assumption:** assess/milestone are handled **unconditionally** (not behind
> `--no-recover`) — they are core T-078 lifecycle paths, not recovery.
> `--no-recover` still exits 7 for `plan-iteration` only. *(Vetoable.)*
> **Assumption:** the milestone input-request is remembered in `.openup/cycle.json`
> (like T-094 replenishment) so a still-open request re-suspends without a
> duplicate. *(Vetoable.)*

## Requirements

1. **`cycle` handles `assess-iteration`** instead of exit 7.
   - **Given** a T-090-planned iteration whose committed lanes are all done and
     whose instance has no `## Assessment`, so `resolve` returns
     `assess-iteration` (with `lane.plan` the instance), **When** `cycle` runs,
     **Then** it does not return `EXIT_UNSUPPORTED`; it dispatches exactly one
     grading sub-run and reads its result from `.openup/assessment.json`.

2. **Assess appends `## Assessment` deterministically and commits.**
   - **Given** the grading sub-run produced criteria grades + a verdict, **When**
     the engine records the assessment, **Then** an `## Assessment` section is
     appended to the iteration-plan instance (criteria met/unmet + evidence, demo
     scope, discovered-work notes, one-line verdict), the instance still passes
     `check-docs`, it is committed, and `resolve` afterwards no longer returns
     `assess-iteration` for that iteration.

3. **Assess emits `/openup-next`-parity sentinel.**
   - **Given** the assessment is recorded, **When** `cycle` returns, **Then** it
     prints `OPENUP-NEXT: ADVANCED — assessed <iteration>` on stdout and exits 0.

4. **`cycle` handles `milestone-review` as a zero-LLM human pause.**
   - **Given** `resolve` returns `milestone-review` (phase exit criteria met,
     roadmap drained, no milestone record), **When** `cycle` runs, **Then** no LLM
     sub-run is dispatched, an input-request capturing the phase go/no-go evidence
     is created under `docs/input-requests/`, the `SUSPEND` sentinel is printed,
     and it exits 5 — the phase is **not** advanced and no milestone record is
     written.

5. **The milestone pause does not duplicate its request.**
   - **Given** a milestone input-request already open (recorded in
     `.openup/cycle.json`), **When** a later `cycle` re-resolves to
     `milestone-review`, **Then** it re-suspends pointing at the same request and
     creates no second file.

6. **Both paths are removed from `UNSUPPORTED_PATHS`; `--no-recover` unaffected.**
   - **Given** `--no-recover`, **When** `resolve` returns `assess-iteration` or
     `milestone-review`, **Then** `cycle` still handles them (they are not
     recovery); only `plan-iteration` stays exit 7 under `--no-recover`.

7. **The affected procedures defer ceremony to the engine.**
   - **Given** `openup-assess-iteration.md` and `openup-phase-review.md`, **When**
     read, **Then** each carries a short note that the `cycle` engine is the
     ceremony authority for its path (judgment content unchanged; Claude Code path
     intact).

## Behavior Delta

Ring-1 truth for the driver lives in `docs-eng-process/`.

**Added:**
- `cycle` handlers for `assess-iteration` (grade + record `## Assessment`) and
  `milestone-review` (evidence + input-request pause, zero LLM).

**Modified:**
- `cycle`'s supported decision paths — `docs-eng-process/reference-driver.md` +
  `script-cli-reference.md`: assess/milestone no longer exit 7.
- `docs-eng-process/procedures/openup-assess-iteration.md`,
  `openup-phase-review.md`: an engine-ceremony-authority note (judgment content
  unchanged).

**Removed:** the exit-7 fallback for `assess-iteration`/`milestone-review`
(they are now handled).

## Entities

- **assess/milestone handlers** (new) — `scripts/openup_agent/assess.py`
- **`run_cycle` wiring** (modified) — `scripts/openup_agent/cycle.py`
- **iteration-plan instance** (read + appended) — `docs/phases/<phase>/…`
- **board readers** (read-only) — `_active_iteration_plan`, `_has_assessment`,
  `_phase_exit_ready`, `_milestone_exists`
- **input-request / suspend** (reused) — `openup-input.py`, `EXIT_SUSPEND`,
  `.openup/cycle.json`
- **affected procedures** (noted) — `openup-assess-iteration.md`,
  `openup-phase-review.md`

## Approach

A new `assess.py` holds both handlers + the grading contract + the `## Assessment`
renderer, taking injected callables (dispatch a sub-run, run gates, git-commit,
run scripts) so it stays testable and imports nothing heavyweight from `cycle`.
`cycle.run_cycle` calls them on the two decision paths (removed from
`UNSUPPORTED_PATHS`). Assess = derive-in-code done-ness (already true) + one
grading sub-run + deterministic `## Assessment` append + commit + `ADVANCED`
sentinel. Milestone = evidence prep + one input-request + `SUSPEND` (exit 5),
remembered in `.openup/cycle.json` (reusing the T-094 request-memory pattern). The
pack procedures get a short engine-authority note. Sentinels/exits match
`/openup-next`.

## Structure

**Add:**
- `scripts/openup_agent/assess.py` — `run_assess(...)`, `run_milestone(...)`,
  `GRADING_CONTRACT`/system prompt, `read_assessment`, `render_assessment_section`.
  Stdlib-only; driver-coupled ops injected.
- `scripts/tests/test_openup_agent_assess.py` — hermetic unit + seam tests.

**Modify:**
- `scripts/openup_agent/cycle.py` — handle `assess-iteration` /
  `milestone-review` in `run_cycle` (dispatch to `assess.py`; `_assess` /
  `_milestone` test seams); drop both from `UNSUPPORTED_PATHS`.
- `scripts/process-manifest.txt` — ship `openup_agent/assess.py`.
- `scripts/tests/test_openup_agent_cycle.py` — wiring tests + update the
  `UNSUPPORTED_PATHS` test (assess/milestone now handled; plan-iteration under
  `--no-recover` remains unsupported).
- `docs-eng-process/reference-driver.md`, `script-cli-reference.md` — assess /
  milestone paths + parity.
- `docs-eng-process/procedures/openup-assess-iteration.md`,
  `openup-phase-review.md` — engine-ceremony-authority note (the pack is the
  editable source; the `.claude-templates/skills/` mirror is regenerated from it
  via `render-skills-mirror.py --write`, not hand-edited).

**Do not touch:**
- `openup-board.py` resolve / lifecycle readers — the engine consumes them; no
  reader change.
- The T-094 consent gate — assess does not auto-enqueue product scope.
- `openup-lifecycle.py` milestone stamping — the human go/no-go owns it.

## Operations

- [x] Add `scripts/openup_agent/assess.py`: `run_assess` (read instance →
  grading sub-run → `read_assessment` → `render_assessment_section` → append →
  gate → commit → ADVANCED) and `run_milestone` (evidence → input-request +
  SUSPEND, remembered, no dup) + the grading contract/system prompt.
- [x] Wire both into `cycle.py` `run_cycle` (with `_assess` / `_milestone`
  seams) and remove `assess-iteration`/`milestone-review` from
  `UNSUPPORTED_PATHS`.
- [x] Add `openup_agent/assess.py` to `scripts/process-manifest.txt`.
- [x] (tester) Add `scripts/tests/test_openup_agent_assess.py` (unit: assessment
  render/parse; orchestration: assess happy path appends `## Assessment` + commits
  + ADVANCED; milestone creates request + suspends + no-dup) and update the cycle
  wiring/UNSUPPORTED_PATHS test.
- [x] Update `reference-driver.md` + `script-cli-reference.md` for the assess /
  milestone paths and full parity.
- [x] Add the engine-ceremony-authority note to
  `openup-assess-iteration.md` + `openup-phase-review.md`.
- [x] (tester) Full driver suite green; `check-docs`, `openup-spec-scenarios`,
  `openup-fence.py check --base harness-optional` green.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, process conventions
- `docs-eng-process/reference-driver.md` — driver contract (sentinels, exit
  codes, bounded sub-runs)
- `.claude/skills/openup-assess-iteration/SKILL.md`,
  `.claude/skills/openup-phase-review/SKILL.md` — the judgment content being
  deferred to
- `docs-eng-process/model-tiers.md` — grading tier

## Safeguards

- **Token / size budget.** Assess = exactly one grading sub-run (bounded);
  milestone = zero LLM. Done-ness / evidence / rendering / suspend are code.
- **Reversibility.** Assess appends a record + commits (git-revertible); milestone
  only creates an input-request + suspends (no phase change). A failed gate after
  the append aborts before commit.
- **No-go zones.** The engine never advances a phase, never writes a milestone
  record, and never auto-enqueues roadmap scope (T-094 consent boundary).
- **Stdlib-only**; ships via process-manifest.

## Success Measures

n/a — internal process tooling. Falsifiable acceptance = the hermetic tests
(Req 1–7). Program acceptance (§6 of the exploration — `cycle`-driven ShareShed
Inception at ≥80% clean-pass and ≤1/10th tokens vs `next`) is the **T-080
benchmark's** job and the owner's live batch; this sandbox reaches no endpoint.

## Rollout

`n/a — not user-facing`: reference-driver developer tooling. The paths are core
engine behavior (not flagged); backout is a version pin. No flag-removal owed.

## Verification

- `python3 -m pytest scripts/tests/test_openup_agent_assess.py
  scripts/tests/test_openup_agent_cycle.py -q` — all green.
- Scripted assess: a planned+delivered iteration → `## Assessment` appended,
  instance still `check-docs`-clean, `resolve` no longer `assess-iteration`,
  `ADVANCED` sentinel.
- Scripted milestone: drained phase → input-request created + exit 5 + `SUSPEND`;
  a re-run re-suspends with no second request.
- `openup-spec-scenarios.py check docs/changes/T-091/plan.md` → 0; `check-docs.py`
  → 0; `openup-fence.py check --base harness-optional` → clean.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

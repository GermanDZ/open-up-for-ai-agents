---
id: T-096
title: Process-agnostic next-cycle — LLM process navigator behind the driver
status: ready   # proposed → ready → in-progress → done → verified
priority: high   # critical | high | medium | low
estimate: 1–2 sessions
plan: docs/explorations/2026-07-13-deterministic-cycle-engine.md
depends-on: [T-095, T-077]
blocks: []
touches:
  - scripts/next-cycle
  - scripts/openup_agent/navigator.py
  - scripts/openup_agent/cycle.py
  - scripts/openup-agent.py
  - scripts/process-manifest.txt
  - scripts/tests/test_next_cycle.py
  - scripts/tests/test_openup_agent_navigator.py
  - scripts/tests/test_openup_agent_cycle.py
  - docs-eng-process/reference-driver.md
  - docs-eng-process/getting-started-reference-driver.md
  - docs-eng-process/script-cli-reference.md
  - docs/changes/archive/T-095/plan.md
last-synced: ""
---

# T-096 — Process-agnostic `next-cycle`: an LLM process navigator behind the driver

## Story

> **As an** operator running OpenUP with my own harness (the reference driver),
> **I want** the single entry point to figure out *what the process needs next*
>   by evaluating the OpenUP workflow against my project's actual state — instead
>   of a wrapper that hardcodes the pre-Inception state machine,
> **So that** it keeps working as the process evolves and handles project states
>   T-095 never anticipated (partial Inception, an existing codebase adopting
>   OpenUP) without me hand-picking a procedure.

INVEST — ✅ Independent (deterministic layers still answer first; navigator only fills the gap) · ✅ Negotiable (navigator inputs/output-shape) · ✅ Valuable (owner architecture direction 2026-07-13) · ✅ Estimable · ✅ Small (one new bounded judgment + a wrapper strip + doc/test moves) · ✅ Testable (hermetic scripted-LLM sub-run, the T-089/`_subrun` seam)

## Analysis Context

State the *why* the spec needs but the code can't show:

- **Domain.** The reference-driver control surface. Two layers exist today: the
  deterministic engine (`openup-board.py resolve` → `cycle` in
  `scripts/openup_agent/cycle.py`) which answers when the repo state is
  classifiable, and — above it — `scripts/next-cycle` (T-095), a Python wrapper
  that hardcodes the fresh-project state machine (`agent.env` → template brief →
  `openup-create-vision` → `cycle`). This task moves process *navigation* out of
  that wrapper and into a bounded LLM judgment invoked by the driver, keeping the
  deterministic layers first (preserving the measured T-080 token/reliability win).
- **Scope boundaries.** This does **not** touch the deterministic engine's happy
  path — `resolve` → `pick`/`resume`/`plan-iteration`/`assess`/`milestone` behave
  byte-for-byte as before. The navigator fires **only** when the deterministic
  layers yield nothing actionable (the `noop` decision — most importantly the
  fresh/`no docs/roadmap.md` case the hardcoded hint at `cycle.py:951` handles
  today). It does **not** implement T-090/T-091 (those own `plan-iteration`/
  `assess`/`milestone`); it does **not** invent product scope (that stays behind
  the T-094 consent gate); it does **not** add a new `openup-agent.py` subcommand
  (the navigator is reached from inside the existing `cycle` path).
- **Definition of done.** (1) `scripts/next-cycle` contains no process knowledge —
  no brief template, no `VISION_INSTRUCTION`, no vision/roadmap stage machine;
  only env guidance, one driver invocation, and exit translation remain. (2) On a
  `noop`/unclassifiable state the driver runs a bounded process-navigator sub-run
  that reads the process map + lifecycle status + a Ring-1 artifact survey +
  the procedures index and emits a structured decision file; the driver then runs
  the named procedure, or raises the named missing input as a T-074 input-request
  (suspend / exit 5). (3) The end-to-end fresh-project path (empty repo →
  navigator picks Inception authoring → vision + roadmap) works hermetically, and
  T-095's superseded stage tests are removed with the supersession recorded on the
  archived T-095 spec.

> **Assumption:** the navigator emits its decision as a **structured JSON file**
> the driver reads back (the T-072 write-a-file-then-read-it pattern already used
> for spec authoring), not as parsed stdout — a file is inspectable, testable, and
> survives a crash mid-run. *(Vetoable at review.)*
> **Assumption:** the navigator hooks the existing **`noop`** decision path in
> `run_cycle` (after recovery, at `cycle.py:949`), reusing the `recover`-style
> gating so `--no-recover` (or a new `--no-navigate` sibling) disables it and
> restores exact T-089/T-095 behavior. *(Vetoable at review.)*
> **Assumption:** the deterministic **Ring-1 artifact survey** (which of
> vision / roadmap / use-cases / architecture exist) is computed in Python and
> handed to the navigator as facts — the LLM classifies, it does not go hunting
> the filesystem itself. *(Vetoable at review.)*

## Requirements

1. **`next-cycle` carries no process knowledge.** After this task the wrapper
   holds only: env loading/guidance (`agent.env`, `ensure_env`), exactly one
   `openup-agent.py` invocation, and exit-code → guidance translation. The brief
   template, `VISION_INSTRUCTION`, `brief_state`, `write_template_brief`, and the
   `fresh`-project branch are gone.
   - **Given** a fresh project (no `docs/vision.md`, no `docs/roadmap.md`) with a
     configured endpoint, **When** `./scripts/next-cycle` runs, **Then** it makes
     a single driver invocation (no brief file is written by the wrapper) and its
     exit code is the driver's, byte-for-byte passed through.
   - **Given** the wrapper source, **When** grep'd for `BRIEF_TEMPLATE`,
     `VISION_INSTRUCTION`, `stakeholder-brief`, **Then** there are no matches.

2. **A bounded process-navigator judgment exists in the driver**, invoked only
   when the deterministic layers yield nothing actionable.
   - **Given** a `resolve` decision whose path is `pick`/`resume`/`plan-iteration`
     (recoverable) — i.e. the deterministic layers *do* have an answer — **When**
     `cycle` runs, **Then** the navigator is **not** invoked and behavior is
     identical to T-089/T-092/T-094.
   - **Given** a `noop` decision on a fresh repo with no `docs/roadmap.md`,
     **When** `cycle` runs (navigation enabled), **Then** exactly one bounded
     navigator sub-run is dispatched (default cap, authoring tier) before any
     terminal sentinel is printed.

3. **The navigator reads the process as data, not as hardcoded prose.** Its input
   is assembled deterministically from: `docs-eng-process/process-map.yaml` (via
   `openup-process-map.py`), `openup-lifecycle.py status --json`, a Python Ring-1
   artifact survey, and the procedures index (`docs-eng-process/procedures/`).
   - **Given** the process map names Inception's first activity as
     `initiate-project` → `openup-create-vision`, **When** the navigator runs on a
     fresh repo, **Then** its input payload contains that phase/activity/procedure
     mapping (proven by the scripted sub-run receiving it), and the wrapper/driver
     contain no literal `"openup-create-vision"` fallback string driving the choice.

4. **The navigator returns a structured decision** — the next `procedure`, its
   `--instruction`, and any `missing_inputs` — as a file the driver reads back.
   - **Given** a fresh repo with a filled-in stakeholder brief present, **When**
     the navigator runs, **Then** the decision file names an authoring procedure
     (e.g. `openup-create-vision`) with a non-empty `instruction` and empty
     `missing_inputs`.
   - **Given** a fresh repo with **no** brief and no other product input, **When**
     the navigator runs, **Then** the decision file names a `missing_inputs` entry
     describing the human input required (the product/stakeholder brief), and
     names no runnable authoring procedure.

5. **The driver acts on the navigator's decision.** A named procedure with no
   missing inputs is run in the same invocation; a `missing_inputs` result is
   raised as a T-074 input-request and suspends (exit 5), reusing the existing
   suspend machinery — never a hardcoded template brief written by the driver.
   - **Given** a navigator decision naming `openup-create-vision` + instruction,
     **When** the driver consumes it, **Then** it dispatches that procedure and
     the run's exit code / sentinel are that procedure's.
   - **Given** a navigator decision with `missing_inputs`, **When** the driver
     consumes it, **Then** an input-request file is written under
     `docs/input-requests/` and the cycle returns `EXIT_SUSPEND` (5), and a later
     cycle with the request still open re-suspends without duplicating it.

6. **The consent boundary is preserved.** Navigation that authors *process*
   artifacts (vision, use-cases, architecture, iteration plan) runs directly;
   anything that would propose *product scope* (new roadmap entries) stays behind
   the T-094 consent gate and is never invented silently by the navigator.
   - **Given** a navigator decision whose procedure would add roadmap scope,
     **When** the driver consumes it, **Then** it routes through the existing
     T-094 consent path (interactive yes/no or input-request), not a direct run.
   - **Given** a navigator decision for a process-artifact authoring procedure,
     **When** consumed, **Then** it runs directly with no consent prompt.

7. **Fix-spec-first: T-095's stage tests are superseded, not silently dropped.**
   The `next-cycle` stage-detection tests (brief/template/vision stages) are
   removed or rewritten as navigator tests, and the archived T-095 spec
   (`docs/changes/archive/T-095/plan.md`) records that its stage machine +
   stage tests were superseded by T-096.
   - **Given** `scripts/tests/test_next_cycle.py` after this task, **When** run,
     **Then** it asserts the *thin* wrapper contract (single invocation,
     passthrough, env guidance) and contains no assertion on a brief/template/
     vision stage machine.
   - **Given** the archived T-095 plan, **When** read, **Then** it carries a
     dated supersession note pointing to T-096.

## Behavior Delta

How this task changes existing product behavior. This project's product **is** the
OpenUP process tooling; Ring-1 truth for the reference driver lives in
`docs-eng-process/` (reference-driver docs + process map), not `docs/product/`.

**Added:**
- A bounded process-navigator judgment in the driver that classifies an
  unclassifiable/`noop` project state against the OpenUP process map and returns
  the next procedure + instruction, or the missing human input.

**Modified:**
- `scripts/next-cycle` behavior — `docs-eng-process/reference-driver.md`
  (`next-cycle` section) + `docs-eng-process/getting-started-reference-driver.md`:
  the wrapper no longer detects project stage or writes a template brief; the
  fresh-project path is now driven by the navigator inside the driver.
- The `cycle` `noop`/no-roadmap outcome — `docs-eng-process/reference-driver.md`
  (`cycle` section): instead of printing a hardcoded "run create-vision" hint, the
  driver navigates (or raises a missing-input request).

**Removed:**
- The wrapper's hardcoded pre-Inception state machine (brief template →
  `VISION_INSTRUCTION` → vision/roadmap gate) — `docs/changes/archive/T-095/plan.md`
  (T-095 Approach / Requirements): its stage detection is retired in favor of
  navigation.

## Entities

- **`next-cycle`** (modified) — `scripts/next-cycle`
- **`navigator`** (new) — `scripts/openup_agent/navigator.py` (input assembly +
  decision-file schema + consume)
- **`run_cycle` noop hook** (modified) — `scripts/openup_agent/cycle.py`
- **process map** (read-only) — `docs-eng-process/process-map.yaml`,
  `scripts/openup-process-map.py`
- **lifecycle status** (read-only) — `scripts/openup-lifecycle.py status --json`
- **procedures index** (read-only) — `docs-eng-process/procedures/openup-*.md`
- **input-request / consent machinery** (read-only, reused) — `EXIT_SUSPEND`,
  `replenish_flow`/T-094 consent in `scripts/openup_agent/cycle.py`
- **archived T-095 spec** (annotated) — `docs/changes/archive/T-095/plan.md`

## Approach

Invert T-095: the wrapper becomes a dumb passthrough, and the *only* new
intelligence is one bounded LLM judgment the driver reaches when — and only when —
its deterministic layers have no actionable answer. Compute everything the
navigator needs in Python (process-map lookups, lifecycle status, a Ring-1 file
survey, the procedures list) and hand it as facts; the LLM's sole job is to
classify state → next procedure + instruction, or name the missing human input.
The decision comes back as a small JSON file (T-072 pattern) the driver reads and
acts on: run the procedure, or suspend with a T-074 input-request. Reuse the
existing `_subrun`/`_completion` seams (T-089), the suspend path (T-074), and the
consent gate (T-094) rather than adding new control machinery.

## Structure

**Add:**
- `scripts/openup_agent/navigator.py` — input assembly (`build_navigator_input`),
  decision-file schema + parse (`read_navigator_decision`), and the
  consume/dispatch helper. Stdlib-only.
- `scripts/tests/test_openup_agent_navigator.py` — hermetic navigator tests
  (scripted sub-run via the `_subrun`/`_completion` seam).

**Modify:**
- `scripts/next-cycle` — strip the stage machine; keep env + one invocation +
  exit translation.
- `scripts/openup_agent/cycle.py` — invoke the navigator on the `noop` path
  (behind a `navigate`/`--no-navigate` gate mirroring `recover`); consume its
  decision (run procedure | suspend). Replace the hardcoded no-roadmap hint.
- `scripts/openup-agent.py` — add the `--no-navigate` flag to the `cycle`
  subparser and thread it to `run_cycle(navigate=...)`.
- `scripts/process-manifest.txt` — ship `openup_agent/navigator.py`.
- `scripts/tests/test_next_cycle.py` — supersede stage tests with the thin-wrapper
  contract (Req 7).
- `scripts/tests/test_openup_agent_cycle.py` — add `NavigatorDispatchTest` (noop
  hooks the navigator; a deterministic path does not) and switch the pre-existing
  noop-hint tests to `navigate=False` (the gated fallback they still assert).
- `docs/changes/archive/T-095/plan.md` — supersession note (Req 7, fix-spec-first).
- `docs-eng-process/reference-driver.md`, `getting-started-reference-driver.md`,
  `script-cli-reference.md` — document navigation replacing the wrapper stage
  machine.

**Do not touch:**
- `scripts/openup-board.py` / `resolve` decision logic — the deterministic layer
  is unchanged; the navigator sits *after* a `noop`, never edits resolution.
- The T-090/T-091 paths (`plan-iteration`, `assess-iteration`, `milestone-review`)
  — out of scope; those remain their own tasks.
- `docs-eng-process/process-map.yaml` — read-only input; the navigator consumes
  it, does not extend it.

## Operations

- [x] Add `scripts/openup_agent/navigator.py`: `build_navigator_input(root)`
  (deterministic — process-map phase/activities, `lifecycle status --json`,
  Ring-1 artifact survey, procedures index) and the decision-file schema +
  `read_navigator_decision(root)`.
- [x] Wire the navigator into `cycle.py`'s `noop` path behind a `navigate` gate
  (default on; `--no-navigate` restores T-089/T-095 behavior): dispatch one
  bounded sub-run (reusing the `_subrun`/`_completion` seam), read its decision
  file, then run the named procedure **or** raise a T-074 input-request (suspend)
  for `missing_inputs`, routing scope-proposing procedures through the T-094
  consent gate.
- [x] Strip all process knowledge from `scripts/next-cycle` — remove the brief
  template, `VISION_INSTRUCTION`, `brief_state`, `write_template_brief`, and the
  `fresh` branch; leave env guidance + one invocation + exit translation.
- [x] Add `openup_agent/navigator.py` to `scripts/process-manifest.txt`.
- [x] (tester) Supersede `scripts/tests/test_next_cycle.py` stage tests with the
  thin-wrapper contract, and add `scripts/tests/test_openup_agent_navigator.py`
  (fresh-repo-with-brief → procedure decision; fresh-repo-no-input →
  `missing_inputs` → suspend; deterministic-path → navigator NOT invoked).
- [x] Record the supersession note on `docs/changes/archive/T-095/plan.md`
  (fix-spec-first, Req 7).
- [x] Update `reference-driver.md`, `getting-started-reference-driver.md`, and
  `script-cli-reference.md` to describe navigation replacing the wrapper stage
  machine.
- [x] (tester) Run the full driver+cycle+navigator suite green; run
  `openup-spec-scenarios.py check`, `check-docs.py`, and
  `openup-fence.py check --base harness-optional`.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.)
- `docs-eng-process/reference-driver.md` — driver contract (stdlib-only, sentinel
  on stdout, guidance on stderr, typed exit codes)
- `docs-eng-process/model-tiers.md` — the authoring/MID tier for the sub-run

## Safeguards

- **Token / size budget.** One bounded navigator sub-run per cycle (default step
  cap, authoring tier) — no unbounded loop; it fires only on `noop`, never on a
  deterministic answer, so the T-080 token profile of the happy path is unchanged.
- **Reversibility.** The navigator is gated (`--no-navigate`, mirroring
  `--no-recover`); disabling it restores exact T-089/T-095 behavior. The wrapper
  strip is a pure deletion recoverable from git.
- **No-go zones.** `resolve` decision logic and the deterministic engine paths do
  not change; the navigator never edits resolution and never writes product-scope
  roadmap rows without the T-094 consent gate.
- **Stdlib-only.** `navigator.py` adds no dependencies (driver stays stdlib-only).

## Success Measures

n/a — internal process tooling with no user-facing telemetry. The falsifiable
acceptance is the hermetic navigator test set (Req 2–7) plus the fresh-project
end-to-end scripted run: an empty repo drives itself to a vision + roadmap through
navigation with **zero** hardcoded procedure strings in the wrapper. (Live-model
behavior is read back through the T-080 benchmark harness, the owner's batch step,
as with T-072/T-095 — this sandbox reaches no endpoint.)

## Rollout

`n/a — <reason>`: not user-facing in the flag sense — the reference driver is a
developer tool configured by env, not a deployed service. The change is guarded by
a code-level gate (`--no-navigate`) rather than a feature flag; a project pins the
driver by framework version, so backout is a version pin or the gate, not a flag
toggle. No flag-removal follow-up is owed.

## Verification

- `python3 -m pytest scripts/tests/test_openup_agent_navigator.py
  scripts/tests/test_next_cycle.py scripts/tests/test_openup_agent_cycle.py -q`
  — all green.
- Scripted fresh-project run: empty repo (+ filled brief) → navigator decision
  names an authoring procedure → vision + roadmap produced; empty repo, no input →
  `missing_inputs` → input-request written + exit 5.
- `grep -E 'BRIEF_TEMPLATE|VISION_INSTRUCTION|stakeholder-brief' scripts/next-cycle`
  → no matches.
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-096/plan.md` → 0.
- `python3 scripts/check-docs.py` → 0; `python3 scripts/openup-fence.py check
  --base harness-optional` → clean.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

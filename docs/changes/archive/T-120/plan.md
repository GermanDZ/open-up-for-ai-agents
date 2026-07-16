---
id: T-120
title: "Inline engine-held context into sub-run briefings (E1) — paths become content"
status: done
priority: high
estimate: 1 session
plan: docs/roadmap.md
depends-on: [T-106, T-118]
blocks: []
last-synced: ""
touches:
  - scripts/openup_agent/cycle.py
  - scripts/openup_agent/plan_iteration.py
  - scripts/openup_agent/assess.py
  - scripts/tests/test_openup_agent_cycle.py
  - scripts/tests/test_openup_agent_plan_iteration.py
  - scripts/tests/test_openup_agent_assess.py
  - docs-eng-process/reference-driver.md
---

# T-120 — Inline engine-held context into sub-run briefings

## Story

> **As a** weak local model running a bounded cycle sub-run
> **I want** the briefing to carry the CONTENT of the files the engine already read (or can read once, deterministically)
> **So that** I start authoring on turn 1 instead of spending 2–4 turns re-reading plan.md/design.md/vision that the engine held in memory when it built my instruction

INVEST — ✅ Independent · ✅ Negotiable · ✅ Valuable · ✅ Estimable · ✅ Small · ✅ Testable

## Analysis Context

- **Domain.** The four sub-run briefing builders in the cycle engine. Evidence
  (2026-07-16 review, `docs/explorations/2026-07-16-cycle-orchestration-economics.md`):
  `build_step_instruction` (cycle.py:374-393) hands the executor *paths*
  ("Briefing (read before acting): docs/changes/<t>/plan.md …") although the
  engine parsed plan.md to find the Operations boxes (cycle.py:1352) and
  discarded the text — every judgment box burns ≥1 `read_file` on plan.md plus
  typically a design.md probe. `render_task_instruction`
  (plan_iteration.py:187-193) still emits unresolvable workproduct
  display-names ("Additional inputs to consider: Vision") beyond the one
  `requires_input` path T-118 fixed. `LANE_SPEC_CONTRACT`
  (plan_iteration.py:69-86) makes each of N spec lanes independently re-read
  the same vision. `render_grading_instruction` (assess.py:80-87) inlines the
  instance but tells the model to grade on "repo evidence" it must grep for.
  T-118 is the proven precedent: naming one concrete path killed a measured
  5-glob/4-turn hunt; this task finishes the principle — content, not paths.
- **Scope boundaries.** Instruction/briefing assembly ONLY. No change to the
  execution seam (`loop.run`, `run_task`, `_dispatch_judgment` signatures stay),
  no change to stamping, gates, the map, or `task-library.yaml` data. The
  name→path map is derived at runtime from the already-loaded task defs (a
  def's `output_path` is the workproduct's home) — no compiler (`build-task-
  library.py`) change. Tool-surface additions (batch read etc.) are explicitly
  OUT (sequenced behind this task's re-measure, per the exploration's
  product-manager challenge pass).
- **Definition of done.** All four briefing builders inline engine-held
  content, size-capped with an explicit truncation marker that names the path
  (so a model can still `read_file` the remainder); absent files degrade to
  today's path-naming lines; hermetic tests cover each builder + the cap +
  the fallback.

## Requirements

1. Judgment-box briefings inline the change folder's content.
   - **Given** a lane whose `docs/changes/<id>/plan.md` exists and `design.md` is present **When** `build_step_instruction` builds the step instruction **Then** the instruction contains the plan.md text and the design.md text inline, and no longer instructs the model to read those paths first.
   - **Given** the same lane resumed from an answered input request **When** the instruction is built **Then** the answered request's content is inlined (not just its path).
2. Task-def instructions resolve workproduct-name inputs to concrete paths and inline small ones.
   - **Given** a def with `inputs: [Vision]` and a loaded library in which the `develop-technical-vision` def declares `output_path: docs/product/vision.md`, that file existing **When** `render_task_instruction` builds the instruction **Then** it names `docs/product/vision.md` and inlines its content; the display-name "Vision" remains as secondary context.
   - **Given** a workproduct name no def resolves, or a resolved path that does not exist **When** the instruction is built **Then** the line degrades to the current display-name form (no phantom path, no crash).
3. Spec-lane instructions carry engine-read vision content.
   - **Given** a plan-iteration with N>1 generated lanes and an existing vision file **When** each lane's spec instruction is built **Then** each contains the vision content inline (read once by the engine) and drops the "Read docs/vision.md … first" directive.
4. Assess grading instructions carry a deterministic evidence bundle.
   - **Given** an iteration with delivered lanes **When** the grading instruction is built **Then** it includes an engine-assembled evidence section (delivered lane ids + their plan titles/status, landed artifact paths) so grading needs no discovery grep.
5. Every inlined block is size-capped with an explicit marker.
   - **Given** a file larger than the per-file inline cap **When** any builder inlines it **Then** the block is truncated at the cap and ends with a marker naming the path and stating truncation (e.g. `… [truncated — full file at <path>]`).
6. No regression on absent context.
   - **Given** a missing plan.md/design.md/vision **When** any builder runs **Then** the instruction degrades to the current path-naming behavior and the sub-run still launches.

## Behavior Delta

**Modified** — the four instruction builders: `cycle.build_step_instruction`
(+ its callers pass the already-parsed plan text), `plan_iteration.render_task_instruction`
(input resolution + inlining), the spec-lane instruction assembly around
`LANE_SPEC_CONTRACT`, and `assess.render_grading_instruction` (evidence
bundle). Ring-1 driver-behavior doc: `docs-eng-process/reference-driver.md`
briefing description — a short note that briefings inline content, size-capped.

**Added** — a small shared helper (engine-side) for capped inlining with the
truncation marker. **Removed** — n/a.

## Entities

- **Step-instruction builder** (modified) — `scripts/openup_agent/cycle.py`
  `build_step_instruction` + `run_judgment_step` call sites.
- **Task/spec instruction builders** (modified) —
  `scripts/openup_agent/plan_iteration.py` `render_task_instruction`,
  spec-lane instruction assembly.
- **Grading-instruction builder** (modified) — `scripts/openup_agent/assess.py`.

## Approach

One shared `inline_block(root, rel_path, cap)` helper returns the capped
content block or `None` when absent. `build_step_instruction` gains optional
content arguments (plan text the caller already holds; design/resumable-input
read once by the engine). `render_task_instruction` builds a name→path map
from the loaded `task_defs` (`inputs` display-name ↔ another def whose
artifact/`output_path` produces it) and inlines resolvable, existing, small
inputs; T-118's `requires_input` path keeps first position. Spec-lane and
assess builders receive engine-read vision / evidence text. All changes are
additive to instruction strings — sub-run mechanics untouched.

## Structure

**Modify:**
- `scripts/openup_agent/cycle.py` — `build_step_instruction(…, plan_text=None, design_text=None, input_text=None)`; callers thread the text they hold.
- `scripts/openup_agent/plan_iteration.py` — name→path resolution + inlining in `render_task_instruction`; vision inlining for spec lanes; the shared inline helper (or import site).
- `scripts/openup_agent/assess.py` — deterministic evidence bundle in the grading instruction.
- `scripts/tests/test_openup_agent_cycle.py`, `…_plan_iteration.py`, `…_assess.py` — new briefing-shape tests.
- `docs-eng-process/reference-driver.md` — briefing note.

**Do not touch:** `loop.py` (execution/tool loop), `tools.py`, `stamping.py`,
`build-task-library.py`, `docs-eng-process/task-library.yaml`,
`process-map.yaml`, gates.

## Operations

- [x] Add the capped `inline_block` helper (truncation marker names the path); thread plan/design/resumable-input content into `build_step_instruction` from the engine-held text.
- [x] `render_task_instruction`: build the name→path map from loaded task defs; inline resolvable existing inputs (cap + marker); keep T-118's requires_input first; degrade cleanly on unresolvable names.
- [x] Inline engine-read vision into spec-lane instructions; drop the read-first directive when inlined.
- [x] Assess: assemble the deterministic evidence bundle (delivered lanes + artifact paths) into the grading instruction.
- [x] (tester) Hermetic tests: each builder's inlined shape; cap + marker; absent-file fallback; no-regression when nothing is inlinable.

## Norms

Inherits from:
- `docs-eng-process/conventions.md`
- T-118 `render_task_instruction` (the precedent this generalizes)

## Safeguards

- **No execution change.** Only instruction strings change; `loop.run`,
  `run_task`, dispatch signatures, stamping, and gates are untouched.
- **Bounded prompts.** Every inlined block is capped; a pathological repo
  cannot blow a sub-run's first prompt past cap × block-count.
- **Graceful degradation.** Any absent/unresolvable context falls back to the
  exact current path-naming lines — never a crash, never a phantom path.
- **No tool-surface change.** New tools (batch read, patch) are explicitly out
  of scope until the post-T-120 bench re-measure (exploration challenge pass).

## Verification

- `python3 -m pytest scripts/tests/test_openup_agent_cycle.py scripts/tests/test_openup_agent_plan_iteration.py scripts/tests/test_openup_agent_assess.py -q` passes.
- Full suite green; fence `--base harness-optional` clean.
- Bench (`inception-taskdef` / `cycle-quick-doc`, owner endpoint): sub-runs no
  longer `read_file` the inlined paths.

## Success Measures

We expect the T-080 bench on the same scenario to show **median turns per
authoring/judgment sub-run ≤3, with zero `read_file` calls for files the
engine inlined** (was: ~4–10 turns with 2–4 briefing reads). Instrumentation:
`OPENUP_AGENT_DEBUG_LOG` tool-call trace + `OPENUP_AGENT_USAGE_LOG` per-call
tokens. Read-back: the next live batch on the owner's endpoint (same gate as
T-107).

## Rollout

n/a — internal driver briefing text on harness-optional; no flag, no
user-facing runtime.

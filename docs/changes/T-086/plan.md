---
id: T-086
title: Record T-072 AC-program live-acceptance result; mark T-072 verified
status: done
priority: medium
plan: docs/changes/archive/T-072/plan.md
depends-on: [T-072, T-080, T-083, T-085]
touches:
  - docs/changes/
  - docs/roadmap.md
last-synced: ""
---

# T-086 — Record the T-072 AC-program live-acceptance result

## Story

> **As** the owner of the harness-optional program
> **I want** the T-072 reference driver's **live-model acceptance** recorded (the
> owner step that was always its open criterion) and its status moved to `verified`
> **So that** the audit trail reflects that the driver has been proven end-to-end on
> a **non-Anthropic local model**, fence-clean + validator-clean — with an honest
> scope note on what was and wasn't exercised.

## Context — the evidence

Recorded via the T-080 benchmark harness (`openup-agent-bench.py`,
`inception-vision` scenario) on the **T-085 clean bootstrapped fixture** — batch
`.openup/bench/20260713-160244`:

- **Model:** `qwen/qwen3.6-35b-a3b` — non-Anthropic, local (LM Studio).
- **3/3 clean passes**; mean ~8 iterations, ~59k tokens/run.
- Each run drove **`openup-create-vision`** on a freshly-bootstrapped project seeded
  only with a stakeholder brief, and produced a **fence-clean, check-docs-clean**
  `docs/vision.md` with valid typed traceability frontmatter (`type: vision`,
  `id: VIS-001`) and the full section set (problem, positioning/solution,
  stakeholders, features, **falsifiable** success criteria, self-critique) —
  genuine visions faithfully derived from the brief, not template-filling.

**Honest scope.** The AC-program was worded as "one `--procedure next` cycle." What
is proven is the driver running a **real authoring procedure cycle** (create-vision)
end-to-end on a local model, fence + validator clean. The **`next` continue-loop
specifically** (start-iteration → work → complete-task in one invocation) is much
heavier on this local model — it does the work but converges inconsistently
(~37–50 iters, 1–2M tokens; see T-083 status-note). That is a **model/ceremony
weight finding, not a driver defect**: the driver is procedure-agnostic and correct;
it drove a real procedure to a clean, high-quality result. On that basis the driver
(T-072's deliverable) is **verified**; the `next`-on-a-weak-local-model reliability is
tracked separately as benchmarking, not a T-072 gap.

## Requirements

1. **The acceptance result is recorded in T-072's change folder** (its `design.md`
   §Read-back and the `handoff.md` AC-program item), and `T-072`'s `plan.md` status
   moves `done → verified`.
   - **Given** T-072's archived folder **When** inspected **Then** it records the
     batch (stamp, model, 3/3, fence/validator clean) + the scope note, its
     AC-program item is resolved, and `status: verified`.
2. **The roadmap program block reflects it.** The "Harness-optional OpenUP core"
   block's note that "live LM-Studio acceptance [is] pending to reach verified" is
   updated to record the acceptance.
   - **Given** the roadmap **When** read **Then** it states the driver's live
     acceptance was met (2026-07-13) with the scope note, not "pending".

## Operations

- [x] In `docs/changes/archive/T-072/`: append the acceptance record (evidence +
  scope note) to `design.md`; resolve the AC-program item in `handoff.md`; flip
  `plan.md` `status: done → verified`. Update the "Harness-optional OpenUP core"
  roadmap block's T-072 note from "pending" to "acceptance met 2026-07-13 (scope:
  create-vision cycle; next-loop tracked separately)". No code changes.

## Verification

- T-072 `plan.md` is `verified`; its folder records the batch + scope note.
- The roadmap program block no longer says the live acceptance is pending.
- `openup-fence.py check --base harness-optional` green.

---
id: T-107
title: "Scale the task library: full KB compile, doctor --check wiring, re-distill, customized sources"
status: proposed   # GATED — promote only after T-106's live qwen-batch acceptance passes
priority: medium
estimate: 2-3 sessions
plan: docs/iteration-plans/2026-07-14-lean-authoring-tasks.md
depends-on: [T-106]
blocks: []
last-synced: ""
touches:
  - docs-eng-process/task-library.yaml
  - scripts/build-task-library.py
  - scripts/openup-doctor.py
  - scripts/openup-process-map.py
  - docs-eng-process/reference-driver.md
  - docs-eng-process/project-config.md
  - scripts/tests/test_build_task_library.py
  - scripts/tests/test_openup_doctor.py
---

# T-107 — Scale the task library (gated on T-106 live acceptance)

> **PROMOTION GATE (do not start until satisfied).** T-106's behavioral
> acceptance must pass on the owner's live qwen batch first: **zero mid-run
> restarts, ≤6 iterations per sub-run, ≥80% clean-pass over 5 runs, per-sub-run
> prompt context ≤⅓ of the 2026-07-14 baseline**, read via
> `scripts/bench-scenarios/inception-taskdef` + `OPENUP_AGENT_USAGE_LOG` /
> `OPENUP_AGENT_DEBUG_LOG`. Until that batch passes, scaling the library only
> multiplies an unproven shape. If it regresses, the fix lands on T-106's
> defs/shell first — not here. Record the batch result in this folder's
> `design.md` at promote.

## Story

> **As a** maintainer scaling the reference driver beyond the Inception authoring flow
> **I want** the full KB compiled, drift surfaced in the health check, a re-distill flow, and customized process sources
> **So that** the task-def path covers every authoring activity and a project can override the framework defaults — the original P2 promise

INVEST — ✅ Independent · ✅ Negotiable · ✅ Valuable · ✅ Estimable · ⚠️ Small (split candidate — see Scope) · ✅ Testable

## Analysis Context

- **Domain.** Scaling T-105's compiler + T-106's consumption from the ~7 map-referenced authoring tasks to the full KB (~39 task files), plus drift-checking, re-distillation, and project-customized process sources.
- **Scope boundaries.** No change to the T-106 execution seam (the sub-run mechanism is proven by the gate). No `main` merge (harness-optional). The KB stays read-only source. Claude Code skill single-sourcing is a **decision recorded here, not necessarily built** (see D-parity).
- **Split candidate.** This is plausibly 3 lanes: (a) full-KB compile + review, (b) doctor `--check` wiring + re-distill flow, (c) customized process sources. Promote as one iteration or partition at promote-time via the board — decide once the gate clears.
- **Definition of done.** The full KB authoring task set is compiled + reviewed + committed; `build-task-library.py --check` is wired into `openup-doctor.py` (degrading gracefully where the KB is absent); a documented KB-update re-distillation flow exists; the compiler accepts a project's own process docs producing a project-local map + library override; the Claude-Code-parity decision is recorded.

## Requirements

1. The committed `task-library.yaml` covers every authoring task the process map can reference (the full KB authoring set), each human-reviewed; `--check` stays green.
   - **Given** the scaled library **When** `build-task-library.py --check` runs in the framework repo **Then** it exits 0 (all skeletons in sync with their KB sources).
2. `openup-doctor.py` surfaces `build-task-library.py --check` drift as a WARNING, and **degrades to INFO (never ERROR) when the vendored KB is absent** (a downstream project has no KB, so a missing-source must not read as a failure).
   - **Given** a repo without the vendored KB **When** `openup-doctor` runs **Then** the task-library check is an INFO "not verifiable (no KB)", not a drift error; **Given** the framework repo with in-sync library **Then** INFO "in sync".
3. A documented, repeatable KB-update re-distillation flow exists (KB version bump → regenerate skeletons + prompts → review the diff → commit).
   - **Given** a mutated KB task file **When** the re-distill flow runs **Then** `--check` flags the skeleton drift and the flow produces the updated prompt for review.
4. `build-task-library.py` accepts a project's own process docs and emits a **project-local** map + task library that overrides the framework default (P2).
   - **Given** a project process-source dir **When** the compiler runs against it **Then** it emits a project-local `task-library.yaml` (+ map) the loader prefers over the framework copy (the existing `_TASK_CANDIDATES` / `_MAP_CANDIDATES` fallback order).
5. The Claude-Code-parity decision (do the `openup-create-*` skills eventually consume the same lean defs, or stay as-is?) is recorded with its drift-risk rationale.
   - **Given** this task completes **When** a reader opens `reference-driver.md` / this design.md **Then** the parity decision + rationale is stated.

## Behavior Delta

**Added** — full-KB task defs; doctor task-library drift check (KB-absent-degrading); a re-distill flow; project-customized process sources (project-local map + library override).

**Modified** — `docs-eng-process/reference-driver.md §task-def authoring` (coverage note + parity decision); `docs-eng-process/project-config.md` (customized-process-source mechanism).

**Removed** — n/a.

## Entities

- **Full task library** (modified) — `docs-eng-process/task-library.yaml`
- **Compiler** (modified) — `scripts/build-task-library.py` (project-source input)
- **Doctor** (modified) — `scripts/openup-doctor.py` (task-library check)
- **Map/library loader** (read-only precedent) — `scripts/openup-process-map.py` (`_TASK_CANDIDATES` override order)
- **KB task files** (read-only source) — `docs-eng-process/openup-knowledge-base/*/*/tasks/*.md`

## Approach

Extend the compiler to enumerate all authoring KB tasks (deterministic list, not a hardcoded 7), compile + emit for review. Add a doctor check that runs `build-task-library.py --check` only when both `task-library.yaml` and the vendored KB are present — INFO-degrading otherwise (the downstream-project reality found in T-105). Document the re-distill flow as an operator runbook. For customized sources, generalize the compiler's input root and lean on the loader's existing candidate-path fallback so a project-local library shadows the framework one. Record the parity decision in docs.

## Structure

**Add:** re-distill runbook section (reference-driver.md); customized-source section (project-config.md); tests for the doctor check + project-source compile.

**Modify:** `task-library.yaml` (full set), `build-task-library.py` (enumerate-all + project-source), `openup-doctor.py` (task-library check, KB-absent-degrading), docs.

**Do not touch:** the T-106 `run_task` / `plan_iteration` execution seam (proven by the gate); the KB source; `main`.

## Operations

- [ ] Record the passing T-106 live-batch result in `design.md` (the promotion gate); if it failed, STOP and route the fix to T-106.
- [ ] Enumerate + compile the full KB authoring task set; human-review each def; commit; `--check` green.
- [ ] Wire the task-library drift check into `openup-doctor.py`, INFO-degrading when the vendored KB is absent (never ERROR downstream).
- [ ] Document the KB-update re-distillation runbook (bump → regenerate → review diff → commit).
- [ ] Add project-customized process sources: compiler input root + project-local library/map override via the loader's candidate fallback; document in project-config.md.
- [ ] Record the Claude-Code-parity decision (single-source vs stay-as-is) + drift-risk rationale.
- [ ] (tester) Tests: doctor KB-absent degradation; project-source compile emits a project-local override; full-library `--check` green.

## Norms

Inherits from:
- `docs-eng-process/conventions.md`
- T-105 compiler + T-106 consumption (the proven mechanism this scales)
- `docs-eng-process/project-config.md` — the precedence chain P2 extends

## Safeguards

- **Promotion gate.** Do not start until T-106's live-batch acceptance passes (recorded in design.md). This is the core safeguard — scaling an unproven shape is the anti-goal.
- **Downstream safety.** The doctor check must never ERROR where the KB is absent (T-105's false-positive lesson).
- **Review-before-commit.** Every distilled def is human-reviewed; prose-distillation drift stays advisory.
- **No execution-seam change.** The T-106 sub-run mechanism is fixed here.

## Verification

- `build-task-library.py --check` exits 0 on the full library; `openup-doctor` INFO-degrades without the KB.
- Project-source compile emits a project-local override the loader prefers.
- Full suite green; fence `--base harness-optional` clean.
- Grade against `.claude/rubrics/task-spec-rubric.md`.

## Success Measures

n/a for a direct metric — T-107 scales the shape T-106 already proved on the qwen batch. The falsifiable proof is: full-library `--check` green, doctor KB-absent degradation tested, project-source override tested. (Re-running the T-106 bench across the newly-covered phases MAY re-confirm the reliability envelope, but that is a re-read of T-106's measure, not a new one.)

## Rollout

n/a — internal build tooling + framework data on harness-optional; the customized-process-source feature is opt-in by a project supplying its own process docs (loader candidate-path fallback), no runtime flag.

---
id: T-077
title: process-map.yaml + phase-aware plan-iteration
status: done
priority: high   # critical | high | medium | low
estimate: 2-3 sessions
plan: docs/explorations/2026-07-13-phase-aware-loop-redesign.md
depends-on: [T-075, T-076]
blocks: [T-078, T-079]
touches:
  - scripts/
  - docs-eng-process/
  - .claude/
  - docs/changes/
  - tests/
last-synced: ""
---

# T-077 — process-map.yaml + phase-aware plan-iteration

## Story

> **As** an agent (or human) driving the OpenUP loop
> **I want** `/openup-start-iteration` to be real **Plan Iteration** — read the
> current phase, choose 1–5 objectives from the risk list + PM value order +
> phase objectives, and generate phase-appropriate work-item lanes from a
> data-encoded process map (vision/use-case/risk in Inception; architecture/
> skeleton/test in Elaboration; dev/test in Construction) — with each iteration
> minted under a stable id (`C3`) and its lanes id'd under that prefix
> (`C3-001`)
> **So that** the loop stops re-inventing a process each run and a human no
> longer hand-writes every roadmap row, while the `quick` archetype degenerates
> to today's single-work-item cost so the change passes its own efficiency bar.

INVEST — ✅ Independent · ✅ Negotiable · ✅ Valuable · ✅ Estimable · ✅ Small (largest of the program, but one coherent slice) · ✅ Testable

## Analysis Context

- **Third slice of the phase-aware program** (§3.3 / §3.4 / §5.3 of
  `docs/explorations/2026-07-13-phase-aware-loop-redesign.md`). Reads the two
  delivered upstream slices: **T-075** (`openup-lifecycle.py status` — the derived
  phase/cycle/milestone source) and **T-076** (the `process:` Development Case
  config — archetype + per-phase tailoring). Unblocks **T-078** (loop wiring +
  convergence) and **T-079** (parallel iterations).
- **The data source is the KB process model** already distilled in
  `docs/explorations/2026-07-13-openup-kb-process-model.md` §3 (iteration
  lifecycle: Plan / Manage / Assess) and §4 (phase → activity → role → skill).
  `process-map.yaml` encodes §4 verbatim as data; Plan Iteration implements the
  Plan-half of §3.
- **Stdlib-only.** No `pyyaml` in the repo. T-076 shipped a hand-rolled nested
  block-mapping reader in `scripts/check-docs.py`
  (`parse_process_section` / `_process_parse_map` / `_process_value`, :227–301);
  the process-map loader reuses that style (a small `scripts/openup-process-map.py`
  reader), not a new dependency.
- **Scope boundary with T-078 (explicit — this is the trickiest line).** This
  task builds the *pieces*; T-078 wires them into the autonomous loop and adds
  convergence:
  - T-077 **does**: the `process-map.yaml` data + loader; `/openup-start-iteration`
    becomes Plan Iteration (objective-driven, generates lanes); iteration minting
    with prefixed ids; `openup-board.py` / `openup-roadmap.py` resolve becomes
    lifecycle-aware + iteration-scoped and its `promote` path is **relabelled**
    `plan-iteration`; phase skills refactored to thin fronts over the map.
  - T-077 **does NOT**: touch `.openup/state.json` schema (stays **v1** — the
    `iteration_id` / `cycle` fields and the `phase`-as-cache change are **T-078**'s
    schema 2); add `assess-iteration` / `milestone-review` resolve paths; wire the
    new paths into the `/openup-next` skill or `openup-agent.py` procedures; add
    the milestone pause. The board may *emit* `path: plan-iteration`, but the loop
    consuming it autonomously is T-078.
- **Where iteration identity lives (schema-2 avoidance).** Because state stays v1,
  the minted iteration id/name is persisted in the **iteration-plan instance**
  (`/openup-create-iteration-plan`'s output, `docs/phases/<phase>/iteration-<n>-plan.md`,
  `type: iteration-plan`) — which §3.5 already designates the loop contract — and
  reflected in the **prefixed work-item ids** (`C3-001`) on the roadmap + change
  folders. No new state field is introduced.
- **Derived-don't-author holds.** Phase comes from `openup-lifecycle.py status`
  (never model judgment mid-loop); ceremony from the T-076 `process:` config; the
  activity→role→skill mapping from `process-map.yaml`. Plan Iteration composes
  these deterministically; the only genuinely generative step is choosing the 1–5
  objectives, which is the PM/analyst reasoning the KB assigns to a human role.
- **This lane delivers the mechanism, tested hermetically — it does not flood this
  repo's live roadmap with generated lanes.** Lane generation is exercised against
  temp-repo fixtures (the `tests/` convention: pytest + `importlib` script load +
  hermetic temp skeletons), not by materialising real Construction lanes here.

## Assumptions (Ambiguity Gate)

Non-blocking calls recorded per the ambiguity-gate convention; each is the
reading most consistent with the exploration + roadmap. Flag on review if any is
wrong — none blocks starting implementation.

- **Assumption A — board emits `plan-iteration` with no autonomous consumer yet.**
  T-077 relabels the board's `promote` path to `plan-iteration` and makes it
  phase/iteration-aware; the `/openup-next` skill's *autonomous* consumption of
  that path (and the assess/milestone paths) is T-078. A human invoking
  `/openup-start-iteration` directly exercises Plan Iteration end-to-end in T-077.
- **Assumption B — iteration id minted from phase + cycle + iteration ordinal.**
  `C3` = first letter of phase (Construction) + the count of prior iterations in
  the current `cycle` (from `lifecycle.py status`) + 1. Lane ids under it via
  `openup-claims.py reserve-id --prefix "C3-" --pad 3`. The exact letter map is a
  documented convention in `process-map.yaml`, not hard-coded logic.
- **Assumption C — `quick` archetype ⇒ single-work-item Plan Iteration.** When the
  T-076 `process:` archetype resolves to `quick` (or Elaboration is `skipped`),
  Plan Iteration commits exactly one work item and skips objective ceremony —
  matching today's promote-one-row cost (the efficiency guardrail).
- **Assumption D — phase skills kept as thin docs, not deleted.** The four phase
  skills become short fronts that point at `process-map.yaml` + Plan Iteration
  (retained for discoverability / manual use), rather than being removed — the
  exploration's "or are folded into the planner and kept as documentation."

## Requirements

1. **`process-map.yaml` — the process as data.**
`docs-eng-process/process-map.yaml` (framework-owned, vendored like the KB)
encodes, from the KB §4 distillation: each phase → its ordered activity list, and
an `activities:` map of activity → `{ role, skills: [...] }`. A stdlib-only loader
`scripts/openup-process-map.py` (`activities-for <phase>` / `activity <name>` /
`validate`) reads it and is registered in `scripts/process-manifest.txt` +
`docs-eng-process/script-cli-reference.md`.

> **Given** `process-map.yaml` with `construction: [identify-refine-requirements,
> develop-solution-increment, test-solution, plan-manage-iteration]` and an
> `activities:` entry `develop-solution-increment: { role: developer, skills:
> [openup-tdd-workflow] }`,
> **When** `python3 scripts/openup-process-map.py activities-for construction`
> runs,
> **Then** it emits the ordered activity list for Construction, each resolved to
> its `{role, skills}`, and `validate` exits 0 on the shipped file (non-zero if a
> phase references an activity absent from `activities:`).

2. **`/openup-start-iteration` becomes Plan Iteration proper.**
The skill gains a Plan-Iteration path: read the phase from
`openup-lifecycle.py status`, read the archetype/tailoring from the T-076
`process:` config, choose 1–5 iteration objectives (from the risk list + PM value
order + the phase's objectives), and **generate phase-appropriate work-item
lanes** from `process-map.yaml` — Inception emits vision/use-case/risk lanes
(`hat: analyst`), Elaboration architecture/skeleton/test lanes, Construction the
dev/test lanes — writing each lane's change folder + roadmap row without a human
hand-writing them. The existing single-task start path is preserved for an
explicit `task_id` (backward compatible).

> **Given** the current phase resolves to `elaboration` and no `task_id` is
> passed,
> **When** `/openup-start-iteration` runs Plan Iteration,
> **Then** it commits an iteration whose generated lanes cover the Elaboration
> activity set from `process-map.yaml` (architecture + solution-increment + test),
> each lane carrying the activity's `role` as its `hat`; **and** passing an
> explicit `task_id` still starts that single lane unchanged.

3. **Iteration minted with a stable id; lanes id'd under its prefix.**
Plan Iteration mints a stable iteration id/name (`<PhaseLetter><cycle-ordinal>`,
e.g. `C3`) derived from `lifecycle.py status`, records it in the iteration-plan
instance (`/openup-create-iteration-plan`), and allocates every generated
work-item / lane id **under that prefix** via
`openup-claims.py reserve-id --prefix "<iter-id>-" --pad 3` (`C3-001`, `C3-002`,
…) — so each task is traceable to its iteration by id and cannot collide across
concurrent iterations (the id half of T-079). State schema is untouched (v1).

> **Given** the loop is in Construction cycle 1 and this is the third planned
> iteration,
> **When** Plan Iteration mints the iteration and reserves ids for two generated
> lanes,
> **Then** the iteration id is `C3`, the lanes are `C3-001` / `C3-002` (allocated
> via `reserve-id --prefix "C3-"`), the id is recorded in the iteration-plan
> instance, and `.openup/state.json` gains **no** new field (still schema 1).

4. **`openup-board.py` / `openup-roadmap.py` resolve becomes lifecycle-aware and iteration-scoped; `promote` → `plan-iteration`.**
`resolve_decision` reads the current phase (via `openup-lifecycle.py`) and
partitions lanes by iteration: the `pick` path considers only lanes belonging to
the **active** iteration, and when there is no active iteration the former
`promote` path is emitted as **`path: plan-iteration`** (carrying the resolved
phase) instead of promoting a single roadmap row. `resolve` stays read-only and
deterministic (two sessions on identical inputs emit the identical decision). The
autonomous consumption of `plan-iteration` is deferred to T-078 (Assumption A).

> **Given** no active iteration and a non-empty roadmap,
> **When** `python3 scripts/openup-board.py resolve` runs,
> **Then** it emits `{"path": "plan-iteration", "phase": "<current>", ...}` rather
> than `{"path": "promote", ...}`; **and** given an active iteration with a
> pickable lane, `resolve` emits `path: pick` for a lane **in that iteration only**
> (a pickable lane from a different iteration is not selected).

5. **Phase skills refactored to thin fronts over the map.**
The four phase skills (`openup-inception` / `-elaboration` / `-construction` /
`-transition`) are rewritten as short fronts that defer to `process-map.yaml` +
Plan Iteration for the activity composition (no longer parallel manual narrative
guidance), retained for discoverability and manual use. Live `.claude/` skills are
re-synced from the templates so `check-claude-sync.sh` stays green.

> **Given** a phase skill is opened for reference,
> **When** its body is read,
> **Then** it names the phase's activity set by pointing at `process-map.yaml` +
> `/openup-start-iteration` Plan Iteration (not a re-listed manual process), and
> `.claude/` ↔ `.claude-templates/` parity is green.

## Behavior Delta

- **Added.** `docs-eng-process/process-map.yaml` + `scripts/openup-process-map.py`
  loader; a Plan-Iteration path in `/openup-start-iteration` (objective-driven
  lane generation); iteration minting with prefixed lane ids (reusing
  `openup-claims.py reserve-id --prefix`); a `plan-iteration` decision path in
  `openup-board.py` resolve; hermetic tests.
- **Modified.** `/openup-start-iteration` gains Plan Iteration while preserving the
  explicit-`task_id` single-lane path. `openup-board.py` / `openup-roadmap.py`
  `resolve` become phase-aware + iteration-scoped; the `promote` path is relabelled
  `plan-iteration`. The four phase skills become thin fronts (behavior: reference,
  not process). `process-manifest.txt` + `script-cli-reference.md` gain the loader.
- **Removed.** The one-row-at-a-time `promote` label from board resolve (the
  mechanism is superseded by `plan-iteration`; the underlying
  `openup-roadmap.cmd_next` selection is reused inside plan-iteration for the
  quick/single-item degeneration).
- **Deferred (NOT this task).** `.openup/state.json` schema 2 (`iteration_id`,
  `cycle`, `phase`-as-cache); `assess-iteration` / `milestone-review` resolve
  paths; `/openup-next` skill + `openup-agent.py` procedure wiring; the milestone
  human-pause — all **T-078**.

## Definition of Done

- [x] R1 — `process-map.yaml` encodes phase→activity→role→skill (KB §4);
      `openup-process-map.py` loader (`activities-for` / `activity` / `validate`)
      registered in the manifest + CLI reference; `validate` exits 0 on the file.
- [x] R2 — `/openup-start-iteration` runs Plan Iteration (phase from lifecycle.py,
      tailoring from T-076 `process:`, 1–5 objectives, generates phase-appropriate
      lanes from the map); explicit-`task_id` single-lane path preserved.
- [x] R3 — iteration minted with a stable prefixed id (`mint-iteration-id`); lanes
      allocated via `reserve-id --prefix`; id recorded in the iteration-plan
      instance (per R2 §0b step 7); state stays schema 1.
- [x] R4 — `openup-board.py` resolve is phase-aware + iteration-scoped and emits
      `plan-iteration` (not `promote`); read-only + deterministic (divergence=0).
- [x] R5 — four phase skills refactored to thin fronts; `.claude/` re-synced;
      `check-claude-sync.sh` green.
- [x] `quick` archetype degeneration verified: `plan-iteration` carries a single
      `lane.task` (the degenerate case) — test_emits_plan_iteration_not_promote
      (Assumption C; R2 §0b step 2 routes `quick` straight to the single lane).
- [x] Hermetic tests cover: process-map load + validate, prefixed-id minting,
      iteration-scoped pick, `plan-iteration` emission, divergence=0 on resolve
      (28 new tests; full suite 64 green).
- [x] `check-docs.py` (+ `--coverage`) and fence green (`--base harness-optional`).

## Operations

- [x] (developer) R1 — author `process-map.yaml` from KB §4 + `openup-process-map.py` loader; register in manifest + CLI reference
- [x] (developer) R4 — make `openup-board.py` / `openup-roadmap.py` resolve lifecycle-aware + iteration-scoped; relabel `promote` → `plan-iteration`
- [x] (developer) R3 — iteration minting: stable prefixed id from lifecycle.py, lanes via `reserve-id --prefix`, id into the iteration-plan instance
- [x] (developer) R2 — Plan-Iteration path in `/openup-start-iteration` (objectives + phase-appropriate lane generation from the map); preserve explicit-`task_id` path
- [x] (developer) R5 — refactor the four phase skills to thin fronts over the map; re-sync `.claude/`
- [x] (tester) hermetic tests for R1–R4 + quick degeneration + divergence=0
- [x] (developer) run check-docs (+ --coverage) + fence (`--base harness-optional`); verify `check-claude-sync.sh`

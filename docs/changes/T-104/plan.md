---
id: T-104
title: Engine-owned authoring ceremony + restore the pinned roadmap contract
status: ready
priority: high   # critical | high | medium | low
estimate: 1 session
plan: docs/iteration-plans/2026-07-14-lean-authoring-tasks.md
depends-on: []
blocks: [T-105, T-106]
touches:
  - scripts/openup_agent/stamping.py
  - scripts/openup_agent/plan_iteration.py
  - scripts/openup_agent/cycle.py
  - scripts/process-manifest.txt
  - scripts/tests/test_openup_agent_stamping.py
  - scripts/tests/test_openup_agent_plan_iteration.py
  - scripts/tests/test_openup_agent_cycle.py
  - docs-eng-process/reference-driver.md
last-synced: ""
---

# T-104 — Engine-owned authoring ceremony + restore the pinned roadmap contract

## Story

> **As** the maintainer of the reference driver,
> **I want** the driver's direct authoring sub-runs to hand ceremony (typed
>   frontmatter, config lookup, self-critique) to the **engine** — the model
>   authors the document body only — and the fresh-Inception roadmap to again
>   carry the T-099 parser-pinned format,
> **So that** a weak local model's authoring call shrinks toward the shape that
>   measured 3/3-reliable (T-080), the live restart-mid-run failure mode
>   (debug log, 2026-07-14) loses its trigger, and `openup-roadmap.py` can
>   promote from a fresh roadmap again (T-103 regression).

INVEST — ✅ Independent (no schema/compiler; S1 of the program) · ✅ Negotiable
(stamping module shape) · ✅ Valuable (reliability bottleneck + live regression) ·
✅ Estimable · ✅ Small (engine-side only) · ✅ Testable (hermetic stamping +
promotable-roadmap tests)

## Analysis Context

- **Domain.** The driver's direct-execution authoring path:
  `plan_iteration.py` builds the `execution: direct` instruction and
  `cycle.py`'s `run_procedure` runs the sub-run. Today the sub-run reads the
  full procedure file (~650+ lines of ceremony: frontmatter contract, rubric
  self-critique, config probing) — observed live to make a weak model restart
  mid-run and probe `project-config.yaml` 5×.
- **Scope boundaries.** No task-def schema, no compiler, no pack-procedure
  surgery (T-105/T-106); the Claude Code skill path is untouched. The sub-run
  still reads the procedure file in S1 — the instruction *counteracts* its
  ceremony fan-out; the file read itself disappears in T-106.
- **Regression being fixed.** T-103 deleted the navigator whose
  `VISION_INSTRUCTION` carried the T-099 pinned roadmap format; the
  fresh-Inception `execution: direct` path lost it, so a fresh run can again
  produce a roadmap `openup-roadmap.py` (ID_RE `T-\d+`) finds empty.
- **Definition of done.** A scripted direct authoring run produces a body-only
  artifact that the engine stamps with valid typed frontmatter (`check-docs`
  green); the instruction carries ceremony-exclusion + injected project
  config + (for `initiate-project`) the pinned roadmap format; full suite and
  fence green.

> **Assumption:** the artifact-type → id-prefix map is a small fixed table in
> the stamping module (vision → `VIS-`, use-case → `UC-`, …, consistent with
> `doc-frontmatter.md`'s examples), scanned next-free the way `reserve-id`
> scans task ids. *(Vetoable at review.)*

> **Assumption:** stamped `status` is `draft` (the maturity enum's entry
> state); promotion is a later human/gate act. *(Vetoable at review.)*

## Requirements

1. **The engine stamps typed instance frontmatter deterministically.**
   - **Given** a direct authoring sub-run has written an artifact body (no
     frontmatter) **When** the engine post-processes it **Then** the file
     carries `type`, `id` (next-free for that type's prefix), `title`, and
     `status: draft`, and `check-docs` accepts it.
   - **Given** the model wrote its own frontmatter block **When** the engine
     post-processes **Then** the block is replaced/normalized to the stamped
     one (no duplicate frontmatter).
   - **Given** a `VIS-001` instance already exists **When** a second vision
     artifact is stamped **Then** it allocates `VIS-002`.

2. **The direct-run instruction excludes ceremony.**
   - **Given** the assembled `execution: direct` instruction **When** read
     **Then** it tells the model to author the document body only and NOT to
     read/write frontmatter, rubrics, trace models, or schemas, and not to
     self-critique.
   - **Given** a sub-run transcript (`OPENUP_AGENT_DEBUG_LOG`) of a hermetic
     direct run **When** inspected **Then** it shows zero reads of
     `doc-frontmatter.md`, `docs-meta.schema.json`, `trace-model.json`, rubric
     files, or `project-config.yaml`.

3. **Project config is injected, never probed.**
   - **Given** a `docs/project-config.yaml` with `context:`/relevant `rules.*`
     **When** the engine assembles the instruction **Then** those values are
     embedded in the instruction text (one deterministic read by the engine).
   - **Given** no `docs/project-config.yaml` **When** the instruction is
     assembled **Then** no config section is injected and the run proceeds.

4. **The fresh-Inception roadmap contract is pinned again (regression fix).**
   - **Given** a fresh-Inception scripted flow through the `initiate-project`
     direct path **When** the roadmap is authored **Then** the instruction
     carried the T-099 format constant (strict header row; `T-001, T-002, …`
     ids; `pending`; `high|medium|low`; comma-separated `T-NNN` deps; ordered
     by priority; no YAML frontmatter) and the produced `docs/roadmap.md` is
     promotable: `openup-roadmap.py next` finds an entry.

5. **Self-critique is dropped from the weak-model authoring path.**
   - **Given** the direct-run instruction **When** read **Then** it contains no
     self-critique step (the deterministic gate is the critic); a note in
     `reference-driver.md` records that a strong-model tier MAY later run
     critique as a separate tiny sub-run (not built now).

## Behavior Delta

Ring-1 truth for the driver lives in `docs-eng-process/`.

**Added:**
- Engine-side frontmatter stamping for direct authoring artifacts (new
  `stamping.py`; documented in `reference-driver.md`).
- Project-config injection into direct-run instructions.

**Modified:**
- The `execution: direct` instruction contract — body-only + ceremony-exclusion
  + injected config — `docs-eng-process/reference-driver.md` §direct execution.
- The `initiate-project` direct instruction re-carries the pinned roadmap
  format — `docs-eng-process/reference-driver.md` (T-099 contract, interim
  constant in `plan_iteration.py` until T-106 moves it to the task library).

**Removed:**
- Model-side ceremony (frontmatter authoring, self-critique) from the driver's
  direct authoring sub-runs — `docs-eng-process/reference-driver.md` §authoring
  sub-runs (the procedure files themselves are untouched).

## Entities

- **stamping** (new) — `scripts/openup_agent/stamping.py`: prefix table,
  next-free id scan, frontmatter normalize/replace.
- **plan_iteration** (modified) — instruction assembly (ceremony-exclusion,
  config injection, `ROADMAP_FORMAT` constant on `initiate-project`).
- **cycle** (modified) — `run_procedure` seam invokes stamping after a
  successful direct authoring run.
- **check-docs** (read-only) — remains the validator; the gate is the critic.

## Approach

Ceremony moves from prompt to engine. A new stdlib `stamping.py` owns the
typed-frontmatter contract: a fixed type→prefix table, a next-free scan over
existing instances, and normalize-or-stamp on the artifact file. Instruction
assembly in `plan_iteration.py` gains three deterministic ingredients: the
ceremony-exclusion paragraph, an injected `<project-context>/<project-rules>`
block read once from `docs/project-config.yaml`, and — for `initiate-project`
only — the reintroduced T-099 roadmap-format constant (interim until T-106).
`cycle.py` calls the stamper after the sub-run succeeds, before gates run, so
`check-docs` (already in `run_gates`) validates the stamped result.

## Structure

**Add:**
- `scripts/openup_agent/stamping.py`
- `scripts/tests/test_openup_agent_stamping.py`

**Modify:**
- `scripts/openup_agent/plan_iteration.py` — instruction assembly: ceremony
  exclusion + config injection + `ROADMAP_FORMAT` constant (initiate-project).
- `scripts/openup_agent/cycle.py` — invoke stamping after a successful direct
  authoring run.
- `scripts/process-manifest.txt` — ship `openup_agent/stamping.py`.
- `scripts/tests/test_openup_agent_plan_iteration.py`,
  `scripts/tests/test_openup_agent_cycle.py` — instruction + wiring tests.
- `docs-eng-process/reference-driver.md` — direct-execution contract; the
  self-critique-by-tier note.

**Do not touch:**
- `docs-eng-process/procedures/openup-create-*.md` — the Claude Code path;
  pack surgery is explicitly out of scope (parity is at the artifact level).
- `docs-eng-process/process-map.yaml` / task-library — schema work is T-105.
- `scripts/check-docs.py` — it already validates; the gate is the critic.

## Operations

- [ ] Add `scripts/openup_agent/stamping.py` (type→prefix table, next-free id
  scan, stamp/normalize frontmatter) + ship it in `process-manifest.txt`.
- [ ] (tester) Add `test_openup_agent_stamping.py`: stamp body-only file,
  replace model-written frontmatter, `VIS-001`→`VIS-002` allocation,
  `check-docs` accepts the stamped artifact.
- [ ] `plan_iteration.py`: assemble ceremony-exclusion + project-config
  injection into the direct-run instruction; reintroduce the T-099
  `ROADMAP_FORMAT` constant appended to the `initiate-project` instruction.
- [ ] `cycle.py`: wire stamping after a successful direct authoring sub-run,
  before gates.
- [ ] (tester) Instruction tests (exclusion text present; config injected when
  present, absent otherwise; roadmap format pinned) + the fresh-Inception
  regression test: scripted flow → `openup-roadmap.py next` finds a promotable
  entry; hermetic transcript shows zero ceremony-file reads.
- [ ] Update `docs-eng-process/reference-driver.md` (direct-execution contract;
  self-critique-by-tier note).
- [ ] (tester) Full driver suite green; `spec-scenarios`, `check-docs`,
  `process-map validate`, fence (`--base harness-optional`) green.

## Norms

Inherits from:
- `docs-eng-process/conventions.md`
- `docs-eng-process/reference-driver.md` — the driver contract
- `docs-eng-process/doc-frontmatter.md` — the typed-frontmatter contract the
  stamper implements
- `docs/iteration-plans/2026-07-14-lean-authoring-tasks.md` — the program plan

## Safeguards

- **Stdlib-only** (driver invariant; no pyyaml).
- **No pack surgery.** `docs-eng-process/procedures/` and the skills mirror are
  out of this lane's diff; the Claude Code path must behave byte-identically.
- **The gate is the critic.** Do not add model-side validation loops; only
  `check-docs` (already in `run_gates`) judges the stamped artifact.
- **Interim constant is marked.** The `ROADMAP_FORMAT` constant carries a
  comment naming T-106 as its retirement (task-library def takes over).
- **Reversibility.** Additive engine module + instruction text; git-revertible.

## Success Measures

We expect **direct authoring sub-run context** to drop toward the lean shape
(the ~10× cut lands fully in T-106; this task removes the ceremony *behavior*)
and **fresh-Inception convergence** to be restored — measured by the T-106
behavioral acceptance run on the qwen fixture (zero restarts, ≤6 iters/sub-run,
≥80%/5 runs, ≤⅓ context) and, for this task, the hermetic regression test that
`openup-roadmap.py next` promotes from a freshly-authored roadmap.
Instrumentation: `OPENUP_AGENT_DEBUG_LOG` transcripts + the T-080 usage log.
Read-back: at the T-106 gate (live acceptance is the owner's batch — this
sandbox reaches no endpoint).

## Rollout

`n/a — not user-facing`: reference-driver internals, no flag; backout is a
version pin. The pinned-roadmap fix restores prior (T-099) behavior.

## Verification

- `python3 -m pytest scripts/tests/test_openup_agent_stamping.py scripts/tests/test_openup_agent_plan_iteration.py scripts/tests/test_openup_agent_cycle.py -q` green; full driver suite green.
- Hermetic: stamped artifact passes `python3 scripts/check-docs.py`; second
  instance allocates the next id.
- Hermetic: fresh-Inception scripted flow → `openup-roadmap.py next` finds a
  promotable entry.
- Debug-log transcript of a hermetic direct run shows zero reads of
  `doc-frontmatter.md`, `docs-meta.schema.json`, `trace-model.json`, rubrics,
  `project-config.yaml`.
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-104/plan.md` → 0;
  `python3 scripts/openup-fence.py check --base harness-optional` → clean.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

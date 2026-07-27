---
id: T-145
title: "sync-status.py must derive `completed` from delivery evidence, not bookkeeping gates alone"
status: ready
priority: high
estimate: 1 session
plan: ""
depends-on: []
blocks: []
last-synced: ""
touches:
  - scripts/sync-status.py
  - scripts/openup-state.py
  - scripts/openup-state.schema.json
  - scripts/tests/test_sync_status_notes.py
  - scripts/tests/test_openup_state.py
  - scripts/tests/test_t006_hooks.py
  - docs-eng-process/procedures/openup-complete-task.md
  - docs-eng-process/procedures/openup-quick-task.md
  - docs-eng-process/state-file.md
  - docs-eng-process/tracks.md
  - docs-eng-process/skills-guide.md
  - docs-eng-process/.claude-templates/skills/openup-complete-task/SKILL.md
  - docs-eng-process/.claude-templates/skills/openup-quick-task/SKILL.md
---

# T-145 — `sync-status.py` derives `completed` from bookkeeping gates alone, no delivery evidence

## Story

> **As a** human or agent reading `docs/roadmap.md` to decide what work is left
> **I want** a `completed` Status cell to be backed by evidence that the task's
>   implementation was actually verified against its spec
> **So that** a lane that produced only a spec and a run log can never be
>   reported as delivered

INVEST check:
✅ Independent — one new gate key threaded through the derivation and the two
completion skills; no dependency on T-146 (which fixes a different field of the
same script) or T-141.
✅ Negotiable — *which* evidence the gate records is a design choice; the spec
fixes only that the derivation must consume one.
✅ Valuable — closes an observed downstream incident where a lane with zero
implementation was stamped `completed` in the roadmap and had to be corrected by
hand.
✅ Estimable — `sync-status.py`'s `derive_status`/`TRACK_REQUIRED`,
`openup-state.py`'s gate CLI, and the schema's `gates` object were all read in
full this session.
✅ Small — one gate key, one required-set change, two skill steps, docs.
✅ Testable — gate-absent and gate-present states are independently constructible
fixtures against the existing hermetic `sync-status.py` harness.

## Analysis Context

- **Domain.** The derived-view pipeline: `.openup/state.json` `gates` →
  `sync-status.py derive_status()` → the roadmap Status cell and the
  `project-status.md` header.
- **Scope boundaries.** Does not change *how* `/openup-complete-task` step 1a
  verifies (that per-requirement grading already exists and is already BLOCKING);
  it only makes the result **recorded** and **consumed**. Does not touch the
  `Iteration`-header clobber (T-146) or the roadmap-reconcile path
  (`--reconcile`, which derives from archived change folders and never reads
  gates).
- **Definition of done.** A `quick`/`standard`/`full` state whose only truthy
  gates are bookkeeping (`log_written`, `roadmap_synced`, `team_deployed`)
  derives `in-progress`; it derives `completed` only once
  `implementation_verified` is also truthy, and both completion skills set that
  gate at the point where they already confirm the work.

**Confirmed this session, before writing code**: every gate currently in
`TRACK_REQUIRED` is bookkeeping. `roadmap_synced` is set by `sync-status.py`
*itself* (`set_gate_roadmap_synced`, `scripts/sync-status.py:359-363`) and is
pre-applied to the in-memory state before deriving (`scripts/sync-status.py:443`)
— so it is true by construction on every run. `log_written` is set once a log
line is appended. `team_deployed` records that a team was spawned. None of the
three observes the diff. `/openup-complete-task` step 1a already performs a
per-requirement ✅/❌ grade against `git diff` and already blocks on any ❌, but
records the verdict only in `design.md` prose — nothing machine-readable, so
nothing downstream can consume it.

> **Assumption:** the gate is set from inside the two completion skills at the
> point they already verify, rather than by a new standalone verifier script.
> The verification itself is a judgment step (grading requirements against a
> diff); only its *result* is mechanical. A script that tried to re-derive the
> verdict would either duplicate the judgment badly or degrade to a checksum of
> "the diff is non-empty," which is exactly the weak evidence this task rejects.
> *(Vetoable at review.)*

> **Assumption:** `implementation_verified` is added to
> `openup-state.py`'s `DEFAULT_REQUIRED_GATES` too, so `check-gates` with no
> `--require` agrees with `sync-status.py`'s derivation. A default that
> disagreed with the derived view would let a lane pass `check-gates` and still
> read `in-progress` on the roadmap — a confusing split-brain.
> *(Vetoable at review.)*

## Requirements

1. `scripts/openup-state.schema.json` declares an `implementation_verified`
   property under `gates`, **not** in `gates.required`.
   - **Given** a `.openup/state.json` written before this gate existed (its
     `gates` object has no `implementation_verified` key), **When** it is
     validated (`openup-session.py end`, which validates before archiving),
     **Then** validation succeeds — the key's absence is not a schema error.
   - **Given** the same file, **When** `openup-state.py get
     gates.implementation_verified` runs, **Then** it reports the key as unset
     (a falsy read, not a crash).

2. `sync-status.py`'s `TRACK_REQUIRED` requires `implementation_verified` on
   **every** track (`quick`, `standard`, `full`).
   - **Given** a `standard`-track state whose `log_written` and `roadmap_synced`
     gates are true and whose `implementation_verified` gate is absent, **When**
     `sync-status.py` runs, **Then** the task's roadmap Status cell reads
     `in-progress` and the run prints `status=in-progress`.
   - **Given** a `quick`-track state in the same shape, **When**
     `sync-status.py` runs, **Then** the cell reads `in-progress` — the quick
     track is relaxed on *ceremony*, never on delivery evidence.
   - **Given** the same `standard` state with `implementation_verified` also
     true, **When** `sync-status.py` runs, **Then** the cell is stamped
     `completed (YYYY-MM-DD)`.

3. `openup-state.py`'s `DEFAULT_REQUIRED_GATES` includes
   `implementation_verified`, so an un-flagged `check-gates` agrees with the
   derivation.
   - **Given** a state with `team_deployed`, `log_written` and `roadmap_synced`
     all true and `implementation_verified` unset, **When**
     `openup-state.py check-gates` runs with no `--require`, **Then** it exits 6
     and names `implementation_verified` on stderr.

4. `/openup-complete-task` step 1a sets the gate — and only after every
   requirement graded ✅.
   - **Given** a reader following `openup-complete-task.md` step 1a, **When**
     they reach the end of the step with all requirements ✅, **Then** the step
     instructs them to run
     `openup-state.py set-gate implementation_verified true`, and states
     explicitly that any ❌ means the gate stays unset.
   - **Given** the same skill's step 7 gate check, **When** the reader runs the
     printed `check-gates --require …` invocation for their track, **Then**
     `implementation_verified` is in that required list for both the
     `quick`/`standard` and the `full` invocation.

5. `/openup-quick-task` sets the gate at its own verification step.
   - **Given** a reader following `openup-quick-task.md`, **When** they finish
     step 3 ("Execute Task") having confirmed the change works, **Then** the
     skill instructs them to set `implementation_verified`, and its step-6
     `check-gates --require` line includes it.

6. The gate is documented where the gate set is documented —
   `docs-eng-process/state-file.md` (gate table + who-sets-it table + the
   track-required paragraph) and `docs-eng-process/tracks.md`'s `check-gates`
   row.
   - **Given** a reader looking up "what gates does the quick track require" in
     `state-file.md`, **When** they read the track-required paragraph, **Then**
     `implementation_verified` is listed alongside `log_written` and
     `roadmap_synced`.

## Behavior Delta

**Modified:**
- Derived roadmap Status / `project-status.md` `**Status**` — a lane now needs a
  third (quick/standard) or fourth (full) truthy gate to read `completed`. No
  Ring-1 `docs/product/` use case describes the completion derivation; the
  governing artifacts are `docs-eng-process/state-file.md` §gates and
  `docs-eng-process/tracks.md` §check-gates, both updated in this task
  (requirement 6).
- `openup-state.py check-gates` default required set — `docs-eng-process/state-file.md`
  line 52 documents the default; updated here.

**Added:**
- `gates.implementation_verified` (schema property; optional).

**Removed:** none.

## Success Measures

We expect **the count of roadmap rows stamped `completed` whose task produced no
implementation diff** to be **zero** from this change onward — the failure mode
observed downstream (a spec-and-log-only lane reading `completed`, corrected by
hand in `be2ee16`). Instrumentation: the existing
`sync-status.py --reconcile --dry-run` drift report plus `git log --stat` per
stamped task; a recurrence shows up as a `completed` row with no source diff.
Read-back: the next `/openup-retrospective` (this repo's retro cadence
counter is at 1 of 5, so within the next four completions).

## Rollout

**Flagged?** No. This is process tooling with no deployed user-facing surface,
and a flag would be actively harmful here: a gate that can be toggled off is not
a gate. The change is reversible by revert (see Safeguards) and its blast radius
is bounded to lanes completed after it lands — an in-flight lane's state simply
reads the gate as unset until its completion skill sets it, which is the
intended behavior, not a migration.

## Entities

- **`TRACK_REQUIRED`** (modified) — `scripts/sync-status.py:60-64`
- **`derive_status()`** (read-only, unchanged logic) — `scripts/sync-status.py:99-106`
- **`DEFAULT_REQUIRED_GATES`** (modified) — `scripts/openup-state.py:64`
- **`gates` object** (modified — one new optional property) —
  `scripts/openup-state.schema.json`
- **`cmd_set_gate` / `cmd_check_gates`** (read-only, reused unchanged) —
  `scripts/openup-state.py:484-509`
- **`openup-complete-task.md` step 1a + step 7** (modified) —
  `docs-eng-process/procedures/openup-complete-task.md`
- **`openup-quick-task.md` steps 3 + 6** (modified) —
  `docs-eng-process/procedures/openup-quick-task.md`

## Approach

Add one optional boolean gate, `implementation_verified`, and thread it through
the two places that decide "is this task done": `sync-status.py`'s
`TRACK_REQUIRED` (the derived view) and `openup-state.py`'s
`DEFAULT_REQUIRED_GATES` (the imperative check). `derive_status()` itself needs
no change — it already ANDs whatever the track requires, so requiring one more
key is a data edit, not a logic edit. The gate is *set* by the two completion
skills at the points where a human/agent has already done the verification work
(`/openup-complete-task` step 1a's per-requirement grade;
`/openup-quick-task`'s "verify the fix works"), which is why the schema keeps
the key optional: a state file that predates the gate must still validate, and
an absent key must read falsy — "not verified" — rather than raising.

## Structure

**Add:**
- `implementation_verified` property in `scripts/openup-state.schema.json` under
  `gates.properties` (not `gates.required`)
- Gate-setting instruction in `openup-complete-task.md` step 1a and
  `openup-quick-task.md` step 3
- Tests: derive-status gate matrix per track; `check-gates` default;
  end-to-end `sync-status.py` run with the gate absent then present

**Modify:**
- `scripts/sync-status.py` — `TRACK_REQUIRED` (all three tracks) + module
  docstring
- `scripts/openup-state.py` — `DEFAULT_REQUIRED_GATES`
- `docs-eng-process/state-file.md`, `docs-eng-process/tracks.md`
- Existing tests that set only the bookkeeping gates and expect `completed`
  (`test_sync_status_notes.py`, `test_t006_hooks.py`, `test_openup_state.py`)
- Generated skill mirrors under `docs-eng-process/.claude-templates/skills/`
  and `docs-eng-process/skills-guide.md` (via `render-skills-mirror.py --write`,
  `check-skills-guide.py --write`, `sync-templates-to-claude.sh` — never
  hand-edited)

**Do not touch:**
- `derive_status()`'s logic — the AND-over-required-gates contract is correct
  as-is
- `sync-status.py --reconcile` — it derives from archived change folders, not
  gates, and is the deliberate self-heal path for historical rot
- `gates.required` in the schema — adding the key there would break every
  pre-existing state file, the exact backward-incompatibility this design avoids
- T-146's `Iteration`-header guard — separate lane, same file

## Operations

- [x] Add `implementation_verified` to `gates.properties` in
      `scripts/openup-state.schema.json` (optional; documented as
      "delivery evidence, set by the completion skills")
- [x] Add `implementation_verified` to all three `TRACK_REQUIRED` entries in
      `scripts/sync-status.py` and update the module docstring's description of
      the derivation
- [x] Add `implementation_verified` to `DEFAULT_REQUIRED_GATES` in
      `scripts/openup-state.py`
- [x] Update `openup-complete-task.md` (step 1a set-gate + step 7 `--require`
      lines) and `openup-quick-task.md` (step 3 set-gate + step 6 `--require`
      line) in `docs-eng-process/procedures/`
- [x] Update `docs-eng-process/state-file.md` and `docs-eng-process/tracks.md`
- [x] (tester) Tests: gate-absent derives `in-progress` on quick/standard/full;
      gate-present derives `completed`; `check-gates` default names the gate;
      a schema-valid state without the key still validates
- [x] Regenerate the skill mirrors (`render-skills-mirror.py --write`,
      `sync-templates-to-claude.sh`) and run the full test suite

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, pre-commit housekeeping
- `docs-eng-process/state-file.md` — the gate contract this task extends
- `scripts/sync-status.py`'s own design rules (deterministic, stdlib-only,
  idempotent, `--state-dir` override for tests)

## Safeguards

Invariants and limits that must hold:
- **Backward compatibility.** A state file written before this change must still
  validate and must still be archivable — the key is optional and an absent key
  reads falsy. Never add it to `gates.required`.
- **No weakening.** No existing required gate is removed from any track; this is
  strictly additive to the required sets.
- **Judgment stays with the skill.** Nothing in this task attempts to *compute*
  whether the implementation is correct — the gate records a verdict the
  completion skill already reaches and already blocks on.
- **Reversibility.** A revert restores the previous required sets; states
  carrying the extra key still validate against the reverted schema only if the
  key is removed, so the revert note must say `set-gate` writes stop, not that
  existing states break. No data migration either way.

## Verification

- `python3 -m unittest scripts.tests.test_sync_status_notes
  scripts.tests.test_openup_state scripts.tests.test_t006_hooks -v` — green
- Full suite green (no regression)
- Live check on this very lane: after step 1a's grade, `sync-status.py` must
  refuse to stamp `completed` until `implementation_verified` is set — this
  task's own completion is its first end-to-end exercise
- `python3 scripts/check-docs.py` and `python3 scripts/openup-fence.py check`
  exit 0
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅ or a
  clear gap call-out

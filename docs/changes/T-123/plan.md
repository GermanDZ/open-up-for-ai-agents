---
id: T-123
title: "Dirty-aware gating (E2): per-box check-docs runs only when docs changed; completion re-run deduped; check-docs.py --changed-only"
status: ready
priority: medium
estimate: 1 session
plan: docs/roadmap.md
depends-on: []
blocks: []
last-synced: ""
touches:
  - scripts/check-docs.py
  - scripts/openup_agent/loop.py
  - scripts/openup_agent/cycle.py
  - scripts/tests/test_check_docs.py
  - scripts/tests/test_openup_agent_cycle.py
  - docs-eng-process/reference-driver.md
  - docs-eng-process/script-cli-reference.md
---

# T-123 — Dirty-aware gating (E2)

## Story

> **As** the cycle engine (and any harness re-running `check-docs` defensively)
> **I want** to skip a full docs rescan when nothing check-docs cares about has
> changed since the last pass
> **So that** a 6-box lane stops paying 13 full-doc scans (run_gates after every
> box + again at completion) when most boxes touch no docs — cutting deterministic
> cost with **no** removed judgment point and **no** weakened gate

INVEST — ✅ Independent · ✅ Negotiable · ✅ Valuable · ✅ Estimable · ✅ Small · ✅ Testable

## Analysis Context

- **Domain.** The E2 enhancement from the 2026-07-16 orchestration-economics
  review (`docs/explorations/2026-07-16-cycle-orchestration-economics.md`,
  §"Engine round-trip economics" + E2). Measured: "`run_gates` after every
  Operations box (cycle.py:1496) + again at complete (cycle.py:887);
  `check-docs.py` rglobs all docs each time. 6-box lane = 13 full-doc scans."
- **Two consumers, two baselines (design note).** The waste appears in two
  flows with genuinely different "since when" baselines, so each gets the
  mechanism fit for it:
  - **Harness flow** (Claude Code skills re-run `check-docs` 107× defensively,
    often back-to-back on an *unchanged* tree): a stat-signature cache keyed to
    "since the last `--changed-only` pass" skips the identical re-run. This is
    `check-docs.py --changed-only`.
  - **Cycle engine box loop** (no per-box commit — the working tree accumulates;
    plan.md is re-ticked every box): a git-delta of *check-docs-relevant* docs
    since the last gate pass, **excluding** the active change folder + the
    derived views + lane-owned audit trees (none of which affect check-docs'
    result), lets code-only boxes skip check-docs while the fence still runs
    every box.
- **What determines check-docs' result** (so a skip is provably safe): the set +
  content of the typed instance docs and the `.md` link graph under `docs/`, plus
  the schema (`docs-meta.schema.json`) and trace model (`trace-model.json`).
  Change-folder `plan.md`/`design.md` carry **no spine `type:`**, so they are
  never scanned instances — ticking a box or writing design notes cannot change
  the result. The derived views and status-note/agent-log/exploration trees are
  likewise never instances. Excluding them from the "did it change" signal is
  **correct**, not merely convenient.
- **Scope boundaries.** Gate *frequency* only. The fence runs on **every** box
  unchanged (it is cheap + diff-based); no gate is removed; check-docs runs at
  least once per lane (the first box establishes the baseline) and whenever a
  relevant doc changes. No new tool (T-121), no briefing change (T-120), no
  process-gate change (T-122).
- **Definition of done.** `check-docs.py --changed-only` skips an unchanged
  rescan and re-runs on any docs/schema delta; the engine runs check-docs per box
  only when a relevant doc changed since the last pass; the completion re-run is
  deduped when nothing relevant changed since the last box's pass. Each has a
  hermetic test.

## Requirements

1. **`check-docs.py --changed-only` skips an unchanged rescan.** With the flag,
   check-docs short-circuits (exit 0) when the docs tree + schema + trace-model
   are byte-identical (by a cheap stat signature) to the last successful
   `--changed-only` pass; otherwise it runs the full check and records the new
   signature.
   - **Given** a clean docs tree already validated once with `--changed-only`
     **When** `check-docs.py --changed-only` runs again with no file changed
     **Then** it prints a "no docs delta since last pass — skipping" line and
     exits 0 **without** re-validating.
   - **Given** any `docs/**/*.md` (or the schema / trace-model) changed since the
     last pass **When** `--changed-only` runs **Then** it runs the full check.
   - **Given** the previous `--changed-only` run **failed** **When** it runs again
     unchanged **Then** it does **not** skip (it re-runs so the failure resurfaces).
   - **Given** `--changed-only --coverage` **When** it runs **Then** its cache
     entry is distinct from the non-coverage entry (a coverage run validates more,
     so its skip is tracked separately).
   - Without `--changed-only`, behavior and exit codes are **byte-identical** to
     today (default path untouched).

2. **`run_gates` can skip a named gate.** `loop.run_gates(root, skip=None)` runs
   every present gate except those whose label is in `skip`; a skipped gate is
   reported (not failed). `skip=None` is today's behavior exactly.
   - **Given** `run_gates(root, skip={"check-docs"})` **When** it runs **Then**
     the fence runs and check-docs does not, and `ok` reflects only the gates that
     ran.

3. **The engine runs per-box check-docs only on a relevant-docs delta.** In the
   box loop, the engine computes a signature of check-docs-relevant docs changes
   (git-based; excludes the active change folder, the derived views, and the
   lane-owned audit trees; includes the schema/trace-model files). check-docs runs
   on the first box (baseline) and on any box after which that signature differs
   from the last pass; otherwise the box's gate runs the fence and **skips**
   check-docs. Git unavailable ⇒ fail-open (run the full gate).
   - **Given** a multi-box lane where a box authors a `docs/product/*.md` and a
     later box touches only code **When** the cycle runs **Then** check-docs runs
     for the doc-authoring box and is **skipped** for the code-only box (the fence
     still runs for both), and the lane still completes.
   - **Given** a box that introduces a check-docs failure **When** its gate runs
     **Then** the failure is still caught (the relevant-docs delta forces the run)
     and the box is left unticked (exit 6) — unchanged from today.

4. **The completion check-docs re-run is deduped.** `complete()` skips its
   check-docs re-run when the relevant-docs signature is unchanged from the last
   box's pass (the fence still runs); it runs the full gate otherwise. A genuine
   completion-time gate failure is still caught when the signature differs.
   - **Given** a lane whose last box passed check-docs and whose completion writes
     only the status flip + status-note + regenerated views **When** `complete()`
     gates **Then** check-docs is **not** re-run (all completion writes are
     check-docs-irrelevant) and the lane completes with the fence green.

## Behavior Delta

**Added** — `check-docs.py --changed-only` (stat-signature cache under
`.openup/check-docs-cache.json`, Ring-3/gitignored). `loop.run_gates` gains an
optional `skip` parameter. `cycle.py` gains `_relevant_docs_sig(root, task_id)`.

**Modified** — `cycle.py` box loop: track `last_docs_sig`; run check-docs only on
first box or a relevant-docs delta. `complete()`: accept `last_docs_sig` and dedup
the completion check-docs re-run. Docs: a "dirty-aware gating" note in
`reference-driver.md`, a `--changed-only` entry in `script-cli-reference.md`.

**Removed** — n/a.

## Entities

- **Doc validator** (modified) — `scripts/check-docs.py`: `--changed-only` +
  stat-signature cache.
- **Gate runner** (modified) — `scripts/openup_agent/loop.py`: `run_gates(skip=)`.
- **Box executor + completion** (modified) — `scripts/openup_agent/cycle.py`:
  `_relevant_docs_sig`, the box loop's per-box gate, `complete()`.

## Approach

- **`--changed-only`:** compute `sig = sha256(sorted "<relpath>\0<size>\0<mtime_ns>"
  for docs/**/*.md, + the schema and trace-model stats)`; cache
  `{ "<docs_resolved>|cov=<bool>": {sig, ok} }` at `<docs>/../.openup/check-docs-cache.json`.
  Skip (print + exit 0) only when the cached entry's `sig` matches AND its `ok` is
  true; else run the full check and persist `{sig, ok:(not hard)}`. The default
  path (no flag) never touches the cache.
- **`run_gates(root, skip=None)`:** a gate whose label ∈ `skip` appends
  `"<label>: skipped (dirty-aware — unchanged since last pass)"` and is not run;
  `ok` is unaffected by skipped gates.
- **`_relevant_docs_sig(root, task_id)`:** parse `git status --porcelain -- docs`
  (+ include changed `docs-meta.schema.json` / `trace-model.json` by basename);
  drop paths under `docs/changes/<task>/`, `docs/changes/archive/<task>/`, the
  three views, and `docs/status-notes|agent-logs|explorations/`; return the sorted
  join of the surviving `<xy>:<path>` lines (empty string = no relevant delta;
  `None` = git unavailable ⇒ caller runs the full gate).
- **Box loop (cycle.py):** `last_docs_sig=None` before the loop; per box, compute
  `sig`; if `last_docs_sig is not None and sig == last_docs_sig` →
  `run_gates(root, skip={"check-docs"})`; else `run_gates(root)` and, on success,
  `last_docs_sig = sig`. Pass `last_docs_sig` to `complete()`, which applies the
  same skip decision to its own gate.

## Structure

**Modify:**
- `scripts/check-docs.py` — `--changed-only` flag + signature/cache helpers.
- `scripts/openup_agent/loop.py` — `run_gates(skip=None)`.
- `scripts/openup_agent/cycle.py` — `_relevant_docs_sig`, box-loop gate, `complete()`.
- `scripts/tests/test_check_docs.py` — `--changed-only` skip/rerun/fail/coverage/default.
- `scripts/tests/test_openup_agent_cycle.py` — per-box skip on code-only box, gate
  failure still caught, completion dedup.
- `docs-eng-process/reference-driver.md` — dirty-aware gating note.
- `docs-eng-process/script-cli-reference.md` — `--changed-only` entry.

**Do not touch:** the fence (runs every box unchanged), the sentinel/exit
contract, the sub-run briefing (T-120), the tool surface (T-121), the process
gates (T-122), `sync-status.py` / `openup-fence.py` internals.

## Operations

- [x] `check-docs.py --changed-only`: stat-signature (docs/**/*.md + schema + trace-model) cached under `.openup/check-docs-cache.json`; skip (exit 0) when unchanged & last ok, else run full; coverage-keyed; default path untouched.
- [x] `loop.run_gates(root, skip=None)`: skip a named gate (reported, not failed); `skip=None` unchanged.
- [x] `cycle._relevant_docs_sig(root, task_id)`: git-delta of check-docs-relevant docs (excludes change folder + views + audit trees; includes schema/model; `--untracked-files=all` so new subtrees list files; fail-open None).
- [x] cycle box loop: run check-docs per box only on first box or a relevant-docs delta; fence always runs.
- [x] `cycle.complete()` accepts `last_docs_sig` and dedups the completion check-docs re-run.
- [x] (tester) check-docs tests: skip-unchanged, rerun-on-delta, no-skip-after-failure, coverage-keyed, default-byte-identical.
- [x] (tester) cycle tests: code-only box skips check-docs + completion dedup, relevant-later-box reruns, gate failure still exits 6, sig unit tests (fail-open/excludes noise/includes schema).
- [x] Docs: reference-driver dirty-aware note + script-cli `--changed-only` entry.
- [x] Full suite green; fence `--base harness-optional` + check-docs clean.

## Norms

Inherits from:
- `docs-eng-process/conventions.md`
- T-089 box executor + T-091/T-108 completion (the paths §3–§4 touch)
- T-072 deterministic gates in the loop (`run_gates`)

## Safeguards

- **No gate is removed; the fence runs every box.** Only check-docs *frequency*
  changes, and only when its result provably cannot have changed (the excluded
  paths are never check-docs instances).
- **check-docs runs at least once per lane.** The first box always establishes the
  baseline (`last_docs_sig is None`), so a pre-existing docs problem is caught.
- **Fail-open.** No git, no `.openup/`, or a stat error ⇒ the full gate runs (the
  driver's absent-capability spirit) — the optimization never blocks a run.
- **Default check-docs path is byte-identical.** `--changed-only` is opt-in; the
  no-flag path (used everywhere today) is untouched, asserted by a test.
- **Conservative signature.** Any doubt (a changed relevant `.md`, a schema/model
  change, a git failure) forces the full check — the skip only fires on a proven
  no-op delta.
- **Reversibility.** The three pieces are independent; reverting one leaves the
  others working (the engine simply runs check-docs more often).

## Verification

- `python3 -m pytest scripts/tests/test_check_docs.py scripts/tests/test_openup_agent_cycle.py scripts/tests/test_openup_agent_loop.py -q` passes (loop suite if present; else the loop change is covered via cycle tests).
- Full suite green; fence `--base harness-optional` clean; `check-docs` clean.

## Success Measures

Falsifiable: on the T-080 bench's `cycle-quick-doc` scenario, the number of
full `check-docs` invocations in a lane drops (a 6-box lane no longer runs 7
per-box + 1 completion = fewer full scans), with **zero** change to the lane's
exit code / sentinel and **zero** gate escapes (the gate-failure and completion
tests prove failures are still caught). Instrument: the existing gate-run lines in
the cycle log (`check-docs: OK` vs `check-docs: skipped (dirty-aware …)`) — countable
per lane without new telemetry. (This lane's hermetic proof is the code-only-box
skip test + the completion-dedup test; the bench read-back is the T-080 owner batch,
as this sandbox reaches no endpoint.)

## Rollout

n/a — internal engine/validator optimization on harness-optional; `--changed-only`
is opt-in and off by default, no runtime user-facing flag beyond the CLI option.

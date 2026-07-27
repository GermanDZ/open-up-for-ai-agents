---
id: T-138
title: "T-107 split: doctor --check wiring + KB re-distill runbook"
status: ready
priority: medium
estimate: 1 session
plan: docs/changes/archive/T-107/plan.md
depends-on: [T-137]
blocks: []
last-synced: ""
touches:
  - scripts/openup-doctor.py
  - scripts/tests/test_openup_doctor.py
  - docs-eng-process/reference-driver.md
---

# T-138 — T-107 split: doctor `--check` wiring + KB re-distill runbook

## Story

> **As a** maintainer of an OpenUP-managed project (framework repo or a
>   downstream project that vendors it)
> **I want** `openup-doctor.py` to surface task-library drift as a WARNING,
>   without ever false-positiving on a project that has no vendored KB
> **So that** drift is caught early without T-105's "false ERROR on absent
>   KB" bug landing again at the doctor layer

INVEST check:
✅ Independent — one new doctor check function + docs; no dependency on
T-139.
✅ Negotiable — the exact KB-presence detection mechanism is a design
choice (Approach), not fixed by the spec.
✅ Valuable — closes a real gap: `build-task-library.py --check` already
reports drift when a task's KB *source file* is individually missing
(exit 1, same code as real drift) — a project vendoring `task-library.yaml`
but not the KB source tree would currently read as "drifted," not
"unverifiable."
✅ Estimable — `openup-doctor.py`'s existing `detect_all()` composition
pattern and `_AGGREGATED` mechanism were read in full this session.
✅ Small — one new check function following an established pattern; a docs
section.
✅ Testable — KB-absent, KB-present-in-sync, and KB-present-drifted are all
independently constructible fixtures.

## Analysis Context

- **Domain.** `scripts/openup-doctor.py`'s check composition
  (`detect_all()`) and `scripts/build-task-library.py --check`'s exit
  codes.
- **Scope boundaries.** Does not modify `build-task-library.py`'s own exit
  codes or drift logic — the fix lands at the doctor layer (where the
  KB-presence context actually needs to change the *severity*, not the
  underlying compiler's behavior). Does not touch T-139's scope
  (customized process sources).
- **Definition of done.** `openup-doctor.py` reports task-library drift as
  WARNING when the vendored KB is present and drifted, INFO "in sync" when
  present and clean, and INFO "not verifiable (no KB)" when the KB source
  tree is absent — never ERROR in any case. The re-distill runbook is
  documented in `reference-driver.md`.

**Confirmed this session, before writing code**: `build-task-library.py
--check`'s `check_drift()` (`scripts/build-task-library.py:173-192`) treats
a task's *individually missing KB source file* as drift (`exit 1`,
`EXIT_DRIFT`) — the exact same exit code as a genuine skeleton mismatch.
There is no distinguishing exit code for "the whole KB source tree isn't
vendored here" vs "one field drifted." Confirmed the KB source tree
(`docs-eng-process/openup-knowledge-base/`) is **not** listed in
`scripts/process-manifest.txt` — unlike `task-library.yaml` itself, which
ships to every project (per that file's own comment: "the task-library.yaml
itself ships under docs-eng-process/"). So a downstream project routinely
has the compiled library but not the KB — exactly the shape that would
misreport as drift today if `--check`'s exit code alone decided severity.

> **Assumption:** the doctor-side check pre-tests
> `os.path.isdir(docs-eng-process/openup-knowledge-base/)` **before**
> running `build-task-library.py --check` at all, and reports INFO
> "not verifiable" without running the check when absent — rather than
> running `--check` regardless and trying to parse its stderr messages to
> distinguish "missing source" drift from "real" drift. Simpler and more
> robust: no message-format coupling between the two scripts.
> *(Vetoable at review.)*

## Requirements

1. `openup-doctor.py` gains a new check, `check_task_library()`, wired into
   `detect_all()`.
   - **Given** a repo with `build-task-library.py` present, the vendored KB
     present, and the library in sync, **When** `openup-doctor.py` runs,
     **Then** it reports `INFO "task-library.yaml: in sync with KB
     sources"`.

2. The check reports WARNING (never ERROR) when the KB is present and the
   library has genuinely drifted.
   - **Given** a repo with the vendored KB present and a task's KB source
     file's `name`/`role`/`inputs` field changed since the library was last
     compiled, **When** `openup-doctor.py` runs, **Then** it reports
     `WARNING` naming the drifted task.

3. The check degrades to INFO — never WARNING, never ERROR — when the
   vendored KB source tree is absent.
   - **Given** a repo with `task-library.yaml` present (vendored, as every
     downstream project has it) but `docs-eng-process/openup-knowledge-base/`
     absent, **When** `openup-doctor.py` runs, **Then** it reports `INFO
     "not verifiable (no KB)"`, not a warning or error, even though
     `build-task-library.py --check` alone would exit 1 (drift) in this
     exact situation.

4. The check degrades to INFO "not present" when `build-task-library.py`
   itself is absent (matching the existing `_AGGREGATED` pattern's
   convention for every other aggregated check).
   - **Given** a repo without `scripts/build-task-library.py`, **When**
     `openup-doctor.py` runs, **Then** it reports `INFO "not present
     (skipped)"`.

5. A documented, repeatable KB-update re-distillation runbook exists in
   `docs-eng-process/reference-driver.md`: bump the KB (or edit a task
   file) → regenerate skeletons/prompts → review the diff → commit.
   - **Given** a reader following the runbook after editing a KB task file,
     **When** they run `build-task-library.py --check`, **Then** it flags
     the drift, and the runbook's next step (re-run without `--check`)
     produces the updated skeleton + distillation prompt for review.

## Behavior Delta

`n/a — all Added`. No Ring-1 (`docs/product/`) use-case describes
`openup-doctor.py`'s check set — it is process/health tooling, not product
behavior. Additive: a new check function, composed into the existing
`detect_all()` list; no existing check's behavior changes.

## Success Measures

We expect zero false-positive WARNING/ERROR reports on a downstream project
that vendors `task-library.yaml` but not the KB source tree — the exact
failure mode T-105 already found once and this task closes at the doctor
layer. Instrumentation: `openup-doctor.py`'s own JSON output
(`--json`), inspectable any time. Read-back: the next time `openup-doctor`
runs against a real downstream project (owner-initiated, no fixed date —
matching this repo's existing conditional-trigger convention for
spike/hardening work).

## Rollout

**Flagged?** No. Internal health-diagnostic tooling, read-only, no deployed
user-facing surface — `openup-doctor.py` is already opt-in-by-invocation
(a maintainer runs it; nothing calls it automatically that would need a
kill-switch).

## Entities

- **`check_task_library()`** (new) — `scripts/openup-doctor.py`, follows the
  existing `check_*(repo) -> list[Finding]` convention (e.g.
  `check_state_integrity`, `scripts/openup-doctor.py:229-246`)
- **`detect_all()`** (modified) — `scripts/openup-doctor.py:425-434` — one
  new `findings += check_task_library(repo)` line
- **`Finding`** (read-only, reused) — `scripts/openup-doctor.py:82-97`
- **`build-task-library.py --check` / `check_drift()`** (read-only,
  invoked not modified) — `scripts/build-task-library.py:173-192`
- **`docs-eng-process/reference-driver.md`** (modified) — new re-distill
  runbook section

## Approach

Add one new check function that pre-tests KB-tree presence via
`os.path.isdir()` before ever invoking `build-task-library.py --check`,
so the severity decision doesn't depend on parsing the compiler's own
output — a project without the KB reads INFO "not verifiable" without the
subprocess call even running. When the KB is present, invoke `--check`
exactly like the other `_AGGREGATED` entries and map its exit code to
INFO/WARNING (never ERROR — task-library drift is advisory, matching its
existing `_AGGREGATED` severity precedent for `docs-index.py --check`,
`build-trace-model.py --check`, etc.). Document the re-distill flow as a
runbook section, since `build-task-library.py`'s default (non-`--check`)
mode already regenerates skeletons + prompts for review — no new compiler
behavior needed, only the documented sequence.

## Structure

**Add:**
- `check_task_library()` in `scripts/openup-doctor.py`
- Re-distill runbook section in `docs-eng-process/reference-driver.md`
- Tests in `scripts/tests/test_openup_doctor.py`

**Modify:**
- `scripts/openup-doctor.py`'s `detect_all()` — one new composed check

**Do not touch:**
- `scripts/build-task-library.py` — its exit codes and `check_drift()` stay
  exactly as-is; the fix is entirely at the doctor layer, not the compiler
- `_AGGREGATED` / `check_aggregate()` — the new check is its own function,
  not folded into the generic list (it needs KB-presence pre-testing the
  generic mechanism doesn't support)
- T-139's scope (customized process sources) — separate lane

## Operations

- [x] Add `check_task_library(repo)` to `scripts/openup-doctor.py`:
      KB-tree presence pre-test → INFO "not verifiable" when absent;
      script-presence check → INFO "not present" when absent; otherwise
      run `--check` and map exit 0 → INFO "in sync", exit 1 → WARNING
      naming the drift, other exit → INFO "could not run"
- [x] Wire it into `detect_all()`
- [x] Write `docs-eng-process/reference-driver.md`'s re-distill runbook
      section (bump → regenerate → review diff → commit)
- [x] (tester) Tests: KB absent → INFO; KB present + in sync → INFO;
      KB present + genuine drift → WARNING; script absent → INFO; confirm
      no ERROR is ever produced by this check regardless of scenario
- [x] Run the full existing test suite; confirm no regression (767/767
      green, 1 correctly skipped)

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format,
  etc.)
- `scripts/openup-doctor.py`'s own existing `check_*` functions — the
  pattern this new check follows

## Safeguards

Invariants and limits that must hold:
- **Never ERROR.** Task-library drift is advisory (matching its
  `_AGGREGATED` severity precedent) — this check must never produce
  `ERROR`, in any scenario, including a malformed library (falls back to
  `INFO "could not run"`, mirroring the existing `_AGGREGATED` exit-127
  handling).
- **No change to `build-task-library.py`.** The compiler's own exit codes
  and drift definition are unchanged — the severity mapping lives entirely
  in the doctor-side check.
- **Reversibility.** Purely additive; a revert removes the new check
  function and doc section with no migration.

## Verification

- `python3 -m unittest scripts.tests.test_openup_doctor -v` — all green,
  including the new fixtures
- `python3 scripts/openup-doctor.py --json` on this repo (KB present, in
  sync) → the new check reports INFO "in sync"
- Full existing test suite green (no regression)
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅
  or a clear gap call-out

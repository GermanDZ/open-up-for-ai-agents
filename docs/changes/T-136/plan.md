---
id: T-136
title: "Inception authoring-reliability measure independent of the post-authoring consent gate"
status: ready
priority: medium
estimate: 1 session
plan: docs/iteration-plans/t-136-authoring-reliability-measure.md
depends-on: [T-106]
blocks: []
last-synced: ""
touches:
  - scripts/analyze-authoring-reliability.py
  - scripts/tests/test_analyze_authoring_reliability.py
  - docs/changes/T-107/design.md
  - docs/iteration-plans/t-136-authoring-reliability-measure.md
---

# T-136 — Inception authoring-reliability measure independent of the post-authoring consent gate

## Story

> **As an** owner deciding whether T-107 (scaling the task library) is safe
>   to start
> **I want** T-106's gate measured by what actually happened in each
>   authoring sub-run, not by the overall `cycle` run's terminal driver exit
>   code
> **So that** the gate reads a real signal instead of a structural 0% that
>   holds regardless of model quality

INVEST check:
✅ Independent — one new analysis script + tests; reads already-saved logs,
touches no shared harness code.
✅ Negotiable — the restart-detection threshold is explicitly open (Open
Questions), not fixed.
✅ Valuable — the difference between "T-107 stays blocked" and "T-107 has a
real, defensible go/no-go" is exactly this measurement.
✅ Estimable — the parsing target (`run-0N.driver.log`) was read in full
this session; the classification logic is confirmed against real data
before writing a line of code (see Analysis Context).
✅ Small — no new subsystem; one script, one test file.
✅ Testable — synthetic fixtures for each classification case, plus a
regression check against this session's real saved logs.

## Analysis Context

- **Domain.** `scripts/openup-agent-bench.py`'s saved per-run artifacts
  (`run-0N.driver.log`), read by a new, separate analysis script. Does not
  touch the bench harness's own `aggregate()`/`pass` definition.
- **Scope boundaries.** Does not attempt to make the driver itself exit
  `0`/`pass` for this scenario (would need cycle-engine phase-completion
  detection — separate, larger scope). Does not modify
  `openup-agent-bench.py`. Not a general-purpose log analyzer — scoped to
  the specific sub-run block shape `cycle.py`'s task-def dispatch produces.
- **Definition of done.** The analyzer classifies each of this session's 5
  saved `t107-gate-nano` runs correctly (verified by hand this session — see
  below), the result is recorded in `docs/changes/T-107/design.md`, and unit
  tests cover the four classification cases on synthetic fixtures.

**Confirmed this session, before writing any code** (`grep -c` over all 5
saved driver logs for any tool-call line repeated more than twice): **only
run-04** has a repeat pattern — `glob docs/**/technical-specification*.md`
called **12 times consecutively** inside its final sub-run ("Plan Iteration"),
before an unrelated `HTTP 429` cut the run off at iteration 25. Runs 1, 2, 3,
and 5 have **zero** repeated tool calls across any sub-run. This means the
real, honest measurement is very likely **4/5 = 80%** — exactly the gate's
bar — with run-04 correctly failing for a **genuine** reliability bug (an
unresolved "Technical Specification" input name in the Plan Iteration
task-def, not fully covered by T-124's alias fix), not the rate limit that
happened to end it.

> **Assumption:** a "restart" is **3 or more consecutive identical tool
> calls** (same name + same primary argument) within one sub-run block. The
> real observed case (12 consecutive repeats) is unambiguous at any
> reasonable threshold ≥2; 3 is chosen to avoid flagging a single legitimate
> incidental duplicate read. *(Vetoable at review.)*
> **Assumption:** a sub-run block is delimited by consecutive
> `procedure=<name> model=<model> ...` lines (the start of the next sub-run,
> or end of file/a `FATAL:` line, ends the current one) — matches
> `cycle.py`'s `run_task()` calling `loop.run()` once per task-def,
> confirmed against real logs this session. *(Vetoable at review.)*

## Requirements

1. `scripts/analyze-authoring-reliability.py` parses a bench-run directory's
   `run-0N.driver.log` files into per-sub-run blocks (procedure name, turn
   count, tool-call sequence).
   - **Given** `.openup/bench/t107-gate-nano/run-01.driver.log` (a real,
     clean run), **When** the analyzer parses it, **Then** it reports 7
     sub-run blocks with the turn counts observed this session (2–3 turns
     each).

2. A sub-run is classified `not-clean` if its turn count exceeds 6, or if
   any tool call repeats 3+ times consecutively within it; otherwise
   `clean`.
   - **Given** `run-04.driver.log`'s "Plan Iteration" block (12 consecutive
     identical `glob` calls), **When** the analyzer classifies it, **Then**
     it reports `not-clean` with the repeated call named in the reason.
   - **Given** any of run-01/02/03/05's sub-run blocks, **When** the
     analyzer classifies them, **Then** every one reports `clean`.

3. A run is `authoring-chain clean` iff every sub-run block it reached is
   `clean` (a run that never started any sub-run — e.g. an `endpoint-error`
   on iteration 1 — is `not-clean` with a distinct reason, not silently
   excluded).
   - **Given** the 5 saved `t107-gate-nano` runs, **When** the analyzer
     runs, **Then** it reports run-04 as `not-clean` and the other four as
     `clean` — a `4/5 = 0.8` clean rate.

4. The analyzer's output is one JSON object: `{runs, authoring_chain_clean,
   clean_rate, per_run: [{run, clean, reason?}], per_sub_run: [...]}`
   — machine-readable, suitable for pasting into `design.md`.
   - **Given** a completed analyzer run, **When** its stdout is parsed as
     JSON, **Then** `clean_rate` is a float and `per_run` has one entry per
     input log file.

5. The re-measured result is recorded in `docs/changes/T-107/design.md`
   (new file), stating the number plainly against the ≥80% bar — whichever
   way it comes out.
   - **Given** the analyzer's real output against `t107-gate-nano`, **When**
     `design.md` is written, **Then** it states the clean rate, names
     run-04's specific failure (the unresolved "Technical Specification"
     input, not the rate limit), and states plainly whether T-107's gate is
     satisfied.

## Behavior Delta

`n/a — all Added`. No Ring-1 (`docs/product/`) use-case describes this
measurement tooling — it is process/reliability tooling, not product
behavior. Purely additive: a new script reading already-saved artifacts,
touching no shared harness code path.

## Success Measures

We expect this task to produce one honest, defensible number for T-107's
gate, replacing a measurement that structurally read 0% regardless of model
quality. Instrumentation: the analyzer's own JSON output, pasted into
`docs/changes/T-107/design.md`. Read-back: immediate — this is the artifact
the gate needs to resolve now, not a deferred measure.

## Rollout

**Flagged?** No. Internal analysis tooling with no deployed surface;
nothing to stage or roll back beyond a normal code revert.

## Entities

- **`scripts/analyze-authoring-reliability.py`** (new) — driver-log parser +
  classifier + JSON reporter
- **`scripts/tests/test_analyze_authoring_reliability.py`** (new) — unit
  tests against synthetic fixture logs
- **`docs/changes/T-107/design.md`** (new) — records the re-measured result
- **`.openup/bench/t107-gate-nano/run-0{1..5}.driver.log`** (read-only,
  input) — this session's already-saved real gate-check logs

## Approach

Parse each `run-0N.driver.log` line-by-line, splitting on
`[openup-agent] procedure=<name> model=<model> ...` into sub-run blocks;
within each block, count `model turn i/N` lines and detect 3+ consecutive
identical `read_file`/`write_file`/`glob`/`grep`/`exec` lines. Classify each
sub-run, then each run, then aggregate a batch-level `clean_rate` — the same
shape as the bench harness's own `pass_rate`, but measuring the thing the
gate actually cares about.

## Structure

**Add:**
- `scripts/analyze-authoring-reliability.py`
- `scripts/tests/test_analyze_authoring_reliability.py`
- `docs/changes/T-107/design.md`

**Modify:**
- (none — purely additive)

**Do not touch:**
- `scripts/openup-agent-bench.py` — shared harness pass/fail semantics used
  by every other scenario; not touched
- `scripts/bench-scenarios/inception-taskdef/scenario.json` — the scenario
  itself is unchanged; this task changes how its already-saved output is
  measured, not the scenario
- `docs-eng-process/process-map.yaml` / the Plan Iteration task-def's input
  resolution — run-04's real bug (unresolved "Technical Specification"
  input) is a genuine finding but fixing it is separate scope from T-136
  (T-136 measures; it doesn't fix the measured bug)

## Operations

- [ ] Write `scripts/analyze-authoring-reliability.py`: log parser (sub-run
      block splitting), turn-count + repeated-tool-call classifier, JSON
      output
- [ ] Write `scripts/tests/test_analyze_authoring_reliability.py` with
      synthetic fixture logs for: clean run, over-turn-ceiling sub-run,
      3+-repeat restart, never-started run (endpoint-error on iteration 1)
- [ ] Run the analyzer against `.openup/bench/t107-gate-nano/` and confirm
      the output matches this session's hand-verified finding (4/5 clean,
      run-04 flagged for the repeated `glob` call)
- [ ] Write `docs/changes/T-107/design.md` recording the result plainly
      against the ≥80% bar, naming run-04's real failure reason
- [ ] (tester) Run the new test file plus the full existing suite; confirm
      no regression

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format,
  etc.)
- `scripts/openup-agent-bench.py`'s own driver-log format (read, not
  copied — this script is a consumer of that format, not a reimplementation
  of the harness)

## Safeguards

Invariants and limits that must hold:
- **Read-only w.r.t. the bench harness.** No change to
  `openup-agent-bench.py`'s shared pass/fail semantics.
- **Honest reporting.** The result — whatever it is — goes into
  `docs/changes/T-107/design.md` verbatim; this task does not exist to
  manufacture a passing number.
- **Reversibility.** Purely additive; a revert removes the new script and
  test file with no migration.

## Verification

- `python3 -m unittest scripts.tests.test_analyze_authoring_reliability -v`
  — all green
- `python3 scripts/analyze-authoring-reliability.py --bench-dir
  .openup/bench/t107-gate-nano` → `clean_rate: 0.8`, run-04 flagged
- Full existing test suite green (no regression)
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅
  or a clear gap call-out

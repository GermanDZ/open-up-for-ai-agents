# T-136: Inception authoring-reliability measure independent of the post-authoring consent gate

**Phase**: construction
**Status**: pending
**Goal**: Give T-106's gate a real ≥80%-clean-pass measurement that reflects sub-run authoring reliability, not the whole `cycle` run's terminal driver exit code — so T-107's promotion gate can be honestly satisfied or honestly failed, instead of structurally reading 0% regardless of model quality.
**Priority**: medium

---

## Context

T-107's spec (`docs/changes/T-107/plan.md`) writes a literal promotion gate: "T-106's behavioral acceptance must pass on the owner's live qwen batch first: zero mid-run restarts, ≤6 iterations per sub-run, ≥80% clean-pass over 5 runs... read via `scripts/bench-scenarios/inception-taskdef`."

This session ran exactly that batch against a real endpoint (`gpt-5.4-nano`, after fixing two environment issues — a stale bundled OpenSSL cert path and a missing `OPENUP_MODEL_MID`/`OPENUP_MODEL_SMALL` fallback). Result: `pass_rate: 0.0, clean_passes: 0` — by the bench harness's own metric, the gate failed outright, despite every individual authoring sub-run completing cleanly (zero restarts, 2-3 turns each, well under the ≤6 ceiling) across 4 of 5 runs (the 5th hit an unrelated `HTTP 429` rate limit at iteration 25).

Root cause, confirmed by reading the code this session: `openup-agent-bench.py`'s `aggregate()` defines `pass` as `outcome == "pass"`, and `outcome` is derived from the **driver subprocess's own exit code** (`OUTCOME_BY_EXIT`). The `inception-taskdef` scenario runs `openup-agent.py cycle --procedure next`, which — by design (T-092's recovery mode) — doesn't stop once the fixed Inception authoring activities finish; it keeps resolving, finds nothing further deterministically promotable, and hits the **consent-gated auto-replenish** pause (T-094) — exit 5, `"suspended"`. This happens on **every** run regardless of model quality: the process-map's Inception phase has exactly four `execution: direct` activities, and once they're done for one iteration, `resolve()` always looks for more work and always finds none without a human granting the LLM-replenish consent. Confirmed: `--no-recover` doesn't help either — it just trades one non-`pass` exit code (`5`, suspended) for another (`7`, unsupported-path; `cycle.py:93-95`) — because true `pass`/`DONE` for this scenario would require the engine to recognize Inception's phase-exit criteria are met and route to `milestone-review`, not "stuck." That phase-completion-detection gap is real but is separate, larger scope than this task (see Out of Scope).

Owner decision (this session): fix the measurement so a clean authoring-chain completion can be recognized, re-run the batch, then record a literal result (pass or fail) against the ≥80% bar in `docs/changes/T-107/design.md` before T-107 starts.

---

## Current State

### The bench harness's pass definition is driver-exit-code-only (`scripts/openup-agent-bench.py:44-53, 365-378`)

```python
OUTCOME_BY_EXIT = {
    0: "pass",
    2: "config-error",
    3: "endpoint-error",
    4: "max-iterations",
    5: "suspended",
    6: "gate-failure",
    7: "unsupported-path",
    8: "step-failure",
}
...
def aggregate(records, meta):
    n = len(records)
    passes = [r for r in records if r["outcome"] == "pass" and r["gates"]["fence"]
              and r["gates"]["check_docs"] and r["work"]["deliverable_produced"]]
```

### Each run's full driver log is already saved (`scripts/openup-agent-bench.py` run loop) — this session read these by hand

`.openup/bench/<out>/run-0N.driver.log` — plain text, already contains everything needed: one `procedure=<name> model=<model> ...` line per sub-run, one `model turn i/N` line per LLM call, and `procedure complete on iteration N; gates clean` on success. Verified this session (T-107 gate run): 7 sub-runs per run (`plan-objectives`, `develop-technical-vision`, `author-initial-roadmap`, `envision-the-architecture`, `identify-and-outline-requirements`, `detail-use-case-scenarios`, `plan-iteration`), each completing in 2-3 turns, zero restarts, across every run.

### `--no-recover` does not produce a `pass` outcome either (`scripts/openup_agent/cycle.py:93-95`)

```python
# (T-090/T-092), so it only lands here under --no-recover.
"plan-iteration": "T-090 (only reachable here under --no-recover)",
```

Confirms: without recovery mode, `plan-iteration` after the fixed Inception activities still doesn't resolve to a `pass`/`DONE` terminal state — it exits 7 instead of 5. True completion would require the engine itself to detect Inception's phase-exit criteria are met (a `milestone-review` decision), which is real, separate, larger-scope work (see Out of Scope).

---

## Proposed Design

A new, standalone analysis script that reads the **already-saved** driver logs from a completed `openup-agent-bench.py` run and computes the gate's actual criterion — independent of the run's overall driver exit code. Does **not** modify `openup-agent-bench.py`'s shared `aggregate()`/`pass` definition (used by every other scenario) — that stays exactly as-is, avoiding any risk of weakening pass/fail semantics elsewhere.

**New file**: `scripts/analyze-authoring-reliability.py`

```python
#!/usr/bin/env python3
"""Measures T-106's authoring-reliability gate from a completed
openup-agent-bench.py run's saved driver logs — independent of the run's
overall driver exit code (T-136).

The inception-taskdef scenario's driver process cannot report a clean
"pass" exit today: by design (T-092 recovery mode), it runs past the fixed
Inception authoring activities into a deterministic consent-gate pause that
every run hits, regardless of model quality (see docs/changes/T-136/plan.md
Current State). This script measures the thing the gate actually cares
about — did each authoring sub-run complete without restarting and within
the turn ceiling — directly from the driver's own per-sub-run log lines.

A run's "authoring-chain clean" iff every one of its sub-runs (each
"procedure=<name> ... model turn 1/N" through "procedure complete on
iteration K; gates clean" block) used <= --max-turns turns and no sub-run
restarted (a restart = a repeated first tool call within one sub-run —
T-106's own definition).
"""
```

Parses `run-0N.driver.log`, splits on `procedure=` lines into per-sub-run blocks, counts `model turn` lines per block, and flags a restart when the same tool-call signature (name + primary argument) repeats as a sub-run's first tool call. Outputs one JSON summary: `{runs, authoring_chain_clean, clean_rate, per_run: [...]}`.

`clean_rate` is the number this task's re-measurement will read against the ≥80% bar — the same runs, the same logs, a different (and more accurate) definition of "did the thing the gate cares about actually work."

---

## Acceptance Criteria

- [ ] `scripts/analyze-authoring-reliability.py` parses a bench-run directory's `run-0N.driver.log` files and reports per-sub-run turn counts + restart detection, without modifying `openup-agent-bench.py`
- [ ] Hermetic unit tests cover: a clean run (all sub-runs ≤6 turns, no restart) classified clean; a sub-run exceeding the turn ceiling classified not-clean; a detected restart (repeated first tool call) classified not-clean; a run that never reached any sub-run (e.g. `endpoint-error` on iteration 1) classified not-clean with a clear reason
- [ ] Re-running the analyzer against this session's already-saved T-107 gate-check logs (or a fresh batch, if the owner wants to re-run against the live endpoint) produces a `clean_rate` — recorded, whatever the number is, honestly
- [ ] The result (pass or fail against ≥80%) is recorded in `docs/changes/T-107/design.md`, unblocking (or explicitly re-blocking, if it fails) T-107's promotion gate

---

## Success Measures

We expect this task to produce one honest number: the authoring-chain clean rate across a 5-run batch, measured correctly. Instrumentation: the analyzer's own JSON output. Read-back: immediately — this is the artifact T-107's gate needs to proceed or explicitly stay blocked, not a deferred measure.

---

## Testing Strategy

- Unit: driver-log parsing against small synthetic fixture logs covering the four classification cases above (clean / over-ceiling / restart / never-started)
- Regression: run against this session's real saved bench output (if still present in `.openup/bench/`) as a live sanity check that the parser handles real log format correctly, not just synthetic fixtures

---

## Dependencies

- T-106 (the mechanism being measured — completed)
- T-107's gate references this measurement but is not a dependency in the DAG sense — T-136 doesn't depend on T-107

---

## Key Files

| File | Change |
|------|--------|
| `scripts/analyze-authoring-reliability.py` | New — driver-log parser + authoring-chain-clean classifier |
| `scripts/tests/test_analyze_authoring_reliability.py` | New — unit tests |
| `docs/changes/T-107/design.md` | Record the re-measured result (new file if absent) |

---

## Out of Scope

- Making the driver itself exit 0/`pass` for this scenario — would require the cycle engine to detect Inception's phase-exit criteria are met and route to `milestone-review` after the fixed authoring activities complete, instead of "stuck, awaiting consent." Real gap, confirmed this session, but separate and larger scope than a measurement fix.
- Any change to `openup-agent-bench.py`'s shared `aggregate()`/`OUTCOME_BY_EXIT`/pass definition — used by every scenario; not touched here.
- Re-running a fresh live batch is optional — analyzing this session's already-saved logs may be sufficient if they're still on disk; if not, a fresh run is needed and costs real API credits (small, same as the original T-107 gate check).

---

## Open Questions

1. **Are this session's original bench-run logs still on disk?** ✅ Checked —
   `.openup/bench/t107-gate-nano/run-0{1..5}.driver.log` are all present.
   Resolved: no fresh live run needed; analyze these directly.
2. **What counts as a "restart" precisely, in code?** T-106's own definition ("repeated opener") is prose, not a formal spec. **Assumed: a sub-run's first tool call (name + primary path/command argument) repeating verbatim within the same sub-run's later turns** — the same signal T-098's `OPENUP_AGENT_DEBUG_LOG` design intended to make inspectable. Vetoable at review.

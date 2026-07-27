# T-107 — design notes

## T-106 live-batch gate result (re-measured via T-136, 2026-07-27)

**Gate satisfied: 4/5 = 80% authoring-chain clean rate**, measured against
`.openup/bench/t107-gate-nano/` (5 real runs against `gpt-5.4-nano`,
originally captured 2026-07-26) via `scripts/analyze-authoring-reliability.py`:

```json
{
  "runs": 5,
  "authoring_chain_clean": 4,
  "clean_rate": 0.8
}
```

| run | clean | reason |
|---|---|---|
| run-01 | ✅ | — |
| run-02 | ✅ | — |
| run-03 | ✅ | — |
| run-04 | ❌ | restart: `('glob', 'docs/**/technical-specification*.md')` repeated 12 times consecutively (Plan Iteration sub-run) |
| run-05 | ✅ | — |

### Why this measurement replaces the original bench-harness number

The original batch (this session, 2026-07-26) reported `pass_rate: 0.0`
using `openup-agent-bench.py`'s own `aggregate()`, which requires the
driver subprocess to exit `0`. The `inception-taskdef` scenario runs
`openup-agent.py cycle --procedure next`, which — by design (T-092 recovery
mode) — continues past the fixed Inception authoring activities into a
deterministic consent-gate pause (T-094) that **every** run hits regardless
of model quality, once those activities finish for one iteration. That
pause exits `5` (`suspended`), never `0`, so `pass_rate` structurally reads
0% for this scenario independent of authoring reliability. T-136 built a
separate, purpose-built analyzer that reads the same already-saved driver
logs and measures the thing the gate actually specifies — per-sub-run turn
count and restart detection — instead of the driver's terminal exit code.

### run-04's failure is real, not a rate-limit artifact

Before writing any analysis code, a manual check (`grep -c` for any
repeated tool-call line across all 5 logs) found run-04 has 12 consecutive,
identical `glob docs/**/technical-specification*.md` calls in its final
sub-run ("Plan Iteration") — the model got stuck retrying an unresolvable
input name and never gave up — **before** an unrelated `HTTP 429` rate
limit cut the run off at iteration 25. Runs 1, 2, 3, and 5 have **zero**
repeated tool calls across any sub-run — genuinely clean throughout.

This is a real, separate finding: the "Plan Iteration" task-def's input
resolution doesn't have an alias for "Technical Specification" the way
T-124's fix covered other unresolvable KB workproduct names (e.g.
"Technical Specification" → the architecture notebook). **Not fixed as
part of T-136** (T-136 measures; it doesn't fix the measured bug) — worth
its own small follow-up task extending T-124's `_INPUT_ALIASES` map in
`scripts/openup_agent/plan_iteration.py`, referencing this finding.

### Disposition

**T-107's promotion gate is satisfied** — 80% meets the literal ≥80%
bar, and the one failing run fails for a real, well-understood reason
(an input-alias gap), not noise. T-107 is unblocked to start.

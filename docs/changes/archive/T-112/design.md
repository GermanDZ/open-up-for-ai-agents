# T-112 — Design Notes

## Classification-fidelity check (Requirement 2 / Operations step 5)

Ran `cycle.py`'s real `parse_boxes`/`classify_box` (`scripts/openup_agent/cycle.py`)
against the Operations boxes of 6 archived plans (T-093, T-100, T-104, T-108,
T-109, T-089 — 33 boxes total, spanning prose judgment steps, bare
`` `scripts/<name>.py` `` backtick spans, and full `` `python3 scripts/x.py ...` ``
backtick spans):

```
T-093 (1 box):  1 judgment
T-100 (6 boxes): 4 judgment, 2 script (`scripts/tests/test_openup_process_map.py` bare-span;
                 `python3 scripts/openup-process-map.py ...` full-span)
T-104 (7 boxes): 1 script (`scripts/openup_agent/stamping.py` bare-span), 6 judgment
T-108 (6 boxes): 6 judgment
T-109 (6 boxes): 6 judgment
T-089 (7 boxes): 1 script (`` `cycle` `` backtick skipped — no match; second span
                 `scripts/openup-agent.py` bare-span matches), 6 judgment
```

Cross-checked each result against `docs-eng-process/procedures/openup-cycle.md`'s
written classification rule (step 4.2 of the Process section):

- Prose boxes with no backtick command and no `(auto)` marker → **judgment**.
  Matches all 27 judgment-classified boxes above (e.g. T-093's sole box, T-108's
  and T-109's boxes, which are pure prose/handoff descriptions).
- A bare `` `scripts/<name>.py ...` `` backtick span → **script**
  (implicitly `python3`-prefixed). Matches T-100 box 4
  (`` `scripts/tests/test_openup_process_map.py` ``), T-104 box 1
  (`` `scripts/openup_agent/stamping.py` ``).
- A backtick span starting with `python3 ` → **script**. Matches T-100 box 6
  (`` `python3 scripts/openup-process-map.py ...` ``).
- A body with multiple backtick spans, only one of which qualifies (T-089 box
  4: `` `cycle` `` — no match — followed by `` `scripts/openup-agent.py` `` —
  bare-span match) → **script**, same as `cycle.py`'s scan-in-order behavior.
  The procedure's prose describes *which* span-shapes qualify, not scan order;
  since only the qualifying-vs-not distinction affects the script/judgment
  **classification** (not which substring becomes "the command"), this is not
  a fidelity gap for the purpose this check verifies.

No divergence found between `cycle.py`'s actual classification and the
procedure's written rule across the 33 sampled boxes. The `(auto)`/`(judgment)`
marker paths and the no-backticks `CMD_START_RE` fallback were not exercised by
this sample (no archived plan used them), but their behavior is copied
verbatim from `cycle.py`'s source in the procedure body, not re-derived.

## Requirement grading at completion (step 1a)

Graded against the actual diff (`docs-eng-process/procedures/openup-cycle.md`
+ its generated mirrors, this file, and `plan.md` itself):

- ✅ **Req 1** (route non-pick/resume paths) — `openup-cycle.md` §Process 2
  "Route": prints the `/openup-next` handoff message + `reason`, emits
  `OPENUP-NEXT: DONE — routed to /openup-next (<path>)`, no claim/box attempt.
- ✅ **Req 2** (script/judgment classification) — §Process 4.2 states the rule
  verbatim from `cycle.py`; fidelity checked above against 33 real boxes, zero
  divergence.
- ✅ **Req 3** (gate before tick) — §Process 4 step 4 "Gate before tick" runs
  fence (exit 3 = skip) + check-docs before every tick, stops on a non-skip
  failure with the box left unticked.
- ✅ **Req 4** (claim/completion delegate unchanged) — §Process 3 "Claim"
  `pick` branch calls `/openup-start-iteration` verbatim; §Process 5 "Exit"
  calls `/openup-complete-task` / `/openup-create-handoff` only, no third path.
- ✅ **Req 5** (resumable_input fold) — §Process 3 first bullet: re-runs
  `/openup-create-task-spec`, drops `awaiting-input:`, archives the request,
  before the box loop — matches `/openup-next`'s behavior, explicitly notes
  the divergence from `cycle.py`'s driver-only shortcut.
- ✅ **Req 6** (`/openup-next` untouched) — `git diff harness-optional -- docs-eng-process/procedures/openup-next.md`
  produced no output (checked twice: mid-work and again below).

All 6 requirements ✅. No blockers.

## Success-measure instrumentation grading at completion (step 1b)

Standard track, not `n/a`. First-drafted instrumentation (grep `docs/agent-logs/`
for per-tool-call `read_file` records) was checked against the real log shape
(`docs/agent-logs/runs/2026-07-14-T-112.jsonl`) and found **false** — those
records are session-level events only (`session_begin`, etc.), never
individual tool calls. ❌ on the original draft, fixed by revising the Success
Measures section (this file's plan.md) to point at instrumentation that
genuinely exists in the diff: the procedure's own mandated `## Output` section,
which requires every invocation to report its script-vs-judgment box split.
✅ instrumentation — `docs-eng-process/procedures/openup-cycle.md` §Output,
"how many boxes ran as script steps vs. judgment steps" (present in the diff).
Read-back date: after the 5th real `/openup-cycle` invocation (no fixed
calendar date — usage-triggered).

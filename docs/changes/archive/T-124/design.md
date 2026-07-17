# T-124 — design & completion notes

## Live acceptance (Req 3, the falsifiable gate) — 2026-07-17

Endpoint: `http://192.168.200.142:1234/v1`, model `qwen/qwen3.6-27b-q6k`,
scenario `inception-taskdef` (`command: cycle`). Per-sub-run turn counts read
from `OPENUP_AGENT_DEBUG_LOG`.

**Before** (`.openup/bench/t107-smoke`, pre-fix):

| Sub-run | Turns | Notes |
|---|---|---|
| develop-technical-vision | 4 | ✓ |
| author-initial-roadmap | 3 | ✓ |
| envision-the-architecture | 9 | over ≤6 |
| identify-and-outline-requirements (use-case) | **28+** | **TIMEOUT** — 5× input re-reads, 4× post-write re-reads of UC-001.md, no sentinel |

**After** (`.openup/bench/t124-after3`, this fix):

| Sub-run | Turns | writes | reads | globs | post-write re-reads | DONE |
|---|---|---|---|---|---|---|
| objectives | 2 | 1 | 0 | 0 | — | ✓ |
| develop-technical-vision | 3 | 1 | 1 | 0 | — | ✓ |
| author-initial-roadmap | 3 | 1 | 1 | 0 | — | ✓ |
| envision-the-architecture | **4** | 1 | 1 | 0 | — | ✓ |
| **identify-and-outline-requirements (use-case)** | **6** | 1 | **0** | **0** | **0** | ✓ |

Every sub-run ≤6 turns. The use-case sub-run — the T-107-gate blocker — needed
**zero** reads/globs (F1 pre-packed Vision + Architecture Notebook, so no hunt)
and **zero** post-write re-reads (F2's single-write / emit-DONE contract), writing
`UC-001.md` once and emitting `OPENUP-TASK: DONE`. The two pre-fix failure modes
are both eliminated. (The bench process was externally killed on the 6th activity,
`plan-manage-iteration`, turn 1 — orthogonal to the fix; the acceptance criterion
is the use-case sub-run's convergence, fully captured above.)

## Implementation-vs-spec grade (complete-task step 1a)

- ✅ **Req 1** (alias resolves non-resolving KB inputs) — `_INPUT_ALIASES` +
  `render_task_instruction`; hermetic `test_task_instruction_aliases_nonresolving_input`
  (+ absent-target-degrades, direct-resolve-unchanged); verified against the real
  library (use-case def inlines actual vision+architecture); live: use-case reads=0.
- ✅ **Req 2** (convergence contract) — `cycle._task_system_prompt` carries the
  four clauses; `test_task_system_prompt_carries_convergence_contract`; live:
  0 post-write re-reads across all sub-runs.
- ✅ **Req 3** (live acceptance) — use-case 28+→6 turns, DONE emitted, no re-read
  (table above).

No ❌.

## Success-measure instrumentation (step 1b)

Instrument = the live bench driver log / `OPENUP_AGENT_DEBUG_LOG` (pre-existing,
T-098). ✅ read-back recorded above: use-case sub-run iteration count 28+ → 6,
0 read_file against its own output_path after the write. before=`t107-smoke`,
after=`t124-after3`.

## Notes

- Every Inception sub-run now converges ≤6 turns on the weak model, which strongly
  indicates the T-107 promotion gate's "≤6 iters/sub-run" + "zero restarts"
  criteria are met on the cycle path; the gate's "≥80% clean-pass over 5 runs"
  needs a stable endpoint for a full 5-run batch (T-107 owner decision, separate
  from this fix). The endpoint was intermittently unreachable during acceptance
  (LM Studio restarts); the convergence data was captured across partial runs.
- F1 is render-time (an alias table), not a `task-library.yaml` edit — the
  compiled library stays in sync (`build-task-library.py --check` green).

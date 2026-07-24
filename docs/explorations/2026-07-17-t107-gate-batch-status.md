# T-107 promotion-gate batch — status & resume (paused 2026-07-17)

**Status:** PAUSED — the T-124 fix is validated; the 5-run gate batch is blocked
purely on **LM Studio endpoint stability + model speed** (framework-external).
Resume when the endpoint can stay up ~55 min/run.

## What is complete (all merged into `harness-optional`)

- **T-122** (process-gate fixes B8/B9) — `completed (2026-07-16)`.
- **T-123** (dirty-aware gating E2) — `completed (2026-07-16)`. Closes the
  Cycle orchestration economics program (T-120→T-123).
- **T-124** (task-def convergence on the weak model) — `completed (2026-07-17)`.
  Unblocks the T-107 gate. F1: `plan_iteration._INPUT_ALIASES` aliases a
  non-resolving KB input name (`Technical Specification`) → real upstream
  artifacts (Vision + Architecture Notebook), inlined at render time. F2:
  `cycle._task_system_prompt` convergence contract (single write, no
  verify-reread, no input re-read, emit `OPENUP-TASK: DONE` immediately).

## The T-107 gate (from `docs/changes/T-107/plan.md`)

T-107 is `status: proposed` behind a promotion gate: T-106's behavioral
acceptance must pass on the owner's live qwen batch —
**zero mid-run restarts · ≤6 iterations per sub-run · ≥80% clean-pass over 5
runs · per-sub-run context ≤⅓ of the 2026-07-14 baseline** — read from
`scripts/bench-scenarios/inception-taskdef` (`command: cycle`) +
`OPENUP_AGENT_USAGE_LOG` / `OPENUP_AGENT_DEBUG_LOG`.

## What the live runs established (fix works)

Across every attempt that reached the model, **all Inception sub-runs converge**
(≤6 turns, `OPENUP-TASK: DONE`, zero restarts):

| Sub-run | Pre-T-124 | Post-T-124 (live) |
|---|---|---|
| objectives | 2 | 2 |
| develop-technical-vision | 4 | 3 |
| author-initial-roadmap | 3 | 3 |
| envision-the-architecture | 9 | 4 |
| identify-and-outline-requirements (use-case) | 28+ → timeout | **6** · 0 reads · 0 globs · 0 post-write re-reads |

So the gate's per-sub-run (≤6) + zero-restart criteria are effectively met on
the cycle path. **What remains is ≥80% clean-pass over 5 FULL runs.**

## The blocker (framework-external)

1. **Model id:** the env value `OPENUP_MODEL_MAIN=qwen/qwen/qwen3.6-27b-q6k` is
   **INVALID** — LM Studio returns HTTP 400 "Invalid model identifier". Use the
   id the endpoint actually lists: **`qwen/qwen3.6-27b`** (from `GET /v1/models`).
   (`qwen/qwen3.6-27b@q6_k` also valid.)
2. **Model speed:** ~140 s/call on the dense 27b → a full 6-activity Inception
   cycle is ~19–22 calls ≈ **~55 min**. `qwen3.6-35b-a3b` was tested and is
   *slower* (50 s vs 32 s for 400 tok), so it is not a faster substitute.
3. **Endpoint stability:** `192.168.200.142:1234` flaps up/down every few
   minutes (connection times out, `[Errno 60]`). No run held a stable 55-min
   window, so each attempt fast-failed on call 1 or was cut off partway.
4. **Sandbox note:** long Claude-Code **background** jobs may also be reaped;
   one run did survive 45 min (hit the bench `--timeout`, not a reap), so the
   reap ceiling is ≳45 min — but 5×55 min ≈ 4.5 h is unrealistic to babysit here.

### Run-1 attempt log (2026-07-17)

| Attempt | Result | Cause |
|---|---|---|
| 1 | fast-fail, 0 iters | HTTP 400 — invalid model id (fixed → `qwen/qwen3.6-27b`) |
| 2 | 45 min, all sub-runs ≤6 + DONE, 6th activity unfinished | model slow; 45-min `--timeout` too short |
| 3 | fast-fail, 0 iters | endpoint dropped on call 1 |

0 / 5 clean runs banked. Evidence dirs (gitignored, Ring-3):
`.openup/bench/t107-r1` (+ `-debug.jsonl`), `.openup/bench/t107-smoke`,
`.openup/bench/t124-after3-debug.jsonl` (the decisive post-fix convergence).

## To resume

**First, stabilize LM Studio** on `192.168.200.142`: load `qwen3.6-27b`
explicitly, disable idle/auto-unload (TTL / "keep model in memory"), and keep
the machine awake for the batch duration.

**Then run the 5-run batch** — best in a plain terminal (unreaped), overnight:

```bash
cd /Users/germandz/personal-code/ai-dev-framework/open-up-for-ai-agents
LLM_API_URL='http://192.168.200.142:1234/v1' \
LLM_API_KEY='<key>' \
OPENUP_MODEL_MAIN='qwen/qwen3.6-27b' \
OPENUP_MODEL_MID='qwen/qwen3.6-27b' \
OPENUP_MODEL_SMALL='qwen/qwen3.6-27b' \
OPENUP_AGENT_TIMEOUT=900 \
OPENUP_AGENT_DEBUG_LOG="$PWD/.openup/bench/t107-gate-debug.jsonl" \
python3 scripts/openup-agent-bench.py \
  --scenario scripts/bench-scenarios/inception-taskdef --runs 5 --command cycle \
  --out .openup/bench/t107-gate --max-iterations 12 --timeout 5400 --keep
cat .openup/bench/t107-gate/summary.md
```

**Then evaluate the gate** from `.openup/bench/t107-gate/summary.md`
(pass rate ≥80% = ≥4/5 clean-pass) + per-sub-run turns from the debug log
(all ≤6, zero restarts). Note: the driver runs `temperature=0`, so the 5 runs
vary mainly by endpoint timing, not sampling — the ≥80% metric is really a
"full cycle completes cleanly, repeatedly" check.

**If it passes → start T-107** (`/openup-start-iteration task_id: T-107` — its
Operations box 1 is "record the passing batch result in `design.md`"): full-KB
compile, `openup-doctor --check` wiring, KB re-distill runbook, project-custom
process sources. **If a run regresses → the fix routes to the T-106/T-119/T-124
def layer, not T-107** (per the gate).

## Pointers

- Fix detail: `docs/changes/archive/T-124/{plan,design}.md`.
- Gate spec: `docs/changes/T-107/plan.md`.
- Memory: `project_lean_authoring_program` (T-124 + endpoint findings),
  `project_cycle_orchestration_economics_program`.

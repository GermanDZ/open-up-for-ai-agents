---
id: T-098
title: Deterministic Inception-bootstrap fast-path + LLM transcript debug log
status: done
priority: high   # critical | high | medium | low
estimate: 1 session
plan: docs/changes/archive/T-096/plan.md
depends-on: [T-096, T-097]
blocks: []
touches:
  - scripts/openup_agent/navigator.py
  - scripts/openup_agent/loop.py
  - scripts/tests/test_openup_agent_navigator.py
  - scripts/tests/test_openup_agent.py
  - docs-eng-process/reference-driver.md
  - docs-eng-process/script-cli-reference.md
last-synced: ""
---

# T-098 — Bootstrap fast-path (don't depend on a weak model to navigate) + LLM debug log

## Story

> **As an** operator running `./scripts/next-cycle` on a fresh project with a weak
>   local model,
> **I want** the unambiguous Inception bootstrap (no vision → get a brief → author
>   the vision) to run **deterministically**, and a way to **record every LLM
>   interaction**,
> **So that** a fresh project converges even when the model fails to emit the
>   navigator's decision file, and I can *see* exactly what the model did when it
>   misbehaves.

INVEST — ✅ Independent (navigator + a log hook) · ✅ Negotiable (fast-path gating, log fields) · ✅ Valuable (fixes a live non-converging loop + adds diagnosis) · ✅ Estimable · ✅ Small · ✅ Testable (hermetic seams)

## Analysis Context

- **The bug (live, my-product / qwen local model, 2026-07-13).** On a fresh
  project the navigator sub-run "completed on iteration 2; gates clean" but **wrote
  no `.openup/navigator-decision.json`**, so the driver exited 8 ("no valid
  decision file — cannot navigate"). Earlier runs *did* write it — the weak model
  is **inconsistent at the write-a-decision-file contract**. Making a fresh
  project's navigation depend on that is fragile.
- **The fresh-Inception bootstrap is unambiguous** and needs no navigator LLM:
  (a) no vision + no filled brief → the human must provide a **stakeholder brief**
  (scaffold it, T-097); (b) filled brief + no vision → **author the vision**
  (`openup-create-vision`, which the model does reliably — the T-080 finding is
  that models *author* fine and only drown in *orchestration*). Only genuinely
  ambiguous states (a vision already exists but the loop is stuck) need the LLM
  navigator.
- **Debug log.** Today `OPENUP_AGENT_USAGE_LOG` records per-call *metadata*
  (iteration, model, latency, token usage) — not content. A transcript log behind
  `OPENUP_AGENT_DEBUG_LOG` recording the **request messages + raw response
  (content, tool calls, finish reason)** makes weak-model behavior inspectable
  (e.g. *why* qwen skipped `write_file`). One hook in the loop, mirroring
  `_append_usage`; opt-in, zero default behavior change.
- **Scope boundaries.** Navigator fast-path + one loop log hook. Does not change
  the deterministic engine, resolve, assess/milestone/plan-iteration, or the LLM
  client's request path.
- **Definition of done.** A fresh project (`phase: inception`, no vision) converges
  through `cycle` **without a navigator LLM call**: no brief → scaffold; filled
  brief → run `openup-create-vision`. With `OPENUP_AGENT_DEBUG_LOG` set, every LLM
  interaction is one JSONL record; unset ⇒ byte-for-byte unchanged.

> **Assumption:** the fast-path fires only when `phase` is `inception` and no
> `docs/vision.md` exists; once a vision exists the LLM navigator handles the
> (now ambiguous) state. *(Vetoable at review.)*
> **Assumption:** `create-vision` is run only if it is in the FACTS' procedures
> index; otherwise fall through to the LLM navigator. *(Vetoable.)*

## Requirements

1. **A fresh pre-vision project scaffolds the brief with no navigator LLM call.**
   - **Given** `phase: inception`, no `docs/vision.md`, no filled
     `docs/inputs/stakeholder-brief.md`, **When** the navigator runs, **Then** it
     scaffolds the brief template and suspends (exit 5) **without** dispatching a
     navigator sub-run.

2. **A filled brief with no vision runs create-vision deterministically.**
   - **Given** `phase: inception`, a **filled** brief (no marker), no vision, and
     `openup-create-vision` in the procedures index, **When** the navigator runs,
     **Then** it runs `openup-create-vision` (via `run_procedure`) with a standard
     read-the-brief instruction and **dispatches no navigator decision sub-run**.

3. **A non-bootstrap state still uses the LLM navigator.**
   - **Given** a `docs/vision.md` already exists (state is no longer the
     unambiguous bootstrap), **When** the navigator runs, **Then** the LLM
     navigator sub-run is dispatched as before.

4. **The bootstrap never fires for a non-inception phase or a missing procedure.**
   - **Given** `phase: construction` (or `create-vision` absent from the index),
     **When** the navigator runs, **Then** the fast-path does not fire (it falls
     through to the LLM navigator).

5. **`OPENUP_AGENT_DEBUG_LOG` records each LLM interaction; unset changes nothing.**
   - **Given** `OPENUP_AGENT_DEBUG_LOG=<path>`, **When** a `loop.run` LLM call
     completes, **Then** one JSONL record is appended with `iteration`, `model`,
     the request `messages`, and the `response` (content, tool_calls,
     finish_reason).
   - **Given** the var is unset, **When** a run executes, **Then** no debug file is
     written and the run is byte-for-byte unchanged.

## Behavior Delta

Ring-1 truth for the driver lives in `docs-eng-process/`.

**Added:**
- A deterministic Inception-bootstrap fast-path in the navigator (scaffold brief /
  run create-vision) that bypasses the navigator LLM for the unambiguous case.
- An opt-in LLM transcript log (`OPENUP_AGENT_DEBUG_LOG`).

**Modified:**
- The navigator's behavior on a fresh project —
  `docs-eng-process/reference-driver.md`: the bootstrap is deterministic; the LLM
  navigator handles only ambiguous states.
- `docs-eng-process/script-cli-reference.md` — the new env var.

**Removed:** the fresh-project dependency on the navigator LLM emitting a decision
file (the failure mode that exited 8).

## Entities

- **navigator** (modified) — `scripts/openup_agent/navigator.py`
  (`VISION_INSTRUCTION`, `_bootstrap_step`, `run_navigator` fast-path)
- **loop** (modified) — `scripts/openup_agent/loop.py` (`_append_debug` +
  `OPENUP_AGENT_DEBUG_LOG` hook, mirroring `_append_usage`)

## Approach

In `run_navigator`, after building the FACTS and before dispatching the LLM
sub-run, consult `_bootstrap_step(root, facts)`: for an inception phase with no
vision it returns `("scaffold", brief_path)` (no brief) or `("procedure",
"openup-create-vision", VISION_INSTRUCTION)` (filled brief) — the driver acts
deterministically and returns; otherwise the existing LLM navigator path runs. In
`loop.run`, read `OPENUP_AGENT_DEBUG_LOG` next to `OPENUP_AGENT_USAGE_LOG` and, when
set, append a full-interaction record right after each `complete(messages)` — a
snapshot of the request messages plus the response's content/tool_calls/
finish_reason. Both additions are opt-in / behavior-preserving when their trigger
(inception-no-vision / env var) is absent.

## Structure

**Modify:**
- `scripts/openup_agent/navigator.py` — `VISION_INSTRUCTION`, `_bootstrap_step`,
  the fast-path branch in `run_navigator`.
- `scripts/openup_agent/loop.py` — `_append_debug` + the `OPENUP_AGENT_DEBUG_LOG`
  call site.
- `scripts/tests/test_openup_agent_navigator.py` — fast-path tests (scaffold /
  create-vision / defers-when-vision-exists / not-for-construction).
- `scripts/tests/test_openup_agent.py` — debug-log records a completion; unset
  writes nothing.
- `docs-eng-process/reference-driver.md`, `script-cli-reference.md` — the
  fast-path + the env var.

**Do not touch:**
- The deterministic engine / resolve / assess / milestone / plan-iteration.
- The LLM client request path (`llm.chat_completion`) — the log reads the response,
  it does not alter the call.

## Operations

- [x] Add `VISION_INSTRUCTION` + `_bootstrap_step(root, facts)` to `navigator.py`
  and wire the fast-path into `run_navigator` before the LLM sub-run (scaffold /
  run create-vision; else defer to the LLM navigator).
- [x] Add `_append_debug` + the `OPENUP_AGENT_DEBUG_LOG` hook to `loop.run`
  (mirroring `_append_usage`; snapshot request messages + response).
- [x] (tester) Navigator fast-path tests + a debug-log test (set → one record;
  unset → no file, behavior unchanged).
- [x] Update `reference-driver.md` (navigator fast-path) + `script-cli-reference.md`
  (`OPENUP_AGENT_DEBUG_LOG`).
- [x] (tester) Full driver+navigator suite green; `check-docs`,
  `openup-spec-scenarios`, `openup-fence.py check --base harness-optional` green.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format
- `docs-eng-process/reference-driver.md` — driver contract; the `OPENUP_AGENT_USAGE_LOG`
  precedent this log mirrors
- `docs/changes/archive/T-096/plan.md`, `docs/changes/archive/T-097/plan.md` — the
  navigator design this hardens

## Safeguards

- **Reversibility.** Both additions are opt-in-by-condition; the LLM navigator
  path is unchanged for non-bootstrap states. The debug log is env-gated and never
  alters the request.
- **Convergence guarantee.** The fresh-Inception bootstrap no longer depends on the
  model writing a decision file — it is code.
- **No-go zones.** No change to the engine, resolve, other decision paths, or the
  LLM request. Instrumentation failures are swallowed (never break a run).
- **Stdlib-only.**

## Success Measures

n/a — internal tooling / robustness + diagnostics. Falsifiable acceptance = the
hermetic tests (Req 1–5). Live confirmation is the owner re-running `next-cycle` on
my-product after re-sync (fresh project converges; `OPENUP_AGENT_DEBUG_LOG`
captures the transcript).

## Rollout

`n/a — not user-facing`: reference-driver developer tooling; env-gated, no flag.
Backout is a version pin.

## Verification

- `python3 -m pytest scripts/tests/test_openup_agent_navigator.py
  scripts/tests/test_openup_agent.py -q` — green.
- Scripted fresh project: no-vision-no-brief → scaffold (no sub-run dispatched);
  filled-brief-no-vision → create-vision run; vision-exists → LLM navigator.
- `OPENUP_AGENT_DEBUG_LOG=/tmp/x.jsonl` on a scripted run → one record per call
  with request+response; unset → no file.
- `openup-spec-scenarios.py check docs/changes/T-098/plan.md` → 0; `check-docs.py`
  → 0; `openup-fence.py check --base harness-optional` → clean.

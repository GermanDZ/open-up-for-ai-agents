---
id: T-109
title: Narrated console output — say what the loop is doing, drop the noise
status: done
priority: high   # critical | high | medium | low
estimate: 1 session
plan: docs/roadmap.md#planned-driver-delivery-trail--console-narration-t-108-t-109
depends-on: []
blocks: []
touches:
  - scripts/openup_agent/loop.py
  - scripts/openup_agent/cycle.py
  - scripts/openup_agent/plan_iteration.py
  - scripts/tests/test_openup_agent.py
  - scripts/tests/test_openup_agent_cycle.py
  - scripts/next-cycle
  - scripts/tests/test_next_cycle.py
  - docs-eng-process/reference-driver.md
last-synced: ""
---

# T-109 — Narrated console output

## Story

> **As** a practitioner watching `./scripts/next-cycle`,
> **I want** the console to narrate what the loop is doing and how — which
>   activity, which file each tool touched, progress against the iteration
>   cap, and a closing summary of what was produced —
> **So that** I can follow (and trust) an autonomous run without reading
>   JSONL debug logs; today's output is blank-line spam, `tool read_file ->
>   5706 chars` lines that name no file, and truncated instruction dumps.

INVEST — ✅ Independent (presentation layer) · ✅ Negotiable (exact wording) ·
✅ Valuable (usability of the one human surface) · ✅ Estimable · ✅ Small
(print sites only) · ✅ Testable (captured-stderr assertions)

## Analysis Context

- **Domain.** The driver's console narration: `loop.py` `_log` lines (tool
  dispatch, iteration events), `cycle.py` step headers (`judgment step (…):
  <200 chars of instruction>`), and `next-cycle`'s exit-code guidance.
  Observed live (my-product, 2026-07-14): runs of blank lines between tool
  batches, tool lines showing only result char-counts, and instruction dumps
  truncated mid-word.
- **The stdout contract is load-bearing.** The cycle's **stdout sentinel**
  (`OPENUP-NEXT: …`, byte-exact pass-through in `next-cycle`) is consumed by
  outer loops — narration must stay on **stderr** (where `_log` already
  writes) and the stdout contract must not change by a single byte.
- **Scope boundaries.** No new information is computed — this presents what
  the engine already knows. No TTY colors/spinners (plain lines; logs are
  piped). The debug/usage JSONL logs are untouched.
- **Definition of done.** A fresh-project run reads as a narrative: one header
  per sub-run naming the activity and its purpose, one line per tool call
  naming the operation target, iteration progress, no blank lines, and a
  cycle-end summary naming produced artifacts + commits + the next step.

> **Assumption:** default output is the new narrated form;
> `OPENUP_AGENT_VERBOSE=1` adds the old detail (result char counts, full
> instruction text) rather than a flag to *enable* readability. *(Vetoable.)*

> **Assumption:** the blank lines come from streamed/empty assistant content
> echoes; whatever the source, the acceptance is "no blank lines" — fix at
> the print site. *(Vetoable.)*

## Requirements

1. **Tool lines name their target, not a char count.**
   - **Given** a sub-run calls `read_file`/`write_file`/`edit_file`/`glob`/
     `exec` **When** the call is logged **Then** the line shows the operation
     and its path/pattern/command (truncated ~60 chars), e.g.
     `read docs/vision.md`, `write docs/roadmap.md`, `exec: git status` —
     with result size only under `OPENUP_AGENT_VERBOSE=1`.

2. **No blank lines on the console.**
   - **Given** any cycle run **When** stderr/stdout are captured **Then** no
     empty lines are emitted between events.

3. **Sub-run headers narrate intent and progress.**
   - **Given** a sub-run starts **When** the header is logged **Then** it
     names the purpose (activity/lane + skill + role hat) in one line, and
     each LLM turn logs `iteration k/cap` — replacing the raw 200-char
     instruction dump (full instruction only under `OPENUP_AGENT_VERBOSE=1`).

4. **The cycle ends with a summary.**
   - **Given** a cycle completes on any path **When** the final sentinel is
     printed **Then** stderr carries a short summary block: artifacts
     produced/changed (with stamped ids), commits made, gates result, and the
     next step in plain words.

5. **The stdout sentinel contract is byte-identical.**
   - **Given** the pre-existing sentinel tests and `next-cycle` pass-through
     **When** the suite runs **Then** every existing stdout assertion passes
     unchanged (narration lives on stderr only).

## Behavior Delta

Ring-1 truth for the driver lives in `docs-eng-process/`.

**Modified:**
- Console narration format (stderr) — `docs-eng-process/reference-driver.md`
  §output; `next-cycle` guidance unchanged in role, wording aligned.

**Added:**
- `OPENUP_AGENT_VERBOSE=1` detail switch — `reference-driver.md` §configuration.

**Removed:**
- Char-count tool lines, blank-line echoes, truncated instruction dumps
  (default mode) — `reference-driver.md` §output.

## Entities

- **loop._log / tool dispatch** (modified) — `scripts/openup_agent/loop.py`
- **cycle step headers + summary** (modified) — `scripts/openup_agent/cycle.py`
- **plan_iteration narration** (modified) — activity start/done lines
- **next-cycle** (read-mostly) — keeps exit-code guidance; no stdout change

## Approach

Present what the engine already knows, at the existing print sites. `loop.py`:
log the tool's salient argument at dispatch (it has `args` in hand), add
`iteration k/cap` to the turn log, and guard empty content echoes. `cycle.py`:
replace the instruction dump in step headers with the lane/activity + hat line
it already receives, and emit a stderr summary before returning (artifacts from
the stamp result + commit messages it made + the decision's next step).
`OPENUP_AGENT_VERBOSE=1` re-enables the old counts/dumps. All narration stays
on stderr; stdout is only the sentinel, unchanged.

## Structure

**Modify:**
- `scripts/openup_agent/loop.py` — tool-line format, progress, blank-line guard,
  verbose switch.
- `scripts/openup_agent/cycle.py` — step headers, cycle-end summary.
- `scripts/openup_agent/plan_iteration.py` — activity narration lines (wording only).
- `scripts/next-cycle` — align guidance wording (no stdout change).
- `scripts/tests/test_openup_agent.py`, `test_openup_agent_cycle.py`,
  `test_next_cycle.py` — narration assertions; existing sentinel tests untouched.
- `docs-eng-process/reference-driver.md` — §output.

**Do not touch:**
- The stdout sentinel strings and exit codes (outer-loop contract).
- `OPENUP_AGENT_DEBUG_LOG` / `OPENUP_AGENT_USAGE_LOG` (JSONL telemetry).

## Operations

- [x] `loop.py`: tool lines name operation + target (verbose keeps counts);
  add `iteration k/cap`; eliminate blank-line output.
- [x] `cycle.py`: step headers name lane/activity + role hat (drop the raw
  instruction dump; verbose restores it); add the cycle-end stderr summary
  (artifacts, commits, gates, next step).
- [x] `plan_iteration.py`: align activity start/done narration wording.
- [x] (tester) Narration tests: tool-target lines, no blank lines, header
  format, summary present on advanced + failed exits, verbose switch; assert
  every existing stdout sentinel test still passes unchanged.
- [x] Update `reference-driver.md` §output + `next-cycle` wording.
- [x] (tester) Full driver suite green; spec-scenarios, check-docs, fence
  (`--base harness-optional`) green.

## Norms

Inherits from:
- `docs-eng-process/conventions.md`
- `docs-eng-process/reference-driver.md` — the stdout/exit-code contract

## Safeguards

- **stdout is sacred**: sentinel strings + exit codes byte-identical; narration
  on stderr only. Any test asserting stdout must pass without edits.
- **No new dependencies, no TTY control codes** (plain lines; output is piped
  and logged).
- **Token budget**: narration adds no LLM calls and no per-call payload.
- **Reversibility.** Print-site changes only; git-revertible.

## Success Measures

We expect a practitioner to answer "what is it doing right now?" from the last
3 console lines alone — checked qualitatively on the next my-product live run
(the T-106 acceptance batch): the run transcript must name, for every sub-run,
the activity, the files touched, and the closing summary. Instrumentation: the
captured console transcript of that run. Read-back: at the T-106 gate.

## Rollout

`n/a — not user-facing beyond the console`: no flag (default-on narration;
`OPENUP_AGENT_VERBOSE=1` for detail); backout is a version pin.

## Verification

- Hermetic: captured-stderr tests for tool-target lines, no blank lines,
  header format, and the cycle-end summary on both a successful and a failing
  cycle; verbose switch restores counts.
- Existing stdout sentinel tests pass with zero edits (the contract check).
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-109/plan.md` → 0;
  `check-docs.py` → 0; fence `--base harness-optional` → clean.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

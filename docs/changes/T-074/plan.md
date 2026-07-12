---
id: T-074
title: Human-in-the-loop input handling in the reference driver
status: ready   # proposed → ready → in-progress → done → verified
priority: high
estimate: 1–2 sessions
plan: docs/plans/2026-06-10-process-v2-claude-code-harness.md   # program block: "Planned: Harness-optional OpenUP core"
depends-on: [T-072]
blocks: [T-073]
touches:
  - scripts/openup_agent/
  - scripts/openup-agent.py
  - scripts/openup-input.py
  - scripts/tests/test_openup_agent.py
  - scripts/tests/test_openup_agent_tools.py
  - scripts/tests/test_openup_input_request.py
  - docs-eng-process/reference-driver.md
  - docs/changes/T-074/
last-synced: ""
---

# T-074 — Human-in-the-loop input handling in the reference driver

## Story

> **As a** practitioner driving OpenUP on a local model with the reference driver
> **I want** the driver to surface a blocking question to me and either wait for my
> answer or suspend the lane cleanly for async resolution
> **So that** I can run realistic procedures that legitimately need a human decision —
> not just ones that never ask — without the process losing its safety.

INVEST check: ✅ Independent (T-072 landed) · ✅ Negotiable (tool vs gate mechanism) · ✅ Valuable (unblocks real procedures + is T-073's precondition) · ✅ Estimable (1–2 sessions) · ✅ Small (one tool + one subcommand + loop branch) · ✅ Testable (round-trip + suspend/resume, hermetic).

## Analysis Context

- **Domain.** The T-072 reference driver auto-proceeds and has no way to ask a human
  (DD6). OpenUP already has an **async input-request** flow: a request doc under
  `docs/input-requests/` + an `awaiting-input:` line in the lane's
  `docs/changes/<task>/plan.md` marks it `suspended` (never pickable); when the request
  goes `pending → answered`, `openup-input.py resumable` + `/openup-next` step 0 resume
  it. The **resume half is already harness-agnostic Python**; only *creation* is
  Claude-skill-only today (`/openup-request-input`). This task closes that gap and wires
  it into the driver.
- **Scope boundaries.** ONLY the driver's question path + a deterministic creator. Does
  NOT: change the resume path (`openup-input.py resumable` stays as-is); change the
  Claude `/openup-request-input` skill; build the T-073 service; add plan-mode
  interactive approval beyond reusing the same flag (noted, not required).
- **Definition of done.** The model can call a 7th tool `ask_user`; with `--interactive`
  the driver prompts on the TTY and returns the answer to the loop; without it (default)
  the driver creates a well-formed input-request, sets `awaiting-input` on the active
  lane, and terminates with a distinct **suspend sentinel + exit code**. A request the
  driver created is resumable by the unchanged `openup-input.py resumable` path.

> **Assumption:** Creation is a new deterministic `openup-input.py request` subcommand
> (writes the doc + sets `awaiting-input`), so both the driver *and* any harness can
> create requests without the Claude skill; the driver invokes it via its allowlisted
> `exec`. *(Vetoable — alternative: driver writes the doc inline.)*
> **Assumption:** The active lane's `task_id` comes from `.openup/state.json` under
> `--dir`; if absent, the request is still created but no lane is suspended. *(Vetoable.)*
> **Assumption:** Suspend sentinel is `OPENUP-AGENT: SUSPENDED — <request-path>`, exit
> code **5** (distinct from 0/2/3/4). *(Vetoable.)*
> **Assumption:** The same `--interactive` flag will later also govern plan-gate
> approval; T-074 wires it for `ask_user` only and leaves a hook. *(Vetoable.)*

## Requirements

1. The driver advertises a 7th tool `ask_user(question, options?)` (OpenAI function def)
   and dispatches it; the six existing tools are unchanged.
   - **Given** the tool set **When** the driver starts **Then** `ask_user` is present and
     `TOOL_NAMES` has 7 entries, all covered by `TOOL_DEFS`.

2. **Interactive mode** (`--interactive`): `ask_user` prompts on the controlling TTY,
   blocks for a line of input, and returns it to the loop as the tool result.
   - **Given** `--interactive` and a scripted stdin answer "yes" **When** the model calls
     `ask_user("Proceed?")` **Then** the tool result contains "yes" and the loop continues.

3. **Async mode** (default, non-interactive): `ask_user` creates an input-request doc,
   sets `awaiting-input` on the active lane, and the driver terminates with the suspend
   sentinel on stdout and exit code 5 — no further model turns.
   - **Given** no `--interactive` and `.openup/state.json` with `task_id: T-XXX` **When**
     the model calls `ask_user("Which DB?", options=["pg","mysql"])` **Then** a file
     appears under `docs/input-requests/`, the lane's `plan.md` gains
     `awaiting-input: <that file>`, stdout ends with `OPENUP-AGENT: SUSPENDED — <path>`,
     and the process exits 5.

4. A new deterministic `openup-input.py request` subcommand creates a well-formed
   input-request (frontmatter `status: pending` + a Questions section with an `**Answer**:`
   placeholder) and, when `--task-id` is given and its change folder exists, adds the
   `awaiting-input:` line to that lane's `plan.md`.
   - **Given** `openup-input.py request --task-id T-9 --title "t" --question "q?"` in a
     repo with `docs/changes/T-9/plan.md` **When** it runs **Then** the request file
     exists with `status: pending`, and `T-9/plan.md` frontmatter contains
     `awaiting-input:` pointing at it.
   - **Given** no `--task-id` **When** it runs **Then** the request is created and no
     `plan.md` is modified.

5. Round-trip interop: a request the driver created, once its `status` is set to
   `answered`, is reported by the **unchanged** `openup-input.py resumable` as resumable
   for its lane.
   - **Given** a driver-created request for T-9 flipped to `answered` **When**
     `openup-input.py resumable --json` runs **Then** T-9 appears with the request path.

## Behavior Delta

**Added:**
- `ask_user` tool (7th) in the reference driver, with interactive + async modes.
- Suspend sentinel `OPENUP-AGENT: SUSPENDED — <path>` + exit code 5.
- `openup-input.py request` — deterministic input-request creator (+ optional lane suspend).

**Modified:**
- `scripts/openup_agent/loop.py`, `tools.py`, `scripts/openup-agent.py` — internal driver
  tooling (T-072 surface); add the tool, the mode branch, and the `--interactive` flag. Not a Ring-1 artifact.
- `docs-eng-process/reference-driver.md` (Ring-2 reference doc) — document `ask_user` + `--interactive`.

**Removed:** none.

> The existing async-input contract (`docs-eng-process/sops/async-input.md`, board
> `suspended` state, `openup-input.py resumable`) is **reused unchanged** — no Ring-1
> behavior is modified; the driver becomes a new *producer* of requests the existing
> consumer already handles.

## Entities

- **`ask_user` tool** (new) — `scripts/openup_agent/tools.py` + `TOOL_DEFS`
- **Loop question handling** (modified) — `scripts/openup_agent/loop.py`
- **Driver CLI** (modified) — `scripts/openup-agent.py` (`--interactive`)
- **Request creator** (new subcommand) — `scripts/openup-input.py request`
- **Input-request doc** (produced) — `docs/input-requests/<date>-<topic>.md`
- **Lane plan** (coordination-frontmatter edit) — `docs/changes/<task>/plan.md` `awaiting-input:`
- **Resume path** (read-only, reused) — `scripts/openup-input.py resumable`

## Approach

Add `ask_user` as the 7th tool. In `loop.py`, dispatch it specially: in interactive mode
read a line from stdin and hand it back as the tool result (the model continues); in async
mode call `openup-input.py request` (via the driver, using the active `task_id` from
`.openup/state.json`) to create the doc + suspend the lane, then stop the loop, print the
suspend sentinel, and return exit 5. The deterministic creator lives in `openup-input.py`
so creation is harness-agnostic and unit-testable, and the driver stays thin. The resume
side is untouched — a driver-created request rejoins the existing `resumable` → `/openup-next`
flow, proving producer/consumer interop.

## Structure

**Add:**
- `scripts/tests/test_openup_input_request.py` — unit tests for the `request` subcommand (+ lane suspend, + resumable round-trip).

**Modify:**
- `scripts/openup_agent/tools.py` — add `ask_user` to `TOOL_NAMES` + `TOOL_DEFS`; the tool body is loop-driven (interactive read / async create), so `Tools` exposes a hook the loop supplies.
- `scripts/openup_agent/loop.py` — mode branch on `ask_user`; suspend sentinel + exit 5; read active `task_id` from `.openup/state.json`.
- `scripts/openup-agent.py` — `--interactive` flag threaded into `loop.run`.
- `scripts/openup-input.py` — new `request` subcommand (create doc + optional `awaiting-input`).
- `scripts/tests/test_openup_agent.py` + `test_openup_agent_tools.py` — cover interactive answer + async suspend.
- `docs-eng-process/reference-driver.md` — document `ask_user`, `--interactive`, the suspend sentinel/exit 5, and the resume story.

**Do not touch:**
- `scripts/openup-input.py` `resumable`/`list` logic — reused as-is (only add a sibling subcommand).
- `.claude/skills/openup-request-input/` — the Claude skill stays; the new subcommand is additive.
- The T-073 service — later layer.

## Operations

- [x] Add `openup-input.py request --task-id? --title --question… [--option…]`: write a well-formed input-request under `docs/input-requests/` (`status: pending`, Questions + `**Answer**:` placeholder); when `--task-id` names an existing change folder, add `awaiting-input:` to its `plan.md`.
- [x] Add `ask_user` as the 7th tool (`TOOL_NAMES` + `TOOL_DEFS`) with `question` + optional `options`.
- [x] Wire `ask_user` into `loop.py`: interactive mode reads a stdin line and returns it as the tool result; async mode calls the `request` creator with the active `task_id` (from `.openup/state.json`), prints `OPENUP-AGENT: SUSPENDED — <path>`, and returns exit 5.
- [x] Thread `--interactive` through `scripts/openup-agent.py` into `loop.run`.
- [x] (tester) `test_openup_input_request.py`: request creation (with/without `--task-id`), the `awaiting-input` edit, and the `resumable` round-trip (answered → resumable).
- [x] (tester) Extend the driver tests: interactive `ask_user` (scripted stdin → answer in loop) and async `ask_user` (suspend sentinel + exit 5 + lane `awaiting-input` set), both hermetic.
- [x] Document `ask_user` + `--interactive` + suspend sentinel/exit 5 + resume story in `docs-eng-process/reference-driver.md`; run the full suite.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format `[T-074]`, etc.
- `docs-eng-process/sops/async-input.md` — the async-input contract this reuses.
- `scripts/tests/test_openup_agent.py` — hermetic stdlib `unittest` style (test seams, mock endpoint).
- `.claude/skills/openup-request-input/SKILL.md` — the request-doc format the new subcommand must match.

## Safeguards

- **Reuse, don't fork, the async-input contract.** The `resumable`/board-`suspended`
  side is untouched; a driver-created request must be indistinguishable to it from a
  skill-created one (same frontmatter keys, same `awaiting-input` line).
- **No new dependency.** Stdlib-only holds (the driver + `openup-input.py`).
- **Distinct exit code (5).** Suspend must not collide with 0/2/3/4 so an outer loop can
  tell "suspended, awaiting human" from success/error.
- **Async is the default.** Interactive requires an explicit `--interactive` (blocking on
  a TTY is wrong for CI/service).
- **Reversibility.** Additive tool + subcommand + flag; back out by removal.
- **Token / size budget.** Loop/tool additions ≤ ~120 new lines; the `request` subcommand ≤ ~120 lines.

## Verification

- `python3 -m unittest scripts.tests.test_openup_input_request scripts.tests.test_openup_agent scripts.tests.test_openup_agent_tools` — green, hermetic.
- Manual: run `--procedure` where the model asks a question — interactive prompts + resumes; async suspends (exit 5) and the lane shows `awaiting-input`, then `openup-input.py resumable` picks it up once answered.
- Grade against `.claude/rubrics/task-spec-rubric.md` — all ✅.

## Success Measures

n/a — internal framework tooling, no user telemetry. Falsifiable expectation: a driver
run whose procedure asks a blocking question **suspends cleanly and resumes on the
answer** through the *unchanged* `resumable` path (read-back: the async round-trip test +
a manual driver suspend/resume, recorded in `design.md`). If a driver-created request is
not resumable by the existing path, the reuse thesis is falsified.

## Rollout

n/a — not user-facing. `ask_user` and `--interactive` are additive to an opt-in CLI; no
flag/toggle affects any existing path until a user runs the driver with a question-asking
procedure. Back-out is removal of the added tool/subcommand/flag.

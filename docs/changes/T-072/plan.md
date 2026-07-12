---
id: T-072
title: Reference OpenAI-compatible driver (`openup-agent run`)
status: ready   # proposed → ready → in-progress → done → verified
priority: high   # critical | high | medium | low
estimate: 2–3 sessions   # rough size
plan: docs/plans/2026-06-10-process-v2-claude-code-harness.md   # program roadmap block: "Planned: Harness-optional OpenUP core"
depends-on: [T-071]
blocks: [T-073]
touches:
  - scripts/openup-agent.py
  - scripts/openup_agent/
  - scripts/tests/test_openup_agent.py
  - scripts/tests/test_openup_agent_tools.py
  - docs-eng-process/reference-driver.md
  - docs/changes/T-072/
last-synced: ""
---

# T-072 — Reference OpenAI-compatible driver (`openup-agent run`)

## Story

> **As a** practitioner with no Claude Code (or any harness) and a local/OpenAI-compatible LLM endpoint
> **I want** a plain Python agentic loop that drives an OpenUP procedure end-to-end by reading the neutral procedure pack and running the deterministic steps itself
> **So that** OpenUP is provably harness-optional — the falsifiable half of the program acceptance test: a delivery cycle runs on a non-Anthropic model with fence-clean, validator-clean commits.

INVEST check — one line per dimension:
✅ Independent (T-071 pack + tier-map already landed) · ✅ Negotiable (tool surface / loop shape open) · ✅ Valuable (proves the whole program thesis) · ✅ Estimable (2–3 sessions, mirrors T-071) · ✅ Small (single new package, no product-behavior change) · ✅ Testable (hermetic mock endpoint drives the loop to a terminal sentinel)

## Analysis Context

State the *why* the spec needs but the code can't show:
- **Domain.** A new **reference driver** — a bare agentic loop over any OpenAI-compatible
  `/v1/chat/completions` endpoint — that consumes the T-071 harness-neutral pack
  (`docs-eng-process/procedures/openup-*.md`) directly, with no Claude Code. It sits at
  **Layer 3** of the harness-optional layering (exploration
  `docs/explorations/2026-07-12-harness-agnostic-openup.md` §Target layering). The repo's
  own principle — "if a step is deterministic, the harness does it" — means the LLM is only
  invoked for judgment (authoring specs/code, grading); the driver sequences everything
  deterministic (board, fence, validators, state) itself, so enforcement is *strictly
  stronger* than any harness gate.
- **Scope boundaries.** This task builds **only the CLI driver** and its tests. It does NOT:
  build the FastAPI service (T-073, gated on a named consumer — exploration Pushback 1);
  add Codex/Cursor adapters (owner decision 4 — deferred); change any product behavior or
  Ring-1 artifact; modify the neutral pack, tier-map, or Claude Code adapter (T-071, done);
  or require the owner's LM Studio server to be reachable from CI (the live end-to-end run
  is an owner verification step, see Verification).
- **Definition of done.** `python3 scripts/openup-agent.py run --dir <path> --procedure <name>`
  runs an agentic loop against an OpenAI-compatible endpoint configured by `LLM_API_URL` +
  `LLM_API_KEY`; exposes the six-tool surface; resolves the procedure's `tier:` through the
  `tier-map.yaml` **driver** column; runs the deterministic gates (`openup-fence.py check`,
  `check-docs.py`, `openup-state.py`) itself; and terminates on the procedure's sentinel
  (e.g. `OPENUP-NEXT: ADVANCED|DONE`) or a max-iteration cap. A hermetic test drives a
  trivial procedure to a terminal sentinel against a stdlib mock endpoint with zero network.

Non-blocking questions resolved by default (each vetoable at review):

> **Assumption:** The driver is **procedure-agnostic** — it loads
> `docs-eng-process/procedures/openup-<procedure>.md` verbatim as the LLM's task instruction
> and lets the model drive via tools; no per-procedure logic is hardcoded. *(Vetoable at review — exploration Open Q "team procedures".)*
> **Assumption:** **One model per run.** The driver resolves a single model from the
> top-level procedure's `tier:` via the tier-map `driver` column; team/subagent procedures
> declare `capabilities.optional: [subagents]` and **degrade to sequential** on this driver
> (exploration §Layer 2 capability tiers). *(Vetoable at review.)*
> **Assumption:** **Stdlib-only, no new dependency.** HTTP to the endpoint uses
> `urllib.request` (the OpenUP workflow scripts are stdlib-only per `requirements.txt`).
> *(Vetoable at review.)*
> **Assumption:** The **plan gate auto-proceeds** non-interactively on this reference driver;
> the real enforcement is the deterministic gates the driver runs itself. Interactive
> plan-approval is out of scope (a service concern, T-073). *(Vetoable at review — exploration Open Q "plan-mode gating".)*
> **Assumption:** `exec` is narrowed to an **allowlist** — `git <subcmd>` and
> `python3 scripts/<known-script>.py` only — matching the exploration's hardening note; any
> other command is refused by the tool, not the shell. *(Vetoable at review.)*
> **Assumption:** Module layout is `scripts/openup-agent.py` (CLI entry, mirrors
> `openup-*.py` naming) delegating to a `scripts/openup_agent/` package (loop, tools, llm
> client, tier resolution). *(Vetoable at review.)*

## Requirements

1. A CLI entry `scripts/openup-agent.py` exposes `run --dir <path> --procedure <name>` and
   reads endpoint config from `LLM_API_URL` + `LLM_API_KEY` (owner decision 3).
   - **Given** `LLM_API_URL`/`LLM_API_KEY` are set and `--dir` is a repo with the neutral pack
     **When** `python3 scripts/openup-agent.py run --dir . --procedure next` is invoked
     **Then** the driver loads `docs-eng-process/procedures/openup-next.md`, opens a chat-completions
     session against `LLM_API_URL`, and enters the agentic loop (exit 0 on a clean terminal sentinel).
   - **Given** `LLM_API_URL` is unset **When** the driver starts **Then** it exits non-zero with a
     clear "set LLM_API_URL/LLM_API_KEY" message and makes no network call.

2. The driver exposes exactly the six-tool surface (`read_file`, `write_file`, `edit_file`,
   `list_dir`/`glob`, `grep`, `exec`) to the model as OpenAI tool/function definitions, and
   dispatches each tool call against `--dir` as the working root.
   - **Given** the model returns a `read_file` tool call for a path under `--dir`
     **When** the loop dispatches it **Then** the file contents (honoring `offset`/`limit`) are
     returned as the tool result and appended to the message history.
   - **Given** the model returns an `edit_file` call whose `old_str` is absent or non-unique
     **When** it is dispatched **Then** the tool returns a structured error (not a crash) so the
     model can retry — mirroring the harness `edit_file` contract.

3. `exec` refuses any command outside the allowlist (`git …` or `python3 scripts/*.py …`),
   returning a structured refusal rather than executing.
   - **Given** the model calls `exec` with `rm -rf /` (or any non-allowlisted command)
     **When** it is dispatched **Then** no subprocess runs and the tool result is a refusal naming the allowlist.
   - **Given** the model calls `exec` with `python3 scripts/openup-board.py resolve`
     **When** it is dispatched **Then** the command runs in `--dir` and its stdout/stderr/exit-code are returned.

4. The driver resolves the run's model from the procedure's `tier:` through
   `docs-eng-process/tier-map.yaml` **driver** column, expanding `${ENV:-default}` placeholders
   against the environment (owner decision 6 — tiers matched by runtime name).
   - **Given** `openup-next.md` declares `tier: reasoning` and the map's driver column has
     `reasoning: "${OPENUP_MODEL_MAIN:-local-main}"` **When** the driver resolves the model with
     `OPENUP_MODEL_MAIN` unset **Then** the chat-completions `model` field is `local-main`; with
     `OPENUP_MODEL_MAIN=foo` set **Then** it is `foo`.
   - **Given** a procedure declares a `tier:` absent from the driver column **When** resolution runs
     **Then** the driver exits with a hard error (no silent default), matching the pack's contract.

5. The driver runs the deterministic gates itself at the loop's persistence points — it does
   not rely on the model to run them: `openup-fence.py check` and `check-docs.py` are invoked
   and a non-zero result is surfaced back into the loop (as a tool/system message) so the model
   must fix before terminating.
   - **Given** a loop iteration where the model has written files and signals it is ready to finish
     **When** the driver runs `openup-fence.py check` and it exits non-zero **Then** the driver
     re-injects the fence failure into the conversation and continues the loop instead of exiting clean.
   - **Given** all gates pass and the procedure's terminal sentinel is emitted **When** the loop sees it
     **Then** the driver exits 0 and prints the sentinel line as its own last line.

6. The loop terminates deterministically: on the procedure's sentinel (e.g.
   `OPENUP-NEXT: ADVANCED — <id>` / `DONE — <reason>`), on a `--max-iterations` cap (default
   sensible, e.g. 50), or on an unrecoverable tool/endpoint error — never an unbounded spin.
   - **Given** the model never emits a sentinel **When** the iteration count reaches `--max-iterations`
     **Then** the driver exits non-zero with a "max iterations reached" message and a transcript pointer.

## Behavior Delta

This task adds a **new, standalone tool** (the reference driver). It changes **no existing
Ring-1 product behavior** — Claude Code's runtime experience, the neutral pack, the tier-map,
and every `scripts/*.py` CLI are held invariant (the driver only *reads* the pack and *calls*
existing scripts; it does not modify them).

**Added** — behavior that did not exist before (no prior Ring-1 artifact):
- `openup-agent run --dir --procedure` reference driver: an OpenAI-compatible agentic loop.
- Six-tool surface (`read_file`, `write_file`, `edit_file`, `list_dir`/`glob`, `grep`, `exec`)
  with `exec` allowlisted to `git` + `python3 scripts/*.py`.
- Runtime tier→model resolution against the `tier-map.yaml` driver column.
- Deterministic in-loop gate enforcement (fence + `check-docs.py` + state), model-independent.

**Modified** — none. (`tier-map.yaml`'s driver column already exists from T-071; the driver consumes it read-only.)

**Removed** — none.

## Entities

- **Driver CLI** (new) — `scripts/openup-agent.py` (`run` subcommand)
- **Driver package** (new) — `scripts/openup_agent/` (`loop.py`, `tools.py`, `llm.py`, `tiers.py`)
- **Neutral procedure pack** (read-only) — `docs-eng-process/procedures/openup-*.md`
- **Tier map** (read-only) — `docs-eng-process/tier-map.yaml` (**driver** column)
- **Deterministic gates** (read-only, invoked) — `scripts/openup-fence.py`, `scripts/check-docs.py`, `scripts/openup-state.py`
- **Driver usage doc** (new) — `docs-eng-process/reference-driver.md`

## Approach

Build a small, procedure-agnostic agentic loop. `run` loads the requested procedure markdown
from the neutral pack as the system/task instruction, resolves the model from the procedure's
`tier:` via the tier-map driver column, and opens a `/v1/chat/completions` session (stdlib
`urllib`) advertising the six tools as OpenAI function definitions. Each turn: post the message
history, dispatch any tool calls against `--dir` (with `exec` allowlisted), append results, and
repeat. The driver — not the model — runs the deterministic gates (`openup-fence.py check`,
`check-docs.py`) at persistence points and re-injects failures, and watches for the procedure's
terminal sentinel to stop. Teams degrade to sequential (one model). The design keeps the LLM on
judgment only; every deterministic step is code the driver owns.

## Structure

**Add:**
- `scripts/openup-agent.py` — CLI entry (`run --dir --procedure --max-iterations`), arg/env parsing, delegates to the package.
- `scripts/openup_agent/__init__.py`
- `scripts/openup_agent/loop.py` — the agentic loop + sentinel/gate orchestration.
- `scripts/openup_agent/tools.py` — the six-tool surface + `exec` allowlist.
- `scripts/openup_agent/llm.py` — stdlib `urllib` OpenAI-compatible chat-completions client.
- `scripts/openup_agent/tiers.py` — load `tier-map.yaml` driver column + `${ENV:-default}` expansion.
- `scripts/tests/test_openup_agent.py` — hermetic loop test against a stdlib mock endpoint.
- `scripts/tests/test_openup_agent_tools.py` — unit tests for the six tools + exec allowlist.
- `docs-eng-process/reference-driver.md` — usage + the owner's live LM-Studio run checklist.

**Modify:**
- (none expected — the driver is additive and consumes T-071 artifacts read-only)

**Do not touch:**
- `docs-eng-process/procedures/`, `docs-eng-process/tier-map.yaml`, `scripts/render-claude-adapter.py`, `.claude/` — T-071 surface; the driver reads it, never rewrites it.
- `scripts/openup-fence.py`, `scripts/check-docs.py`, `scripts/openup-state.py` — invoked as-is; changing them is a different task.
- FastAPI / any service wrapper — that is T-073, gated on a named consumer.

## Operations

- [x] Scaffold `scripts/openup-agent.py` + `scripts/openup_agent/` package: `run --dir --procedure --max-iterations` arg parsing, `LLM_API_URL`/`LLM_API_KEY` env config (fail-fast if unset), and the procedure-file loader that reads `docs-eng-process/procedures/openup-<procedure>.md` from `--dir`.
- [x] Implement `tiers.py`: parse `tier-map.yaml`, read a procedure's `tier:`, resolve it through the **driver** column with `${ENV:-default}` expansion, hard-error on an unknown tier.
- [x] Implement `tools.py`: the six-tool surface (`read_file`, `write_file`, `edit_file`, `list_dir`/`glob`, `grep`, `exec`) rooted at `--dir`, with `edit_file` returning structured errors on absent/non-unique `old_str` and `exec` refusing anything outside the `git` + `python3 scripts/*.py` allowlist.
- [x] Implement `llm.py` + `loop.py`: stdlib `urllib` chat-completions client advertising the tools as function defs; the turn loop (post → dispatch tool calls → append results), sentinel detection, and the `--max-iterations` cap.
- [x] Wire deterministic gates into `loop.py`: run `openup-fence.py check` and `check-docs.py` at persistence points, re-inject non-zero results into the conversation, and only accept the terminal sentinel when gates are clean.
- [x] (tester) Write `test_openup_agent_tools.py` (six tools + exec allowlist, hermetic) and `test_openup_agent.py` (a stdlib `http.server` mock scripted to drive a trivial procedure to a terminal sentinel — zero real network, asserts tool dispatch + gate invocation + clean exit). **Result: 38/38 green.**
- [x] Author `docs-eng-process/reference-driver.md`: usage, env vars, tool surface, and the **owner's manual live-run checklist** for the LM Studio end-to-end acceptance (the non-Anthropic half of program acceptance).
- [x] (tester) Run the full suite (`python3 -m unittest discover -s scripts/tests`) plus a mock-endpoint dry-run of `--procedure next`; confirm the loop stays fence-/validator-clean and terminates on the sentinel. **Result: 38 driver tests green; CLI e2e exit 0 + sentinel; 5 failures are pre-existing on base (see design.md).**

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format `[T-072]`, etc.)
- `scripts/tests/test_openup_board.py` — reference for hermetic, CLI-exercised, stdlib `unittest` style (tempfile fixtures, subprocess invocation).
- `requirements.txt` (header note) — OpenUP workflow scripts are **stdlib-only**; the driver honors this.
- `docs-eng-process/procedure-frontmatter.md` — the neutral schema (`tier:`, `capabilities:`) the driver reads.

> Reference, don't copy — no rule bodies inlined here.

## Safeguards

Invariants and limits that must hold:
- **No new runtime dependency.** Driver is stdlib-only (`urllib`, `json`, `subprocess`, `http.server` for tests). Adding to `requirements.txt` is out of bounds for this task.
- **`exec` allowlist is mandatory.** The tool must refuse anything but `git <subcmd>` and `python3 scripts/<script>.py …`; this is a safety invariant, not a convenience.
- **Deterministic gates are driver-run, never model-trusted.** Fence + `check-docs.py` enforcement lives in `loop.py`, not in a prompt instruction.
- **Read-only over T-071 surface.** The driver must not write to `docs-eng-process/procedures/`, `tier-map.yaml`, or `.claude/`.
- **Bounded loop.** `--max-iterations` cap guarantees termination; no unbounded spin.
- **Reversibility.** Purely additive new files under `scripts/` + one doc; back out by deleting them — no existing behavior changes, nothing to migrate.
- **Token / size budget.** Each package module ≤ ~250 lines; keep the loop legible.

## Verification

How a reviewer (human or agent) confirms the task is done:
- `python3 -m unittest scripts.tests.test_openup_agent scripts.tests.test_openup_agent_tools` — both green, hermetic (no network).
- `python3 scripts/openup-agent.py run --dir . --procedure next` against a **mock** endpoint drives to a terminal sentinel; against the owner's **LM Studio** endpoint (manual, per `reference-driver.md` checklist) completes one real cycle producing fence-clean, validator-clean commits — the non-Anthropic half of program acceptance.
- `grep -rn "import requests\|import httpx" scripts/openup_agent/` returns nothing (stdlib-only holds).
- Grade the final spec against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

## Success Measures

n/a — internal framework tooling with no user-facing telemetry surface. The falsifiable
expectation is the **program acceptance test itself**: a single `--procedure next` cycle
completes on a non-Anthropic/local model producing fence-clean, validator-clean commits
(read-back: the owner's live LM Studio run recorded in `docs/changes/T-072/design.md` at
completion). If that cycle cannot complete, the harness-optional thesis is falsified — which is
the whole point of building this driver.

## Rollout

n/a — not user-facing. The driver is a new, opt-in CLI (`scripts/openup-agent.py`) with no
flag, no runtime toggle, and no effect on any existing Claude Code / script path until a user
explicitly invokes it. Config is read from env (`LLM_API_URL`/`LLM_API_KEY`) at startup; a flag
would add no safety over "don't run the command." Back-out is deletion of the added files.

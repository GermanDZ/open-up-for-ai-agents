---
type: reference
id: reference-driver
status: living
title: Reference OpenAI-compatible driver (openup-agent)
traces-from: [T-072]
---

# Reference driver — `openup-agent`

Run OpenUP with **no harness** — no Claude Code, no Cursor — driving a delivery
cycle with a plain Python loop against any **OpenAI-compatible** chat-completions
endpoint (a local model in LM Studio / Ollama / vLLM, or hosted OpenAI). It reads
the neutral procedure pack (`docs-eng-process/procedures/openup-*.md`) directly and
runs the deterministic OpenUP scripts itself.

This is **Layer 3** of the harness-optional program and the proof that OpenUP is
genuinely harness-optional: the loop runs on a non-Anthropic model, and the process
still holds because the deterministic steps are code, not prompt instructions.

> **No install.** The driver is stdlib-only — you do **not** need `requirements.txt`.
> You need `python3` (3.8+) and `git`, which the process already requires.

> **New here?** For a task-oriented walkthrough — bootstrap a new project, or adopt
> OpenUP into an existing codebase (and backfill its missing docs) — start with
> [getting-started-reference-driver.md](getting-started-reference-driver.md). This
> page is the complete reference.

---

## Quick start

```bash
# 1. Point at any OpenAI-compatible endpoint (local example: LM Studio)
export LLM_API_URL=http://localhost:1234/v1
export LLM_API_KEY=lm-studio                 # any non-empty string for local servers
export OPENUP_MODEL_MAIN=your-loaded-model   # a model your endpoint actually serves

# 2. From an OpenUP project root, drive one procedure to completion
python3 scripts/openup-agent.py run --dir . --procedure next
```

On success the driver prints the procedure's sentinel (e.g.
`OPENUP-NEXT: ADVANCED — T-074`) to **stdout** and exits 0; all progress goes to
**stderr**, so an outer loop can read the sentinel exactly as it does from
`/openup-next`.

---

## Configuration

All configuration is environment variables — nothing to edit in the repo.

| Variable | Required | Purpose |
|---|---|---|
| `LLM_API_URL` | **yes** | Base URL of the endpoint. Accepts a full endpoint, a `…/v1` base, or a bare host (the `/v1/chat/completions` suffix is added when absent). |
| `LLM_API_KEY` | no* | Bearer token. Required by hosted OpenAI; local servers accept any non-empty value. Sent as `Authorization: Bearer …` when set. |
| `OPENUP_MODEL_MAIN` | recommended | Model for the `reasoning` / `quality-gate` tiers (the heavy judgment work). |
| `OPENUP_MODEL_MID` | optional | Model for the `authoring` tier. Falls back to `local-mid` if unset. |
| `OPENUP_MODEL_SMALL` | optional | Model for the `scribe` / `coordination` tiers. Falls back to `local-small` if unset. |
| `OPENUP_AGENT_USAGE_LOG` | optional | Path to append one JSON line per LLM call — `{iteration, model, latency_ms, usage:{prompt_tokens, completion_tokens, total_tokens}}`. Unset ⇒ no file, no behavior change. Used by the benchmark harness (see [reference-driver-benchmark.md](reference-driver-benchmark.md)). |
| `OPENUP_AGENT_DEBUG_LOG` | optional | Path to append one JSON line per LLM call with the **full interaction** — `{iteration, model, request:[messages…], response:{content, tool_calls, finish_reason}}`. The transcript to inspect *why* a (weak local) model misbehaved — e.g. skipped a required `write_file` or emitted the sentinel too early. Unset ⇒ no file, no behavior change; write failures are swallowed. |
| `OPENUP_AGENT_TIMEOUT` | optional | Per-LLM-call socket timeout in seconds (default **600**). Raise it for slow local models with long generations. A call that exceeds it surfaces as a clean `endpoint-error` (exit 3), never an uncaught crash. |

\* If your endpoint requires auth and `LLM_API_KEY` is empty, you'll get an HTTP 401
from the endpoint (surfaced as exit 3).

### How the model is chosen (runtime tiers)

No model name is hardcoded. Each procedure declares a **tier** (`scribe`,
`coordination`, `authoring`, `quality-gate`, `reasoning`); the driver resolves it
through the **`driver` column** of `docs-eng-process/tier-map.yaml`, whose values are
`${ENV:-default}` placeholders that expand against the three `OPENUP_MODEL_*` vars
above. An unknown tier is a hard error — never silently defaulted.

If you only have one model, point all three vars at it — every tier resolves to the
same model and the loop still runs.

### CLI flags

```
python3 scripts/openup-agent.py run --dir <path> --procedure <name> [--max-iterations N] [--instruction TEXT]
```

- `--dir` — the OpenUP project root (must contain `docs-eng-process/procedures/`).
- `--procedure` — a procedure name; `next` resolves `openup-next.md`. Any procedure
  in the pack works (the driver is procedure-agnostic).
- `--max-iterations` — turn cap before the loop gives up (default 50). Raise it for
  weaker models that take more turns.
- `--instruction TEXT` — extra task context appended to the driver's initial user
  message (e.g. *"read the stakeholder brief at docs/inputs/stakeholder-brief.md and
  produce the vision"*). This is how you hand a procedure its inputs when it normally
  takes arguments (`openup-create-vision` wants a project name + problem statement).
  Absent ⇒ unchanged behavior.
- `--interactive` — answer the procedure's questions on the TTY. Without it (the
  default), a question **suspends** the run into an input-request for async resolution
  (see [Asking the human](#asking-the-human--ask_user)).

---

## Endpoint recipes

### LM Studio
1. Load a model; **Developer → Start Server** (default `http://localhost:1234`).
2. `export LLM_API_URL=http://localhost:1234/v1 LLM_API_KEY=lm-studio`
3. `export OPENUP_MODEL_MAIN=<the model id LM Studio lists>`

### Ollama
1. `ollama serve` (default `http://localhost:11434`); it exposes an OpenAI-compatible
   surface at `/v1`.
2. `export LLM_API_URL=http://localhost:11434/v1 LLM_API_KEY=ollama`
3. `export OPENUP_MODEL_MAIN=llama3.1` (or any pulled model).

### vLLM
1. `python -m vllm.entrypoints.openai.api_server --model <hf-model>` (default `:8000`).
2. `export LLM_API_URL=http://localhost:8000/v1 LLM_API_KEY=vllm`
3. `export OPENUP_MODEL_MAIN=<the served model name>`

### Hosted OpenAI
1. `export LLM_API_URL=https://api.openai.com/v1 LLM_API_KEY=sk-…`
2. `export OPENUP_MODEL_MAIN=gpt-4o` (or another tool-calling model).

> **Model capability matters.** The driver makes the loop *possible* and *enforced*;
> it does not make a weak model smart. The `reasoning`-tier procedures (spec
> authoring, code) want a capable model **with tool-calling support**. A small model
> may need a larger `OPENUP_MODEL_MAIN` or a higher `--max-iterations`.

---

## First-run walkthrough

1. Confirm your endpoint serves models: `curl $LLM_API_URL/models` should list ids.
   Use one of them as `OPENUP_MODEL_MAIN`.
2. From the project root on a clean lane branch, run
   `python3 scripts/openup-agent.py run --dir . --procedure next`.
3. Watch **stderr**: you'll see `procedure=next model=… endpoint=…`, then a line per
   tool call (`tool exec -> …`, `tool read_file -> …`).
4. Before it finishes, the driver runs the gates itself — you'll see
   `procedure complete … gates clean` (or a re-injected gate failure it works to fix).
5. On success it prints the sentinel to **stdout** and exits 0.

---

## The six-tool surface

The model is handed exactly six tools (OpenAI function definitions), all rooted at
`--dir`:

| Tool | Purpose |
|---|---|
| `read_file(path, offset?, limit?)` | load specs, state, docs |
| `write_file(path, content)` | create artifacts |
| `edit_file(path, old_str, new_str)` | tick checkboxes / targeted edits (errors on absent or non-unique `old_str`) |
| `glob(pattern)` | discover change folders, templates (also lists a dir via `dir/*`) |
| `grep(pattern, path?)` | find task IDs, frontmatter |
| `exec(command, cwd?)` | run **allowlisted** commands only: `git <subcmd>` or `python3 scripts/<script>.py …` |
| `ask_user(question, options?)` | ask the human a blocking question (7th tool — see below) |

`exec` refuses anything outside the allowlist **without spawning a process**, and
every file tool refuses paths that escape `--dir` — a bare model gets the
deterministic OpenUP scripts, not an arbitrary shell.

## Asking the human — `ask_user`

Many OpenUP procedures legitimately hit a **blocking question** — a choice the specs
and repo don't answer. The model raises it with the `ask_user(question, options?)`
tool, and the driver handles it one of two ways:

- **`--interactive`** — the driver prints the question on the TTY, waits for your
  answer, and feeds it back into the loop. Good for running the driver at your desk.
- **default (non-interactive)** — the driver creates an OpenUP **input-request** under
  `docs/input-requests/`, sets `awaiting-input:` on the active lane's `plan.md` (so the
  board reports it `suspended`), prints `OPENUP-AGENT: SUSPENDED — <request-path>`, and
  exits **5**. Good for CI / unattended runs.

The async path reuses OpenUP's existing input-request machinery unchanged. To resume
after answering:

1. Open the printed request file, fill in the `**Answer**:` section, and set its
   frontmatter `status: pending → answered`.
2. Run `/openup-next` (or `python3 scripts/openup-input.py resumable`) — the answered
   request is mapped back to its lane and the work continues.

The deterministic creator is also available directly for any harness:
`python3 scripts/openup-input.py request --task-id T-NNN --title "…" --question "…" [--option …]`.

## Deterministic gate enforcement

Before the driver accepts a procedure's **terminal sentinel**, it runs each present
gate itself:

- `python3 scripts/openup-fence.py check` — the write-fence
- `python3 scripts/check-docs.py` — doc frontmatter / traceability validation

A non-zero gate result is re-injected into the conversation and the loop continues —
the sentinel is honored only once the gates are clean. Enforcement never depends on
the model remembering to check. A gate whose script is absent under `--dir` is
skipped, so the driver stays usable on partial trees.

## The guided entry point — `scripts/next-cycle` (T-095, thinned in T-096)

```
./scripts/next-cycle [--dir PATH]
```

The one command a practitioner needs to remember. A thin, stdlib-only wrapper
that composes the driver and **knows nothing about the OpenUP process** (T-096):
it loads `.openup/agent.env`, guides missing endpoint config (TTY prompt with
optional persist, or a copy-paste block + exit 2), and otherwise runs ONE
`cycle` (adding `--interactive` on a TTY) — translating every typed exit into
next-step guidance on stderr while the driver's stdout sentinel passes through
byte-exact. Outer loops can consume it exactly like `cycle`:
`while ./scripts/next-cycle; do :; done`.

Deciding *what a project needs next* — Inception authoring on a fresh repo, the
next delivery lane, a missing human input — is the driver's job, not the
wrapper's, and it is **deterministic** (T-101/T-103): navigation is a walk of the
process map, never a per-cycle LLM call. A fresh authoring phase resolves to
`plan-iteration` from `activities-for(phase)` (no roadmap needed); each activity's
declared `requires_input` (process-map data, T-100) is scaffolded as a
marker-guarded template and the cycle suspends until the human fills it; an
`execution: direct` activity runs its `create-*` procedure directly. The per-cycle
LLM **navigator** and the hardcoded Inception bootstrap were **retired** (T-103) —
the LLM is used only to *author* artifacts, never to decide the next step. See
the `cycle` engine's Plan Iteration below.


## The cycle engine — `openup-agent.py cycle` (T-089)

```
python3 scripts/openup-agent.py cycle --dir <path> [--step-max-iterations 10] [--step-tier authoring] [--interactive]
```

`run` hands a whole procedure to the model and lets it orchestrate; `cycle`
**inverts that control**. One invocation runs ONE delivery cycle as a
deterministic state machine over the existing scripts — `openup-board.py
resolve` → `openup-session.py begin` (in-place `task/<id>-cycle` branch) → the
**Operations-step executor** → gates → deterministic completion (spec status →
`done`, status-note shard, `sync-status.py`, archive, commit, `session end`,
merge back to the starting branch) — and prints the `/openup-next`-parity
sentinel (`OPENUP-NEXT: ADVANCED — <task>` / `DONE — <reason>`). The measured
motivation (T-080 benchmark, same local model): LLM-orchestrated `next` cost
37–50 iterations / 1–2M tokens and finished inconsistently; single authoring
runs cost ~8 iterations / ~59k tokens at 3/3 clean. `cycle` reshapes the loop
into that second, cheap shape.

Per **unchecked `## Operations` box** in the picked lane's `plan.md`:

- a box carrying an extractable `git …` / `python3 …` command (backtick-quoted,
  or from the first such token to end of line; a backticked `scripts/<x>.py`
  span gets `python3` prepended) is executed **as code** — zero LLM;
- an explicit marker overrides the pattern: `- [ ] (auto) …` forces script
  execution, `- [ ] (judgment) …` forces a sub-run;
- every other box is a **judgment sub-run**: a fresh, bounded `loop.run()` with
  a step-scoped instruction (the box text, the `(role)` hat, the change-folder
  briefing) and its own small turn cap (`--step-max-iterations`, default 10).
  The sub-run's model resolves from the tier map's `driver` column via
  `--step-tier` (default `authoring` → `OPENUP_MODEL_MID`).

Keep script-step boxes **command-only** — trailing prose after an unquoted
command becomes part of the command line.

After each successful step the engine runs the deterministic gates, and **only
then** ticks the box — so a gate failure (exit 6) leaves the box unchecked and
a re-run retries the step. All inter-step state lives in the repo (boxes,
`.openup/state.json`, the lease): a killed cycle resumes at the first unchecked
box. `ask_user` inside a sub-run suspends the whole cycle (exit 5) exactly like
`run`. As of T-091 the engine has **full `/openup-next` parity** — every
`resolve` decision path is handled: `pick`/`resume` (T-089), `plan-iteration`
(T-090/T-092, under recovery), and `assess-iteration`/`milestone-review`
(T-091, see below). Only `plan-iteration` under `--no-recover` still exits 7.
`scripts/openup-loop.sh` can now drive `cycle` end-to-end.

### Recovery mode (T-092, default on)

When the engine cannot proceed deterministically it **rebuilds the repo state
that blocks it**, then continues the same cycle. `--no-recover` opts out and
restores the bare typed exits below.

- **Unclosed-lane reconcile (zero LLM).** On a `plan-iteration`/`noop`
  decision, any *active* `docs/changes/<id>/` whose plan `status:` is already
  satisfied (`done`/`verified`) is closed first: archived, committed, views
  resynced (fail-open), and — when the delivered work sits on a side branch —
  merged `--no-ff` into the trunk (`origin/HEAD` → `main` → `master`). A dirty
  working tree skips closure (commit or stash first); a merge conflict exits 8
  with the branch left intact. This stops the loop from planning new work atop
  an unfinished delivery (the live my-product T-001 case).
- **Consent-gated replenishment (T-094).** When nothing is promotable at all
  — the roadmap exists but is exhausted or fully blocked mid-phase, or a
  recovery round cannot advance — the engine **asks before acting**: under
  `--interactive` a TTY yes/no prompt; otherwise it creates an input-request
  (multiple-choice yes/no, owned by no lane), prints the SUSPEND sentinel, and
  exits 5. The request path is remembered in `.openup/cycle.json`: while it is
  `pending` every stuck cycle re-suspends pointing at it (no duplicates);
  flipping it to `status: answered` with `yes` (ticked option or the
  `**Answer**:` line) lets the next cycle run ONE bounded
  **product-manager**-hat sub-run that appends 1–5 pending roadmap entries
  (each with a Value rationale, ids reserved via `openup-claims.py
  reserve-id`). Acceptance is deterministic — `openup-roadmap.py next` must
  find something promotable (plus `check-docs`) or the cycle fails typed with
  nothing committed; on success the roadmap commit lands `[openup-skip]` and
  the SAME invocation chains into missing-spec recovery and delivery. An
  answered `no` is remembered and ends that and later cycles cleanly — the LLM
  proposes, the human consents; scope is never invented silently. (A bypass
  flag for unattended loops — `--auto-replenish` — was deliberately deferred.)
- **Missing-spec recovery (one bounded sub-run).** A persisting
  `plan-iteration` decision already names the next roadmap work item, so an
  `analyst`-hat sub-run authors `docs/changes/<id>/plan.md` (the instruction
  carries the spec contract: frontmatter with `touches`, Given/When/Then
  scenarios, engine-convention Operations boxes). The spec is gated
  (`check-docs.py`, plus `openup-spec-scenarios.py` when present), committed,
  and the re-resolved `pick` runs **in the same invocation**. One recovery
  round only — a decision that does not advance to `pick`/`resume` exits 7 as
  before. This single-row promote is the **construction/transition** path (and
  the degenerate one-work-item case); the multi-lane Plan Iteration below is the
  **authoring-phase** path.
- **Plan Iteration (T-090, authoring phases).** For an `inception`/`elaboration`
  `plan-iteration` decision with no active iteration, the engine plans a full
  phase-appropriate iteration deterministically (porting `/openup-start-iteration`
  §0b into code): it mints the iteration id (`openup-process-map.py
  mint-iteration-id`), runs **one** bounded sub-run to choose 1–5 objectives,
  generates one lane per phase activity from `activities-for(phase)` with
  iteration-prefixed ids (`I1-001`, reserved via `openup-claims.py reserve-id
  --prefix`), partitions them (T-079), authors **each lane's spec** with one
  bounded sub-run (gated by `check-docs.py`, committed), and writes the
  `type: iteration-plan` instance under `docs/phases/<phase>/` (tracing every
  lane id, with evaluation criteria). Only the objectives + per-lane specs are
  LLM calls; mint/activities/reserve/partition/instance are code. A failed lane
  spec aborts with a typed exit before the instance is written (no half-planned
  iteration is left picked). The re-resolve then picks the first lane, so
  Inception on a bootstrapped project (the ShareShed flow) runs end-to-end through
  `cycle`.
  - **Fresh project, no roadmap (T-101, P1).** `resolve` now emits
    `plan-iteration` for a fresh **authoring** phase (unmet machine criteria,
    nothing promotable, no active iteration) directly from the process map — no
    roadmap entry required — so a brand-new project reaches its work products
    **deterministically, without the per-cycle LLM navigator**. Before minting,
    Plan Iteration honours each activity's declared **`requires_input`** (T-100):
    the first missing input is **scaffolded** as a marker-guarded template and the
    cycle suspends (exit 5) until the human fills it — the data-driven,
    process-agnostic replacement for the hardcoded brief bootstrap. An activity
    marked **`execution: direct`** (e.g. `initiate-project` → `openup-create-vision`)
    **runs its procedure directly** — no intermediate lane spec, killing the
    redundant re-authoring — and is recorded in the iteration-plan instance body;
    `spec-then-execute` activities keep the lane flow above. *(The per-cycle
    navigator/bootstrap were deleted in T-103.)*
  - **Engine-owned authoring ceremony (T-104).** On the `execution: direct` path
    the **model authors the document body only**; every piece of ceremony is
    engine work:
    - **Frontmatter stamping** (`openup_agent/stamping.py`): after the sub-run
      succeeds — and before the gates — the engine stamps the typed instance
      frontmatter (`type`, next-free `id` per type prefix e.g. `VIS-001`,
      `title`, `status: draft`) on the artifact the procedure produced
      (`stamping.PROCEDURE_ARTIFACTS`; interim table until T-106's task-library
      defs carry `artifact` + `output_path`). A model-written frontmatter block
      is replaced; a valid already-stamped id is kept (re-runs never reallocate).
      `check-docs` (already in the gates) validates the stamped result — **the
      gate is the critic**.
    - **Ceremony exclusion**: the direct-run instruction tells the model to
      author the body only and NOT to read/write frontmatter, rubrics, trace
      models, schemas, or `docs/project-config.yaml`, and not to self-critique.
      (A strong-model tier MAY later run critique as a separate tiny sub-run —
      noted, not built.)
    - **Project-config injection**: the engine reads `docs/project-config.yaml`
      once and injects its `context:` / relevant `rules.<artifact>` into the
      instruction as `<project-context>` / `<project-rules>` — the model never
      probes for the file.
    - **Pinned initial-roadmap contract** (restores the T-099 format the T-103
      deletion regressed): the `initiate-project` direct instruction carries
      `plan_iteration.ROADMAP_FORMAT` — strict header row, `T-001, T-002, …`
      ids, `pending` status, `high|medium|low` priority, comma-separated
      `T-NNN` deps, priority-ordered, no YAML frontmatter — so
      `openup-roadmap.py next` can promote from a freshly-authored roadmap.
      Interim constant until T-106 moves it into the task library.
  - **Everything the engine produces is committed (T-108).** A successful
    direct activity is **gated and committed at the point of production**
    (produce → stamp → gate → commit the `docs/` delta, message
    `docs(<iter>): <activity> — authored via <skill> [<iter>]`); a gate failure
    aborts with the typed step exit and nothing committed — same discipline as
    the lane specs. And on **every** `run_cycle` exit path (advanced, done,
    suspend, typed failure) the cycle's `docs/agent-logs/` shards are swept
    into a log-only `chore(process): sweep run-log shards [openup-skip]`
    commit, so each cycle is durably registered even when it fails mid-lane. A
    sweep error is logged and never changes the cycle's exit code.
- **Assess (T-091, one grading sub-run).** When a T-090-planned iteration's
  committed lanes are all delivered and its instance has no `## Assessment`,
  `resolve` returns `assess-iteration`. Done-ness is already code (it fired the
  decision); the engine runs **one** bounded grading sub-run to grade the
  **non-derivable** evaluation criteria against repo evidence (objectives met?
  demo verdict), writing `.openup/assessment.json`, then **deterministically
  appends** an `## Assessment` section to the iteration-plan instance (criteria
  grades + evidence, demo scope, excluded items, discovered-work notes, verdict),
  gates + commits it, and emits `OPENUP-NEXT: ADVANCED — assessed <iteration>`.
  It records evidence; it does **not** auto-enqueue discovered work as roadmap
  scope (that stays behind the T-094 consent gate) and never advances a phase.
- **Milestone (T-091, zero LLM).** When the roadmap is drained and the phase's
  exit criteria are met with no milestone record, `resolve` returns
  `milestone-review`. The engine prepares the evidence and raises the human
  go/no-go as a T-074 input-request (GO / NO-GO), prints the SUSPEND sentinel, and
  exits 5 — remembered in `.openup/cycle.json` so a re-run re-suspends without a
  duplicate. It **records evidence and pauses; it never advances the phase** — the
  human go/no-go + `openup-lifecycle.py` own that, exactly like
  `/openup-phase-review`.

## Console output (T-109)

The driver narrates on **stderr**; **stdout carries only the sentinel** (the
outer-loop contract — byte-exact through `next-cycle`). Default output is the
narrated form:

- **Sub-run step header** — one line naming the role hat, model, turn budget,
  and what the step does (the instruction's first line).
- **Tool lines name their target** — `read_file docs/vision.md`,
  `write_file docs/roadmap.md`, `exec: git status` (truncated ~60 chars).
- **Progress** — `model turn k/N` per LLM call, so a long wait is visibly a
  turn, not a hang.
- **Cycle-end summary** — every `run_cycle` exit closes with the commits the
  cycle made (which name the artifacts) and what the exit code means in plain
  words.
- **No blank lines** — narration never emits empty lines.

`OPENUP_AGENT_VERBOSE=1` restores the full detail (tool-result char counts,
complete step instructions). The JSONL telemetry (`OPENUP_AGENT_USAGE_LOG`,
`OPENUP_AGENT_DEBUG_LOG`) is unchanged and remains the deep-diagnosis surface.

## Exit codes

| Code | Meaning | Typical cause |
|---|---|---|
| 0 | completed; sentinel on stdout | — |
| 2 | configuration error | `LLM_API_URL` unset, procedure not found, unknown tier |
| 3 | endpoint / transport error | endpoint down, 401/404, non-JSON response |
| 4 | max iterations reached, no clean sentinel | model never finished, or a gate never passed |
| 5 | suspended, awaiting a human answer | `ask_user` in non-interactive mode ([above](#asking-the-human--ask_user)) |
| 6 | `cycle`: gate failed after a step | fence / check-docs red; the box stays unticked |
| 7 | `cycle`: decision path unsupported | `plan-iteration` only under `--no-recover` (or when recovery/planning cannot advance); every path is otherwise handled (T-091 parity) |
| 8 | `cycle`: script-step or ceremony command failed | a box's command exited non-zero; session begin refused |

## Troubleshooting

- **`LLM_API_URL is not set` (exit 2)** — export `LLM_API_URL` (and usually
  `LLM_API_KEY`). No network call is made until it is set.
- **`unknown tier '…'` (exit 2)** — a procedure declares a tier missing from the
  `tier-map.yaml` `driver` column. Add the tier to the map or fix the procedure; the
  driver never guesses a default.
- **HTTP 404 / "model not found" (exit 3)** — `OPENUP_MODEL_MAIN` isn't a model your
  endpoint serves. List them with `curl $LLM_API_URL/models` and use an exact id.
- **HTTP 401 (exit 3)** — the endpoint needs auth; set `LLM_API_KEY`.
- **Loops to max iterations (exit 4)** — either the model isn't emitting the
  sentinel (raise `--max-iterations`, or use a stronger `OPENUP_MODEL_MAIN` with
  tool-calling), or a gate keeps failing (read the re-injected gate output on stderr
  and fix the underlying repo issue).
- **Model ignores tools / replies in prose** — the model likely lacks tool-calling
  support. Use a model that supports OpenAI function calling.

## Owner live-run checklist (program acceptance)

The program's acceptance test has two halves; this driver is the **non-Anthropic**
half — one `--procedure next` cycle on a local model producing fence-clean,
validator-clean output:

1. Start LM Studio's server; note the base URL and the model ids it lists.
2. `export LLM_API_URL=http://localhost:1234/v1 LLM_API_KEY=lm-studio`.
3. `export OPENUP_MODEL_MAIN=<a capable local model>` (set `_MID`/`_SMALL` too for
   distinct tiers, or leave them to point at the same model).
4. From a clean project on a lane branch: `python3 scripts/openup-agent.py run --dir . --procedure next`.
5. **Expected:** one delivery cycle advances, the driver's fence + `check-docs.py`
   pass, and it prints an `OPENUP-NEXT: ADVANCED — <id>` (or `DONE`) sentinel.
6. Record the run outcome (model used, sentinel, any gate friction) in
   `docs/changes/T-072/design.md` as the read-back for this task's Success Measure.

## Layering

This is Layer 3 of the harness-optional program (exploration
`docs/explorations/2026-07-12-harness-agnostic-openup.md`). Layer 4 (a FastAPI
service over this driver, T-073) is **gated on a named consumer** and not built here.

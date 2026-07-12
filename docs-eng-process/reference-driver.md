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
python3 scripts/openup-agent.py run --dir <path> --procedure <name> [--max-iterations N]
```

- `--dir` — the OpenUP project root (must contain `docs-eng-process/procedures/`).
- `--procedure` — a procedure name; `next` resolves `openup-next.md`. Any procedure
  in the pack works (the driver is procedure-agnostic).
- `--max-iterations` — turn cap before the loop gives up (default 50). Raise it for
  weaker models that take more turns.
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

## Exit codes

| Code | Meaning | Typical cause |
|---|---|---|
| 0 | completed; sentinel on stdout | — |
| 2 | configuration error | `LLM_API_URL` unset, procedure not found, unknown tier |
| 3 | endpoint / transport error | endpoint down, 401/404, non-JSON response |
| 4 | max iterations reached, no clean sentinel | model never finished, or a gate never passed |
| 5 | suspended, awaiting a human answer | `ask_user` in non-interactive mode ([above](#asking-the-human--ask_user)) |

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

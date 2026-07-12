---
type: reference
id: reference-driver
status: living
title: Reference OpenAI-compatible driver (openup-agent)
traces-from: [T-072]
---

# Reference driver — `openup-agent`

The reference driver is the **Layer 3** proof that OpenUP is harness-optional: a
plain Python agentic loop that drives an OpenUP procedure end-to-end against any
OpenAI-compatible chat-completions endpoint, with **no Claude Code and no harness**.
It reads the T-071 neutral procedure pack (`docs-eng-process/procedures/openup-*.md`)
directly and runs the deterministic OpenUP scripts itself.

It is stdlib-only — installing `requirements.txt` is not needed to run it.

## Why it exists

The repo's own principle — *if a step is deterministic, the harness does it* — means
the LLM is only needed for judgment (authoring specs/code, grading rubrics). The
driver sequences everything deterministic (board derivation, the write-fence, doc
validation, state) as code it runs itself, so enforcement is **strictly stronger**
than any harness gate: the model cannot "forget" to run the fence, because the driver
runs it before accepting completion.

## Usage

```bash
export LLM_API_URL=http://localhost:1234/v1     # LM Studio / Ollama / vLLM / OpenAI
export LLM_API_KEY=sk-...                        # may be empty for local servers
python3 scripts/openup-agent.py run --dir . --procedure next
```

- `--dir` — the OpenUP project root (must contain `docs-eng-process/procedures/`).
- `--procedure` — a procedure name; `next` resolves `openup-next.md`. The driver is
  **procedure-agnostic**: it loads the procedure markdown as the model's instruction
  and lets it drive via tools. Any procedure in the pack works.
- `--max-iterations` — turn cap before the loop gives up (default 50). Guarantees termination.

### Model selection (runtime tier resolution)

No model name is hardcoded. The procedure declares a `tier:` (one of `scribe`,
`coordination`, `authoring`, `quality-gate`, `reasoning`); the driver resolves it
through the **`driver` column** of `docs-eng-process/tier-map.yaml`, whose values are
`${ENV:-default}` placeholders expanded against the environment:

| Env var | Tiers it serves | Default |
|---|---|---|
| `OPENUP_MODEL_SMALL` | scribe, coordination | `local-small` |
| `OPENUP_MODEL_MID` | authoring | `local-mid` |
| `OPENUP_MODEL_MAIN` | quality-gate, reasoning | `local-main` |

Set these to the model names your endpoint surfaces (e.g. what LM Studio lists). An
unknown tier is a hard error — never silently defaulted.

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

`exec` refuses anything outside the allowlist without spawning a process — a bare
model gets the deterministic OpenUP scripts, not an arbitrary shell.

## Deterministic gate enforcement

Before the driver accepts a procedure's **terminal sentinel** (e.g.
`OPENUP-NEXT: ADVANCED — T-072` or `OPENUP-NEXT: DONE — <reason>`), it runs each
present gate itself:

- `python3 scripts/openup-fence.py check` — the write-fence
- `python3 scripts/check-docs.py` — doc frontmatter / traceability validation

A non-zero gate result is re-injected into the conversation and the loop continues —
the sentinel is only honored once the gates are clean. A gate whose script is absent
under `--dir` is skipped, so the driver stays usable on partial trees.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | procedure completed; sentinel printed to stdout |
| 2 | configuration error (missing env, procedure, or unknown tier) |
| 3 | endpoint / transport error |
| 4 | max iterations reached with no clean sentinel |

Only the sentinel line goes to **stdout**; all progress goes to **stderr**, so an
outer loop can read the sentinel exactly as it does from `/openup-next`.

## Owner live-run checklist (program acceptance)

The program's acceptance test has two halves; this driver is the **non-Anthropic**
half. To run it end-to-end on a local model (owner runs LM Studio):

1. Start LM Studio's OpenAI-compatible server; note the base URL (typically
   `http://localhost:1234/v1`) and the model names it lists.
2. `export LLM_API_URL=http://localhost:1234/v1`; `export LLM_API_KEY=lm-studio`
   (any non-empty string LM Studio accepts).
3. Map the tiers to real models:
   `export OPENUP_MODEL_MAIN=<a-capable-local-model>` (and `_MID` / `_SMALL` if you
   want distinct tiers; otherwise all tiers can point at one model).
4. From a clean OpenUP project on a lane branch, run
   `python3 scripts/openup-agent.py run --dir . --procedure next`.
5. **Expected:** the loop advances one delivery cycle, the driver's fence +
   `check-docs.py` pass, and it prints an `OPENUP-NEXT: ADVANCED — <id>` (or `DONE`)
   sentinel — a fence-clean, validator-clean cycle on a non-Anthropic model.
6. Record the run outcome (model used, sentinel, any gate friction) in
   `docs/changes/T-072/design.md` as the read-back for this task's Success Measure.

> A weak local model may need more `--max-iterations` or a larger model for the
> `reasoning`-tier procedures. The driver's job is to make the loop *possible* and
> *enforced*; model capability is a separate, tunable variable.

## Layering

This is Layer 3 of the harness-optional program (exploration
`docs/explorations/2026-07-12-harness-agnostic-openup.md`). Layer 4 (a FastAPI
service over this driver, T-073) is **gated on a named consumer** and not built here.

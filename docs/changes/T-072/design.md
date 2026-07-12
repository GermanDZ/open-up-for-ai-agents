# T-072 — Design decisions (in-flight)

Living record of decisions made while building the reference driver. The spec
(`plan.md`) stays the contract; this captures the *why* behind implementation
choices and the read-back for the Success Measure.

## Base branch / lane

- Lane branched **off `harness-optional`** (not `main`), in-place (`worktree: false`),
  matching the T-071 precedent and the program rule "PRs target `harness-optional`;
  `main` stays clean." Iteration 43, phase construction, track **full**.

## Decisions

- **DD1 — Procedure-agnostic driver.** `loop.run` loads
  `docs-eng-process/procedures/openup-<procedure>.md` verbatim as the system prompt
  and lets the model drive via tools. No per-procedure logic is hardcoded, so every
  procedure in the pack (and future ones) works with zero driver changes. (spec Assumption 1)
- **DD2 — One model per run.** The driver resolves a single model from the top-level
  procedure's `tier:` via the tier-map `driver` column. Team/subagent procedures degrade
  to sequential (the loop has no fan-out). (spec Assumption 2)
- **DD3 — Stdlib-only.** HTTP via `urllib` (`llm.py`), YAML via the same minimal
  two-level parser `render-claude-adapter.py` already uses (`tiers.load_tier_map`),
  tests via `unittest` + `http.server`. No addition to `requirements.txt`. (spec Assumption 3)
- **DD4 — Six tools, `exec` allowlisted.** `read_file, write_file, edit_file, glob,
  grep, exec`. `glob` subsumes `list_dir` (the "list_dir/glob" slot). `exec` runs only
  `git …` or `python3 scripts/*.py …`, refusing anything else *without spawning a
  process* (`shlex.split`, no `shell=True`). Path traversal outside `--dir` is refused
  in every file tool. (spec Requirement 3 / Safeguard)
- **DD5 — Gates are driver-run, on sentinel.** When the model emits a terminal sentinel
  (`^OPENUP-[A-Z-]+:`), the driver runs `openup-fence.py check` + `check-docs.py` itself;
  a non-zero result is re-injected as a user message and the loop continues — the sentinel
  is only honored once gates are clean. Absent gate scripts are skipped so the driver
  stays usable on partial trees. (spec Requirement 5)
- **DD6 — Plan gate auto-proceeds.** No interactive plan-approval; the deterministic
  gates are the real enforcement. Interactive gating is a service concern (T-073). (spec Assumption 4)
- **DD7 — Test seam over live network.** `loop.run(_completion=…)` injects a scripted
  completion function for the loop tests (zero sockets, fully deterministic); a separate
  `HttpClientTest` spins a real `http.server` to exercise the urllib path + auth header +
  `model` field. Best of both: deterministic loop coverage + a real-HTTP proof.

## Verification results

- `test_openup_agent_tools.py` + `test_openup_agent.py`: **38/38 green** (hermetic).
- CLI end-to-end: `scripts/openup-agent.py run --dir <fixture> --procedure next` against a
  mock OpenAI server → exit 0, `OPENUP-NEXT: DONE — nothing to do` on stdout, tool
  dispatched, gates clean.
- Tier resolution proven against the **real** `tier-map.yaml` driver column
  (`reasoning → local-main`, override via `OPENUP_MODEL_MAIN`).

## Pre-existing test failures (NOT introduced by T-072)

Running the full `scripts/tests` suite shows **5 failures**, all reproduced identically
on a clean `harness-optional` worktree with none of the T-072 code present:

- `test_check_model_tiers`: 4 failures (`test_check_detects_drift`,
  `test_missing_model_field_is_flagged`, `test_quiet_suppresses_success_output`,
  `test_write_then_check_roundtrips`) — a test-isolation issue where the fixture reads the
  real repo tables.
- `test_docs_index.test_write_creates_index_file` — macOS `/var` → `/private/var` symlink
  string mismatch.

These live in `scripts/check-model-tiers.py` / `scripts/docs-index.py` territory, outside
the T-072 lane's `touches` — fixing them is a separate task (the write-fence would reject
touching them here). Flagged so they are not mistaken for regressions.

## DD8 — User-facing docs (scope addition, increment 2)

Owner feedback after increment 1: the config+usage guidance lived only in
`docs-eng-process/reference-driver.md` (framework internals) — not discoverable to a
*user* deciding how to run OpenUP. Fix-spec-first: `plan.md` touches + Structure +
Operations were extended, then:
- `reference-driver.md` expanded into a full user guide (quick start, env-var table,
  per-endpoint recipes for LM Studio / Ollama / vLLM / OpenAI, first-run walkthrough,
  exit-code + troubleshooting tables).
- `RUNNING-AGENTS.md` gained a first-class **"Running with the harness-free reference
  driver"** section alongside Cursor CLI / Claude Code, plus an Additional Resources link.
- `README.md` gained a "Harness-free / local models" pointer under *For AI Agents*.

No duplication: `RUNNING-AGENTS.md` / `README.md` summarize and link the single
source of truth (`reference-driver.md`).

## Read-back for the Success Measure

The falsifiable expectation (program acceptance, non-Anthropic half) is an **owner live
run** on LM Studio — see the checklist in `docs-eng-process/reference-driver.md`. Record
the outcome (model used, sentinel, gate friction) here when run. As of this task's
completion the loop is proven against a mock endpoint; the live-model run is the owner's
verification step (it needs the owner's local server, unreachable from CI).

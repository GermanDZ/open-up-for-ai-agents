---
type: reference
id: reference-driver-benchmark
status: living
title: Reference-driver benchmark harness (openup-agent-bench)
traces-from: [T-080, T-072]
---

# Reference-driver benchmark harness — `openup-agent-bench`

Run the T-072 reference driver (`openup-agent`) through one `/openup-next` cycle
on a **local / non-Anthropic model**, in an **isolated fresh project**, N times,
and get a **pass/fail + numeric benchmark** (pass rate, tokens, latency,
iterations, work-delta) you can regenerate on demand.

It exists for three jobs:

1. **AC-program acceptance** — the T-072 owner step ("one `--procedure next` cycle
   completes on a non-Anthropic/local model, fence-clean") turned into a scripted,
   recorded run instead of a one-off.
2. **Model benchmarking** — point it at different local models (or endpoints) and
   compare the summaries.
3. **Process-change regression** — change a skill / a procedure / a driver tool,
   re-run, and compare before/after (`--include-working-tree` benchmarks your
   *uncommitted* edits).

> **Stdlib-only, no install.** Like the driver, the harness needs only `python3`
> and `git`. It never writes to the repo under test.

---

## Quick start

```bash
# 1. Point at any OpenAI-compatible endpoint (local example: LM Studio)
export LLM_API_URL=http://localhost:1234/v1
export LLM_API_KEY=lm-studio                 # any non-empty string for local servers
export OPENUP_MODEL_MAIN=your-loaded-model   # a model your endpoint serves

# 2. From the repo under test, run a benchmark batch
python3 scripts/openup-agent-bench.py --repo . --runs 5

# 3. Read the summary
cat .openup/bench/<stamp>/summary.md
```

The last stdout line is a JSON one-liner (`{"out":…, "pass_rate":…,
"clean_passes":…, "runs":…}`); everything else is progress on stderr.

---

## How it works (per run)

1. **Isolate.** The repo under test is snapshotted with `git archive HEAD` (or the
   working tree with `--include-working-tree`) into a **fresh temp directory
   outside the project**, and `git init`'d — a brand-new project with no source
   history or remotes. The source repo is only read.
2. **Seed.** A scenario overlay adds one deterministic **micro-task** (default
   `quick-doc`: a single READY change-folder lane). The seed is committed, and the
   fence's default base (`origin/main`) is pointed at that seed commit — so the
   driver's own `openup-fence.py check` and the harness's re-check judge **only the
   driver's own work**, never the framework. *(This is what a clean git-init
   fixture buys you: it avoids the `origin/main`-vs-integration-branch base
   artifact that broke earlier informal runs.)*
3. **Sanity-check.** `openup-board.py resolve` on the fixture must return
   `pick` for the seeded lane (recorded as `seed_resolves_pick`).
4. **Drive.** `openup-agent.py run --dir <fixture> --procedure next` runs as a
   subprocess (exactly what a user runs), with `OPENUP_AGENT_USAGE_LOG` capturing
   per-call tokens + latency and a wall-clock `--timeout`.
5. **Measure — never trusting the model.** Outcome comes from the driver's typed
   exit code; gate-cleanliness and work-delta are **recomputed on the fixture**;
   tokens/latency come from the usage log.
6. **Aggregate.** All runs fold into `results.jsonl` + `summary.json` +
   `summary.md` under `--out` (default `<repo>/.openup/bench/<stamp>/`).

---

## CLI

```
python3 scripts/openup-agent-bench.py [--repo .] [--runs N] [--procedure next]
    [--scenario DIR] [--out DIR] [--workdir DIR] [--max-iterations 50]
    [--timeout 1800] [--include-working-tree] [--keep]
```

| Flag | Purpose |
|---|---|
| `--repo` | Repo under test (default cwd). Read-only. |
| `--runs N` | Number of runs in the batch (default 1). |
| `--procedure` | Procedure to drive (default `next`; any pack procedure works). |
| `--scenario DIR` | Scenario dir (default `scripts/bench-scenarios/quick-doc`). |
| `--out DIR` | Results dir (default `<repo>/.openup/bench/<stamp>`). |
| `--workdir DIR` | Where fixtures are built (default a fresh temp dir, removed after unless `--keep`). |
| `--max-iterations` | Driver turn cap per run (default 50). |
| `--timeout` | Per-run wall-clock cap, seconds (default 1800). |
| `--include-working-tree` | Seed from the repo's **uncommitted** tracked changes — to benchmark in-progress skill/procedure/tool edits. |
| `--keep` | Keep fixtures (and record their paths) for debugging. |

Endpoint/model come from the **same env as the driver** (`LLM_API_URL`,
`LLM_API_KEY`, `OPENUP_MODEL_MAIN/MID/SMALL`) — see
[reference-driver.md](reference-driver.md).

### Per-endpoint recipes

```bash
# LM Studio          (Local Server tab → Start)
export LLM_API_URL=http://localhost:1234/v1 LLM_API_KEY=lm-studio OPENUP_MODEL_MAIN=<model>
# Ollama             (ollama serve; OpenAI-compat on /v1)
export LLM_API_URL=http://localhost:11434/v1 LLM_API_KEY=ollama   OPENUP_MODEL_MAIN=<model>
# vLLM               (python -m vllm.entrypoints.openai.api_server …)
export LLM_API_URL=http://localhost:8000/v1  LLM_API_KEY=x        OPENUP_MODEL_MAIN=<model>
# Hosted OpenAI
export LLM_API_URL=https://api.openai.com/v1 LLM_API_KEY=sk-…     OPENUP_MODEL_MAIN=gpt-4o-mini
```

---

## Metrics (per run + aggregate)

| Field | Meaning |
|---|---|
| `outcome` | `pass` · `config-error` (2) · `endpoint-error` (3) · `max-iterations` (4) · `suspended` (5) · `timeout` — from the driver exit code. |
| `sentinel` | The `OPENUP-…` line the driver printed (or `null`). |
| `gates.fence` / `gates.check_docs` | Post-run re-check on the fixture (base = seed commit). |
| `iterations` | LLM calls to completion (from the usage log). |
| `wall_ms`, `latency_ms` | Run wall-clock; per-call latency total/mean. |
| `tokens` | Prompt / completion / total, summed over the run. |
| `work.deliverable_produced` | Ground truth: the scenario's deliverable file really exists with its marker. |
| `work.commits`, `work.files_changed`, `work.task_archived` | What the driver committed / changed / completed on the fixture. |

A **clean pass** (the pass-rate numerator) requires `outcome == pass` **and** both
gates clean **and** the deliverable produced — the model reaching a sentinel is not
enough.

### Comparing two batches

Run a batch, change a model (or a skill/procedure/tool, with
`--include-working-tree`), run another, and diff the two `summary.md` /
`summary.json`. `pass_rate`, `tokens_total.mean`, `iterations.mean`, and
`wall_ms.mean` are the headline comparison numbers; the `outcome_histogram` shows
*how* failures shifted.

---

## AC-program pass criterion

The T-072 program-acceptance (non-Anthropic half) is met when a `quick-doc` batch
on a local model reports **at least one clean pass** — a real cycle that reached
its sentinel with fence + check-docs clean and the deliverable produced. Record the
batch under `.openup/bench/` and note the model + pass rate in the T-072/T-080
completion trail.

---

## The two built-in scenarios

| Scenario | What it benchmarks | How |
|---|---|---|
| `quick-doc` (default) | Can the model **drive the `next` continue-loop** to complete a trivial seeded lane? | Seeds one READY change-folder lane; drives `next`; success = a one-line edit + clean cycle. |
| `inception-vision` | Can the model turn a **stakeholder brief into a Vision doc** — the framework's real first-iteration value? | Seeds a fresh project + `docs/inputs/stakeholder-brief.md`; drives `openup-create-vision` with an `--instruction` to read the brief; success = a `docs/vision.md` containing the required sections. |

```bash
# The realistic "stakeholder brief → Vision" benchmark:
python3 scripts/openup-agent-bench.py --repo . --runs 5 \
    --scenario scripts/bench-scenarios/inception-vision
```

`inception-vision` drives a **single authoring procedure** (not the full `next`
ceremony), so it is far cheaper and more deterministic — the tightest measure of
"can this model produce a valid vision from a brief."

## Authoring a new scenario

A scenario is a directory with a `scenario.json` and an `overlay/` tree copied onto
the fixture before the seed commit. `scenario.json` keys:

| Key | Purpose |
|---|---|
| `name`, `description` | Identity. |
| `procedure` | Default procedure to drive (e.g. `openup-create-vision`). A `--procedure` flag overrides it. |
| `instruction` | Passed to the driver as `--instruction` — extra task context (e.g. "read the brief at … and produce the vision"). |
| `expect_pick` | **Optional.** A change-folder lane id `resolve` must pick. Present ⇒ the harness asserts `resolve == pick` before running (lane-based scenarios like `quick-doc`). Omit for procedure-direct scenarios (like `inception-vision`) that seed no lane. |
| `deliverable_file` + `required_markers` | The ground-truth success check: the file must exist and contain **every** marker in the list. `missing_markers` in the record shows which were absent (so a partial result is diagnosable). `deliverable_marker` (single string) is the back-compat form. |

Keep the deliverable check anchored on **brief-fidelity + structural markers** (for
`inception-vision`: the project name `ShareShed` plus `Problem` / `Stakeholder` /
`Success`) so it proves the model both *used the input* and *produced the artifact's
shape* — not that it solved a hard problem.

> **Non-lane procedures and the fence.** A procedure-direct run (no
> start-iteration, so no lane/state) has nothing for the write-fence to check — the
> fence returns exit 3 ("no task"), which the driver and the harness both treat as
> **inapplicable (skip)**, not a failure. `check-docs` still validates the output. A
> run inside a real started lane is still fully fenced.

---

## CI / hermetic validation

`scripts/tests/test_openup_agent_bench.py` drives the whole harness against a
scripted local `http.server` (no live model), covering fixture isolation, seeding,
`resolve == pick`, usage capture, the gate re-check + work-delta, and aggregation.
The live-model batch stays the owner's step — this doc is its runbook.

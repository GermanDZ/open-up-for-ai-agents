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

## Authoring a new scenario

A scenario is a directory with:

- `scenario.json` — `{name, description, expect_pick, deliverable_file,
  deliverable_marker}`. `expect_pick` is the lane id `resolve` must pick;
  `deliverable_file` + `deliverable_marker` are the ground-truth work check.
- `overlay/` — a file tree copied onto the fixture before the seed commit (e.g. a
  `docs/changes/<id>/plan.md` defining a READY lane).

Point the harness at it with `--scenario path/to/dir`. Keep the deliverable trivial
and inside the lane's declared `touches` so a clean cycle is fence-clean by
construction — the benchmark measures whether the driver can *drive the process*,
not solve a hard problem.

---

## CI / hermetic validation

`scripts/tests/test_openup_agent_bench.py` drives the whole harness against a
scripted local `http.server` (no live model), covering fixture isolation, seeding,
`resolve == pick`, usage capture, the gate re-check + work-delta, and aggregation.
The live-model batch stays the owner's step — this doc is its runbook.

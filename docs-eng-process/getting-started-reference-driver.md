---
type: reference
id: getting-started-reference-driver
status: living
title: Getting started with the reference driver (your own harness + your own LLM)
traces-from: [T-072, T-087]
---

# Getting started — run OpenUP with your own harness + your own LLM

Run OpenUP with **no Claude Code and no Anthropic account** — just the reference
driver (`openup-agent`) and any **OpenAI-compatible** chat-completions endpoint (a
local model in LM Studio / Ollama / vLLM, or hosted OpenAI). The driver reads the
neutral procedure pack and runs the deterministic OpenUP scripts itself; the LLM is
needed only for the judgment steps (authoring the vision, a use case, code).

This guide is task-oriented and covers two common starting points:

- **[Scenario A — a brand-new project](#scenario-a--a-brand-new-project)**
- **[Scenario B — an existing project adopting OpenUP](#scenario-b--an-existing-project-adopting-openup)** (incl. backfilling the docs it's missing)

> For the driver's full reference (every flag, env var, exit code, tool) see
> [reference-driver.md](reference-driver.md). For the Claude Code path instead, see
> [QUICKSTART.md](QUICKSTART.md) / [getting-started.md](getting-started.md).

---

## Prerequisites (both scenarios)

1. **`python3` (3.8+) and `git`.** The driver is stdlib-only — nothing to `pip install`.
2. **An OpenAI-compatible endpoint**, configured via environment variables:

   ```bash
   export LLM_API_URL=http://localhost:1234/v1     # your endpoint (…/v1)
   export LLM_API_KEY=lm-studio                    # any non-empty string for local servers
   export OPENUP_MODEL_MAIN=your-loaded-model      # reasoning / quality-gate tiers
   export OPENUP_MODEL_MID=your-loaded-model       # authoring tier (vision, use cases, code)
   export OPENUP_MODEL_SMALL=your-loaded-model     # scribe / coordination tiers
   export OPENUP_AGENT_TIMEOUT=600                 # per-call seconds; raise for slow local models
   ```

   Set all three `OPENUP_MODEL_*` to the same model if you only have one. **Why
   `MID` matters:** the authoring procedures (`openup-create-vision`,
   `openup-create-use-case`, …) resolve to the `authoring` tier, i.e.
   `OPENUP_MODEL_MID` — not `MAIN`. Verify the endpoint responds:

   ```bash
   curl -s "$LLM_API_URL/models" -H "Authorization: Bearer $LLM_API_KEY" | head
   ```

3. **The driver call you'll use throughout:**

   ```bash
   python3 scripts/openup-agent.py run --dir <project> --procedure <name> \
       [--instruction "extra task context"] [--max-iterations N]
   ```

   It prints the procedure's `OPENUP-…:` sentinel to **stdout** and exits 0 on a
   clean, gate-passing finish; all progress goes to **stderr**.

---

## Scenario A — a brand-new project

### 1. Bootstrap a fresh project

```bash
# from a clone of the framework:
bash scripts/bootstrap-project.sh my-product --base-dir ~/projects
cd ~/projects/my-product
```

This creates a new git repo with the framework (`docs-eng-process/` + the process
CLIs in `scripts/`) and an empty `docs/`. Export the env from
[Prerequisites](#prerequisites-both-scenarios) in this shell.

### 2. Give it a stakeholder brief

OpenUP's first Inception activity (`initiate-project`) turns a stakeholder brief
into a **Vision**. Write yours as a plain markdown file:

```bash
mkdir -p docs/inputs
$EDITOR docs/inputs/stakeholder-brief.md   # who's it for, the problem, desired outcomes, constraints, out-of-scope
```

*(No brief handy? See `scripts/bench-scenarios/inception-vision/overlay/docs/inputs/stakeholder-brief.md`
for a worked example.)*

### 3. Produce the Vision

```bash
python3 scripts/openup-agent.py run --dir . --procedure openup-create-vision \
    --instruction "Read the stakeholder brief at docs/inputs/stakeholder-brief.md, then produce the project Vision at docs/vision.md following the create-vision procedure — derive the project name, problem statement, proposed solution, stakeholders, key features, and success criteria from the brief."
```

The `--instruction` flag is how you hand an authoring procedure its input (these
procedures normally take arguments; the driver has none otherwise). When it
finishes, read `docs/vision.md`. This exact flow is the T-072 acceptance test —
proven on a local non-Anthropic model.

### 4. Continue Inception → Elaboration

Drive the remaining phase activities the same way (one procedure per artifact). The
Inception activity order (from `process-map.yaml`) is:

| Activity | Procedure | Produces |
|---|---|---|
| initiate-project | `openup-create-vision` | `docs/vision.md` |
| identify-refine-requirements | `openup-create-use-case` (then `openup-detail-use-case`) | use cases |
| plan-manage-iteration | `openup-create-risk-list`, `openup-create-iteration-plan` | risk list, iteration plan |
| agree-technical-approach (Elaboration) | `openup-create-architecture-notebook` | architecture notebook |

```bash
python3 scripts/openup-agent.py run --dir . --procedure openup-create-use-case \
    --instruction "Derive the primary use cases from docs/vision.md."
python3 scripts/openup-agent.py run --dir . --procedure openup-create-risk-list \
    --instruction "Derive the initial risk list from docs/vision.md and the use cases."
```

Inspect each output, refine the input, re-run if needed — same as a human analyst
iterating a draft.

### 5. Deliver with iterations

Once the product docs exist, drive delivery cycles:

```bash
python3 scripts/openup-agent.py run --dir . --procedure next --max-iterations 40
```

`next` runs **one full continue-loop cycle** (resolve → start-iteration → work →
complete-task). **Heads-up on local models:** the full `next` ceremony is
token-heavy and takes many turns — a small local model may not converge within
`--max-iterations` even when it does the work. The single-procedure authoring runs
above are far cheaper and more reliable; lean on those for Inception/Elaboration,
and use a stronger model (or a higher `--max-iterations`) for `next`.

---

## Scenario B — an existing project adopting OpenUP

You already have a codebase and want to start running OpenUP on it — which means
**creating the OpenUP docs the project is missing** from what already exists.

### 1. Add the framework to your repo

From your project root, install the framework files (the process CLIs + the
procedure pack) without disturbing your code:

```bash
# option 1 — versioned installer (fetches/syncs the framework):
bash /path/to/open-up-for-ai-agents/scripts/install-openup.sh

# option 2 — copy the two framework trees in directly:
cp -r /path/to/open-up-for-ai-agents/docs-eng-process .
cp -r /path/to/open-up-for-ai-agents/scripts .          # merge, don't clobber your own scripts/
```

Then create the `docs/` skeleton if absent (`mkdir -p docs`) and export the env
from [Prerequisites](#prerequisites-both-scenarios).

### 2. Find what's missing

There is **no automated "which product docs am I missing" detector** today
(`python3 scripts/openup-doctor.py` checks the shipped CLIs + state integrity, not
product docs). Use this manual checklist of the core OpenUP artifacts:

| Artifact | Expected path | Backfill procedure |
|---|---|---|
| Vision | `docs/vision.md` | `openup-create-vision` |
| Use cases | `docs/` (project use-case docs) | `openup-create-use-case` / `openup-detail-use-case` |
| Architecture notebook | `docs/` (architecture doc) | `openup-create-architecture-notebook` |
| Risk list | `docs/` (risk list) | `openup-create-risk-list` |
| Roadmap + status | `docs/roadmap.md`, `docs/project-status.md` | created as you plan/run iterations |

> An automated "adopt / backfill gaps" helper (detect missing artifacts, queue the
> backfill runs) is a sensible **future enhancement** — not built yet.

### 3. Backfill each missing doc *from the existing code*

This is the key difference from Scenario A: instead of a stakeholder brief, you
point the same authoring procedures at your **codebase** with `--instruction`, so
the model reverse-engineers the artifact from what's actually there:

```bash
# Vision — inferred from the code + README:
python3 scripts/openup-agent.py run --dir . --procedure openup-create-vision \
    --instruction "This is an EXISTING project. Read README.md and the code under src/ (use glob/grep/read_file), then reverse-engineer docs/vision.md — the problem it solves, its users/stakeholders, the key features it ALREADY has, and reasonable success criteria. Describe what exists, not aspirations."

# Architecture notebook — documented from the current code:
python3 scripts/openup-agent.py run --dir . --procedure openup-create-architecture-notebook \
    --instruction "Document the CURRENT architecture from the code: the major components under src/, how they interact, key technology choices, and the significant decisions evident in the codebase."

# Use cases — for the main existing flows:
python3 scripts/openup-agent.py run --dir . --procedure openup-create-use-case \
    --instruction "Write use cases for the main user-facing flows already implemented (find them via the routes/handlers/entrypoints in the code)."
```

Review each generated doc against reality — this is a *draft from the code*, and a
human should correct it before it becomes the project's source of truth. Re-run
with a sharper `--instruction` (e.g. naming the exact dirs) if a draft misses the mark.

### 4. Continue normally

Once the baseline docs exist and are corrected, adopt the normal loop — plan an
iteration and deliver:

```bash
python3 scripts/openup-agent.py run --dir . --procedure next --max-iterations 40
```

(Same local-model caveat as Scenario A step 5.)

---

## Tips

- **Read the output, then refine the input.** Every authoring run is a *draft*.
  Inspect the file, sharpen the `--instruction`, re-run — cheaper than one perfect prompt.
- **Slow model?** Raise `OPENUP_AGENT_TIMEOUT` (a slow response is surfaced as a
  clean error, never a crash) and `--max-iterations`.
- **See what happened.** Progress + any `FATAL:` reason go to stderr; the sentinel
  is the one stdout line.
- **Benchmark your model / a process change** with
  [reference-driver-benchmark.md](reference-driver-benchmark.md)
  (`scripts/openup-agent-bench.py`) before trusting it on real work.

## See also

- [reference-driver.md](reference-driver.md) — the driver's full reference.
- [reference-driver-benchmark.md](reference-driver-benchmark.md) — measure a model
  / a process change.
- [QUICKSTART.md](QUICKSTART.md), [getting-started.md](getting-started.md) — the
  Claude Code path.

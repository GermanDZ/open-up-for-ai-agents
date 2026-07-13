---
id: T-080
title: Reference-driver acceptance/benchmark harness (repeatable AC-program runner)
status: ready   # proposed → ready → in-progress → done → verified
priority: high   # critical | high | medium | low
estimate: 1-2 sessions
plan: docs/explorations/2026-07-12-harness-agnostic-openup.md
depends-on: [T-072]
blocks: []
touches:
  - scripts/openup-agent.py
  - scripts/openup_agent/loop.py
  - scripts/openup-agent-bench.py
  - scripts/bench-scenarios/
  - scripts/tests/test_openup_agent_bench.py
  - docs-eng-process/reference-driver-benchmark.md
  - docs-eng-process/script-cli-reference.md
  - docs/changes/
last-synced: ""
---

# T-080 — Reference-driver acceptance/benchmark harness

## Story

> **As** the owner of the harness-optional program
> **I want** a repeatable, isolated harness that drives the T-072 reference driver
> (`openup-agent`) through one `/openup-next` cycle on a local/non-Anthropic model
> and records outcome, gate-cleanliness, latency, iterations, work-delta, and token
> usage per run
> **So that** I can (a) finally run the T-072 **AC-program** live acceptance test —
> the owner step that never got recorded — and re-run it on demand, (b) **benchmark**
> different local models across many runs, and (c) **regression-test** changes to
> skills / the procedure pack / the driver tools by comparing runs before and after.

INVEST — ✅ Independent (wraps delivered T-072; nothing depends on it) · ✅ Negotiable · ✅ Valuable (unblocks the AC-program measurement + model benchmarking + process-change regression) · ✅ Estimable · ✅ Small (one runner script + one additive loop hook + a seed scenario + a plan doc) · ✅ Testable (hermetic mock-endpoint run of the whole harness)

## Analysis Context

- **The test being made repeatable.** T-072's `plan.md`/`handoff.md` leaves one
  criterion open — **AC-program**: "one `--procedure next` cycle completes on a
  **non-Anthropic/local model** producing fence-clean, validator-clean output."
  The driver is proven against a *mock* endpoint (41 hermetic tests green); the
  live-model run is the owner step, was attempted informally, errored, and was
  never recorded (`docs/changes/archive/T-072/design.md` §live run). This task
  turns that one-off owner step into a **scripted, isolated, instrumented** run
  that can be executed N times.
- **What T-072 already delivers (do NOT re-spec).** `scripts/openup-agent.py run
  --dir --procedure` + the `openup_agent/` package (`loop.py`, `llm.py`, `tiers.py`,
  `tools.py`): a stdlib-only OpenAI-compatible agentic loop that reads the neutral
  procedure pack, resolves ONE model per procedure `tier:` via the `tier-map.yaml`
  driver column, advertises the six-tool surface, runs the deterministic gates
  (`openup-fence.py check`, `check-docs.py`) itself, and exits with a **typed code**
  — `0` clean sentinel · `2` config/tier · `3` endpoint · `4` max-iterations ·
  `5` suspended-for-input. Config is env (`LLM_API_URL`, `LLM_API_KEY`,
  `OPENUP_MODEL_MAIN/MID/SMALL`). Run doc: `docs-eng-process/reference-driver.md`.
- **The one gap for benchmarking.** The loop **discards** the completions `usage`
  object, so tokens/latency per call are unobservable. This task adds a **single
  additive capture hook** (an env-gated per-call jsonl) — zero behavior change when
  the env is unset — rather than changing the loop's contract.
- **Isolation model (owner decision, this task — refined mid-flight).** Each run
  executes against a **fresh, freshly-`git init`'d project built OUTSIDE the repo
  under test** (owner requirement: "a new directory, a new git project"). The repo
  is snapshotted with `git archive HEAD` (or the working tree, with
  `--include-working-tree`) into a temp dir and `git init`'d — no source history or
  remotes. It is seeded with a **tiny deterministic micro-task** (one READY
  change-folder lane) so `resolve` picks it at §1b (ahead of the real, gated
  backlog like T-073). The real repo is never touched; runs are reproducible. A
  clean git-init fixture also **removes the `origin/main`-vs-integration-branch
  fence-base artifact** that broke earlier informal runs — the seed commit is the
  fence base.
- **Scope boundary.** This is a **test/measurement harness** — it does not change
  the driver's behavior (only adds an opt-in usage log), the procedure pack, or the
  micro-increment layer. It runs on `harness-optional` (where the driver lives).
- **Definition of done.** `openup-agent-bench.py` runs the driver N times against
  isolated seeded fixtures, capturing outcome + gate re-check + latency/iterations +
  work-delta + tokens, and aggregates to `results.jsonl` + a `summary.md`; the
  additive usage hook lands in `loop.py`; a built-in seed scenario exists; the whole
  harness is validated hermetically against a mock endpoint (no live model needed in
  CI); the test plan documents how to run it live; fence green against
  `--base harness-optional`.

> **Assumption:** the usage hook is a new **env var `OPENUP_AGENT_USAGE_LOG`** — a
> path the loop appends `{iteration, model, usage, latency_ms}` to per completion;
> unset ⇒ no file, no behavior change. *(Vetoable at review.)*
> **Decision (owner, mid-flight):** the fixture is a **fresh `git init` project
> built from `git archive HEAD`** (or the working tree) into a temp dir OUTSIDE the
> repo — a brand-new git project, per the owner's requirement — not a
> `git clone`. This gives full isolation AND a clean base ref (the seed commit),
> sidestepping the fence's `origin/main` base artifact.
> **Assumption:** the default scenario `quick-doc` seeds ONE `quick`-track READY
> change-folder lane whose single `## Operations` step is a trivial deterministic
> edit (append a line to a scratch doc under its own `touches`), so a completed
> cycle is fence-clean by construction and cheap in tokens. Scenarios are pluggable
> (`--scenario <dir>`). *(Vetoable at review.)*
> **Assumption:** the harness itself is stdlib-only (mirrors the driver) and runs
> the driver as a subprocess so the measured process is exactly what a user runs —
> not an in-process import. *(Vetoable at review.)*

## Requirements

1. **Additive per-call usage capture in the loop.** When `OPENUP_AGENT_USAGE_LOG`
   is set, `loop.run` appends one JSON line per completion —
   `{iteration, model, latency_ms, usage:{prompt_tokens, completion_tokens,
   total_tokens}}` (usage copied verbatim from the endpoint response, `{}` if the
   endpoint omits it) — to that path. Unset ⇒ the file is never opened and behavior
   is byte-for-byte unchanged.
   - **Given** `OPENUP_AGENT_USAGE_LOG=/tmp/u.jsonl` and a 2-iteration run **When**
     the loop finishes **Then** `/tmp/u.jsonl` has 2 lines, each with `iteration`,
     `model`, `latency_ms`, and a `usage` object.
   - **Given** the env var is unset **When** the loop runs **Then** no usage file is
     created and the existing tests pass unchanged.

2. **`openup-agent-bench.py` runs an isolated, seeded fixture per run.** For each of
   `--runs N`: it snapshots `--repo` with `git archive HEAD` (or the working tree)
   into a temp dir OUTSIDE the repo, `git init`s it, applies the scenario seed and
   commits it (that seed commit becomes the fence base via `origin/main`), then runs
   `openup-agent.py run --dir <fixture> --procedure <p>` as a subprocess with
   `OPENUP_AGENT_USAGE_LOG` pointed into the fixture and a wall-clock `--timeout`.
   The real repo is never written to; fixtures are removed after capture unless
   `--keep`.
   - **Given** `--repo <clean-repo> --runs 2` **When** the harness runs **Then** two
     independent fixtures are cloned+seeded+driven and the source repo's
     `git status` is unchanged.
   - **Given** `--include-working-tree` **When** a fixture is built **Then** the
     source's uncommitted tracked diff is applied into the fixture before seeding.

3. **A built-in, pluggable seed scenario.** `quick-doc` (default) seeds one
   `quick`-track READY change-folder lane (`plan.md` with board-readable
   frontmatter + a one-step `## Operations`) via an `overlay/` tree, such that
   `openup-board.py resolve` on the fixture returns `pick` for that lane (not the
   repo's real backlog — no roadmap row is needed because a READY change folder is
   picked at §1b). `--scenario <dir>` overlays a custom scenario directory instead;
   `scenario.json` carries `expect_pick` + the deliverable ground-truth check.
   - **Given** the seeded fixture **When** `openup-board.py resolve` runs on it
     **Then** `path == "pick"` and `lane.task` is the seeded id.

4. **Per-run metric capture — all four groups.** After each run the harness records
   a run record with: **outcome** (exit code → `pass|config-error|endpoint-error|
   max-iterations|suspended|timeout`) + the **sentinel** line + a **post-run gate
   re-check** (`openup-fence.py check --base <seed>` and `check-docs.py` on the
   fixture); **latency** (run wall-clock + per-call latencies from the usage log) +
   **iteration count**; **work-delta** (commits added over the seed, files changed,
   and whether the seeded task reached `done`/archived); **tokens** (prompt/
   completion/total summed from the usage log).
   - **Given** a completed run **When** the record is written **Then** it carries
     `outcome`, `sentinel`, `gates:{fence,check_docs}`, `iterations`, `wall_ms`,
     `tokens:{prompt,completion,total}`, and `work:{commits,files_changed,task_done}`.

5. **Aggregation across runs.** The harness writes `results.jsonl` (one record per
   run) and a human `summary.md` to `--out` (default a timestamped dir under
   `.openup/bench/`), reporting **pass rate**, mean/median **iterations**, **wall
   time**, and **total tokens**, plus an **outcome histogram** — so two benchmark
   batches (e.g. model A vs B, or before/after a skill change) are directly
   comparable.
   - **Given** `--runs 3` **When** the batch finishes **Then** `results.jsonl` has 3
     lines and `summary.md` reports pass-rate + mean iterations/tokens/wall over the 3.

6. **Hermetic validation (no live model).** A test drives the whole harness against
   a **mock endpoint** (a scripted local `http.server`, reusing T-072's test seam
   style) so fixture setup, seeding, `resolve==pick`, metric capture, and
   aggregation are all exercised in CI without any real LLM. The live run stays the
   owner's step, documented in the test plan.
   - **Given** the mock-endpoint test **When** the suite runs **Then** a full
     bench batch completes, a `results.jsonl` + `summary.md` are produced, and the
     recorded outcome/tokens/work-delta match the mock's scripted behavior.

7. **The test plan documents how to run it live + interpret results.**
   `docs-eng-process/reference-driver-benchmark.md` covers: purpose (AC-program +
   benchmarking + process-change regression), the isolation/scenario model, env +
   flags, per-endpoint recipes (LM Studio / Ollama / vLLM), the metric definitions,
   how to compare two batches, and the AC-program pass criterion.
   - **Given** the doc **When** a maintainer follows it **Then** they can run a batch
     against a local endpoint and read a pass/fail + benchmark summary.

## Behavior Delta

Affected artifacts are **process/test tooling**, not Ring-1 `docs/product/` use
cases — this framework repo's "product" is the process; the driver + its harness are
tooling under `scripts/`.

**Added** — behavior that did not exist before:
- `scripts/openup-agent-bench.py` — the repeatable isolated benchmark runner.
- Built-in seed scenario(s) under `scripts/bench-scenarios/`.
- `OPENUP_AGENT_USAGE_LOG` opt-in per-call usage capture in `loop.py`.
- `docs-eng-process/reference-driver-benchmark.md` — the test plan.

**Modified** — behavior that changes; cite the source:
- `scripts/openup_agent/loop.py` — one additive env-gated usage-log write in the
  completion path (no contract change; the driver's exit codes / sentinel / gates
  are untouched). Source: `docs-eng-process/reference-driver.md` (config table gains
  the optional env var).

**Removed** — none.

## Success Measures

The T-072 **AC-program** metric moves from **"never recorded"** to a **repeatable
pass/fail with a numeric benchmark** (pass rate, mean tokens, mean iterations, mean
wall-clock over N runs) that a maintainer can regenerate on demand. Instrumentation:
the harness's own `summary.md`, plus the hermetic mock-endpoint test proving the
pipeline. Read-back: the owner's first live batch against LM Studio (recorded under
`.openup/bench/`), and thereafter every time a model or a skill/procedure/tool change
is benchmarked.

## Rollout

**Flagged?** No. The harness is a **new standalone script** (absent code cannot
misfire) and the only edit to shipped behavior — the loop's usage log — is **gated
on an env var that defaults unset**, so the driver a user runs today is byte-for-byte
unchanged unless they opt in. `n/a — additive script + env-gated hook; no default
behavior change.`

## Entities

- **`openup-agent-bench.py`** (new) — the isolated, instrumented batch runner.
- **`openup_agent/loop.py`** (modified) — additive `OPENUP_AGENT_USAGE_LOG` capture.
- **`scripts/bench-scenarios/quick-doc/`** (new) — the default seed scenario.
- **Reference driver `openup-agent.py run`** (invoked, unchanged) — the subject.
- **`openup-board.py resolve` / `openup-fence.py` / `check-docs.py`** (invoked,
  read-only) — resolve picks the seeded lane; the gates are the post-run re-check.
- **`docs-eng-process/reference-driver-benchmark.md`** (new) — the test plan.

## Approach

Wrap, don't reshape. The driver already exits with typed codes and prints a single
sentinel — the harness treats it as a black box run as a subprocess (exactly what a
user runs), and derives outcome from the exit code. The one thing the black box
can't tell us — tokens/latency per call — is added as an **opt-in side channel**
(`OPENUP_AGENT_USAGE_LOG`) so the driver's contract is untouched and unit tests stay
green. Reproducibility comes from **cloning to a throwaway fixture and seeding a
deterministic micro-task** so every run does comparable work and `resolve` never
wanders into the real (gated) backlog; the real repo is read-only. Everything the
harness needs to judge a run — did it reach a clean sentinel, are the gates clean,
what did it commit — is recomputed deterministically on the fixture after the run,
so the measurement never trusts the model's self-report. Stdlib-only, mirroring the
driver, so the harness has the same zero-install footprint.

## Structure

**Add:**
- `scripts/openup-agent-bench.py` — clone→seed→run→measure→aggregate (stdlib-only).
- `scripts/bench-scenarios/quick-doc/` — the default seed (plan.md + roadmap row +
  a seed manifest the runner applies).
- `scripts/tests/test_openup_agent_bench.py` — hermetic mock-endpoint batch test.
- `docs-eng-process/reference-driver-benchmark.md` — the test plan.

**Modify:**
- `scripts/openup_agent/loop.py` — env-gated per-call usage-log append.
- `docs-eng-process/reference-driver.md` — document the optional
  `OPENUP_AGENT_USAGE_LOG` env var (config table).
- `docs-eng-process/script-cli-reference.md` — register `openup-agent-bench.py`.

**Do not touch:**
- The driver's loop contract (exit codes, sentinel, gates, tool surface) — only the
  additive usage side channel.
- The procedure pack, the board/fence/claims machinery, `.claude/` mirror.

## Operations

- [x] Add env-gated `OPENUP_AGENT_USAGE_LOG` per-call capture to
  `scripts/openup_agent/loop.py` (iteration, model, latency_ms, usage) + a unit test
  for the set and unset paths; document the env var in `reference-driver.md`.
- [x] Build `scripts/bench-scenarios/quick-doc/` — a deterministic seed (one
  quick-track READY change-folder lane + roadmap row) that `openup-board.py resolve`
  picks; assert `resolve == pick` on the seeded fixture.
- [x] Write `scripts/openup-agent-bench.py` — clone-isolate + seed + subprocess-run
  the driver (timeout, usage-log) + post-run measurement (outcome, gate re-check,
  latency/iterations, work-delta, tokens) + `results.jsonl` + `summary.md`
  aggregation; `--repo/--runs/--procedure/--scenario/--out/--timeout/--max-iterations/
  --include-working-tree/--keep` flags; stdlib-only.
- [x] Author `scripts/tests/test_openup_agent_bench.py` — drive the whole harness
  against a mock endpoint (scripted `http.server`), asserting fixture isolation,
  seeding, metric capture, and aggregation with no live model.
- [x] Write `docs-eng-process/reference-driver-benchmark.md` (purpose, isolation/
  scenario model, env+flags, per-endpoint recipes, metric definitions, batch
  comparison, AC-program pass criterion); register the script in
  `script-cli-reference.md`.
- [x] (tester) Run the driver + bench test suites + `check-docs.py` +
  `openup-fence.py check --base harness-optional`; confirm green.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.).
- `.claude/CLAUDE.openup.md` — derive-don't-author, edit-the-pack, stay-in-lane.
- `docs-eng-process/model-tiers.md` — tier names, not model strings, in the pack.

## Safeguards

- **The real repo is read-only.** Every run works a `git clone --local` fixture in a
  temp dir; the source is only read (and optionally `git diff`ed for
  `--include-working-tree`). Fixtures are torn down unless `--keep`.
- **No default behavior change to the driver.** The usage log is env-gated and
  defaults off; the driver's exit codes / sentinel / gates / tools are untouched.
- **Measurement never trusts the model.** Outcome comes from the process exit code;
  gate-cleanliness and work-delta are recomputed deterministically on the fixture
  after the run.
- **Deterministic scenario.** The seeded micro-task makes `resolve` pick a known
  small lane, so runs are comparable and never start the real (gated) backlog (T-073).
- **Reversibility.** Purely additive: a new script + scenario + doc + one env-gated
  loop line. Nothing existing changes shape.
- **Base is `harness-optional`.** Branch off and fence against it
  (`openup-fence.py check --base harness-optional`); do not run `complete-task`
  verbatim (it hardcodes `main`).

## Verification

- `OPENUP_AGENT_USAGE_LOG=<f>` yields one jsonl line per completion with tokens +
  latency; unset yields no file and unchanged driver tests.
- `openup-agent-bench.py --repo <clean> --runs 2` leaves the source repo's
  `git status` clean and produces `results.jsonl` (2 lines) + `summary.md`.
- `openup-board.py resolve` on a seeded fixture returns `pick` for the seeded id.
- The mock-endpoint harness test completes a full batch in CI with no live model.
- Driver + bench suites + `check-docs.py`(+`--coverage`) green; `openup-fence.py
  check --base harness-optional` green.
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-080/plan.md` exits 0.

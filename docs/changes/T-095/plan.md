---
id: T-095
title: scripts/next-cycle — one guided command from empty project to delivery loop
status: ready   # proposed → ready → in-progress → done → verified
priority: high   # critical | high | medium | low
estimate: 1 session
plan: docs/explorations/2026-07-13-deterministic-cycle-engine.md
depends-on: [T-094]
blocks: []
touches:
  - scripts/next-cycle
  - scripts/process-manifest.txt
  - scripts/tests/test_next_cycle.py
  - docs-eng-process/reference-driver.md
  - docs-eng-process/script-cli-reference.md
  - docs-eng-process/getting-started-reference-driver.md
last-synced: ""
---

# T-095 — `next-cycle`: the tooling guides the human

## Story

> **As** a practitioner (the my-product sessions, 2026-07-13)
> **I want** to run exactly one command — `./scripts/next-cycle` — and have the
> tooling itself tell me what it needs (endpoint config, a filled stakeholder
> brief, an answered input-request) and do everything else (Inception
> authoring, the delivery cycle, exit-code interpretation)
> **So that** the fresh-project path stops being four remembered steps and the
> typed exit codes stop needing a manual to read — the tool guides, the human
> only ever supplies what only a human can.

INVEST — ✅ Independent (pure composition over the shipped driver) · ✅ Negotiable (guidance texts) · ✅ Valuable (verbatim user ask) · ✅ Estimable · ✅ Small (one wrapper + tests + docs) · ✅ Testable (fake-driver fixture)

## Analysis Context

- **Domain.** A new executable `scripts/next-cycle` (stdlib-only Python,
  shebang + exec bit, shipped via `process-manifest.txt`) that **composes**
  `openup-agent.py` — it never reimplements engine behavior; every decision it
  makes is "which driver invocation comes next, and how do I explain the
  result".
- **Guided state machine** (in order):
  1. Load `.openup/agent.env` (simple `KEY=VALUE` lines, `#` comments; never
     overrides variables already exported).
  2. `LLM_API_URL` missing ⇒ on a TTY, prompt for endpoint URL / API key /
     model names and offer to persist them to `.openup/agent.env`; off-TTY,
     print a copy-paste setup block and exit 2.
  3. Fresh project (no `docs/vision.md` AND no `docs/roadmap.md`):
     - no stakeholder brief, or the brief still carries the template marker ⇒
       write the template brief to `docs/inputs/stakeholder-brief.md` (if
       absent), explain what to fill in, exit 0 — the product description is
       the human's, per the T-094 principle;
     - filled brief ⇒ run the Inception step:
       `openup-agent.py run --procedure openup-create-vision --instruction
       <vision+roadmap instruction>`; on failure translate and exit.
  4. Run ONE `openup-agent.py cycle --dir .`, adding `--interactive` when
     stdin is a TTY.
  5. Translate the exit into next-step guidance (0/ADVANCED → "run again",
     0/DONE → the reason, 5 → the request file to answer and how, 2/3/4/6/7/8
     → what to fix), always exiting with the underlying code.
- **Scope boundaries.** No looping flag (an outer `while ./scripts/next-cycle;
  do :; done` already works — 0 means progress); no engine changes; no changes
  to `openup-agent.py` / `openup-loop.sh`; guidance is stderr text, the
  driver's stdout sentinel passes through untouched (outer-loop contract
  preserved).
- **Definition of done.** From an empty bootstrapped project, repeatedly
  running the single command walks a human through env → brief → Inception →
  delivery loop, each stage proven hermetically against a fake driver.

> **Assumption:** The wrapper is a no-extension executable (`scripts/next-cycle`)
> so the user's literal `./scripts/next-cycle` works; tests import it via
> `importlib` (the bench-test precedent for hyphenated scripts). *(Vetoable at
> review.)*

> **Assumption:** Env persistence lives at `.openup/agent.env` (Ring-3,
> already gitignored); the wrapper never writes shell rc files. *(Vetoable at
> review.)*

> **Assumption:** The template brief carries an explicit marker line the
> wrapper checks (`<!-- template: replace every section with your product's
> reality -->`) — a still-marked brief is treated as unfilled. *(Vetoable at
> review.)*

> **Assumption:** Driver stdout (the sentinel) is passed through verbatim;
> all guidance goes to stderr — so `next-cycle` remains scriptable by the same
> outer loops that consume `cycle`. *(Vetoable at review.)*

## Requirements

1. **Env loading + guidance.** `.openup/agent.env` is loaded without
   overriding exported variables; a missing `LLM_API_URL` yields interactive
   setup (TTY, persisted on consent) or a copy-paste guidance block + exit 2
   (off-TTY).
   - **Given** `.openup/agent.env` containing `LLM_API_URL=http://x/v1` and no
     exported override **When** `next-cycle` runs **Then** the driver
     subprocess receives that value in its environment.
   - **Given** no `LLM_API_URL` anywhere and no TTY **When** `next-cycle` runs
     **Then** it exits 2 and stderr contains an `export LLM_API_URL=` setup
     block, and no driver invocation happened.

2. **Fresh project → template brief, human turn.** With no vision, no roadmap,
   and no (filled) brief, the wrapper writes the template brief and stops with
   guidance instead of invoking the driver.
   - **Given** an empty project and no brief **When** `next-cycle` runs (env
     present) **Then** `docs/inputs/stakeholder-brief.md` exists containing
     the template marker, stderr says to fill it and re-run, the exit code is
     0, and the fake driver recorded no invocation.
   - **Given** a brief that still contains the template marker **When**
     `next-cycle` runs **Then** it stops with the same guidance and does not
     overwrite the file.

3. **Filled brief → Inception run.** With a filled brief and still no
   vision/roadmap, the wrapper drives `openup-agent.py run --procedure
   openup-create-vision` with an instruction naming the brief and asking for
   `docs/vision.md` + an initial `docs/roadmap.md`.
   - **Given** a filled brief **When** `next-cycle` runs **Then** the fake
     driver records one `run` invocation whose `--procedure` is
     `openup-create-vision` and whose `--instruction` contains
     `stakeholder-brief.md`, `docs/vision.md`, and `docs/roadmap.md`.

4. **Normal state → one cycle, TTY-aware.** With a vision or roadmap present,
   the wrapper runs exactly one `cycle`, adding `--interactive` iff stdin is a
   TTY.
   - **Given** a project with `docs/roadmap.md` **When** `next-cycle` runs
     off-TTY **Then** the fake driver records one `cycle` invocation without
     `--interactive`, and the wrapper's exit code equals the driver's.

5. **Exit translation, sentinel passthrough.** Every driver exit produces
   plain next-step guidance on stderr while the driver's stdout passes through
   unmodified; the wrapper's exit code is the driver's.
   - **Given** a fake driver exiting 5 with a SUSPENDED sentinel on stdout
     **When** `next-cycle` runs **Then** stdout still carries the sentinel
     line, stderr names the input-request answer flow, and the exit code is 5.
   - **Given** a fake driver exiting 0 with an `ADVANCED` sentinel **When**
     `next-cycle` runs **Then** stderr suggests re-running to continue and the
     exit code is 0.

6. **Shipped + executable.** `next-cycle` is in `scripts/process-manifest.txt`
   and lands executable via the manifest installer.
   - **Given** `install_process_clis` into a fresh temp dir **When** it runs
     **Then** `next-cycle` exists there with the executable bit set and its
     first line is a `python3` shebang.

## Behavior Delta

**Added**
- `scripts/next-cycle` — the guided single entry point (env → brief →
  Inception → one cycle → exit translation).

**Modified** — none (pure composition; `openup-agent.py`, the engine, and the
procedure pack are untouched).

**Removed** — none.

## Entities

- **wrapper** (new) — `scripts/next-cycle`
- **manifest** (modified) — `scripts/process-manifest.txt`
- **tests** (new) — `scripts/tests/test_next_cycle.py`
- **driver** (read-only, composed) — `scripts/openup-agent.py`
- **docs** (modified) — `docs-eng-process/getting-started-reference-driver.md`
  (the one-command path), `reference-driver.md`, `script-cli-reference.md`

## Approach

A thin, honest concierge: detect the project's stage from four files
(agent.env, brief, vision, roadmap), run the one driver invocation that stage
calls for, and wrap its typed exit in human guidance — stderr for words,
stdout untouched for machines. All state it writes (template brief, agent.env)
is input the human was going to have to produce anyway, just pre-shaped.

## Structure

**Add:**
- `scripts/next-cycle`
- `scripts/tests/test_next_cycle.py`

**Modify:**
- `scripts/process-manifest.txt` — ship the wrapper
- `docs-eng-process/getting-started-reference-driver.md` — lead with the
  one-command path
- `docs-eng-process/reference-driver.md` — short `next-cycle` section
- `docs-eng-process/script-cli-reference.md` — entry

**Do not touch:**
- `scripts/openup-agent.py`, `scripts/openup_agent/` — the wrapper composes
  the driver; new engine behavior is its own task
- `scripts/openup-loop.sh` — the `next`-procedure loop stays as-is (T-091
  decides its future)
- `docs-eng-process/procedures/` — no pack changes

## Operations

- [x] Implement `scripts/next-cycle`: agent.env loader, env guidance
      (TTY prompt + persist / off-TTY setup block), stage detection, template
      brief writer with marker, Inception invocation, single TTY-aware cycle
      invocation, exit translation with stdout passthrough (Req 1-5)
- [x] Add `scripts/tests/test_next_cycle.py` — fake-driver fixture recording
      argv + canned exits/sentinels; cover all six requirements' scenarios
- [x] Register `next-cycle` in `scripts/process-manifest.txt` and verify a
      fresh `install_process_clis` lands it executable with the shebang
      (Req 6)
- [x] (analyst) Update `getting-started-reference-driver.md` (one-command
      path first), `reference-driver.md`, `script-cli-reference.md`
- [x] (tester) Run the wrapper suite + full driver/cycle suites +
      `openup-spec-scenarios.py check` + `check-docs.py` + `openup-fence.py
      check --base harness-optional`; live-walk the guided stages on the
      my-product fixture where no endpoint is needed (env block, template
      brief, cycle passthrough); record in `docs/changes/T-095/design.md`

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions
- `docs-eng-process/model-tiers.md` — the wrapper never names a model; env
  placeholders stay the tier-map's business

## Safeguards

- **Compose, never reimplement** — the wrapper contains zero engine logic; its
  only writes are the template brief and (consented) `.openup/agent.env`.
- **Sentinel contract preserved** — driver stdout passes through byte-exact;
  guidance is stderr-only; exit code is the driver's. An outer loop cannot
  tell `next-cycle` from `cycle` programmatically.
- **Never overwrite human input** — an existing brief is never rewritten, even
  when still template-marked.
- **Stdlib-only** (T-072 invariant); no shell rc edits.
- **Driver suites untouched** — pre-existing tests pass unmodified.

## Success Measures

We expect **the fresh-project path to require exactly one remembered command**:
on the owner's next live my-product session, every stage transition (env →
brief → Inception → cycle → answered request) is reached by re-running
`./scripts/next-cycle` alone, with no manually composed `--instruction` or
exit-code lookup — observable directly in the session transcript. Read-back:
recorded in `docs/changes/T-095/design.md` after that session (owner-side;
endpoint-dependent stages can't run in this sandbox — T-089/T-092/T-094
precedent).

## Rollout

Not flagged — **n/a (reason):** a new optional executable; nothing existing
routes to it, so not running it is the kill-switch. The documented flows
(`run`, `cycle`, `openup-loop.sh`) are unchanged. No temporary debt → no
flag-removal follow-up.

## Verification

- `python3 -m unittest scripts.tests.test_next_cycle
  scripts.tests.test_openup_agent scripts.tests.test_openup_agent_cycle
  scripts.tests.test_openup_agent_bench` — all green
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-095/plan.md` — exit 0
- `python3 scripts/check-docs.py` — exit 0
- `python3 scripts/openup-fence.py check --base harness-optional` — exit 0
- Fresh-dir manifest install lands `next-cycle` executable (Req 6 scenario)
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅ or a
  clear gap call-out.

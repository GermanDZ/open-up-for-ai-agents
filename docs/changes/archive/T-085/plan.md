---
id: T-085
title: Benchmark fixture is a clean bootstrapped project, not a copy of the repo
status: done
priority: high
plan: docs/changes/archive/T-080/plan.md
depends-on: [T-080, T-083]
touches:
  - scripts/openup-agent-bench.py
  - scripts/tests/test_openup_agent_bench.py
  - docs-eng-process/reference-driver-benchmark.md
  - docs/changes/
last-synced: ""
---

# T-085 — Benchmark fixture must be a clean bootstrapped project

## Story

> **As** someone benchmarking the driver on a **new-project** scenario
> **I want** each fixture to be a **freshly bootstrapped OpenUP project** — the
> framework (`docs-eng-process/` + `scripts/`) + an empty `docs/` + the scenario —
> **not** a `git archive HEAD` copy of the whole repo under test
> **So that** the model sees a blank project, not our developed repo's `docs/`
> (`project-status.md`, `roadmap.md`, the T-0xx history) — which polluted the
> inception-vision run: the model read our real project status instead of starting
> fresh.

## Context

`build_fixture` snapshots the **entire** repo (`git archive HEAD`) into the
fixture, dragging in our `docs/` — so an "inception" fixture already contains a
fully-developed OpenUP project's status/roadmap/vision. The model reading
`docs/project-status.md` gets *our* iteration-54 status. A new-project benchmark
must start from a bootstrapped project (what `bootstrap-project.sh` produces:
framework + empty `docs/`), seeded only with the scenario's own inputs.

## Requirements

1. **The fixture is framework + empty docs + scenario.** `build_fixture` copies
   only the framework trees (`docs-eng-process/`, `scripts/`, `.gitignore`,
   `.gitattributes`) from the repo under test, creates a **fresh empty `docs/`**,
   then applies the scenario overlay — before `git init` + seed commit. The repo's
   own `docs/` (project-status, roadmap, changes, product) is **never** copied in.
   `--include-working-tree` still applies to the framework trees (benchmark
   in-progress skill/procedure/tool edits).
   - **Given** a built fixture **When** its tree is inspected **Then**
     `docs-eng-process/procedures/` and `scripts/openup-board.py` exist, and the
     repo's `docs/roadmap.md` / `docs/project-status.md` do **not**.
   - **Given** the `inception-vision` fixture **When** inspected **Then** the only
     `docs/` content is the scenario's brief (`docs/inputs/stakeholder-brief.md`) —
     no pre-existing project status/roadmap.
2. **Both scenarios still work on the clean fixture.** `quick-doc`'s seeded lane is
   still picked (`resolve == pick`); the vision run still writes `docs/vision.md`.
   - **Given** the `quick-doc` fixture **When** `openup-board.py resolve` runs
     **Then** it returns `pick` for `BENCH-001` (the only lane in an otherwise empty
     `docs/`).

## Operations

- [x] Rewrite `build_fixture` step 1: `git archive <tree-ish> docs-eng-process
  scripts .gitignore .gitattributes` (framework only) instead of the whole tree;
  create `docs/` fresh (empty). Keep the overlay + git-init + origin/main steps.
  Add a test asserting the fixture has the framework but NOT the repo's
  `docs/roadmap.md`/`docs/project-status.md`, and that the vision fixture's docs/
  holds only the brief. Keep quick-doc + vision pipeline tests green. Note the
  bootstrapped-fixture model in `reference-driver-benchmark.md`.

## Verification

- A built fixture contains `docs-eng-process/` + `scripts/` but not the repo's
  `docs/roadmap.md` / `docs/project-status.md`.
- quick-doc still resolves to `pick`; the vision scenario still produces
  `docs/vision.md`.
- driver + bench tests green; `openup-fence.py check --base harness-optional` green.

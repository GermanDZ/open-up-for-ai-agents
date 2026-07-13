---
id: T-087
title: Getting-started doc — run your own project with the reference driver + your LLM
status: done
priority: high
plan: docs/changes/archive/T-072/plan.md
depends-on: [T-072, T-083]
touches:
  - docs-eng-process/getting-started-reference-driver.md
  - docs-eng-process/getting-started.md
  - docs-eng-process/reference-driver.md
  - docs/changes/
last-synced: ""
---

# T-087 — Getting started with your own harness + your own LLM

## Story

> **As** a practitioner with no Claude Code, only a local/OpenAI-compatible LLM
> **I want** a getting-started guide for driving a real project with the reference
> driver (`openup-agent`) + my own endpoint, covering **(A) a brand-new project**
> and **(B) an already-started project adopting OpenUP** (incl. backfilling the
> docs it is missing)
> **So that** I can go from "I have an LLM endpoint" to "OpenUP is producing my
> vision/architecture/iterations" without a Claude harness.

## Context

The driver is documented (`reference-driver.md`) and the benchmark proves it
(T-072 `verified`), but there is **no task-oriented guide** for running *your own*
project with it. `getting-started.md` is Claude-Code/manual only. Scenario B
("adopt OpenUP into an existing repo") needs a story for **creating the missing
docs from existing code** — the T-083 `--instruction` mechanism (point an authoring
procedure at the codebase) is the tool; there is no automated missing-doc detector
(`openup-doctor` checks shipped CLIs, not product docs) — the guide documents the
manual checklist + backfill flow and flags the gap.

## Requirements

1. **A new getting-started doc for the reference-driver path.** Create
   `docs-eng-process/getting-started-reference-driver.md`: prerequisites (python,
   git, an OpenAI-compatible endpoint + the `LLM_API_URL`/`LLM_API_KEY`/
   `OPENUP_MODEL_*`/`OPENUP_AGENT_TIMEOUT` env), and the two scenarios end-to-end
   with copy-paste commands. Cross-linked from `getting-started.md` and
   `reference-driver.md`.
   - **Given** the doc **When** a reader with only an endpoint follows Scenario A
     **Then** they bootstrap a project and drive `openup-create-vision` to a real
     `docs/vision.md`, then continue to later Inception/Construction procedures.
2. **Scenario B covers backfilling missing docs from existing code.** The
   existing-project path: add the framework, then drive the `openup-create-*`
   authoring procedures with `--instruction` pointing at the codebase to
   reverse-engineer vision/architecture/use-cases; includes the manual "required
   docs" checklist and notes the absence of an automated detector.
   - **Given** an existing repo **When** a reader follows Scenario B **Then** they
     install the framework and backfill each missing artifact via a driver
     `--instruction` run, then continue with normal iterations.

## Operations

- [x] Write `docs-eng-process/getting-started-reference-driver.md` (prereqs +
  Scenario A new-project + Scenario B existing-project-adoption with the
  `--instruction` backfill flow + a required-docs checklist + the honest `next`-loop
  caveat from the benchmark findings). Add a cross-link pointer from
  `getting-started.md` and `reference-driver.md`. Verify the commands against the
  actual CLIs/procedures. (Doc-only; no code.)

## Verification

- The commands in the doc match the real `openup-agent.py` flags (`--procedure`,
  `--instruction`, `--dir`) and env vars, and the real procedure names.
- `getting-started.md` + `reference-driver.md` link to the new doc.
- `check-docs.py` + `openup-fence.py check --base harness-optional` green.

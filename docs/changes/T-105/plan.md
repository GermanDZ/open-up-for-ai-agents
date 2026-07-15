---
id: T-105
title: "Task-def schema + build-task-library.py process compiler + committed library"
status: ready
priority: high
estimate: 1-2 sessions
plan: docs/iteration-plans/2026-07-14-lean-authoring-tasks.md
depends-on: [T-104]
blocks: [T-106]
last-synced: ""
touches:
  - scripts/build-task-library.py
  - docs-eng-process/task-library.yaml
  - scripts/openup-process-map.py
  - scripts/tests/test_build_task_library.py
  - scripts/tests/test_task_library_validate.py
  - scripts/process-manifest.txt
  - docs-eng-process/script-cli-reference.md
---

# T-105 — Task-def schema + the process compiler + the committed library

## Story

> **As a** maintainer of the reference-driver authoring path
> **I want** the KB authoring tasks compiled into a committed, validated lean-task library
> **So that** T-106 can drive each authoring sub-run from a ~10–20-line task def instead of a 650+-line procedure fan-out — the measured weak-model reliability bottleneck

INVEST — ✅ Independent · ✅ Negotiable · ✅ Valuable · ✅ Estimable · ✅ Small · ✅ Testable

## Analysis Context

- **Domain.** Process-as-data compilation. Sibling of `build-trace-model.py` (T-035): deterministically derive object code from the vendored KB, committed + validated + human-reviewed.
- **Scope boundaries.** **No engine behavior change** — the library lands committed/validated but *unconsumed* (T-106 wires it in; T-100's schema-first-then-consumer pattern). No procedure-file surgery, no Claude Code skill changes, no `process-map.yaml` `tasks:` wiring (that is T-106). Library scoped to the **map-referenced authoring tasks only**, not all 39 KB tasks (that is T-107).
- **Definition of done.** A `task-library.yaml` schema + committed defs for the map-referenced authoring tasks; a `tasks` validate path (hard gate); `build-task-library.py` with deterministic Stage-1 extraction, Stage-2 LLM distillation (with `--offline` prompt emission), and `--check` drift; registered in the manifest + CLI reference; full suite behavior unchanged.

> **Assumption:** the committed `judgment` bullets are authored/reviewed by a strong model at compile time. This sandbox cannot reach an LLM endpoint, so Stage-2 distillation is exercised via `--offline` (prompt emission) and the committed defs are authored + reviewed in-session as the sanctioned "strong-model, reviewed, committed" step. *(Vetoable at review.)*
> **Assumption:** library home is one `docs-eng-process/task-library.yaml` in the process-map flow-syntax family (stdlib parser, no pyyaml). *(Vetoable.)*
> **Assumption:** `author-initial-roadmap` is a driver-native def with `source: driver` (no KB source), carrying the T-099 pinned roadmap format. *(Vetoable.)*

## Requirements

1. A task-def schema defines one lean def per task with fields `id`, `name`, `role`, `artifact` (spine type), `output_path`, `judgment` (3–8 bullets), `inputs` (list of paths), `source` (KB file or `driver`).
   - **Given** the committed `task-library.yaml` **When** it is parsed **Then** every def carries all eight fields and `artifact` is one of the v1 spine types.
2. `openup-process-map.py` gains a `tasks` validate path that hard-gates malformed defs (missing field, bad `artifact` enum, `judgment` outside 3–8 bullets, malformed `output_path`).
   - **Given** a def with `artifact: bogus` **When** `openup-process-map.py tasks --validate` runs **Then** it prints `[task-library] ✗ …` and exits 2; **Given** the committed library **Then** it exits 0.
3. `build-task-library.py` Stage-1 deterministically extracts a def skeleton (id, name, role, artifact, inputs) from a KB task file's UMA structure — no LLM.
   - **Given** the `develop-technical-vision-1.md` KB fixture **When** Stage-1 extraction runs **Then** the skeleton's role list, inputs, and name match the frontmatter/Inputs section.
4. Stage-2 distillation produces the `judgment` bullets via `openup_agent/llm.py`; `--offline` emits the distillation prompt to a file instead of calling an endpoint.
   - **Given** `--offline` **When** the compiler runs on a task **Then** a well-formed distillation prompt file is written and no network call is made.
5. `--check` drift mode regenerates Stage-1 skeletons and diffs against the committed library, exiting non-zero on a mutated skeleton.
   - **Given** a committed library and a mutated skeleton **When** `build-task-library.py --check` runs **Then** it reports drift and exits 1; **Given** the in-sync library **Then** it exits 0.
6. The committed library contains reviewed defs for the map-referenced authoring tasks and introduces **zero engine behavior change**.
   - **Given** the full existing test suite **When** it runs after this task **Then** it passes unchanged (no driver/engine test altered).

## Behavior Delta

**Added** — a `task-library.yaml` object-code artifact + `build-task-library.py` compiler + a `tasks` validate path; all new, unconsumed by the engine this task.

**Modified** — n/a (engine behavior unchanged; `openup-process-map.py` gains a new subcommand but existing subcommands are untouched).

**Removed** — n/a.

## Entities

- **Task-def library** (new) — `docs-eng-process/task-library.yaml`
- **Compiler** (new) — `scripts/build-task-library.py`
- **Map/tasks validator** (modified) — `scripts/openup-process-map.py` (`tasks` subcommand + `validate_tasks()`)
- **KB task files** (read-only source) — `docs-eng-process/openup-knowledge-base/*/*/tasks/*.md`
- **LLM client** (read-only, reused) — `scripts/openup_agent/llm.py`

## Approach

Clone the `build-trace-model.py` precedent. `task-library.yaml` mirrors `process-map.yaml`'s flow-syntax so `openup-process-map.py`'s existing stdlib parser reads it (add a `load_tasks()` + `validate_tasks()`). The compiler has three modes: default compile (Stage-1 extract → Stage-2 distill → emit YAML), `--offline` (Stage-1 + emit distillation prompts, no network), `--check` (Stage-1 re-extract → diff committed skeletons). Stage-1 is a small UMA-structure parser (frontmatter `uma_name`/`related.roles`, `Inputs|`/`Outputs|` link lists). Stage-2 calls `chat_completion` with one hand-calibrated vision example as the style anchor. The committed library's `judgment` bullets are authored + reviewed in-session (strong-model-equivalent) since no endpoint is reachable here.

## Structure

**Add:**
- `scripts/build-task-library.py` — the compiler (extract / distill / offline / check).
- `docs-eng-process/task-library.yaml` — the committed, reviewed library.
- `scripts/tests/test_build_task_library.py` — extraction + offline + check tests.
- `scripts/tests/test_task_library_validate.py` — validate accept/reject tests.

**Modify:**
- `scripts/openup-process-map.py` — `load_tasks()`, `validate_tasks()`, `tasks` subcommand.
- `scripts/process-manifest.txt` — register `build-task-library.py`.
- `docs-eng-process/script-cli-reference.md` — document the new CLI.

**Do not touch:**
- `scripts/openup_agent/*` engine path — no consumption this task (T-106).
- `process-map.yaml` activities — `tasks:` wiring is T-106.
- The KB files — read-only source.
- Claude Code `openup-create-*` skills — parity is at artifact level (T-107 decision).

## Operations

- [ ] Author `docs-eng-process/task-library.yaml`: reviewed lean defs for the map-referenced authoring tasks (develop-technical-vision, author-initial-roadmap [driver], identify-and-outline-requirements, detail-use-case-scenarios, envision-the-architecture, refine-the-architecture, plan-iteration, create-test-cases), each with id/name/role/artifact/output_path/judgment/inputs/source.
- [ ] Extend `openup-process-map.py` with `load_tasks()` + `validate_tasks()` + a `tasks` subcommand (`--validate`), mirroring the existing `validate` convention/exit codes.
- [ ] Implement `build-task-library.py` Stage-1 deterministic extraction (UMA frontmatter + Inputs/Outputs parse) → def skeleton.
- [ ] Implement Stage-2 distillation via `openup_agent/llm.py` with an embedded vision style-anchor example; add `--offline` prompt-emission mode.
- [ ] Implement `--check` drift mode (re-extract skeletons, diff committed library); wire into `openup-doctor.py`'s aggregate check table + `_AUTO_FIX` is NOT added (regeneration is a human-reviewed act — advisory only).
- [ ] (tester) Write `test_build_task_library.py` (extraction from the vision KB fixture, `--offline` prompt emission, `--check` drift) + `test_task_library_validate.py` (reject each malformed-def class; committed library passes).
- [ ] Register `build-task-library.py` in `process-manifest.txt` + document it in `script-cli-reference.md`; run the full suite to confirm zero engine behavior change.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions
- `scripts/build-trace-model.py` — the compiler precedent (structure, `--check`, exit codes)
- `scripts/openup-process-map.py` — the stdlib flow-syntax parser + validate convention

## Safeguards

- **No-go zones.** Zero engine/driver behavior change — no `openup_agent/*` consumption, no `process-map.yaml` `tasks:` wiring (T-106). Full suite must stay green unchanged.
- **DD1 / precedent.** Follow `build-trace-model.py` for `--check` drift + exit codes; no pyyaml (stdlib flow-syntax parser).
- **Human review.** Distilled `judgment` bullets are committed only after review; `--check` treats prose-distillation drift as advisory, not CI-hard (regeneration is a reviewed act).
- **Reversibility.** The library is inert object code; deleting `task-library.yaml` + the compiler fully reverts with no engine impact.
- **Token budget.** `task-library.yaml` defs ~10–20 lines each; compiler ≤ ~350 lines.

## Verification

- `python3 scripts/openup-process-map.py tasks --validate` exits 0 on the committed library.
- `python3 scripts/build-task-library.py --check` exits 0 in-sync.
- `python3 -m pytest scripts/tests/test_build_task_library.py scripts/tests/test_task_library_validate.py -q` passes.
- Full suite green; fence `--base harness-optional` clean.
- Grade against `.claude/rubrics/task-spec-rubric.md`.

## Success Measures

n/a — this task ships inert object code with zero behavioral surface; the program's falsifiable measure (weak-model reliability on the qwen fixture) is read at T-106. The T-105 proof is the validate/extract/check test suite + zero-engine-change.

## Rollout

n/a — internal build tooling + committed data; no user-facing runtime, no feature flag. The library is unconsumed until T-106.

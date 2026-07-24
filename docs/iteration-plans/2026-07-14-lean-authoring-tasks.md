# Plan: Lean authoring tasks (S1 → S2′ → S3′)

**Created:** 2026-07-14
**Phase:** construction
**Status:** planned
**Priority:** high
**Branch:** harness-optional
**Seeds from:** [explorations/2026-07-14-generic-procedure-lean-task-library.md](../explorations/2026-07-14-generic-procedure-lean-task-library.md)
(incl. its two appended re-decisions: *S3 named — the process compiler*, and
*re-sequenced: compiler-first after S1*)
**Tasks:** T-104 → T-105 → T-106 → (T-107, gated)

## Goal

Make the **authoring procedures** reliable on a weak local model, by the same
inversion P1 applied to navigation: **ceremony is code; the LLM only authors —
and each authoring call is small, isolated, and fed lean, compiled task
content.** Concretely:

1. The engine owns the authoring **ceremony** (frontmatter stamping, validation,
   project-config injection) — the model never loads the frontmatter contract,
   the traceability rubric, the trace model, the schema, or the self-critique
   SOP during an authoring sub-run. *(S1 / T-104)*
2. A **process compiler** (`build-task-library.py`, sibling of the existing
   `build-trace-model.py`) compiles the vendored KB task files into a
   **lean-task library** — ~10–20-line schema-strict task defs (the LLM prompts)
   — committed, validated, human-reviewed object code. *(S2′a / T-105)*
3. The cycle engine runs each authoring activity as **one or more small isolated
   sub-runs driven by task defs** (a generic prompt shell + one lean def + the
   declared inputs — no procedure file read at all on the driver path).
   *(S2′b / T-106)*
4. Scale: compile the full KB task set, wire drift-checking into doctor/CI, and
   accept **customized process sources** — the original P2 promise. *(S3′ /
   T-107, gated on S2′ acceptance)*

## Evidence / motivation (measured 2026-07-14)

With navigation fixed (P1, T-100…T-103), the authoring procedures are the
reliability bottleneck on the `my-product`/qwen driver:

- **The debug log** (`OPENUP_AGENT_DEBUG_LOG`, T-098) caught a `create-vision`
  sub-run **restarting itself mid-run** (its opener appears twice), probing the
  optional `docs/project-config.yaml` **5×**, and reaching iteration 9/10 with
  no vision written — while the same model had **3 clean create-vision DONEs**
  earlier. Weak-model *inconsistency* caused by context weight, not incapacity.
- **The fan-out:** `openup-create-vision.md` is 143 lines but instructs the
  model to load `templates/vision.md` (32) + `sops/self-critique.md` (56) +
  `doc-frontmatter.md` (104) + `rubrics/doc-traceability-rubric.md` (148) +
  `scripts/trace-model.json` (101) + `scripts/docs-meta.schema.json` (74) +
  project-config/status/brief/vision-rubric — **~650+ lines of spec** held while
  *also* authoring a vision and self-validating. Four conflated jobs: author,
  stamp frontmatter, self-grade, self-critique. The last three are ceremony the
  deterministic layer already owns or gates (`check-docs.py` runs after every
  step regardless).
- **The KB task files are NOT the lean alternative:** measured 86–119 lines of
  verbose UMA/RUP reference prose with link fan-out (39 files total). Linking a
  weak model to them raw reproduces the failure — hence *distill, don't link*
  (the same move T-077 made for the phase map, and `build-trace-model.py`
  already makes for the trace model).
- **A regression discovered while planning this (must fix in S1):** the pinned
  `T-NNN` roadmap-format contract (T-099's fix for the live `RDM-001` parser
  mismatch) lived in the navigator's `VISION_INSTRUCTION`, deleted with the
  navigator in T-103. Today's `execution: direct` instruction
  (`plan_iteration.py` ~line 344) is generic — the fresh flow has **no
  initial-roadmap authoring contract at all**: create-vision (the procedure)
  authors only the vision, and nothing tells any sub-run to author
  `docs/roadmap.md` in the parseable format. Post-Inception construction would
  find nothing promotable again.

**Interim operational stopgap (available today, not a substitute):** point
`OPENUP_MODEL_MID` (the authoring tier) at a stronger model. The program is
justified by the weak-local-model goal plus token cost on all models.

## Current state (load-bearing code)

- **`scripts/openup_agent/plan_iteration.py`** (T-090/T-101): Plan Iteration
  from `activities-for(phase)`; `execution: direct` runs the activity's single
  skill via `run_procedure(skill, instruction)` — which reads the **full
  procedure file** as the system prompt (`loop.run` procedure path); the
  instruction is generic ("Perform the OpenUP activity … in service of these
  objectives"). `requires_input` scaffold gate exists (T-101).
- **`scripts/openup_agent/loop.py`**: `run(system_prompt=, model=, instruction=)`
  — the bounded sub-run seam (T-089); when `system_prompt` is given the
  procedure file is **not** read. `run_gates` (fence + check-docs) after every
  step. `OPENUP_AGENT_USAGE_LOG` (prompt_tokens per call) + `OPENUP_AGENT_DEBUG_LOG`
  (full transcripts) are the measurement surfaces.
- **`scripts/openup_agent/llm.py`**: `chat_completion` — reusable at compile
  time for the distillation stage (any OpenAI-compatible endpoint).
- **`scripts/build-trace-model.py`** (T-035): the existing process compiler
  precedent — deterministically derives `trace-model.json` from the KB;
  `check-docs.py` executes it. Same UMA-regularity parsing the new compiler's
  extraction stage needs.
- **`docs-eng-process/process-map.yaml`** + **`scripts/openup-process-map.py`**
  (T-077/T-100): activities carry `role`, `skills`, `requires_input`,
  `execution`; `validate` hard-gates. The natural home for `tasks:` wiring.
- **`docs-eng-process/doc-frontmatter.md`** + **`scripts/docs-meta.schema.json`**
  + **`scripts/check-docs.py`** (T-034…T-038): the typed-instance contract the
  engine will stamp deterministically (`type`, `id` e.g. `VIS-001`, `title`,
  `status`) instead of the model reading it.
- **The procedures** (`docs-eng-process/procedures/openup-create-*.md`, ~1,417
  lines across 7 files): stay as the **Claude Code** path (skills orchestrate
  in-context; parity is at the artifact level). The driver path stops reading
  them (S2′b).

## Tasks

### T-104 (S1) — Engine-owned authoring ceremony + restore the roadmap contract

**Scope.** Strip the ceremony out of the *driver's* authoring sub-runs and give
it to the engine; fix the T-103 roadmap-contract regression. No new schema, no
compiler, no pack-procedure surgery (the Claude Code path is untouched).

Deliverables:
1. **Deterministic frontmatter stamping.** After a direct authoring sub-run
   produces its artifact body, the engine stamps the typed instance frontmatter
   itself — `type` (from the activity/artifact), `id` (next-free per type
   prefix, e.g. `VIS-001`, scanned from existing instances the way
   `reserve-id` scans task ids), `title`, `status: draft`. If the model wrote
   its own frontmatter block, the engine replaces/normalizes it. `check-docs`
   (already in `run_gates`) remains the validator — the *gate is the critic*.
2. **Ceremony-exclusion instruction.** The direct-run instruction explicitly
   tells the model: *"Author the document body only. Do NOT read or write
   frontmatter, rubrics, trace models, or schemas, and do NOT self-critique —
   the engine stamps and validates."* (Instruction-level, so the procedure file
   the sub-run still reads in S1 is counteracted where it fans out; the file
   read itself disappears in T-106.)
3. **Project-config injection.** The engine reads `docs/project-config.yaml`
   once (deterministically); if present, its `context:`/relevant `rules.*` are
   injected into the instruction — the model never probes for the file (the 5×
   re-read noise observed live).
4. **Restore the pinned roadmap contract (regression fix).** The fresh-Inception
   direct path must again produce `docs/roadmap.md` in the parser-required
   format: reintroduce the T-099 format contract (strict header row; `T-001,
   T-002, …` ids; `pending`; `high|medium|low`; comma-separated `T-NNN` deps;
   ordered by priority; no YAML frontmatter) as a constant in
   `plan_iteration.py`, appended to the `initiate-project` direct instruction —
   explicitly interim until T-106 moves it into the task library as its own
   task def.
5. **Self-critique by tier.** Dropped from the weak-model authoring path (the
   deterministic gate replaces it); note recorded that a strong-model tier MAY
   run it as a separate tiny sub-run later (not built now).

Acceptance (falsifiable):
- Hermetic: a scripted direct create-vision run → model writes body only; the
  engine stamps frontmatter; `check-docs` green; the artifact id allocates
  `VIS-001` then `VIS-002` on a second instance.
- Hermetic: the fresh-Inception scripted flow produces a `docs/roadmap.md` that
  `openup-roadmap.py next` finds promotable (regression test for the T-103 gap).
- Instruction contains the ceremony-exclusion + injected config; the sub-run
  transcript (debug log) shows **zero** reads of `doc-frontmatter.md`,
  `docs-meta.schema.json`, `trace-model.json`, rubric files, or
  `project-config.yaml`.
- Full driver suite green; fence `--base harness-optional` clean.

Depends on: — (first). Track: standard, solo, worktree off `harness-optional`.
Touches (planned): `scripts/openup_agent/plan_iteration.py`,
`scripts/openup_agent/cycle.py`, a new `scripts/openup_agent/stamping.py` (or
equivalent), tests, `docs-eng-process/reference-driver.md`.

### T-105 (S2′a) — Task-def schema + the process compiler + the committed library

**Scope.** The minimal process compiler and its object code. **No engine
behavior change** — the library lands committed/validated but unconsumed (the
T-100 pattern: schema first, consumer next).

Deliverables:
1. **Task-def schema.** One lean def per task: `id`, `name`, `role`,
   `artifact` (spine type: vision | use-case | …), `output_path`, `judgment`
   (4–6 bullets of what-good-looks-like), `inputs` (paths to read),
   `source` (the KB task file it was compiled from). Home:
   `docs-eng-process/task-library.yaml` (single file, same flow-syntax family as
   `process-map.yaml`, read by the same stdlib parser approach — no pyyaml).
2. **Validator.** `openup-process-map.py validate` extended (or a `tasks`
   subcommand): every def has all fields; `artifact` in the spine enum;
   `judgment` 3–8 bullets; `output_path` well-formed; every `tasks:` reference
   from the map (T-106 wiring) resolves. Hard gate.
3. **The compiler: `scripts/build-task-library.py`** (sibling of
   `build-trace-model.py`):
   - **Stage 1 — deterministic extraction (no LLM):** parse the UMA task files'
     regular structure (frontmatter title/uma_name/roles; Inputs/Outputs
     sections; workproduct links) → the def skeleton (id, name, role, artifact,
     inputs). Reuses the KB-parsing approach `build-trace-model.py` proved.
   - **Stage 2 — LLM distillation (compile-time only):** distill each task's
     prose (Purpose/Steps/checklists) into the `judgment` bullets. Schema-strict
     output; **one hand-calibrated example def (vision) embedded in the
     distillation prompt as the style anchor**. Endpoint: any OpenAI-compatible
     via `openup_agent/llm.py` (`--api-url/--model` or driver env) — compile
     with a **strong** model; it is one-time, reviewed, committed. An
     `--offline` mode emits the distillation prompts to files for out-of-band
     completion/review (so the compiler is usable without an endpoint).
   - **`--check` drift mode:** regenerate stage-1 skeletons and diff against the
     committed library (same discipline as `build-trace-model.py`'s derived
     artifact); prose-distillation drift is flagged advisory (regeneration is a
     human-reviewed act, not CI-automatic).
4. **The committed library, scope-limited:** defs for the **map-referenced
   tasks only** (initiate-project/develop-technical-vision, author-initial-
   roadmap *(driver-specific def, no KB source — carries the T-099 pinned
   format)*, identify-refine-requirements/detail-use-case-scenarios,
   agree-technical-approach/architecture, plan-manage-iteration/risk-list,
   test-solution/test-plan) — each **human-reviewed before commit**.

Acceptance (falsifiable):
- `build-task-library.py` extracts correct skeletons from the 4 named KB files
  (hermetic fixture asserts roles/inputs/artifact parsed).
- `validate` rejects each malformed-def class; the committed library passes.
- `--check` detects a mutated skeleton; `--offline` emits well-formed prompts.
- Library committed + reviewed; **zero engine behavior change** (full suite
  byte-identical behavior).

Depends on: T-104 (only for sequencing/lane hygiene — technically independent).
Track: standard. Touches (planned): `scripts/build-task-library.py`,
`docs-eng-process/task-library.yaml`, `scripts/openup-process-map.py`, tests,
`scripts/process-manifest.txt`, `docs-eng-process/script-cli-reference.md`.

### T-106 (S2′b) — The engine consumes the library: generic sub-run + map wiring

**Scope.** Switch the driver's authoring path from procedure files to task-def
driven sub-runs. This is where the behavioral measure is read.

Deliverables:
1. **Generic authoring sub-run.** For a task def, the engine builds a bounded
   `loop.run(system_prompt=…, instruction=…)` call (the T-089 sub-run seam — no
   procedure file read): system prompt = a slim generic shell (*"You are
   performing OpenUP task `<name>` (role `<role>`). Produce `<artifact>` at
   `<output_path>`. What good looks like: `<judgment bullets>`. Read
   `<inputs>`. Save the file; emit the sentinel."*); the T-104 ceremony
   (stamping, config injection, gates) wraps it.
2. **Map wiring: activity → tasks.** `process-map.yaml` activities gain
   `tasks: [task-ids]` (1..n **ordered** — the granularity mechanism);
   `initiate-project: tasks: [develop-technical-vision, author-initial-roadmap]`
   is the flagship split (vision body; then the roadmap with its pinned format —
   retiring the T-104 interim constant). `skills:` stays for the Claude Code
   path; `validate` requires every listed task id to resolve in the library.
3. **plan_iteration integration.** `execution: direct` iterates the activity's
   ordered tasks, one bounded sub-run each; per-task `requires_input` gating
   continues to work; failure semantics unchanged (typed exits; abort before the
   iteration-plan instance).
4. **Bench scenario + measurement.** A bench scenario driving the fresh
   Inception flow through the task-def path, reading `OPENUP_AGENT_USAGE_LOG`
   (prompt_tokens) + the debug log (restart detection = repeated opener).

Acceptance (falsifiable — the program measure):
- Hermetic: scripted fresh Inception → two sub-runs for initiate-project
  (vision, roadmap), no procedure file read (transcript shows the generic
  shell), engine-stamped frontmatter, `check-docs` green, roadmap promotable.
- **Behavioral, on the qwen fixture (owner batch, T-080 bench):** the Inception
  authoring tasks complete with **zero mid-run restarts**, **≤6 iterations per
  sub-run**, **≥80% clean-pass over 5 runs**, **per-sub-run prompt context ≤⅓**
  of the 2026-07-14 baseline (the captured debug log). This is the go/no-go for
  T-107.

Depends on: T-104, T-105. Track: standard. Touches (planned):
`scripts/openup_agent/plan_iteration.py`, `scripts/openup_agent/cycle.py`,
`docs-eng-process/process-map.yaml`, `scripts/openup-process-map.py`,
bench scenario, tests, `docs-eng-process/reference-driver.md`.

### T-107 (S3′) — Scale: full KB, drift-checking, customized processes  *(gated)*

**Gate: promoted only after T-106's behavioral acceptance passes on the live
batch.** Scope sketch (full spec authored on promote):
- Compile the remaining ~32 KB tasks; review + commit the full library.
- Wire `build-task-library.py --check` into `openup-doctor.py` (drift surfaces
  in the health check, like the trace model).
- KB-update re-distillation flow (KB version bump → regenerate → review diff).
- **Customized process sources:** the compiler accepts a project's own process
  docs; output is a *project-local* map + task library overriding the framework
  default (the original P2 promise — this is where P2 lands, for both the map
  and the tasks).
- Decide Claude Code parity: do the `create-*` skills eventually consume the
  same lean defs (single source) or stay as-is? (Drift risk documented either
  way.)

Depends on: T-106 (+ live acceptance). Priority: medium.

## Program acceptance / Success Measure

We expect a fresh Inception-through-delivery run on the qwen fixture (T-080
bench + the my-product scenario) to complete its authoring tasks with **zero
mid-run restarts, ≤6 iterations per sub-run, ≥80% clean-pass over 5 runs, and
per-sub-run prompt context ≤⅓ of the 2026-07-14 baseline** — with the driver
reading **no procedure file and no ceremony spec** during authoring.
Instrumentation: `OPENUP_AGENT_USAGE_LOG` (prompt_tokens) + `OPENUP_AGENT_DEBUG_LOG`
(restart = repeated opener). Baseline: the 2026-07-14 debug log (restart at
cap-10; 5× project-config re-reads). Read-back: at T-106 completion, via the
owner's live batch; T-107 is gated on it.

## Dependencies

- T-104 → T-105 → T-106 → (gate) → T-107. T-105 is technically independent of
  T-104 but sequenced for lane hygiene; T-106 needs both (ceremony machinery +
  library).
- Builds on: T-035 (`build-trace-model.py` precedent), T-077/T-100 (map +
  schema), T-089 (`loop.run` sub-run seam), T-090/T-101 (plan-iteration +
  `execution: direct` + `requires_input`), T-038/T-036 (frontmatter contract +
  `check-docs` gate), T-080/T-098 (measurement surfaces), T-099 (the pinned
  roadmap format, restored in T-104 and made data in T-106).

## Out of scope

- **Claude Code skills** — unchanged this program (parity at artifact level);
  the single-source question is a T-107 decision.
- **KB edits** — the KB stays read-only source, as always.
- **The `next` procedure / openup-loop.sh** — untouched.
- **Non-authoring judgment sub-runs** (cycle-step Operations boxes, assess
  grading, objectives) — already lean; untouched.
- No `main` merge; everything on `harness-optional`.

## Open Questions (with working assumptions)

1. **Stamp-after vs pre-stamped file.** *Assumed:* engine stamps **after** the
   sub-run (model writes body only; engine prepends/normalizes frontmatter) —
   simplest contract, and a model-written stray frontmatter block is normalized
   away. *(Vetoable at T-104 review.)*
2. **Instance-id allocation.** *Assumed:* next-free per type prefix (`VIS-`,
   `UC-`, `TC-`…) scanned from committed instances — mirroring `reserve-id`'s
   repo-scan approach; no claims-dir coordination needed (authoring is
   single-lane inside one iteration). *(Vetoable.)*
3. **Library home/format.** *Assumed:* one `docs-eng-process/task-library.yaml`
   in the process-map flow-syntax family (stdlib parser, no pyyaml); per-file
   `tasks/*.md` rejected for parser simplicity. *(Vetoable at T-105 review.)*
4. **Distillation endpoint.** *Assumed:* `openup_agent/llm.py` against any
   OpenAI-compatible endpoint with a **strong** model + `--offline`
   prompt-emission fallback; compile output always human-reviewed before
   commit. *(Vetoable.)*
5. **Driver-specific tasks with no KB source** (author-initial-roadmap): allowed
   in the library with `source: driver` — the library is the union of compiled
   KB tasks and framework-native defs. *(Vetoable.)*
6. **`author-initial-roadmap` vs T-094 replenishment consent:** the *initial*
   roadmap at Inception is process-artifact authoring (runs directly, like the
   T-098→T-103 lineage); *appending to an existing* backlog stays behind the
   T-094 consent gate. Boundary unchanged. *(Restated to prevent drift.)*

---

*Program plan; each task's REASONS-Canvas spec is authored on promote via
`/openup-create-task-spec`. Compiler-first sequencing per the exploration's
append-2 decision (behavioral acceptance replaces the golden-set requirement);
S1 remains first because without engine-owned ceremony even perfect defs won't
converge.*

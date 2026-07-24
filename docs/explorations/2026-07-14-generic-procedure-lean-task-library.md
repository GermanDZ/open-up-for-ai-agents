# Exploration: generic authoring procedure + distilled lean-task library

**Started:** 2026-07-14
**Question:** Should the seven heavy `create-*` procedures be replaced by **one
generic authoring procedure** driven by a **distilled lean-task library**
(compiled from the vendored OpenUP KB's 39 task files), with the engine owning
all ceremony (frontmatter, traceability, validation) — so each cycle runs small,
isolated authoring tasks a weak local model can complete reliably?

## Context

Direct follow-on to
[2026-07-14-process-map-as-compiled-navigator.md](2026-07-14-process-map-as-compiled-navigator.md)
(P1, delivered: T-100…T-103 — navigation is now a deterministic walk of the
process map; the per-cycle LLM navigator is deleted). Prompted by the next live
failure class on the `my-product` / qwen driver (2026-07-14): with navigation
fixed, the **authoring procedures themselves** are now the reliability
bottleneck.

**Evidence (from `OPENUP_AGENT_DEBUG_LOG`, the T-098 transcript):** a
`create-vision` sub-run **restarted itself mid-run** (its "I'll execute the
procedure step by step" opener appears twice, rows 40 and 45), probed the
optional `docs/project-config.yaml` **5×**, reached iteration 9 of cap 10 with
no vision written. The same model had produced **3 clean create-vision DONEs**
earlier — weak-model *inconsistency*, not incapacity. Root cause is context
weight: the procedure file is only 143 lines, but it **instructs the model to
load a fan-out**:

| loaded during the run | lines |
|---|---|
| `openup-create-vision.md` (procedure) | 143 |
| `templates/vision.md` | 32 |
| `sops/self-critique.md` | 56 |
| `doc-frontmatter.md` | 104 |
| `rubrics/doc-traceability-rubric.md` | 148 |
| `scripts/trace-model.json` | 101 |
| `scripts/docs-meta.schema.json` | 74 |
| + project-config, project-status, brief, vision-rubric | … |

**~650+ lines of spec** held while *also* authoring a vision + format-strict
roadmap *and* self-validating. The task conflates four jobs: (a) author content,
(b) stamp typed frontmatter (T-038), (c) self-grade against the traceability
rubric, (d) self-critique. Jobs (b)–(d) are **ceremony the deterministic layer
already owns or gates** (`check-docs.py` runs after every step anyway).

**The owner's proposal (2026-07-14):** replace the `create-*` procedures with a
**generic procedure** supported by the specific KB tasks (e.g.
`practice-technical/shared_vision/tasks/develop-technical-vision-1.md`,
`use_case_driven_dev/tasks/detail-use-case-scenarios-1.md`,
`test_driven_development/tasks/implement-solution-1.md`,
`iterative_dev/tasks/manage-iteration-1.md`); each cycle identifies the next
step(s) and runs **small isolated tasks**.

## Notes

### Measured: the KB task files are reference prose, not lean instructions

| KB task file | lines |
|---|---|
| `develop-technical-vision-1.md` | 103 |
| `detail-use-case-scenarios-1.md` | 86 |
| `implement-solution-1.md` | 119 |
| `manage-iteration-1.md` | 100 |
| *(vs `openup-create-vision.md`)* | *143* |

They are the **same order of size** as the procedures, and they are verbose
UMA/RUP method prose — Purpose, Relationships, Roles-with-links,
Inputs-with-links, cross-references into `core/role/…`, `workproducts/…`,
`disciplines/…`. Handing one raw to a weak model **reproduces the fan-out** (100
lines + tempting links to follow). There are **39** such task files.

So the literal form of the proposal (link the model to the KB task) does not
reduce load. **The architecture is right with one correction: the task content
must be *distilled*, not linked-to raw.** Precedent: `process-map.yaml` (T-077)
distilled the KB's phase→activity→role structure into ~40 lean lines the driver
executes, while the verbose KB stays human reference. The same move applies one
level down: distill each KB task's *judgment content* into a lean task def.

### The refined shape (owner's proposal + the distill correction)

1. **One generic authoring procedure** — a slim shell: *"You are performing
   OpenUP task `<name>` (role: `<role>`). Produce `<artifact>` at `<path>`. What
   good looks like: `<lean judgment content>`. Read `<declared inputs>`. Save
   the file, emit the sentinel."* Replaces the seven `create-*` procedures
   (~1,417 lines total today).
2. **A distilled lean-task library** — one ~10–20-line def per task (artifact,
   path, the 4–6 bullets of what-good-looks-like, declared inputs), compiled
   *from* the KB tasks. KB files remain the human-readable source + `See also`.
3. **Process map maps activity → lean task(s)** — today `skills:
   [openup-create-vision]`; becomes the task ids. The T-100 schema
   (`requires_input`, `execution`) already carries per-activity data; this
   extends the same file.
4. **Engine owns the ceremony** — frontmatter stamping (T-038) becomes a
   deterministic post-step (the engine knows `type`/`id`/`status` from the task
   def); validation stays the existing `check-docs`/gates (already run after
   every step — the model self-grading against the rubric is redundant with the
   gate); self-critique drops out of the weak-model path (the gate is the
   critic) or becomes a separate tiny sub-run on strong models.
5. **The cycle runs small isolated sub-runs per task** — P1's plan-iteration
   already dispatches per *activity* (`execution: direct`); this refines the
   grain to *task* and slims what each sub-run reads. E.g. vision authoring
   becomes two bounded calls (vision content; then the roadmap with its pinned
   `T-NNN` format) instead of one omnibus call.

What each sub-run holds shrinks from ~650+ lines of spec to **~30–60 lines**
(generic shell + one lean task def + the input artifact) — the shape that
measured 3/3-reliable at ~59k tokens in T-080.

### Relationship to the deferred P2 (compile step)

Distilling 39 KB tasks into lean defs is **exactly the P2 "LLM compiles the
process once" job**, applied to tasks instead of the phase map — and now it has
the *evidenced* need P2 was deferred for. Same discipline as the T-099 lesson:
schema-strict output, a deterministic validator, human review before the loop
trusts it. (First cut can be hand-distilled for the 5–7 tasks the map actually
references; the compiler generalizes it later.)

### What this does NOT change

- The deterministic engine, resolve, gates, sentinels — untouched.
- Claude Code path — skills keep orchestrating in-context; parity stays at the
  artifact level. The `create-*` *skills* remain for that harness; it is the
  *driver's* procedure path that switches to generic+lean.
- The KB — read-only, as always.

## Options Considered

- **Option A — generic procedure + distilled lean-task library + engine-owned
  ceremony (the refined proposal).** Pro: per-call context drops ~10×; small
  isolated calls are the measured-reliable shape; net-negative procedure prose
  (~1,417 lines → 1 shell + N×15-line defs); extends T-077/T-100 patterns
  instead of inventing new ones; gives P2 its concrete, evidenced first job.
  Con: a real program (task-def schema, engine frontmatter-stamping, map
  refinement, distillation + validation); risk of over-thin defs
  under-producing (mitigated by the falsifiable measure + review).
- **Option B — keep per-artifact procedures, just slim them (strip rubric/
  frontmatter/self-critique loading).** Pro: smaller change, no new schema.
  Con: keeps 7 files to maintain in parallel; each still mixes shell + judgment
  content; doesn't give the cycle finer task grain; the fan-out tends to creep
  back (it got in there for a reason each time).
- **Option C — link the generic procedure to the raw KB task files (the literal
  proposal).** Pro: zero distillation work; single source. Con: **measured
  dead-end** — KB tasks are 86–119 lines of reference prose with link fan-out;
  a weak model either ignores the link (useless) or follows it (worse). Rejected
  on the numbers above.
- **Option D — do nothing; run a stronger model for authoring
  (`OPENUP_MODEL_MID`).** Pro: zero work; correct *today* as an operational
  workaround. Con: abandons the weak-local-model goal the whole reference-driver
  program exists to serve; the same fan-out still taxes strong models (tokens).

## Open Questions

1. **Task-def schema + home** — fields (id, artifact type, output path, role,
   judgment bullets, inputs); lives in `docs-eng-process/` next to
   `process-map.yaml` (e.g. `task-library.yaml` or `tasks/*.md` with strict
   frontmatter)? Validated by an extended `openup-process-map.py validate` or a
   sibling checker?
2. **Frontmatter stamping** — engine writes the whole frontmatter block
   post-authoring (model never sees the contract), or hands the model a
   pre-stamped file to fill? (Leaning: engine stamps after; model writes body
   only.)
3. **Granularity** — where does one activity split into multiple sub-runs
   (vision vs vision+roadmap; use-case outline vs detailed scenarios)? Encode as
   1..n ordered tasks per activity in the map.
4. **Self-critique on weak models** — drop (gate is the critic), or keep as an
   optional separate tiny sub-run gated by tier?
5. **Distillation route** — hand-distill the 5–7 map-referenced tasks first
   (fast, reviewable), then build the P2 compiler to cover the rest of the 39 +
   customized processes?
6. **Claude Code parity** — do the skills eventually consume the same lean task
   defs (single source), or stay as-is? (Out of scope for slice 1; note the
   drift risk.)

### Product-manager challenge pass

- **Pushback — "generic procedure" is not the value; smaller reliable calls
  are.** The user-observable outcome is: *a fresh project on a weak local model
  completes Inception authoring without thrash/restarts*. If that outcome could
  be had by Option B (slim the 7 procedures), the unification would be
  architecture-for-its-own-sake. *Disposition: challenge upheld and answered* —
  B fixes today's 7 files but leaves per-artifact shells to re-bloat and gives
  the cycle no finer task grain (the owner's "small isolated tasks per cycle"
  requirement); A is the same slimming plus a structure that stays slim because
  judgment content is data, not prose per artifact. Accepted: A, with B's
  slimming as its core mechanism.
- **Pushback — Option C is rejected on evidence, not preference.** The KB task
  files were measured (86–119 lines, link fan-out); linking them raw recreates
  the failure being fixed. *Disposition: rejected with the numbers recorded
  above* (prevents re-litigation — this was the literal form of the submission).
- **Complement — the distillation is the risk concentrate.** An over-thin task
  def under-produces (a 5-bullet vision def might yield a hollow vision); an
  over-thick one recreates the fan-out. This is the same class as the RDM-id
  lesson: LLM/hand-authored data feeding a machine loop MUST be schema-strict,
  validator-gated, human-reviewed. Folded into open questions 1 and 5 as
  requirements, and the first slice is deliberately **hand-distilled** so review
  quality is high before any compiler exists.
- **Complement — an operational stopgap exists and should be said out loud:**
  point `OPENUP_MODEL_MID` at a stronger model today (Option D). The program is
  justified by the weak-local-model goal + token cost on all models, not by
  there being no workaround.
- **Refine — falsifiable measure.** Not "procedures are simpler" but: on the
  qwen fixture (T-080 bench + my-product scenario), the Inception authoring
  tasks (vision, roadmap) complete with **zero mid-run restarts** (no repeated
  procedure-opener in the debug log), in **≤6 iterations per sub-run**, at
  **≥80% clean-pass over 5 runs**, with per-sub-run prompt context **≤⅓** of
  today's (measured via `OPENUP_AGENT_USAGE_LOG` prompt_tokens). Baseline: the
  2026-07-14 debug log (restart at cap-10, 5× config re-reads).
- **Refine — sequence in slices, each shippable:** (S1) engine-owned frontmatter
  stamping + strip rubric/self-critique loading from the weak-model path — the
  biggest context cut, no new schema; (S2) generic procedure + hand-distilled
  lean defs for the map's 5–7 referenced tasks + map wiring; (S3) the P2
  compiler distills the full KB task set (and customized processes). S1 is
  valuable even if S2 stalls.

Net PM disposition: **accepted as re-shaped** — Option A sequenced S1→S2→S3,
with C rejected on measurement, D named as the interim workaround, and the
distillation discipline (schema + validator + review) as a hard requirement.

## 2026-07-14 (append) — S3 named: the process compiler

Owner follow-up: *"Should we create a 'process compiler' which reads the openup
docs as sources and produces LLM prompts?"* — yes; this names and sharpens S3.

**Framing: process-as-source, compiled.** The KB (+ later a project's customized
process docs) is **source code** — verbose, human-authoritative, read-only. The
compiler produces **object code**: the machine artifacts the runtime executes —
`process-map.yaml`, the lean task-library defs (the LLM prompts), and the
`requires_input` declarations. All object code is **committed and human-reviewed**;
the runtime never reads the source.

**Precedent already in production:** `build-trace-model.py` (T-035) IS a process
compiler — it deterministically derives `trace-model.json` from the vendored KB,
and `check-docs.py` executes it. `process-map.yaml` (T-077) is the same output
shape, hand-compiled. The pattern is proven; S3 extends its scope (task prompts)
and adds one LLM stage.

**Two-stage compiler design:**
1. **Deterministic extraction (no LLM).** The UMA task files are machine-generated
   and regular — frontmatter (title/uma_name/roles), Inputs/Outputs sections,
   workproduct links. Roles, input artifacts, output artifact parse with the same
   stdlib approach `build-trace-model.py` uses → the task-def *skeleton*.
2. **LLM distillation (compile-time only).** The "what good looks like" bullets
   are distilled from the prose (Purpose/Steps/checklists) — once, schema-strict,
   validator-gated, human-reviewed, committed (the T-099 discipline). A bad
   compile is caught at review, never as per-cycle flakiness.

**Sequencing guard (anti-trap):** the compiler is NOT built first. The S2
hand-distilled defs — tuned until the qwen fixture hits the convergence measure —
become the compiler's **golden outputs** (its reference test set). The compiler's
economics start at scale: the remaining ~32 KB tasks, re-distillation when the KB
updates, and above all **customized processes** (a team points the compiler at
their process docs and gets a valid map + task library without forking the
framework — P2's original promise, now with a concrete mechanism).

Open-question additions: (7) compiler CLI shape — a sibling of
`build-trace-model.py` (e.g. `build-task-library.py`) with `--check` comparing
regenerated output against the committed library (drift detection, same as the
trace model); (8) golden-set testing — the compiler must reproduce (or improve
per review) the S2 hand-distilled defs before being trusted on the rest.

## 2026-07-14 (append 2) — re-sequenced: compiler-first (after S1)

Owner follow-up: *"should we do the compiler first?"* — re-examined, and the
earlier hand-distill-first argument **partially collapses**: it assumed
acceptance = matching golden hand-authored text. Acceptance is **behavioral** —
the T-080 bench + debug log on the qwen fixture ("def makes create-vision
converge: ≤6 iters, zero restarts, ≥80% of runs") judges compiler output
directly, no golden text needed. Once acceptance is behavioral, the compiler is
the *better* tuning tool:
- **tune → regenerate → rebench** is a tighter loop than divergent hand-edits
  (adjust the distillation rules once; all defs regenerate consistently);
- **uniformity** across defs (hand distillation drifts in style);
- **schema-first discipline** — building the compiler forces the task-def schema
  + validator up front (the T-099 lesson) instead of a schema emerging
  implicitly from hand files;
- it is **the product** — the whole arc is "compile the process once."

What survives of the earlier caution:
1. **S1 (engine-owned ceremony) still goes first** — the biggest context cut,
   compiler-independent, and without it even perfect defs won't converge (the
   sub-run would still drown in frontmatter/rubric/self-critique ceremony).
2. **Minimal compiler, no gold-plating** — deterministic extraction (structure
   from the regular UMA files, no LLM, same approach as `build-trace-model.py`)
   + ONE schema-strict LLM distillation stage + validator + `--check` drift
   mode; target the 5–7 map-referenced tasks only; seed the distillation prompt
   with **one hand-calibrated example def** (vision) as a style anchor — one
   def, not a hand-library. Extend to all 39 / customized processes only after
   the bench passes.

**Revised sequence (supersedes the S1→S2→S3 above):**
- **S1 — engine-owned ceremony** (frontmatter stamping; strip rubric/
  self-critique from the weak-model authoring path). Unchanged.
- **S2′ — the process compiler, minimal** (`build-task-library.py`: extract +
  distill + validate + `--check`), producing the lean task library for the
  map-referenced tasks + the generic authoring procedure + map wiring;
  acceptance = the behavioral measure on the qwen fixture.
- **S3′ — scale it**: the remaining KB tasks, KB-update re-distillation, and
  customized-process sources (the original P2 promise).

## Where this goes next

→ **iteration** — promote a program **"Lean authoring tasks"** on
`harness-optional`, sequenced per the compiler-first re-decision (append 2):
S1 (engine stamps frontmatter + slims the authoring sub-run context), then
S2′ (the minimal process compiler — `build-task-library.py` extract/distill/
validate/`--check` — producing the lean task library for the map-referenced
tasks, + the generic authoring procedure + map wiring; behavioral acceptance on
the qwen fixture), then S3′ (scale to the full KB + customized processes);
falsifiable measure as refined above, read back via the T-080 bench + debug log.

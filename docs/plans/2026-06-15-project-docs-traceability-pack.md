# Project Docs Traceability & Validation Pack

**Status**: `planned`
**Created**: 2026-06-15
**Priority**: medium
**Goal**: Give every OpenUP project a `docs/` that stays **linked, traceable, and
validated** — work-product instances carry typed traceability frontmatter
(injected by the `openup-create-*` skills and graded by a rubric, never by
editing OpenUP templates), a shipped validator checks schema + cross-links +
OpenUP trace coverage, and a derived index/board surfaces the trace web — all
distributed through the existing `process-manifest.txt` rails and tailorable via
`project-config.yaml`.

---

## Hard Guardrail: Change Surface

Owner rule (carried from the Modern Product Practice Pack, 2026-06-12): **we
never modify the OpenUP artifacts; we modify the claude-templates and the
framework tooling.**

- **Read-only**: `openup-knowledge-base/**` (vendored, converter-generated) and
  `docs-eng-process/templates/**` (OpenUP-derived document templates). The KB is
  *read* — both as the trace-model source and as the citation anchor — never
  edited. The work-product templates stay pristine.
- **Change surface**: `docs-eng-process/.claude-templates/**` (skills,
  rubrics, `CLAUDE.md`), `scripts/**` tooling (validator, schema, trace-model
  generator, `process-manifest.txt`), project-side hook templates, and
  `docs-eng-process/*.md` guide docs as **pointer documentation only** (no
  process rules live there).
- **Consequence for design**: instance frontmatter is introduced through the
  `openup-create-*` **skill instructions** and graded by a **rubric** — the base
  template files (`docs-eng-process/templates/vision.md`, etc.) are not touched.
  Authored work-product *instances* in `docs/product/` and `docs/changes/`
  carry the frontmatter; the OpenUP-derived templates stay clean. This is the
  same precedence chain the practice pack used: framework rubric → project rules
  → safeguards, where a layer adds criteria and never waives base ones.

---

## Context

A fresh OpenUP project's `docs/` starts empty (`bootstrap-project.sh` creates
`docs/` with only `.gitkeep`). It fills as agents generate **OpenUP work
products** from `docs-eng-process/templates/` — vision, work-items-list,
iteration-plan, architecture-notebook, use-case-specification, test-case,
risk-list, glossary. The framework already does linking/traceability/validation
**superbly for one tier and not at all for the other**:

| Tier | State today |
|---|---|
| **Task tier** — `docs/changes/T-NNN/plan.md` | Typed YAML coordination frontmatter (`id`, `status`, `depends-on`, `blocks`, `touches`, `plan:` anchor), a readiness DAG (`/openup-readiness`, `openup-board.py`), JSON-schema validation (`openup-state.schema.json`), githook guards. **Linked, traceable, validated.** |
| **Work-product tier** — `docs/product/**`, generated artifacts | Freeform narrative. The templates ship frontmatter that describes the *template's KB origin* (`type: Template`, `source_url`, `related.workproducts`) — **not** the produced instance. Once an agent fills a template in, the work product lands untyped, with no declared traceability and no validation. |

Two consequences for projects:

1. **No work-product trace web.** OpenUP's defining property is traceability
   between work products — Vision → Requirements → Work Items → Iteration Plan →
   Tasks → Design → Test Cases. Nothing in a project's `docs/` records or checks
   that a requirement is verified by a test, or that a work item cites its
   governing requirement.
2. **Today's traceability is run-log-centric, not artifact-centric.**
   `docs-eng-process/sops/traceability-logging.md` + `docs/agent-logs/*.jsonl`
   trace *agent runs* (commits, docs touched, decisions). That is process
   provenance — complementary to, but not a substitute for, **work-product
   semantics**.

The fix is not new infrastructure; it is generalizing the proven task-tier model
to all work products, distributed on the rails that already ship CLIs to every
project (`process-manifest.txt`: "add a CLI here once and it ships everywhere").

**OpenUP-native differentiator.** The valid trace relationships are not
arbitrary — they are OpenUP's defined work-product dependencies, and **the
vendored KB already encodes them** (`related.workproducts`, task inputs/outputs).
So the trace model can be *derived* from the manifest the converter already
produces, reusing an asset already in the repo, rather than hand-maintained.

This plan supersedes nothing. It is the concrete, project-facing landing of the
2026-06-15 OKF / LLM-Wiki evaluation: a project's `docs/` becomes a typed,
cross-linked, index-backed, validated bundle — an OKF-conformant, OpenUP-aware
knowledge base downstream agents can consume — without adopting OKF wholesale.

---

## Current State

- `docs-eng-process/templates/*.md` — work-product templates carry
  KB-provenance frontmatter only. `vision.md`: `type: Template`, `source_url`,
  `related.workproducts: [vision]`. No prescribed frontmatter for the *instance*
  a project produces.
- `docs/changes/T-NNN/plan.md` — the task tier already proves the model: `id`,
  `status`, `depends-on`, `blocks`, `touches`, `plan:` anchor; schema'd by
  `scripts/openup-state.schema.json`; surfaced by `scripts/openup-board.py` and
  `/openup-readiness`.
- `docs-eng-process/sops/traceability-logging.md` — traces runs/commits into
  `docs/agent-logs/` + `agent-runs.jsonl`. Process provenance, not work-product
  trace.
- `scripts/process-manifest.txt` — single source of truth for the CLIs every
  install/update path ships (`install-process-clis.sh`). New tooling rides here.
- `scripts/openup-state.schema.json` — JSON-schema validation precedent to mirror.
- `scripts/openup-board.py` / `scripts/sync-status.py` — derived-view generators
  (write-fence pattern from T-024) to extend for the trace index.
- `openup-knowledge-base/manifest.json` — `by_type` / `by_slug` indexes plus
  per-work-product `related.workproducts`: the source for the trace model.
- `.claude-templates/skills/openup-create-*` (vision, use-case, test-plan,
  architecture-notebook, iteration-plan, risk-list, task-spec, documentation) —
  each paired with a rubric in `.claude-templates/rubrics/`. These are the
  guardrail-safe injection points for instance frontmatter.

---

## Proposed Design

Six tasks (T-034…T-039), ordered so each builds on the previous. Recommended
defaults from the 2026-06-15 evaluation are baked in and flagged as vetoable in
Open Questions: **derive the trace model from the KB**, **advisory-by-default
with opt-in blocking**, **core work-product spine for v1**, **keep separate from
run-log traceability**.

### T-034 — Work-product taxonomy + instance-frontmatter spec + schema

Define the minimal, OKF-style instance frontmatter (one required field, `type`)
for work-product instances, distinct from template provenance. v1 covers the
**core spine**: `vision`, `requirement`, `work-item`, `iteration-plan`,
`use-case`, `test-case`, `decision` (`type` names align to KB work-product
slugs).

```yaml
---
type: requirement          # required; the only mandatory field
id: REQ-014                 # stable id, project-unique
title: Authenticated checkout
status: approved            # draft | approved | implemented | verified | obsolete
traces-from: [VIS-001]      # upstream work products this satisfies/refines
verified-by: [TC-031]       # test coverage (where the type warrants it)
owner-role: analyst
iteration: construction-2
---
```

`traced-by` is the derived inverse (written by the index generator, not by
hand). Ship `scripts/docs-meta.schema.json` mirroring `openup-state.schema.json`.
Document the contract in a new pointer doc `docs-eng-process/doc-frontmatter.md`.

**Files**: `scripts/docs-meta.schema.json` (new),
`docs-eng-process/doc-frontmatter.md` (new guide).
**Verify**: schema validates a hand-written conformant instance and rejects one
missing `type` / with an unknown `status`.
**Depends on**: none. No template edits (guardrail).

### T-035 — Derive the OpenUP trace model from the vendored KB

`scripts/build-trace-model.py` reads `openup-knowledge-base/manifest.json` and
work-product `related.workproducts` to emit `scripts/trace-model.json`: the valid
`type → type` trace edges and the **required-coverage** edges (e.g.
`requirement` must be `verified-by` a `test-case`; `work-item` must `trace-from`
a `requirement`). The KB is read-only — the model is generated, not edited into
the KB.

**Files**: `scripts/build-trace-model.py` (new), `scripts/trace-model.json`
(generated, committed), `scripts/tests/test_build_trace_model.py` (new).
**Verify**: generated model contains `requirement→test-case` as a coverage edge;
re-running on an unchanged KB is idempotent (stable output).
**Depends on**: T-034 (type names).

### T-036 — `check-docs.py` validator core

The mechanical backbone (ships via `process-manifest.txt`). `scripts/check-docs.py`:

- **Schema-validate** every work-product instance frontmatter under `docs/`
  against `docs-meta.schema.json`.
- **Resolve links**: every relative `.md` link and every trace-ref id
  (`traces-from`, `verified-by`, `plan:` anchors into the task tier) points to a
  real file/task — broken-link / dangling-id detection.
- **Bidirectional consistency**: if A `traces-from` B then B may not contradict
  it; `verified-by` ids must be `test-case` instances that exist.
- Exit non-zero on hard failures (schema + unresolved refs); machine-readable +
  human summary output.

**Files**: `scripts/check-docs.py` (new),
`scripts/tests/test_check_docs.py` (new).
**Verify**: a doc with a dangling `verified-by: [TC-999]` fails; a typed,
fully-resolved set passes; a missing `type` fails schema.
**Depends on**: T-034 (schema), T-035 (model for ref typing).

### T-037 — Trace-coverage checks + derived index/board

`check-docs.py --coverage` evaluates the project against `trace-model.json`:
`approved` requirements with no `verified-by` test, work-items with no governing
requirement, orphan work products (referenced by nothing). Severity is
configurable (advisory by default, T-039). A derived, **read-only** index —
`docs/INDEX.md` (or a section emitted by `openup-board.py`) — renders the trace
web (Vision → … → Tests) and a coverage summary ("3 requirements lack tests"),
using the write-fence / derived-view pattern from T-024 so parallel lanes don't
collide on it. The index also writes the `traced-by` inverse links.

**Files**: `scripts/check-docs.py` (coverage mode),
`scripts/openup-board.py` (trace-web + coverage section) **or** a new
`scripts/docs-index.py` writer, derived `docs/INDEX.md` (generated).
**Verify**: a project with an unverified requirement reports it in coverage and
in the index summary; the index is regenerated deterministically and is not
hand-editable (write-fence).
**Depends on**: T-036.

### T-038 — Author-time frontmatter via `create-*` skills + cross-cutting rubric

The guardrail-respecting wiring that makes docs **born compliant**. Each
`openup-create-*` skill (vision, use-case, test-plan, architecture-notebook,
iteration-plan, risk-list, task-spec) gains an authoring step that writes the
instance frontmatter (T-034) onto the produced doc — populating `type`, `id`,
`status`, and the trace fields it can know (`traces-from` its governing upstream
artifact, `verified-by` for testable types). A single cross-cutting
`.claude-templates/rubrics/doc-traceability-rubric.md` grades presence and
correct trace direction, referenced from each create skill's grading step (one
rubric, not six edits). `/openup-complete-task` runs `check-docs.py` before
"done". **Templates untouched** — frontmatter lands on instances only.

**Files**: `.claude-templates/skills/openup-create-*/SKILL.md` (authoring step
+ rubric reference), `.claude-templates/rubrics/doc-traceability-rubric.md`
(new), `.claude-templates/skills/openup-complete-task/SKILL.md` (validator gate),
`.claude-templates/CLAUDE.md` (convention pointer).
**Verify**: author a vision then a requirement via the skills; confirm both
emit conformant frontmatter with the vision→requirement trace; a requirement
authored with no upstream trace fails the rubric; `complete-task` blocks while
`check-docs` reports a hard failure.
**Depends on**: T-034 (spec), T-036 (validator to call).

### T-039 — Distribution, enforcement, and project-side tailoring

Ship and enforce it everywhere. Add `check-docs.py`, `docs-meta.schema.json`,
`trace-model.json`, `build-trace-model.py` (and `docs-index.py` if introduced)
to `scripts/process-manifest.txt` so every install/update path delivers them to a
project's `scripts/`. Add a project-side hook template
(`.claude-templates/scripts/hooks/check-docs`) wired in the generated
`settings.json`: hard checks (schema + links) block commits; coverage is
advisory. Tailor via `docs/project-config.yaml`: `doc_types:` in play and
`trace_rules:` (which coverage rules **block** vs **advise**) — OpenUP is meant
to be tailored through the development case, so strictness must be project-owned.
Document adoption for existing projects in `docs-eng-process/updating.md`.

**Files**: `scripts/process-manifest.txt`,
`.claude-templates/scripts/hooks/check-docs` (new) + `settings.json` wiring,
`docs-eng-process/project-config.md` (document keys — pointer doc),
`docs-eng-process/updating.md` (adoption note).
**Verify**: a freshly bootstrapped project has `check-docs.py` in `scripts/` and
the hook wired; a commit adding an untyped work product is blocked; flipping a
`trace_rules:` entry to advisory downgrades a coverage failure to a warning.
**Depends on**: T-036, T-037, T-038.

---

## Task Decomposition

| ID | Title | Priority | Depends on | Est. |
|---|---|---|---|---|
| T-034 | Work-product taxonomy + instance-frontmatter spec + `docs-meta.schema.json` | medium | — | 1 session |
| T-035 | Derive `trace-model.json` from the vendored KB (`build-trace-model.py`) | medium | T-034 | 1 session |
| T-036 | `check-docs.py` validator core (schema + link/id resolution + bidirectional) | high | T-034, T-035 | 1–2 sessions |
| T-037 | Trace-coverage checks + derived trace index/board (write-fence) | medium | T-036 | 1 session |
| T-038 | Author-time frontmatter via `create-*` skills + cross-cutting rubric + complete-task gate | high | T-034, T-036 | 1–2 sessions |
| T-039 | Distribution (`process-manifest`) + project-side hook + `project-config` tailoring + updating docs | medium | T-036, T-037, T-038 | 1 session |

**Wave sequencing**:

1. **Wave 1**: T-034 (the contract) → T-035 (model)
2. **Wave 2**: T-036 (validator core — the payoff)
3. **Wave 3**: T-037 (index/coverage) ∥ T-038 (author-time wiring)
4. **Wave 4**: T-039 (ship + enforce + tailor)

```
T-034 ──► T-035 ──► T-036 ──► T-037 ─┐
   └───────────────► T-036 ──► T-038 ─┴─► T-039
```

---

## Acceptance Criteria (program level)

- [ ] A work product authored through any `openup-create-*` skill emits
      conformant instance frontmatter (`type` + trace fields); the OpenUP
      templates remain byte-for-byte unchanged.
- [ ] `check-docs.py` fails on a missing `type`, a dangling trace-ref, or a
      broken relative `.md` link; passes a fully-resolved typed set.
- [ ] `trace-model.json` is generated from the vendored KB and marks
      `requirement → test-case` as a required-coverage edge.
- [ ] `check-docs.py --coverage` reports an `approved` requirement with no
      verifying test, and the derived index surfaces the same gap.
- [ ] The trace index is a generated, write-fenced view (not hand-editable) and
      writes `traced-by` inverses.
- [ ] `/openup-complete-task` blocks while `check-docs` reports a hard failure.
- [ ] A freshly bootstrapped project ships `check-docs.py` (via
      `process-manifest.txt`) with the project-side hook wired; an untyped work
      product is blocked at commit.
- [ ] `project-config.yaml` `trace_rules:` can downgrade any coverage rule from
      blocking to advisory (and back) without code changes.
- [ ] Run-log traceability (`agent-runs.jsonl`) is untouched and continues to
      operate independently.

---

## Key Files

| File | Change |
|---|---|
| `scripts/docs-meta.schema.json` | new — instance frontmatter schema |
| `scripts/build-trace-model.py`, `scripts/trace-model.json` | new — KB-derived trace model + generator |
| `scripts/check-docs.py` | new — validator (schema + links + coverage) |
| `scripts/openup-board.py` *or* `scripts/docs-index.py` | trace-web + coverage derived view |
| `scripts/process-manifest.txt` | register the new CLIs so every install ships them |
| `scripts/tests/test_check_docs.py`, `test_build_trace_model.py` | new — test coverage |
| `.claude-templates/skills/openup-create-*/SKILL.md` | authoring step that writes instance frontmatter |
| `.claude-templates/rubrics/doc-traceability-rubric.md` | new — cross-cutting grading |
| `.claude-templates/skills/openup-complete-task/SKILL.md` | run `check-docs` as a completion gate |
| `.claude-templates/scripts/hooks/check-docs` + `settings.json` | project-side enforcement hook |
| `docs-eng-process/doc-frontmatter.md` | new guide (pointer doc) |
| `docs-eng-process/project-config.md`, `updating.md` | document `doc_types:` / `trace_rules:`; adoption note |

## Out of Scope

- Any edit to `openup-knowledge-base/**` or `docs-eng-process/templates/**`
  (hard guardrail).
- Adopting OKF/Obsidian wholesale, `[[wiki-link]]` syntax, or embeddings/RAG —
  markdown + typed frontmatter + a generated index + a validator covers
  "linked, traceable, validated".
- Replacing or merging run-log traceability — the two stay complementary.
- Retrofitting the trace fields onto a consumer project's existing docs
  automatically — projects adopt by re-syncing templates and backfilling; an
  adoption note ships with T-039.
- Numeric trace-coverage scoring / dashboards beyond the pass/gap summary.
- CI/server-side enforcement — local project-side hooks first.

## Open Questions

Defaults recorded as vetoable assumptions (from the 2026-06-15 evaluation):

1. **Assumed: trace model is derived from the vendored KB** (authoritative,
   auto-updates with the KB) rather than a hand-curated minimal model. *Vetoable
   — a hand-curated spine is simpler if the KB relationships prove too noisy.*
2. **Assumed: coverage rules are advisory-by-default, opt-in blocking** via
   `trace_rules:`. *Vetoable — blocking-by-default gives stronger guarantees at
   higher adoption friction.*
3. **Assumed: v1 covers the core spine** (vision, requirement, work-item,
   iteration-plan, use-case, test-case, decision), not the full OpenUP
   work-product set. *Vetoable at review.*
4. **Assumed: work-product traceability stays separate from run-log
   traceability.** *Vetoable — `check-docs` could optionally cross-check that
   work-product changes appear in run-logs.*
5. **Assumed: the derived trace index lives at `docs/INDEX.md`** (single file)
   rather than per-directory `index.md` files (OKF-style). *Vetoable — per-dir
   indexes are more OKF-conformant but multiply the write-fenced surface.*

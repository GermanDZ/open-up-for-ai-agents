# Project Config — `docs/project-config.yaml`

A single, **project-owned** home for the facts and rules that are true *here* but
not everywhere — injected uniformly into every `/openup-create-*` artifact prompt
so they don't leak into `CLAUDE.md` or get re-typed in every request.

The framework rubrics (`.claude/rubrics/*-rubric.md`) stay **framework-owned**.
Project config **layers on top** of them; it never edits or replaces them.

> Optional by design. If `docs/project-config.yaml` does not exist, every
> create-* skill skips its "Load Project Config" step and behaves exactly as the
> framework default. Adopting or dropping the feature is one file.

---

## File location

`docs/project-config.yaml` — at the root of the consuming project's `docs/`,
beside `project-status.md` / `roadmap.md`. It is committed by the *project*, not
by the framework. `/openup-init` emits a starter copy from
[`templates/project-config.example.yaml`](templates/project-config.example.yaml).

This framework repo does **not** ship a live `docs/project-config.yaml` of its own
(it has no project-specific stack/domain to inject) — only the example template
and the init emitter.

## Schema

Four top-level keys, all optional:

```yaml
context: |            # free-text project facts the framework can't infer
  Tech stack: …
  Domain: …
  Key stakeholders: …

rules:                # per-artifact criteria, ADDITIVE to the framework rubric
  use-case:
    - Reference a named stakeholder, never the generic "the user"
  task-spec:
    - Any auth-touching task must cite the compliance control it affects

environments:         # ordered deployment chain, first = closest to the team
  - name: staging
    promotion: "smoke suite green; no Sev-1 defects open"
  - name: beta
    promotion: "beta-user acceptance recorded; success-measure instrumentation emitting"
  - name: production

trace_rules:          # T-039 — project-side tailoring for the doc-traceability hook
  enabled: true                       # default true; false skips the commit hook
  coverage: true                      # default true; false drops --coverage
  severity:                           # per-rule override map; key = "type -> relation -> target"
    "requirement -> verified-by -> test-case": advisory

process:              # T-076 — Development Case: tailor the lifecycle by archetype
  archetype: product                  # quick | mvp | product (sets the per-phase defaults)
  phases:                             # optional overrides of the archetype defaults
    construction: { iterations: many, parallel: true }
  milestone_review: human             # human | auto-assess
```

- **`context:`** — a block scalar of project-level facts (stack, domain,
  compliance posture, key stakeholders). Injected verbatim into *every* artifact.
- **`rules:`** — a mapping keyed by **artifact type**, each value a list of
  short, checkable criteria. Injected only into the matching artifact's prompt.
- **`environments:`** — an **ordered list** of deployment environments, each with
  a `name` and (except the last) a free-text, checkable `promotion:` criterion
  for advancing a release to the next entry. `staging → beta → production` is
  the documented example, **not** a schema — any ordered chain works. Consumers:
  `/openup-transition` walks the chain hop by hop (one promotion checklist per
  hop; OpenUP's beta-test objective maps onto the pre-production entries) and
  task-spec `## Rollout` sections use the names for per-environment flag default
  states (rubric criterion 13 flags states naming environments the config
  doesn't define). Absent → single-hop deployment, unchanged framework default.
- **`trace_rules:`** — project-side tailoring for the doc-traceability commit
  hook (`.claude/scripts/hooks/check-docs.py`, T-039). Three optional sub-keys:
  - `enabled:` (bool, default `true`) — set `false` to silence the hook
    entirely (the validator is still available on the CLI).
  - `coverage:` (bool, default `true`) — set `false` to drop `--coverage`
    from the hook's run; schema + ref/link checks still gate the commit.
  - `severity:` (mapping) — per-rule override. Keys are rule identifiers
    in the form `"type -> relation -> target"` (matching the messages
    `check-docs.py --coverage` prints); values are `required` or
    `advisory`. Downgrading a rule to `advisory` causes the hook to
    report the gap without blocking the commit. **OpenUP is meant to be
    tailored through the development case**, so strictness must be
    project-owned — the framework's `trace-model.json` is never edited.
    `/openup-complete-task`'s validator gate (step 3a) is **not** subject
    to these overrides — completion is the strictness floor.
- **`process:`** — OpenUP's **Development Case** made machine-readable: an
  `archetype` (quick | mvp | product) sets per-phase defaults, overridable per
  phase. **This `quick` is a different axis from the per-task ceremony
  `quick`/`standard`/`full` track in `tracks.md`** — the archetype tailors an
  entire phase's iteration budget/artifacts, the track sets one task's
  ceremony; don't conflate them. Structurally validated by `check-docs.py`
  (see the dedicated section below). Absent → no archetype tailoring applies
  (see `check-docs.py --show-archetype-defaults` for the exact defaults each
  archetype would set, and confirmation of what "absent" means).

The `context:`, `rules:`, `environments:`, and `trace_rules:` keys are
intentionally **unvalidated** (add a linter only if broadly adopted). The
`process:` key is the exception — it *is* structurally validated by
`check-docs.py`, because downstream lifecycle automation (T-077+) reads it and a
malformed section would misroute real delivery work.

## Artifact-type keys

A `rules:` key equals the **`/openup-create-<type>` skill suffix**, so a reader
maps a rule block to its skill by name. The seven artifact create skills consume
project config:

| `rules:` key            | Skill                                | Artifact |
|-------------------------|--------------------------------------|----------|
| `vision`                | `/openup-create-vision`              | Vision |
| `use-case`              | `/openup-create-use-case`            | Use case specification |
| `architecture-notebook` | `/openup-create-architecture-notebook` | Architecture notebook |
| `iteration-plan`        | `/openup-create-iteration-plan`      | Iteration plan |
| `task-spec`             | `/openup-create-task-spec`           | Task spec (REASONS Canvas) |
| `test-plan`             | `/openup-create-test-plan`           | Test plan |
| `risk-list`             | `/openup-create-risk-list`           | Risk list |

Skills that emit *workflow outputs* rather than project specs
(`create-pr`, `create-handoff`, `create-documentation`) do **not** consume
project rules.

## Injection format

Each consuming skill, before drafting, loads `docs/project-config.yaml` and emits
into its working prompt:

```
<project-context>
{context}
</project-context>

<project-rules>
{rules.<artifact-type>}
</project-rules>
```

`<project-context>` is the same for every artifact; `<project-rules>` carries only
the block for *that* artifact type. If the file is absent, or the relevant key is
empty/missing, the corresponding block is omitted entirely.

## Development Case — the `process:` section

`process:` is OpenUP's **Development Case**
(`project_process_tailoring/guidances/concepts/development-case.md`) made
machine-readable. It lets one config block tailor the whole delivery lifecycle so
ceremony matches scope. The lifecycle automation (T-077 plan-iteration, T-078
milestone-review) reads it; this document defines the shape and
`check-docs.py`/`openup-doctor` validate it.

### Shape

```yaml
process:
  archetype: product        # quick | mvp | product — REQUIRED when process: is present
  phases:                   # OPTIONAL — override any archetype default, per phase
    inception:    { iterations: <int|auto|many|skip>, artifacts: [<name>...], exit: <str> }
    elaboration:  { iterations: …, artifacts: […], exit: …, parallel: <bool> }
    construction: { iterations: …, parallel: <bool> }
    transition:   { gate: human|auto }
  milestone_review: human   # OPTIONAL — human | auto-assess (archetype default otherwise)
```

- `archetype` picks a **default set**; any explicit `phases:` / `milestone_review`
  key **overrides** that default (phases the config omits keep the archetype
  default).
- `iterations` is an int (`0` = phase skipped) or one of `auto` / `many` / `skip`.
  `auto` means "keep planning iterations while architecturally-significant risk
  is open" — the KB's Elaboration rule.
- The section may **only set ceremony levels** — it may not carry a key that
  waives a framework rubric criterion or a safeguard (unknown keys are rejected
  by the validator).

### Archetype defaults

| Phase | `quick` | `mvp` | `product` |
|---|---|---|---|
| **Inception** | 1 iter, no artifacts | 1 iter — vision, use-case-outline, risk-list | 1 iter — vision, use-case-outline, risk-list |
| **Elaboration** | **skipped** | 1 thin iter — architecture-notebook; exit `architecture-validated` | `auto` iters — architecture-notebook, detailed-use-cases, test-plan; exit `architecture-validated` |
| **Construction** | 1 iter, no parallel | `many` iters, no parallel | `many` iters, **parallel** |
| **Transition** | gate `auto` | gate `human` | gate `human` |
| **`milestone_review`** | `auto-assess` | `human` | `human` |

`quick` deliberately degenerates to today's `/openup-quick-task` ceremony
(near-empty Inception, Elaboration skipped, one Construction iteration,
auto-assessed milestones) — the token-efficiency guardrail: a quick project must
not cost more than the quick track does today.

### Validation

`check-docs.py` validates the section **structurally** (known archetype, known
phase keys, well-typed values, no safeguard-waiving keys); a malformed section is
a **hard failure** (blocks `/openup-complete-task` step 3a), an **absent** section
passes. `openup-doctor` reports the same as a read-only `process-config`
line (INFO when absent/valid, WARNING pointing at `check-docs.py` when invalid).
It does **not** judge whether the chosen archetype is *appropriate* — that is a
human call carried by the milestone record, not the script.

## Precedence

```
framework rubric  →  project rules  →  task-spec safeguards
```

Project rules are **additive**. A project rule may *add* a criterion the universal
rubric can't carry, but it may **not** waive a framework rubric criterion or a
task-spec safeguard. When grading an artifact for completeness, satisfy the
framework rubric first, then the injected `<project-rules>`, then the task-spec's
own `## Safeguards`.

The `process:` section extends this same additive chain at the **lifecycle** level:
an archetype may only *raise or lower ceremony* (iteration budgets, artifact sets,
milestone formality) — it may never waive a framework rubric criterion or a
task-spec safeguard. The validator enforces this by rejecting any `process:` key
outside the ceremony vocabulary.

## Consuming skills

The seven artifact create skills above each carry a uniform **Load Project
Config** step at the top of their `## Process` section. `/openup-init` emits the
starter file. This document is the single source of the mechanism; the per-skill
steps point here and name only their own artifact-type key.

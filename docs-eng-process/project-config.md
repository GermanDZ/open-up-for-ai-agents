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

Two top-level keys, both optional:

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
```

- **`context:`** — a block scalar of project-level facts (stack, domain,
  compliance posture, key stakeholders). Injected verbatim into *every* artifact.
- **`rules:`** — a mapping keyed by **artifact type**, each value a list of
  short, checkable criteria. Injected only into the matching artifact's prompt.

Start unvalidated: there is intentionally no schema/linter for this file (add one
only if the feature is broadly adopted).

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

## Precedence

```
framework rubric  →  project rules  →  task-spec safeguards
```

Project rules are **additive**. A project rule may *add* a criterion the universal
rubric can't carry, but it may **not** waive a framework rubric criterion or a
task-spec safeguard. When grading an artifact for completeness, satisfy the
framework rubric first, then the injected `<project-rules>`, then the task-spec's
own `## Safeguards`.

## Consuming skills

The seven artifact create skills above each carry a uniform **Load Project
Config** step at the top of their `## Process` section. `/openup-init` emits the
starter file. This document is the single source of the mechanism; the per-skill
steps point here and name only their own artifact-type key.

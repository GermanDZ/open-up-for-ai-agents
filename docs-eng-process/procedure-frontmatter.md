# Neutral Procedure Frontmatter (harness-optional OpenUP)

The harness-neutral procedure pack lives at `docs-eng-process/procedures/openup-*.md`
— one flat file per procedure. It is the **single editable source** for every
OpenUP procedure body (T-071). Each harness is an adapter that translates this
neutral frontmatter into its own dialect; `scripts/render-claude-adapter.py` +
`scripts/sync-templates-to-claude.sh` do that for Claude Code, reproducing
`.claude/skills/<name>/SKILL.md` with byte parity.

This doc defines the neutral schema. It is distinct from the Claude Code skill
frontmatter (`docs-eng-process/doc-frontmatter.md` covers authored **doc**
instances; this covers **procedure** files).

## Schema

```yaml
---
name: openup-next                 # required — procedure id, matches the filename stem
description: Run ONE OpenUP …      # required — one-line summary (the skill picker reads it)
tier: reasoning                    # required — a tier NAME (see below); NOT a model string
capabilities:                      # required — runtime capability contract
  required: [read_write_files, exec]
  optional: [subagents]
arguments:                         # optional — same shape as Claude Code skill arguments
  - name: task_id
    description: "…"
    required: false
fit:                               # optional — great/ok/poor routing hints
  great: [...]
  ok: [...]
  poor: [...]
---
```

`name`, `description`, `arguments`, and `fit` carry over from the Claude Code
skill frontmatter unchanged. The two neutral-specific fields are `tier` and
`capabilities`.

### `tier` (required) — a runtime-resolved NAME, never a model string

`tier` names one of the five editorial tiers (`docs-eng-process/model-tiers.md`).
**No concrete model string appears in the pack** (owner decision 6): the name is
resolved to a concrete model per target at runtime via `docs-eng-process/tier-map.yaml`.

| Tier name | What belongs here | claude-code model |
|---|---|---|
| `scribe` | fully-specified mechanical writes (logs, status fields, handoff/input-request docs, JSONL) | haiku |
| `coordination` | low-judgment process orchestration (starting iterations, deploying teams, phase checklists, readiness DAG) | haiku |
| `authoring` | template+rubric artifact synthesis (use cases, vision, plans, specs, docs, PRs, retrospectives) | sonnet |
| `quality-gate` | judgment gates deciding *done* (per-criterion rubric grading, phase review) | inherit |
| `reasoning` | open-ended problem solving (implementation, TDD, exploration, orchestration, task completion, spec back-prop) | inherit |

An unknown tier name is a **hard error** in every consumer (adapter, tier check) —
never silently defaulted.

### `capabilities` (required) — runtime capability contract

Makes the harness-optional capability split explicit so a driver/adapter can skip
or degrade a procedure it can't fully support.

- `required: [read_write_files, exec]` — the baseline every procedure needs
  (manipulate repo files, run `python3`/`git`). A harness lacking these cannot run
  OpenUP at all.
- `optional: [subagents]` — present on procedures that spawn a team / parallel
  subagents (`openup-deploy-team`, `openup-fan-out`, `openup-orchestrate`,
  `openup-start-iteration`). They **degrade to sequential** when the capability is
  absent, rather than failing.

Claude Code ignores unknown keys, so the adapter **drops** `capabilities` on emit
(the value is for non-Claude drivers, T-072).

## Adapter contract (neutral → Claude Code)

`scripts/render-claude-adapter.py <procedure> --target claude-code`:

1. `tier: <name>` → `model: <tier-map[claude-code][name]>`.
2. Drop the `capabilities:` key.
3. Everything else (name, description, arguments, fit, body) passes through verbatim.

Result is byte-identical to today's hand-synced `.claude/skills/<name>/SKILL.md`.
`scripts/check-model-tiers.py` reads `tier:` from the pack as the source of truth
and validates the generated `model:` against the same `tier-map.yaml` column.

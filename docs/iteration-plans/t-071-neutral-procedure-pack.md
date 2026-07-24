---
type: iteration-plan
id: T-071
status: draft
title: "Neutral procedure pack + runtime tier map + re-pointed Claude Code adapter"
traces-from: []
verified-by: []
---

# T-071: Neutral procedure pack + runtime tier map + re-pointed Claude Code adapter

**Phase**: construction
**Status**: pending
**Goal**: Extract the skill bodies into a harness-neutral procedure pack with a
neutral frontmatter schema (tiers declared as runtime-resolved *names*), and turn
`sync-templates-to-claude.sh` into a translating adapter so today's `.claude/`
output is reproduced with parity.
**Priority**: high

---

## Context

Today the process ships as a Claude Code plugin surface. The canonical procedures
live at `docs-eng-process/.claude-templates/skills/openup-<name>/SKILL.md` — a
Claude-shaped home — and `scripts/sync-templates-to-claude.sh` copies them
**verbatim** into `.claude/`. That coupling is thin (the exploration's audit shows
enforcement is all files + Python + git), but two things bind the procedures to
Claude Code specifically:

1. **Canonical location** is a `.claude-templates/` tree.
2. **Frontmatter dialect** — `model:` holds a concrete Claude value
   (`inherit` / `haiku` / `sonnet`), so the source of truth encodes Claude model
   choices. Owner decision 6 requires tiers to be declared as **names** resolved
   to concrete models at runtime, per harness.

T-071 is Layer 1 of the harness-optional program
([plans block in roadmap](../roadmap.md) / [exploration](../explorations/2026-07-12-harness-agnostic-openup.md)):
one neutral pack + a Claude Code adapter that reproduces current behavior, so
Claude Code stays first-class while a non-Claude driver (T-072) can read the same
pack.

---

## Current State

### The generator copies skills verbatim (`scripts/sync-templates-to-claude.sh`)

```bash
# Sync skills — FLAT layout.
#   Each templates/skills/openup-<name>/SKILL.md maps to .claude/skills/openup-<name>/SKILL.md
src_dir="$DEV_PROCESS_DIR/skills"          # docs-eng-process/.claude-templates/skills
for skill_src in "$src_dir"/*/; do
  skill_name=$(basename "$skill_src")
  skill_file="$skill_src/SKILL.md"
  copy_item "$skill_file" "$CLAUDE_DIR/skills/$skill_name/SKILL.md" "skills/$skill_name"
done
```

It also syncs (verbatim) `rubrics/`, `scripts/hooks/`, `config/`, `agents/`,
`teammates/`, `teams/`, and `CLAUDE.md` from the same `.claude-templates/` root.

### Frontmatter dialect (all 35 template skills)

```yaml
---
name: openup-next
description: Run ONE OpenUP delivery cycle — ...
model: inherit          # <-- concrete Claude value: inherit | haiku | sonnet
fit:
  great: [...]
  ok: [...]
  poor: [...]
arguments:
  - name: task_id
    description: "..."
    required: false
---
```

Field frequency across the 35 skills: `name` 35, `description` 35, `model` 35,
`arguments` 34, `fit` 20. Concrete `model:` values in use: `inherit` (×11),
`haiku` (×11), `sonnet` (×13) — see `docs-eng-process/model-tiers.md`.

### Tier tables are generated from `model:` (`scripts/check-model-tiers.py`)

`model-tiers.md`'s per-skill and per-agent tables are regenerated from the live
`model:` frontmatter (`--write`); CI (`--check`) fails if the table and
frontmatter disagree or any skill/agent lacks a `model:`. The five editorial
tiers already exist: **Scribe**→haiku, **Coordination**→haiku,
**Authoring**→sonnet, **Quality Gate**→inherit, **Reasoning**→inherit.

---

## Proposed Design

### Change 1: Neutral procedure pack home + schema

**New location**: `docs-eng-process/procedures/openup-<name>.md` (flat; one file
per procedure — no per-skill directory needed in the neutral pack).

**Neutral frontmatter schema** (adapter-translated, not Claude-specific):

```yaml
---
name: openup-next
description: Run ONE OpenUP delivery cycle — ...
tier: reasoning          # <-- tier NAME, not a model string (decision 6)
capabilities:            # exploration Layer-2 capability tiers
  required: [read_write_files, exec]
  optional: [subagents]  # team/fan-out procedures degrade to sequential without these
arguments:
  - name: task_id
    description: "..."
    required: false
fit:
  great: [...]
  ok: [...]
  poor: [...]
---
```

- `model:` → **`tier:`** carrying a name from a fixed vocabulary
  (`scribe`, `coordination`, `authoring`, `quality-gate`, `reasoning`).
- `capabilities:` makes the exploration's required/optional split explicit so an
  adapter/driver can skip or degrade team-based procedures.
- `name`, `description`, `arguments`, `fit` carry over unchanged.

### Change 2: Runtime tier→model map

**New file**: `docs-eng-process/tier-map.yaml` (the neutral default) — a plain
name→model table keyed by adapter/target:

```yaml
# Resolved at runtime; NO concrete Claude strings live in the procedure pack.
claude-code:
  scribe:        haiku
  coordination:  haiku
  authoring:     sonnet
  quality-gate:  inherit
  reasoning:     inherit
driver:                       # T-072 consumes this; overridable by env/config
  scribe:        "${OPENUP_MODEL_SMALL:-local-small}"
  coordination:  "${OPENUP_MODEL_SMALL:-local-small}"
  authoring:     "${OPENUP_MODEL_MID:-local-mid}"
  quality-gate:  "${OPENUP_MODEL_MAIN:-local-main}"
  reasoning:     "${OPENUP_MODEL_MAIN:-local-main}"
```

The map is the single place model choices live; a run selects a column by target
and (for the driver) resolves env placeholders against the model names the
`LLM_API_URL` server actually surfaces. This is decision 6: *tiers configured by
matching names that surface at runtime.*

### Change 3: `sync-templates-to-claude.sh` becomes a translating adapter

Re-point the skills loop at `docs-eng-process/procedures/`, and translate neutral
→ Claude frontmatter on emit:

- `tier: <name>` → `model: <claude-code column value>` (via `tier-map.yaml`).
- Drop `capabilities:` (Claude Code ignores it) — or keep as a passthrough comment.
- `name` / `description` / `arguments` / `fit` copied through.
- Emit to `.claude/skills/openup-<name>/SKILL.md` exactly as today.

Frontmatter translation is small structured YAML surgery; do it in a Python
helper (`scripts/render-claude-adapter.py`) the shell script calls, rather than
`sed`, so key handling is robust. Rubrics/hooks/agents/teammates/teams/CLAUDE.md
stay sourced from `.claude-templates/` for this task (they are already
markdown/Python and not the procedure pack; moving them is out of scope).

### Change 4: Keep `check-model-tiers.py` honest

Decide (Open Question 1) whether the tier tables are generated from the neutral
`tier:` field (preferred — the pack is the source of truth) and validated against
the generated `.claude/` `model:` values via the `tier-map.yaml` claude-code
column. Update `check-model-tiers.py` so `--check` passes with `tier:` in the pack
and concrete `model:` in generated output.

---

## Acceptance Criteria

- [ ] `docs-eng-process/procedures/openup-<name>.md` exists for all 35 procedures;
      each carries the neutral schema (`tier:`, `capabilities:`, `name`,
      `description`, `arguments`, `fit`). No concrete Claude model string appears
      in the pack.
- [ ] `docs-eng-process/tier-map.yaml` exists with a `claude-code` column
      reproducing today's assignments (11 scribe/coordination→haiku,
      13 authoring→sonnet, 11 quality-gate/reasoning→inherit).
- [ ] `sync-templates-to-claude.sh` reads the neutral pack and regenerates
      `.claude/skills/`; the generated files are **parity-equal** to the current
      `.claude/skills/` (parity target settled per Open Question 1 — byte or
      semantic).
- [ ] `python3 scripts/check-model-tiers.py --check` passes; `model-tiers.md`
      still renders the correct per-skill tiers.
- [ ] `python3 scripts/check-claude-sync.sh` (or equivalent parity check) is green.
- [ ] `.claude-templates/skills/` is removed or reduced to a generated/redirect
      stub so there is exactly one source of truth (the neutral pack).

---

## Success Measure

We expect the number of **source-of-truth locations for a procedure body** to drop
from 2 (`.claude-templates/skills/` + live `.claude/skills/`) to **1** (the neutral
pack; `.claude/` fully generated), verified by: editing one procedure's body in the
pack, running the adapter, and observing the change appear in `.claude/` with **no**
hand-edit to any `.claude-templates/` or `.claude/` file. Read-back: at T-072 start
(the driver must read the same pack with zero Claude-specific parsing).

n/a for a runtime product metric — this is internal framework refactoring; the
falsifiable claim is the single-source-of-truth check above.

---

## Testing Strategy

- **Parity test**: snapshot current `.claude/skills/` → run the new adapter over
  the neutral pack → diff. Zero semantic diff (frontmatter `model:` values +
  bodies) is the gate. Hermetic (tmp dir, no network).
- **Tier-map resolution test**: every `tier:` in the pack resolves to a value in
  the `claude-code` column; unknown tier name → hard error (no silent default).
- **check-model-tiers**: `--check` green against generated output.
- **Round-trip test**: edit a body in the pack → adapter → change reflected in
  `.claude/`; edit only in `.claude/` → parity check flags drift.

---

## Dependencies

- None (first deliverable of the harness-optional program).

---

## Key Files

| File | Change |
|------|--------|
| `docs-eng-process/procedures/openup-*.md` | **New** — neutral procedure pack (35 files) |
| `docs-eng-process/tier-map.yaml` | **New** — runtime tier→model map, `claude-code` + `driver` columns |
| `scripts/sync-templates-to-claude.sh` | Re-point skills loop at the neutral pack; call the render helper |
| `scripts/render-claude-adapter.py` | **New** — neutral→Claude frontmatter translation |
| `scripts/check-model-tiers.py` | Read tiers from `tier:` in the pack; validate against generated `model:` |
| `docs-eng-process/.claude-templates/skills/` | Removed / reduced to a stub (single source of truth) |
| `docs-eng-process/doc-frontmatter.md` (or a new `procedure-frontmatter.md`) | Document the neutral schema |

---

## Out of Scope

- Cursor / Codex adapters (deferred — owner decision 4).
- Moving rubrics / hooks / agents / teammates / teams out of `.claude-templates/`
  (they are not the procedure pack; may follow later).
- The reference driver (T-072) and service (T-073).
- Team / fan-out procedure portability beyond marking their `capabilities.optional`.

---

## Open Questions

1. **Parity target**: byte-identical generated `.claude/` (freeze frontmatter key
   order + generated `model:`) vs. semantic parity (same keys/values, order may
   shift). *Assumed: semantic parity — vetoable at review*; byte-parity is a
   stronger, more brittle bar and Claude Code does not depend on key order.
2. **Where `check-model-tiers.py` reads tiers once `model:` is a name in the pack
   but a concrete value in generated `.claude/`.** *Assumed: read `tier:` from the
   pack as source of truth, validate the generated `model:` matches the map's
   `claude-code` column — vetoable.*
3. Keep `capabilities:` out of generated Claude frontmatter (Claude Code ignores
   unknown keys, but cleaner to drop) — *Assumed: drop on emit.*

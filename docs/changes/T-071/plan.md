---
id: T-071
title: Neutral procedure pack + runtime tier map + re-pointed Claude Code adapter
status: ready   # proposed → ready → in-progress → done → verified
priority: high   # critical | high | medium | low
estimate: 2–3 sessions   # rough size
plan: docs/iteration-plans/t-071-neutral-procedure-pack.md   # originating iteration plan
depends-on: []
blocks: [T-072]
touches:
  - docs-eng-process/procedures/
  - docs-eng-process/tier-map.yaml
  - docs-eng-process/procedure-frontmatter.md
  - scripts/sync-templates-to-claude.sh
  - scripts/render-claude-adapter.py
  - scripts/check-model-tiers.py
  - docs-eng-process/.claude-templates/skills/
last-synced: ""
---

# T-071 — Neutral procedure pack + runtime tier map + re-pointed Claude Code adapter

## Story

> **As a** framework maintainer of harness-optional OpenUP
> **I want** every procedure body to live in one harness-neutral pack with tiers declared as runtime-resolved names, and Claude Code's `.claude/` reproduced from it by a translating adapter
> **So that** there is a single source of truth a non-Claude driver (T-072) can read directly, while Claude Code stays first-class and unchanged.

INVEST check:
✅ Independent (first deliverable, no upstream) · ✅ Negotiable (parity target open) · ✅ Valuable (unblocks the whole program) · ✅ Estimable · ✅ Small enough for 2–3 sessions · ✅ Testable (parity diff is the gate)

## Analysis Context

State the *why* the spec needs but the code can't show:
- **Domain.** The procedure-generation pipeline: `docs-eng-process/.claude-templates/skills/openup-<name>/SKILL.md` (canonical source today) → `scripts/sync-templates-to-claude.sh` (verbatim copy) → `.claude/skills/` (live Claude Code surface). Two things Claude-flavor the source: the `.claude-templates/` location and the concrete `model:` frontmatter value.
- **Scope boundaries.** ONLY the **skills/procedures** move to the neutral pack. Rubrics, hooks, config, agents, teammates, teams, and CLAUDE.md stay sourced from `.claude-templates/` (they are markdown/Python, not the procedure pack — out of scope, owner decision 4). No Cursor/Codex adapter. No driver (T-072) or service (T-073).
- **Definition of done.** All 35 procedures exist under `docs-eng-process/procedures/openup-<name>.md` with the neutral schema (no Claude model string in the pack); `tier-map.yaml` resolves tier name → model per target; `sync-templates-to-claude.sh` regenerates `.claude/skills/` at **parity**; `check-model-tiers.py --check` and the sync/parity check are green; `.claude-templates/skills/` is removed or reduced to a stub so exactly one source of truth remains.

> **Assumption:** Parity target is **semantic** (same frontmatter keys/values + identical bodies; key *order* may shift), not byte-identical. Claude Code does not depend on frontmatter key order; byte-parity is a more brittle bar. *(Vetoable at review — iteration plan Open Q1.)*
> **Assumption:** `check-model-tiers.py` reads tiers from the neutral `tier:` field as source of truth and validates the generated `.claude/` `model:` against the `tier-map.yaml` `claude-code` column. *(Vetoable at review — iteration plan Open Q2.)*
> **Assumption:** `capabilities:` is dropped on emit into generated Claude frontmatter (Claude Code ignores unknown keys, but cleaner to omit). *(Vetoable at review — iteration plan Open Q3.)*
> **Assumption:** The neutral tier vocabulary is the five existing editorial tiers named `scribe`, `coordination`, `authoring`, `quality-gate`, `reasoning` (from `docs-eng-process/model-tiers.md`). *(Vetoable at review.)*

## Requirements

1. A harness-neutral procedure pack exists at `docs-eng-process/procedures/openup-<name>.md` for all 35 procedures, each carrying the neutral schema (`tier:`, `capabilities:`, `name`, `description`, `arguments`, `fit`) and **no concrete Claude model string**.
   - **Given** the 35 template skills under `.claude-templates/skills/` **When** the pack is authored **Then** `ls docs-eng-process/procedures/openup-*.md | wc -l` equals the count of source skills, and `grep -rlE '^\s*model:\s*(inherit|haiku|sonnet)' docs-eng-process/procedures/` returns nothing.
2. `docs-eng-process/tier-map.yaml` exists with a `claude-code` column reproducing today's assignments and a `driver` column for T-072.
   - **Given** the tier map **When** each tier name in the pack is resolved through the `claude-code` column **Then** the resulting `model:` values reproduce today's distribution (11 scribe/coordination→haiku, 13 authoring→sonnet, 11 quality-gate/reasoning→inherit) and every `tier:` used in the pack has a row (unknown tier → hard error, no silent default).
3. `sync-templates-to-claude.sh` reads the neutral pack and regenerates `.claude/skills/` via a Python render helper, producing files that are **parity-equal** (semantic) to the pre-change `.claude/skills/`.
   - **Given** a snapshot of the current `.claude/skills/` **When** the re-pointed adapter runs over the neutral pack **Then** each generated `SKILL.md` has the same body and the same frontmatter key/value set (including the concrete `model:` restored via the map) as the snapshot — zero semantic diff.
4. `python3 scripts/check-model-tiers.py --check` passes and `model-tiers.md` still renders the correct per-skill tiers after the source of tiers moves to the pack.
   - **Given** the neutral pack + generated `.claude/` **When** `check-model-tiers.py --check` runs **Then** it exits 0 and the per-skill tier table matches the pack's `tier:` values resolved through the map.
5. Exactly one source of truth for a procedure body remains: `.claude-templates/skills/` is removed or reduced to a generated/redirect stub.
   - **Given** the completed change **When** a procedure body is edited **only** in the neutral pack and the adapter is re-run **Then** the change appears in `.claude/skills/` with no hand-edit to any `.claude-templates/` or `.claude/` file, and no second editable copy of the body exists.

## Behavior Delta

This task changes **internal framework tooling** (the procedure-generation pipeline), not Ring-1 product behavior. No `docs/product/` use-case is affected — Claude Code's runtime experience is held **invariant** by the parity gate.

**Added:**
- Neutral procedure pack (`docs-eng-process/procedures/`) as the canonical procedure source.
- `tier-map.yaml` runtime tier→model resolution (`claude-code` + `driver` columns).
- `render-claude-adapter.py` neutral→Claude frontmatter translation.
- `procedure-frontmatter.md` documenting the neutral schema.

**Modified:**
- `scripts/sync-templates-to-claude.sh` — skills loop now reads the neutral pack and translates on emit instead of copying `.claude-templates/skills/` verbatim. (Internal tooling; not a Ring-1 artifact.)
- `scripts/check-model-tiers.py` — reads tiers from the pack's `tier:`; validates generated `model:`. (Internal tooling.)

**Removed:**
- `.claude-templates/skills/` as an editable source of truth — removed or reduced to a stub. (Internal tooling; no Ring-1 artifact.)

## Entities

- **Neutral procedure pack** (new) — `docs-eng-process/procedures/openup-<name>.md`
- **Tier map** (new) — `docs-eng-process/tier-map.yaml`
- **Render adapter** (new) — `scripts/render-claude-adapter.py`
- **Sync adapter** (modified) — `scripts/sync-templates-to-claude.sh`
- **Tier checker** (modified) — `scripts/check-model-tiers.py`
- **Template skills** (removed/stubbed) — `docs-eng-process/.claude-templates/skills/`
- **Generated Claude surface** (read-only / regenerated) — `.claude/skills/`

## Approach

Extract each `.claude-templates/skills/openup-<name>/SKILL.md` into a flat neutral file `docs-eng-process/procedures/openup-<name>.md`, rewriting only the frontmatter: `model: <value>` → `tier: <name>` (via the inverse of the current model assignment) and adding a `capabilities:` required/optional split; bodies copy through byte-for-byte. Author `tier-map.yaml` as the single home for concrete model choices, keyed by target. Turn `sync-templates-to-claude.sh` into a translating adapter that calls `render-claude-adapter.py` to convert neutral → Claude frontmatter (restoring `model:` from the `claude-code` column, dropping `capabilities:`) while emitting bodies unchanged. Parity is proven by snapshot-diffing generated `.claude/skills/` against the pre-change tree. Only after parity is green is `.claude-templates/skills/` removed/stubbed.

## Structure

**Add:**
- `docs-eng-process/procedures/openup-<name>.md` (35 files)
- `docs-eng-process/tier-map.yaml`
- `scripts/render-claude-adapter.py`
- `docs-eng-process/procedure-frontmatter.md`

**Modify:**
- `scripts/sync-templates-to-claude.sh` — re-point skills loop at the pack; call render helper
- `scripts/check-model-tiers.py` — source tiers from the pack's `tier:`; validate generated `model:`

**Do not touch:**
- `.claude-templates/{rubrics,scripts/hooks,config,agents,teammates,teams}/`, `CLAUDE.md` — not the procedure pack; stay verbatim-synced (owner decision 4, out of scope)
- `.claude/skills/` by hand — it is *generated*; only the adapter writes it
- The driver (T-072) / service (T-073) — later layers

## Operations

- [ ] Snapshot the current `.claude/skills/` tree (copy to a temp dir) as the parity baseline before any change.
- [ ] Author `docs-eng-process/tier-map.yaml` with `claude-code` (reproducing today's haiku/sonnet/inherit assignments) and `driver` columns, plus `docs-eng-process/procedure-frontmatter.md` documenting the neutral schema.
- [ ] Extract all 35 skills into `docs-eng-process/procedures/openup-<name>.md`, rewriting `model:` → `tier:` and adding `capabilities:`; copy bodies verbatim.
- [ ] Write `scripts/render-claude-adapter.py` (neutral→Claude frontmatter translation) and re-point `scripts/sync-templates-to-claude.sh`'s skills loop at the pack via the helper.
- [ ] Update `scripts/check-model-tiers.py` to read tiers from the pack's `tier:` and validate the generated `.claude/` `model:` against the map's `claude-code` column.
- [ ] (tester) Run the parity diff (baseline snapshot vs regenerated `.claude/skills/`), `check-model-tiers.py --check`, and the round-trip edit test; confirm zero semantic diff.
- [ ] Remove or stub `.claude-templates/skills/` so exactly one source of truth remains; re-run the full sync + checks green.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.)
- `docs-eng-process/model-tiers.md` — the five editorial tiers and current model assignments
- `docs-eng-process/doc-frontmatter.md` — existing frontmatter contract (neutral schema documented separately in `procedure-frontmatter.md`)

## Safeguards

- **Parity is the hard gate.** No semantic diff between the pre-change `.claude/skills/` snapshot and the regenerated tree. Claude Code behavior must not change.
- **No Claude model strings in the pack.** `grep` for `inherit|haiku|sonnet` under `docs-eng-process/procedures/` must be empty; model choices live only in `tier-map.yaml`.
- **Unknown tier → hard error.** The adapter/checker must fail loudly on a `tier:` with no map row — never silently default.
- **Reversibility.** `.claude-templates/skills/` removal is the *last* step, only after parity is green; until then both trees coexist so a revert is `git checkout`.
- **Token / size budget.** Extraction is mechanical; keep the render helper small and single-purpose (frontmatter YAML surgery only, not sed).
- **No-go zones.** Do not move rubrics/hooks/agents/teammates/teams/CLAUDE.md; do not hand-edit generated `.claude/skills/`.

## Verification

- Parity: `diff -r <baseline-snapshot> .claude/skills/` (semantic) is empty after regeneration.
- `python3 scripts/check-model-tiers.py --check` exits 0.
- The project sync/parity check (`scripts/check-claude-sync.sh` or equivalent) is green.
- Round-trip: edit one body in the pack → run adapter → change appears in `.claude/`; edit only `.claude/` → parity check flags drift.
- `grep -rlE '^\s*model:\s*(inherit|haiku|sonnet)' docs-eng-process/procedures/` returns nothing.
- Grade the final spec against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

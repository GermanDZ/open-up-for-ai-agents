# T-071 — In-flight design decisions

## DD1 — Tier assignment (model → tier name)

`model:` alone can't recover the tier name (haiku ⇒ {scribe, coordination};
inherit ⇒ {quality-gate, reasoning}); `sonnet ⇒ authoring` is the only 1:1. The
per-skill tier is editorial prose in `model-tiers.md`, not machine-recorded, so
tiers were assigned from the tier definitions. Parity is preserved for any
assignment consistent with the model (all haiku-tiers → haiku, etc.), which was
verified mechanically (see DD2).

| Tier | Model (claude-code) | Skills |
|---|---|---|
| authoring | sonnet (13) | all `create-*`, detail-use-case, plan-feature, retrospective, shared-vision |
| scribe | haiku (3) | create-handoff, log-run, request-input |
| coordination | haiku (8) | construction, deploy-team, doctor, elaboration, inception, readiness, start-iteration, transition |
| quality-gate | inherit (2) | assess-completeness, phase-review |
| reasoning | inherit (9) | complete-task, explore, fan-out, init, next, orchestrate, quick-task, sync-spec, tdd-workflow |

`capabilities`: all procedures get `required: [read_write_files, exec]`; the four
team/subagent procedures (deploy-team, fan-out, orchestrate, start-iteration) add
`optional: [subagents]` (they degrade to sequential without it).

## DD2 — Byte-parity, not just semantic (exceeds the spec assumption)

The spec assumed *semantic* parity (Open Q1). Achieved **byte-identical**: the
neutral file is the original SKILL.md with only the `model:` line swapped for
`tier:` + a one-line `capabilities:` key; `render-claude-adapter.py` reverses
exactly (tier→model via the map, drop capabilities), reproducing the original
verbatim. Verified: rendering all 35 procedures and diffing against a pre-change
`.claude/skills/` snapshot → **0/35 mismatches**. This is a stronger gate than
required and needs no key-order freezing.

## DD3 — `.claude/` is gitignored; the tracked source is `.claude-templates/`

Confirmed `git check-ignore`: `.claude/` is a **local generated surface**, not
tracked. The git-tracked skill source is `docs-eng-process/.claude-templates/skills/`,
shipped to other projects by `sync-from-framework.sh`. So "single source of truth"
in git terms = removing `.claude-templates/skills/` in favor of the pack. That
removal is **not** a one-liner — four consumers read `.claude-templates/skills/`:

1. `check-model-tiers.py` — reads `model:` per skill (in this lane's surface; re-pointed at the pack here).
2. `check-claude-sync.sh` — pre-commit gate; pairs `.claude/skills/*` ↔ `.claude-templates/skills/*`.
3. `check-skills-guide.py` — pre-commit gate; regenerates `skills-guide.md` from `.claude-templates/skills/`.
4. `sync-from-framework.sh` — ships `.claude-templates/skills/` to downstream projects.

## DD4 — Split into two increments (this lane = increment 1)

**Increment 1 (this commit) — establish the pack as source, all gates green,
`.claude-templates/skills/` retained:**
- New: `docs-eng-process/procedures/` (35), `tier-map.yaml`, `procedure-frontmatter.md`, `scripts/render-claude-adapter.py`.
- `sync-templates-to-claude.sh` re-pointed: local `.claude/skills/` is generated from the pack via the adapter.
- `check-model-tiers.py` re-pointed: tiers read from the pack's `tier:`, resolved through the `claude-code` column.
- `.claude-templates/skills/` kept (redundant, still byte-equal to the generated `.claude/skills/`), so `check-claude-sync.sh` and `check-skills-guide.py` stay green untouched.

**Increment 2 (follow-up, handed off) — reach single tracked source + a
distribution decision that is owner-facing:**
- Rewire `check-claude-sync.sh` and `check-skills-guide.py` off `.claude-templates/skills/` (compare/read the pack via the adapter).
- **Design decision for the owner:** how does downstream distribution work without
  `.claude-templates/skills/`? Options: (A) `sync-templates`/a generator also emits
  `.claude-templates/skills/` as a *generated* mirror (single editable source = pack;
  downstream + gates unchanged) — lowest disruption; (B) point `sync-from-framework.sh`
  at the pack and render on the fly, remove `.claude-templates/skills/` entirely;
  (C) ship the pack itself downstream (aligns with T-072's harness-neutral premise).
  Recommend surfacing to the product-manager/owner — it shapes what "harness-neutral
  distribution" means before T-072.
- Then remove/stub `.claude-templates/skills/` and update Requirement 5's single-source check.

Rationale: increment 1 is self-contained, reviewable, and green; increment 2's
consumer set + distribution question is a distinct decision that shouldn't be
resolved inline by execution (value/shape call, per the OpenUP execution-is-mechanical rule).

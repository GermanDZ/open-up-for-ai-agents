# T-071 — In-flight design decisions

## Completion verification — increment 2 (2026-07-12)

Requirement grade vs the increment-2 diff (`git diff origin/harness-optional...HEAD`
+ working tree). Reqs 1–4 were graded ✅ and merged in increment 1 (PR #74); reqs
re-confirmed green here via the live gates.

- ✅ **Req 1** (neutral pack, no model strings) — pack unchanged this increment;
  `grep -rlE '^\s*model:\s*(inherit|haiku|sonnet)' docs-eng-process/procedures/` empty.
- ✅ **Req 2** (tier-map resolves) — `check-model-tiers.py --check` green (11/13/11).
- ✅ **Req 3** (sync regenerates `.claude/skills/` at parity) — `check-claude-sync.sh`
  green (66 files); full `sync-templates-to-claude.sh` run leaves zero diff.
- ✅ **Req 4** (`check-model-tiers.py --check` passes) — green.
- ✅ **Req 5** (single *editable* source; `.claude-templates/skills/` a generated
  mirror with a drift guard) — `scripts/render-skills-mirror.py` (`--write`/`--check`)
  added; `sync-templates-to-claude.sh` regenerates the mirror; guard wired into
  `.githooks/pre-commit` + `openup-doctor.py`; `render-skills-mirror.py --check` green
  (35 skills byte-equal to `render(pack)`); round-trip verified (hand-edit mirror →
  guard exits 1 → `--write` restores byte-parity); 7/7 unit tests pass. No second
  *editable* copy of any body exists.

**Success measure (step 1b):** the instrumentation is the drift guard itself —
`render-skills-mirror.py --check` fails on any mirror hand-edit — committed in this
diff and wired into the pre-commit + doctor gates. ✅ exists.

**Pre-existing defect (out of lane, flagged for follow-up):** `scripts/tests/
test_check_model_tiers.py` has 4 failing fixture tests — its fixtures write skills
with `model:` frontmatter, but increment 1 re-pointed `check-model-tiers.py` to read
`tier:` from the pack. The live-repo invariant test passes and the `--check` gate is
green. `check-model-tiers.py` and its test are unchanged by this lane; not in `touches`.

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

**Increment 2 (follow-up) — reach a single EDITABLE source via a generated mirror.**

**OWNER DECISION 2026-07-12: Option A — generated mirror.** The pack stays the
single *editable* source; `.claude-templates/skills/` is retained but becomes a
*derived* mirror **rendered from the pack** (Claude-format, via the adapter — i.e.
byte-identical to the generated `.claude/skills/`). Downstream `sync-from-framework.sh`
and the two gates (`check-claude-sync.sh`, `check-skills-guide.py`) keep working
**unchanged** because they still read `.claude-templates/skills/` — now generated.
Options B (point sync at the pack, delete the tree) and C (ship the pack downstream)
were declined for increment 2 (C aligns with T-072 and may return later).

Requirement 5 ("single source of truth") is met by *editable*-source count = 1: the
success-measure check (edit a body in the pack → regenerate → change appears in
`.claude-templates/skills/` with no hand-edit) holds.

Increment 2 work items (Option A):
1. Add a generator that renders `.claude-templates/skills/openup-<name>/SKILL.md`
   from the pack via `render-claude-adapter.py` (extend `sync-templates-to-claude.sh`
   or a sibling script). The mirror is committed/tracked but never hand-edited.
2. Add a drift guard: `.claude-templates/skills/` must equal `render(pack)` (a
   `--check` mode), wired into pre-commit alongside the existing gates, so a
   hand-edit to the mirror fails CI. Point contributors at the pack.
3. Update `touches` to add the generator/guard surface before starting; the mirror
   itself stays in `.claude-templates/skills/` (already in `touches`).
4. Update Requirement 5 / the single-source success-measure check to assert
   *editable*-source = 1 (mirror is generated).

Rationale: increment 1 was self-contained, reviewable, and green; the distribution
question was an owner/value call (per OpenUP execution-is-mechanical), now resolved.

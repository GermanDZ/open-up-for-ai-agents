# Bootstrap-overhead fixes (T-116 → T-114 → T-115)

**Phase**: construction
**Status**: planned
**Goal**: Close three evidenced, independently-shippable overhead gaps in the Claude-Code-driven fresh-project bootstrap path, found by a live dry run of `/openup-cycle` routing into `/openup-next` on a fresh project.
**Priority**: medium

---

## Context

Source: [`docs/explorations/2026-07-14-fresh-bootstrap-tool-call-overhead.md`](../explorations/2026-07-14-fresh-bootstrap-tool-call-overhead.md).
A live session bootstrapping a fresh project through `/openup-next` → `/openup-init`
→ `/openup-start-iteration` → `/openup-create-vision` took 105 tool calls (88
Bash), of which the exploration isolated three concrete, fixable causes — not
the legitimate judgment-work ceremony (rubric reads, self-critique, vision
authoring), which stays untouched.

Value order (product-manager challenge pass in the exploration): cheapest and
most mechanically certain first.

1. **T-116 — hook-sweep parity with `cycle.py`.** `.claude/scripts/hooks/auto-log-commit.py`
   can only append its log line *after* a commit lands (`PostToolUse` cannot
   run before `git commit` returns), leaving the tree dirty and forcing a
   human/agent-noticed follow-up commit — observed 6 times in one lane. The
   fix pattern already exists and works: `scripts/openup_agent/cycle.py:1060-1084`
   (`_sweep_run_logs`) sweeps the whole `docs/agent-logs/` delta into one
   `[openup-skip]` commit on every exit path, but only the headless driver
   gets it — the Claude-Code-driven skills (`/openup-next`, `/openup-complete-task`,
   `/openup-cycle`) never picked it up. This is a parity gap, not a new
   mechanism to invent.

2. **T-114 — `/openup-init` template completeness.** `docs-eng-process/procedures/openup-init.md`
   copies a template for `docs/project-config.yaml` (line 130-131) but
   authors `docs/project-status.md` and `docs/roadmap.md` freehand (no
   template exists for either), and never references the existing, ready
   `docs-eng-process/templates/input-request.md` for the stakeholder-brief
   step (only `mkdir -p docs/input-requests`, line 87).

3. **T-115 — queryable Development Case archetype default.** `PROCESS_ARCHETYPE_DEFAULTS`
   (`scripts/check-docs.py:170-204`) is the only source of truth for
   quick/mvp/product defaults, but it's only consulted when an explicit
   `process:`/`archetype:` block already exists — there is no code path or
   CLI an agent can query for "what applies when `docs/project-config.yaml`
   is absent," forcing prose-hunting (4 chained greps observed live).
   Compounded by a naming collision with the unrelated `quick`/`standard`/`full`
   **ceremony track** concept (`docs-eng-process/tracks.md`), which shares the
   token "quick" with a different axis entirely.

Each item is scoped, specced, and delivered as its own task — bundling them
was explicitly rejected in the exploration's product-manager pass (disjoint
surfaces, different risk levels; a gate failure in one must not block the
other two's value).

---

## T-116: hook-sweep parity — sweep hook-appended run-log shards into the same completion, not a manual follow-up commit

**Priority**: medium
**Depends on**: —

**Problem**: after `auto-log-commit.py` appends its log line post-commit, the
Claude-Code-driven skills (`/openup-next`, `/openup-complete-task`, and the new
`/openup-cycle`) have no instruction to fold that shard into their own next
commit — an agent has to notice the dirty `docs/agent-logs/` tree itself and
improvise a second commit, repeatedly.

**Approach**: port the `_sweep_run_logs` pattern (`cycle.py:1060-1084`) into
prose the Claude-Code skills already gate through — the natural seam is
`/openup-complete-task`'s existing commit steps (it already does the "final
commit" ceremony) and `/openup-cycle`'s box-loop tick/gate step (it already
gates+commits per box). Add an explicit instruction: immediately before any
commit these skills make, `git add -- docs/agent-logs/` and fold any
hook-appended shard delta into that same commit instead of committing,
noticing dirt, and committing again. No new script needed — this is a
procedure-pack wording addition (mirrors T-108's `_sweep_run_logs` design,
restated for the Claude Code substrate the same way `/openup-cycle`'s box
loop restates `cycle.py`'s classification logic).

**Acceptance criteria**:
- [ ] `docs-eng-process/procedures/openup-complete-task.md` and
      `docs-eng-process/procedures/openup-cycle.md` each fold
      `docs/agent-logs/` deltas into their existing commit steps instead of
      leaving them for a separate follow-up commit.
- [ ] `docs-eng-process/procedures/openup-next.md` — **not edited** unless the
      fold-in point genuinely lives there rather than in the skills it
      delegates to (`/openup-start-iteration`/`/openup-complete-task`); prefer
      editing the skill that actually issues the commit.
- [ ] Manual dry run (or a re-read of a prior transcript) confirms no
      "check for further hook-triggered changes" → second-commit round trip
      is needed after this change.

---

## T-114: `/openup-init` template completeness

**Priority**: medium
**Depends on**: —

**Problem**: `docs/project-status.md` and `docs/roadmap.md` are authored
freehand by `/openup-init` (no template exists); the stakeholder-brief step
never references the existing `docs-eng-process/templates/input-request.md`.

**Approach**: (1) add two small new templates,
`docs-eng-process/templates/project-status.md` and
`docs-eng-process/templates/roadmap.md`, matching the shape `/openup-init`
already freehands (so this is a "lift the existing inline markdown into a
template file" change, not a redesign). (2) Update
`docs-eng-process/procedures/openup-init.md` to copy+fill those templates the
same way it already does for `project-config.example.yaml`, and to copy
`docs-eng-process/templates/input-request.md` for the stakeholder-brief file
instead of only `mkdir -p`ing the directory.

**Acceptance criteria**:
- [ ] `docs-eng-process/templates/project-status.md` and `.../roadmap.md`
      exist, byte-equivalent in structure to what `/openup-init` currently
      freehands.
- [ ] `docs-eng-process/procedures/openup-init.md` copies all three templates
      (project-config, project-status, roadmap) plus `input-request.md` for
      the brief, consistent with its existing project-config.example.yaml
      copy step.
- [ ] A fresh bootstrap (manual dry run or transcript re-check) shows no
      freehand heredoc authoring of these files and no live template-hunt for
      the input-request convention.

---

## T-115: queryable Development Case archetype default + track/archetype disambiguation

**Priority**: medium
**Depends on**: —

**Problem**: `PROCESS_ARCHETYPE_DEFAULTS` (`scripts/check-docs.py:170-204`) is
unreachable when `docs/project-config.yaml` is absent — no CLI or script path
answers "what applies by default," and the *ceremony track* concept
(`docs-eng-process/tracks.md`) shares the token "quick" with the *Development
Case archetype* concept, causing agents to conflate the two.

**Approach**: (1) add a read-only accessor — the natural home is
`check-docs.py` (where the dict already lives) via a flag like
`--show-archetype-defaults`, or `openup-doctor.py` (which already aggregates
read-only project health info) — decide at delivery time which fits the
existing CLI surface better, per the exploration's open question. (2) add one
clarifying sentence to `docs-eng-process/project-config.md` and
`docs-eng-process/tracks.md` the first time each concept is introduced,
naming the other explicitly ("this is a different axis from the ceremony
track — see tracks.md") so an agent reading either doesn't have to
rediscover the distinction by grepping.

**Acceptance criteria**:
- [ ] A single command prints the resolved archetype defaults (name TBD at
      delivery — this doc intentionally leaves the exact flag/subcommand open
      per the exploration's open question).
- [ ] `project-config.md` and `tracks.md` each name the other concept
      explicitly where "quick" is first introduced.
- [ ] `docs-eng-process/procedures/openup-init.md` (and any other procedure
      that currently free-text-asserts "framework defaults apply") points at
      the new accessor instead of leaving the claim unexplained.

---

## Testing Strategy

- Each task is doc/procedure-only (T-114, T-115's disambiguation half) or a
  small CLI addition (T-115's accessor) plus procedure wording (T-116) — no
  behavior-changing script logic beyond the new read-only accessor.
- `render-skills-mirror.py --check`, `check-skills-guide.py --check`,
  `check-model-tiers.py --check`, `check-docs.py` after each task.
- Where a script changes (T-115's accessor), add a hermetic unit test.

## Dependencies

None between the three — they touch disjoint files and can be delivered in
any order, though value order (cost/certainty) is T-116 → T-114 → T-115.

## Out of Scope

- Making the Claude Code skills literally call into `scripts/openup_agent/cycle.py`
  helpers as a shared library (the exploration's first open question) — a
  bigger architectural change than any of these three tasks, left for a
  future decision if the restated-logic pattern (`/openup-cycle` mirroring
  `classify_box`, this program mirroring `_sweep_run_logs`) proves to drift.
- Any change to `/openup-cycle`'s or `/openup-next`'s already-shipped,
  dry-run-validated `resolve()`-branching logic.

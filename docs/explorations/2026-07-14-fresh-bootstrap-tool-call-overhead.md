# Exploration: fresh-project bootstrap tool-call overhead in the Claude Code path

**Started:** 2026-07-14
**Question:** A live `/openup-cycle` dry run correctly routed away on a fresh
project (`resolve() == plan-iteration`), then the resulting `/openup-next` →
`/openup-init` → `/openup-start-iteration` → `/openup-create-vision` chain took
105 tool calls (88 Bash) to bootstrap one Inception iteration. Is that overhead
genuinely fixable, and if so, what's the smallest correct fix?

## Context

Follow-on from T-112 (`/openup-cycle` skill) and T-113 (its sentinel-emission
fix). Both shipped and were validated live on `/tmp/openup-samples/my-product-2`
— `/openup-cycle`'s own routing logic works correctly (confirmed twice: once
mid-development, once after the T-113 fix landed, in a fresh session that
emitted the exact sentinel and stopped cleanly). This exploration is about the
**downstream** `/openup-next` fresh-bootstrap path it correctly hands off to,
which is explicitly outside what T-112/T-113 are scoped to touch (`/openup-next`
was preserved byte-unchanged by design).

Evidence source: live session transcript
`~/.claude/projects/-private-tmp-openup-samples-my-product-2/35a5628a-f9da-417f-a91c-e8dc3edeb074.jsonl`
and the resulting project tree at `/tmp/openup-samples/my-product-2`.

## Notes

Three concrete, evidenced findings (research done via a dispatched Explore
agent, citations below):

### 1. Development Case archetype has no queryable default

The live session spent 4 chained grep/search calls (transcript idx ~65–79)
hunting for "what's the default archetype when `docs/project-config.yaml` is
absent." Root cause:

- `docs-eng-process/project-config.md:94,135,170` all assert *"framework
  defaults apply"* without naming them.
- The actual data, `PROCESS_ARCHETYPE_DEFAULTS = {"quick": {...}, "mvp": {...},
  "product": {...}}`, lives in `scripts/check-docs.py:170-204` — but it's only
  consulted by `resolve_process()` (`check-docs.py:330`), which only runs when
  an explicit `process:`/`archetype:` block already exists. **When the file is
  absent, no code path resolves an implicit archetype at all** — "framework
  defaults apply" means "no Development Case tailoring," not one of
  quick/mvp/product. There is no CLI a fresh-bootstrap agent could call to get
  a straight answer.
- Compounding it: `docs-eng-process/tracks.md:3-21` defines a **separate**
  `quick`/`standard`/`full` "ceremony track" concept (a different axis, stored
  in `.openup/state.json.track`) that shares the token "quick" with the
  Development Case archetype's `quick`/`mvp`/`product`. An agent grepping
  "default" without already knowing the two systems are distinct will (and
  did) conflate them.

**Verdict (researcher's): fixable but nontrivial** — the data already exists as
one dict; missing is a queryable accessor and disambiguating language.

### 2. Hook-induced post-commit ping-pong

`.claude/scripts/hooks/auto-log-commit.py` is a `PostToolUse`/Bash hook that
can only inspect a commit **after** it has already landed (its own docstring,
line 13: *"the current HEAD resolves to a SHA"*; line 27: *"PostToolUse cannot
block; this hook only appends"*). It then appends a JSONL line to a run-log
shard, leaving the tree dirty — which the agent must notice (`git status`) and
commit again. This repeated ~6 times through the observed T-002 lane
(transcript idx 348, 359, 377, 387, 411, 419).

The codebase **already has the fix pattern**, just not wired into this path:
`scripts/openup_agent/cycle.py:1060-1084` (`_sweep_run_logs`) runs
deterministically in `run_cycle`'s `finally` block (`cycle.py:1109`) and
commits the whole `docs/agent-logs/` delta as one `[openup-skip]` commit,
every exit path, no ping-pong. But `docs-eng-process/procedures/openup-cycle.md`
and `openup-next.md` are **ported restatements** of the deterministic core, not
wrappers calling into `cycle.py` — so a live Claude-Code-driven session never
gets `_sweep_run_logs`'s benefit. This is a **parity gap between the headless
engine and the Claude Code skills**, not a new problem to invent a fix for.

**Verdict (researcher's): fixable, cheaply** — port the sweep pattern (or an
equivalent single instruction: "before your next commit, `git add -A --
docs/agent-logs/` and fold any hook-appended shard into it") into the
skills that currently improvise a second commit per hook-touched file.

### 3. `/openup-init` mixes templated and freehand authoring

`docs-eng-process/procedures/openup-init.md` does instruct copying a template
for `docs/project-config.yaml` (line 130-131, from
`docs-eng-process/templates/project-config.example.yaml` — confirmed present).
But:
- `docs/project-status.md` and `docs/roadmap.md` are authored **freehand**
  (inline markdown in the skill body, lines 98-126) — no template exists for
  either in `docs-eng-process/templates/` at all.
- The stakeholder-brief/input-request file is never written by `/openup-init`
  at all (only `mkdir -p docs/input-requests`, line 87) — despite
  `docs-eng-process/templates/input-request.md` already existing, ready to
  copy, and simply not referenced.

**Verdict (researcher's): fixable, cheaply** for the input-request gap (point
at the existing template — a one-line doc fix); needs two small new templates
for `project-status.md`/`roadmap.md` to close the rest.

### Product-manager challenge pass

- **Pushback:** not all 105 tool calls are waste. Reading full skill bodies,
  the vision rubric, and the self-critique SOP before authoring a genuinely
  novel Vision document (idx 268, 275, 278) is legitimate judgment-work
  ceremony, not overhead — cutting it would degrade output quality for the
  one artifact in this flow that actually needs human-grade judgment. The
  three findings above account for maybe 15-20 of the 105 calls, not the
  bulk. Framing this as "fix the bootstrap flow" overstates the win; the
  honest framing is "close three specific, evidenced, avoidable gaps."
- **Complement:** the "ceremony track" vs "Development Case archetype" naming
  collision (finding 1) is a documentation-clarity problem independent of the
  archetype-default question — it will keep costing agent (and human) time
  reading `tracks.md`/`project-config.md` even after a default-accessor ships,
  unless the two concepts are explicitly distinguished in prose the first time
  either is introduced.
- **Refine:** the three findings are independently shippable and touch
  disjoint surfaces (a hook/sweep wiring change; two new templates + one doc
  reference fix; a CLI accessor + doc disambiguation). They should not be
  forced into one task — value-order them by cost/evidence-strength: (a) the
  hook-sweep parity gap first (cheapest, proven pattern already exists in
  `cycle.py`, most mechanically certain fix), (b) the `/openup-init` template
  gaps second (cheap, concrete, two small new files), (c) the archetype
  accessor + disambiguation third (needs new CLI surface, more design
  judgment about where the accessor lives).
- Disposition per challenge: **all three accepted** into the options below;
  no challenge rejected — the pushback narrows the framing rather than killing
  the finding, and is folded into the "Where this goes next" scope note.

## Options Considered

- **Option A — fix only the hook-sweep ping-pong.** Port
  `cycle.py`'s `_sweep_run_logs` pattern into the Claude-Code-driven
  completion skills (or document the fold-into-next-commit instruction
  inline). Pro: cheapest, already-proven pattern, closes a real headless/
  Claude-Code parity gap. Con: leaves findings 1 and 3 unaddressed.
- **Option B — fix all three findings as one bundled task.** Pro: one pass
  touches the whole fresh-bootstrap flow. Con: violates the product-manager
  refine above (disjoint surfaces, different judgment/risk levels bundled
  together; a gate failure in one slice blocks the other two's value).
- **Option C — do nothing (irreducible ceremony).** Rejected by the evidence:
  all three researcher verdicts were "fixable" (cheap or nontrivial-but-real),
  not "irreducible."

## Open Questions

- Should the hook-sweep fix live in `/openup-next`/`/openup-complete-task`
  directly (Claude-Code-only), or should the Claude Code skills start
  literally calling into `scripts/openup_agent/cycle.py`'s helpers (e.g.
  `_sweep_run_logs`) as a shared library function instead of restating the
  pattern a second time? The latter is more correct (single source of truth)
  but is a bigger architectural change than this exploration is scoped to
  decide — flag for the delivery task to weigh.
- Where should the archetype-default accessor live — `check-docs.py` (where
  `PROCESS_ARCHETYPE_DEFAULTS` already is), a new flag on
  `openup-process-map.py`, or `openup-doctor.py` (which already aggregates
  read-only project health info)? Needs a delivery-time decision, not an
  exploration-time one.
- Do `docs/project-status.md`/`docs/roadmap.md` templates belong in
  `docs-eng-process/templates/` (alongside `project-config.example.yaml`) or
  should `/openup-init` just inline slightly more structured boilerplate?
  Minor, but affects where the new files land.

## Where this goes next

→ iteration — promote to a roadmap entry ("close the Claude-Code-path
fresh-bootstrap overhead gaps: hook-sweep parity with `cycle.py`, `/openup-init`
template completeness, and a queryable Development Case archetype default"),
scoped at delivery time (via `/openup-plan-feature`) into either one iteration
plan with three ordered work items or three separate quick-tasks, value-ordered
(a) hook-sweep → (b) `/openup-init` templates → (c) archetype accessor, per the
product-manager refine above. None of these touch `/openup-cycle` or
`/openup-next`'s already-shipped, dry-run-validated behavior.

# T-078 — In-flight design decisions

## DD1 — State schema 2 (Operations step 1, delivered)

**What.** `.openup/state.json` `schema` 1→2; added `iteration_id`
(nullable pointer to the iteration-plan instance, e.g. `C3`) and `cycle`
(project lifecycle counter, default 1); documented `phase` as a **derived
cache** stamped from `openup-lifecycle.py status`.

**Migration is in-memory-on-read + persist-in-place.** `read_state()` calls a
pure `migrate_state(state) -> (state, changed)` that additively backfills the two
new fields and bumps `schema`; if changed it best-effort persists the upgrade
(wrapped in `try/except OSError` so a read-only fixture still yields the upgraded
dict in memory). Rationale: every hook calls `openup-state.py get`, so an
in-flight schema-1 lane must not error on the bump, and `migrate_state` must stay
cheap — it does **not** shell out to `openup-lifecycle.py` (that would put a
subprocess in every hook read). `cycle` therefore defaults to `1` on migration
and is authoritatively (re)derived at init / plan-iteration time.

**`begin` needs no change.** `openup-session.py begin` shells `openup-state.py
init` via argv, and `init` now emits schema 2 with defaults (`iteration_id` null,
`cycle` 1) — so the atomic session path upgrades for free. Later slices (the
plan-iteration wiring) will pass `--iteration-id` / `--cycle` explicitly.

**Get/set.** No new subcommands — the generic `set iteration_id C3` / `set cycle
N` and `get iteration_id` already cover R5's "set/get" via the dotted-path
helpers, and both keys are now in-schema so `additionalProperties:false` accepts
them.

**Tests.** `tests/test_state_schema2.py` (7 hermetic): init-schema2-defaults,
init-carries-id+cycle, schema1→2 migrate-in-place (fields preserved),
migrated-schema1-validates, migrate pure+idempotent, migrate preserves explicit
id/cycle, invalid-schema2 (missing keys) still rejected. Full python suite 71
passed (64 + 7), no regression.

## DD2 — resolve paths: assess-iteration + milestone-review (Operations step 2, delivered)

**Precedence.** New order in `resolve_decision`: resume → pick → **assess-iteration**
→ (compute promote entry) → **milestone-review** → plan-iteration → noop.

**assess-iteration** fires when a minted phase-aware iteration is exhausted and
unassessed. "Minted iteration" is detected purely from data with **no new
frontmatter**: an iteration-plan instance (`type: iteration-plan` under
`docs/iteration-plans/` or `docs/phases/`) whose `traces-from` contains at least
one **iteration-prefixed** lane id (`C3-001`, matching `^[A-Z]\d+-\d+$`). Legacy
per-task plans trace to `T-NNN`/requirement ids and never match — so single-lane /
promote flows (and this very repo) never trigger it. "Exhausted" = every committed
lane done (archived change folder, or active plan `status ∈ {done,verified,
completed}`); "assessed" = the plan body carries a `## Assessment` section.

**milestone-review** fires only when the roadmap is **drained** (`_promote_next`
returns nothing), the phase's exit criteria are met (no criterion `unmet`;
`human-judgment` ones are what the review resolves), and no milestone record
exists for the current phase+cycle. Gating on "nothing promotable" — the *same*
check plan-iteration uses — was the key fix: lifecycle's `roadmap-clear`
criterion only sees table rows, so without this gate a manual-`## T-NNN`-section
pending task would be milestone-reviewed instead of planned. The `phase`/`cycle`
come from `openup-lifecycle.py compute_status` (T-075); `resolve` now carries
`cycle` on every decision (additive field).

**Zero behavior change for existing flows** — verified: the live repo still
resolves `resume T-078`, and the full suite is green. Both paths are covered by
`tests/test_board_assess_milestone.py` (14: helper units + both fires + the
work-remains / already-assessed / recorded / pending-work negatives).

**Deferred to later steps (not this one):** consuming these paths in
`openup-next` (step 5), the `/openup-assess-iteration` procedure that writes the
`## Assessment` section (step 3), and `/openup-phase-review` writing the milestone
record on GO (step 4). Step 2 is detection only.

## DD3 — /openup-assess-iteration procedure (Operations step 3, delivered)

New `docs-eng-process/procedures/openup-assess-iteration.md` (tier: authoring).
Six steps: read the iteration-plan contract → grade evaluation criteria from repo
evidence → demo only completed+acceptance-tested items (exclude+name the rest) →
feed discovered work/defects back as pending roadmap items → append the
`## Assessment` section (the marker `resolve` reads; sanctioned progress state,
like a ticked box — no `/openup-create-iteration-plan` re-run unless objectives
changed) → phase-end trigger that **names** `/openup-phase-review` but never
advances the phase. Composes `/openup-retrospective` for the reflection/cadence
half rather than duplicating it.

**No manifest edit.** `process-manifest.txt` lists runtime *scripts*, not
procedures; the pack is glob-discovered by `render-skills-mirror.py` and
`check-skills-guide.py`. Delivery here = author pack → `render-skills-mirror
--write` (36 skills, +1) → `check-model-tiers --write` + `check-skills-guide
--write` (both tables regen) → `sync-templates`. The committed mirror is
`.claude-templates/skills/…`; `.claude/skills/…` is gitignored (regenerated at
session start). All four guards (render/model-tiers/skills-guide/claude-sync)
exit 0.

## DD4 — /openup-phase-review loop-driven milestone pause (Operations step 4, delivered)

Rewrote `openup-phase-review.md` around a **two-cycle async interaction** gated by
a milestone input-request (no new machinery — composes T-074 `/openup-request-input`):
- **First reach** (no request): derive phase/cycle/criteria from
  `openup-lifecycle.py`, prepare go/no-go evidence (criteria + the iteration's
  `## Assessment`), create the milestone request, and stop → loop exits `DONE —
  milestone-review pending human input`.
- **Pending**: stop, no record.
- **Answered**: write `docs/product/milestones/<phase>-<cycle>.md` (frontmatter
  exactly as lifecycle reads it — phase/cycle/milestone/decision/date/decided-by),
  archive the request.

**Key modelling choice: no `related_task`.** A milestone is a phase-level
decision, not a lane, so the request suspends no change folder. It is therefore
NOT a `_resumable_input` (which maps answered requests to lanes) — so it never
hijacks resolve's §0; instead resolve keeps returning `milestone-review` (record
absent) until the record is written, and each cycle re-runs phase-review, which
processes the answer when it arrives. The loop's DONE sentinel is what pauses it.

**Never advances the phase.** Only the record advances it (lifecycle derives
phase from records). GO → next phase; NO-GO → record + re-queue Construction in
`cycle`+1 (phase stays); CONDITIONAL → record + enqueue conditions. Matches the
"humans own the go/no-go" design principle.

## DD5 — openup-next path handling + DONE semantics (Operations step 5, delivered)

Rewired `openup-next.md`:
- **Intro precedence** now 6 steps: resume → pick → assess → milestone-review →
  plan+start → noop.
- **Removed** the T-077 "treat plan-iteration like promote" transition note.
- **Two new branches**: `assess-iteration` → run `/openup-assess-iteration`,
  exit ADVANCED (or DONE if it spawned a milestone pause); `milestone-review` →
  run `/openup-phase-review`, exit DONE (`milestone-review pending human input`)
  when it created/awaits the request, ADVANCED when it recorded an answered
  decision. Both are non-lane paths (skip claim/worktree).
- **plan-iteration** now branches on the Development Case archetype (T-076):
  `mvp`/`product` (budget > 1) → real Plan Iteration (`/openup-start-iteration`
  with **no task_id** → §0b generates lanes); `quick`/single → today's promote
  (the degenerate `lane.task`). The full promote-by-shape guidance is retained
  under the degenerate case.
- **noop** narrowed: it no longer tells the human to run `/openup-phase-review`
  (that is now the automated `milestone-review` path); noop means no delivery + no
  phase gate applies.
- **DONE sentinel** reframed as a **phase-gate** signal: the headline DONE reason
  is `milestone-review pending human input` (the convergence the loop exists to
  reach), alongside the drained-queue / blocked / delivered-but-unmerged reasons.
  ADVANCED now also covers "iteration assessed" and "milestone recorded".

Mirror + skills-guide regenerated; all guards (render/guide/claude-sync) green.

## DD6 — spec verification + final gates (Operations steps 6–7, delivered)

`script-cli-reference.md` updated (board `resolve` path enum + `cycle`). Final
gates all green from the worktree: full python suite **85 passed** (64 baseline +
7 schema-2 + 14 assess/milestone), `check-docs.py` 0, `check-docs.py --coverage`
0, `openup-fence.py check --base harness-optional` 0 (19 files, all in-lane),
`openup-spec-scenarios.py check` 0.

**Requirement grade (against the diff):**
- R1 resolve emits `assess-iteration` + `milestone-review` — ✅ (board tests, both
  fires + negatives).
- R2 `/openup-assess-iteration` Assess Results — ✅ (procedure DD3).
- R3 `/openup-phase-review` pauses via input-request, writes the milestone record,
  never sets phase — ✅ (procedure DD4).
- R4 `openup-next` handles both paths + real plan-iteration delegation — ✅ (DD5).
- R5 schema 2 + schema-1→2 auto-migration — ✅ (state tests DD1).
- R6 DONE sentinel = phase-gate signal — ✅ (DD5).
- R7 hermetic tests for every new/changed path — ✅ (21 new tests, suite green).

**Scope honesty:** the new resolve paths + procedures are *wired and tested*, but
no multi-lane phase-aware iteration has actually *run* in this repo yet (all
program tasks were single-lane). The behavior is proven by fixtures; the first
live multi-lane run is the T-079 / next-live-run concern (the Success Measure's
read-back). Single-lane/promote flows are provably unchanged (live board still
resolves `resume T-078`; full suite green).

**Note (framework flaw surfaced at start).** Committing the spec fired the
auto-log hook → `log_written=true`; with `roadmap_synced=true` both standard-track
gates were true and `sync-status.py` derived **completed** for a just-started
task. Corrected by `set-gate log_written false` + re-sync → in-progress. Not
fixed here (out of lane); logged to memory for the program.

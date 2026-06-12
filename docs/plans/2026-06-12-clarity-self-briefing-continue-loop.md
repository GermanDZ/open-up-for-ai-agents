# Clarity, Self-Briefing, and the Sequential Continue-Loop

**Status**: `planned`
**Created**: 2026-06-12
**Priority**: high
**Goal**: Reduce development waste caused by unclear objectives and misunderstandings, by making specs unambiguous, roles self-briefing from the repo, and the execution loop a mechanical "read the next task and execute."
**Exploration**: [explorations/2026-06-12-openspec-clarity-waste.md](../explorations/2026-06-12-openspec-clarity-waste.md)
**Supersedes**: absorbs the one un-implemented item (#2, `project-config.yaml`) of [2026-05-13-openspec-ideas-for-openup.md](2026-05-13-openspec-ideas-for-openup.md) as T-018.

---

## Context

OpenUP's Process v2 (T-004…T-011, all delivered) mechanized *process adherence*:
model tiering, blocking gates, state files, three-ring docs, the readiness DAG,
graded tracks, worktrees. What it did **not** address is *intent clarity* — the
class of waste where the process runs perfectly but produces the wrong thing
because the objective was never pinned down, or a mid-flight ambiguity was
resolved silently by the agent.

A focused re-reading of OpenSpec against that single goal (the exploration
above) found that items #1/#3/#4/#5 of the 2026-05-13 plan already landed, and
surfaced three operator principles that reshape the remaining work:

1. **Specs must be unambiguous before work starts.** A requirement that two
   readers parse differently is a misunderstanding waiting to happen. OpenUP's
   REASONS spec is strong on *scope* but asserts testability rather than
   demonstrating it, and writes requirements fresh rather than as deltas against
   product truth.
2. **Roles should self-brief from `docs/`.** Status from roadmap/plans/logs;
   *what* from vision/use-cases/specs; *how* from OpenUP guidelines and
   elaboration outputs. A custom per-session briefing is redundant when the spec
   is complete and a silent patch over the spec's gaps when it isn't — so custom
   briefings are a *symptom* of incomplete specs.
3. **Execution is a sequential loop with repo-persisted handover.** No
   conversation-only state. The ideal operating mode is a loop whose body is one
   instruction — "read the next task and execute" — where selection and
   continuation are a *lookup against one simple file*, not reasoning over many
   docs. Parallelism is wanted, but **per-lane** (a feature in one lane, an
   unrelated refactor in another), never as multiple teammates inside one task.

These principles do not discard Process v2; they build on it. The readiness DAG
(T-008), worktrees + lease claims + collision pre-flight (T-009), and graded
tracks (T-010) are exactly the primitives the continue-loop composes — the gap
is a skill that ties them together plus a derived data layer to read from.

---

## Current State

### Specs assert testability, never demonstrate it
`docs-eng-process/templates/task-spec.md` `## Requirements` are "numbered,
testable assertions" — nothing forces a requirement concrete enough that two
readers parse it identically, and requirements are written fresh rather than as
a delta against Ring 1 product truth.

### The clarifying-questions path exists but is never required
`/openup-request-input` lists "ambiguous requirements" as a great fit, yet
neither `create-task-spec` nor `openup-plan-feature` reference it. An agent that
guesses wrong never hits a gate.

### Custom briefings compensate for incomplete specs
`.claude/teammates/project-manager.md` instructs the PM to hand each specialist
scope + context-docs + deliverable + done-when — all of which are (or should be)
derivable from the task spec, coordination frontmatter, ring rules, and rubric.
Teammate cold-start reading lists are uneven across roles (the developer file has
one; others don't).

### Teams are default; the loop is uncomposed
`CLAUDE.openup.md` makes teams "active by default" and `/openup-start-iteration`
deploys one as mandatory step 3. The pieces of a sequential continue-loop all
exist (`/openup-readiness`, tracks, change folders, `/openup-log-run`,
`/openup-create-handoff`, `.openup/state.json`) but nothing composes them into a
single cycle, and there is no materialized queue to read from — selection means
reading prose roadmap + judging.

### No project-level fact/rule injection
The one un-implemented item of the 2026-05-13 plan: project-specific facts
(stack, domain, compliance) have no canonical home and leak into prompts.

---

## Proposed Design

Seven tasks, ordered so each builds on the previous. Letters in parentheses map
to the options in the exploration.

### T-015 (C) — Mandatory ambiguity gate in spec authoring `HIGH / LOW`
Add a numbered step to `create-task-spec` and `openup-plan-feature`: before
drafting, list open questions and classify each as **blocking** (answer changes
scope/requirements) or **non-blocking** (assumption). Blocking → invoke
`/openup-request-input` and stop. Non-blocking → record as `**Assumption:**`
lines in the spec's Analysis Context so the requester can veto at review.
Converts silent guesses into visible, vetoable assumptions.

- **Files**: `.claude/skills/openup-artifacts/create-task-spec/SKILL.md`,
  `.claude/skills/openup-plan-feature/SKILL.md`,
  `docs-eng-process/templates/task-spec.md` (Assumption convention),
  `.claude/rubrics/task-spec-rubric.md` (criterion: open questions classified).
- **Verify**: author a spec from a deliberately ambiguous request; confirm a
  blocking question routes to `/openup-request-input` and non-blocking ones land
  as `**Assumption:**` lines.
- **Depends on**: none.

### T-016 (F) — Self-briefing roles: pointer-only delegation `HIGH / LOW–MED`
(1) Give every `.claude/teammates/*.md` a uniform "On start, read:" block scoped
to the role (status + the one change folder + role-relevant guideline docs).
(2) Collapse the PM Delegation Brief Format to `[ROLE]: T-NNN. Deltas: <only what
the docs don't say — usually nothing>`; make "I'm writing scope into a brief" a
recognized signal to fix the spec (fix-spec-first), not patch it with prose.

- **Files**: all `.claude/teammates/*.md` (+ `*-compact.md`),
  `.claude/CLAUDE.openup.md` (briefing-from-docs principle).
- **Verify**: cold-start a developer-role session given only a task ID; confirm
  it loads the correct ring-scoped docs and needs no extra briefing.
- **Depends on**: T-015 (specs must carry assumptions to brief from).

### T-017 (G) — `/openup-next`: sequential continue-loop + execution board `HIGH / MED` — headline
One skill = one cycle of "read the next task and execute":
1. Refresh `.openup/board.json` (derived; see below) and take the top READY,
   collision-free, unleased item; if none, print why and stop cleanly.
2. Claim it (lease) and work in its worktree; self-brief per T-016; infer the
   role hat from the first unchecked Operations step.
3. Execute under the task's track ceremony.
4. Persist: tick Operations checkboxes, write `design.md` decisions, run log,
   state.json; exit via `/openup-complete-task` or `/openup-create-handoff`
   (the only two legal exits).
5. End the session; the outer loop (`/loop`, cron, or a human) repeats.

**Data layer (the "one simple file"):**
- **`.openup/board.json`** — a derived, machine-readable queue of all active/ready
  lanes, regenerated by a deterministic `.claude/scripts/openup-board.py` from
  change-folder frontmatter + roadmap + leases + checklist state. The model
  **never** authors it ("if a step is deterministic, the harness does it"). Each
  item carries `task, title, track, state, lease, hat, next_action, plan,
  collides_with, depends_ok`.
- **Operations as checkboxes** — change the task-spec `## Operations` convention
  from `1. <step>` to `- [ ] <step>`; the board derives `next_action` from the
  first unchecked box and `hat` from the phase that work belongs to. (OpenSpec
  `tasks.md` pattern grafted onto the REASONS spec — no new artifact.)

**Policy changes shipped in the same task** (or the skill contradicts the guides):
- Teams demote from default to **opt-in for `full`-track** work; the mandatory
  "deploy team as step 3" gate becomes track-conditional.
  > **Pulled forward 2026-06-12** (commit on `main`, quick track): this policy
  > slice landed early on user feedback ("teams active by default didn't work
  > well"). `CLAUDE.openup.md`, `on-task-request.py`, `start-iteration` (team now
  > opt-in; `deploy_team` default `auto`), `complete-task` (standard gates on the
  > team-less set), and `tracks.md` are updated. The `/openup-next` skill itself
  > (T-017) remains to be built on top of this now-correct default.
- New rule in `CLAUDE.openup.md`: *no information needed to continue work may
  live only in a conversation.*
- Parallelism reframed as **per-lane**: T-009's worktrees/leases/collision
  pre-flight are the lane enabler; two `/openup-next` loops naturally pick
  disjoint tasks with no coordination protocol beyond the repo.

- **Files**: `.claude/skills/openup-workflow/next/SKILL.md` (new),
  `.claude/scripts/openup-board.py` (new),
  `docs-eng-process/templates/task-spec.md` (checkbox Operations),
  `.claude/CLAUDE.openup.md` (teams opt-in, no-conversation-only-state, per-lane),
  `.claude/skills/openup-workflow/start-iteration/SKILL.md` (track-conditional team gate).
- **Verify**: from a cold session with two READY non-colliding tasks, run
  `/openup-next` twice in two sessions; confirm each claims a disjoint task,
  ticks boxes on exit, and the next cycle resumes from the board without
  re-reading prose. Confirm a no-op cycle (nothing READY) exits cleanly.
- **Depends on**: T-015, T-016 (and leverages done T-008/T-009/T-010).

### T-018 (D) — `docs/project-config.yaml` context/rules injection `MED / LOW`
The surviving 2026-05-13 item #2. Project-owned `context:` (stack, domain,
compliance) and `rules:` keyed by artifact type, injected as `<project-context>`
/ `<project-rules>` into every `/openup-create-*` prompt; framework rubrics stay
framework-owned, project rules layer on top.

- **Files**: `docs-eng-process/templates/project-config.example.yaml` (new),
  `.claude/skills/openup-init/SKILL.md` (emit starter),
  each `.claude/skills/openup-artifacts/*/SKILL.md` (read + inject),
  `.claude/CLAUDE.openup.md` (precedence: rubric → project rules → safeguards).
- **Verify**: add a fake `rules.use-case: ["Must reference a stakeholder by
  name"]`, run `/openup-create-use-case`, confirm injection + satisfaction;
  remove and confirm revert.
- **Depends on**: none.

### T-019 (A) — Behavior Delta section in the task spec `HIGH / MED`
Add `## Behavior Delta` to the task-spec template: requirements grouped
**Added / Modified / Removed**, each Modified/Removed naming the Ring 1 artifact
+ section it changes (`docs/product/use-cases/UC-3 §main-flow`). Makes
misunderstandings about *existing* behavior visible at review; gives
`/openup-sync-spec` an exact list of Ring-1 artifacts to update. Greenfield
tasks render "n/a — all Added."

- **Files**: `docs-eng-process/templates/task-spec.md`,
  `.claude/skills/openup-artifacts/create-task-spec/SKILL.md`,
  `.claude/rubrics/task-spec-rubric.md`,
  `.claude/skills/openup-workflow/sync-spec/SKILL.md` (consume the delta).
- **Verify**: write a spec that modifies an existing use case; confirm the
  Modified entry names the artifact+section and sync-spec targets exactly it.
- **Depends on**: T-007 (Ring 1 populated). Do before T-020.

### T-020 (B) — Scenario-per-requirement + deterministic validation `HIGH / MED`
Every `## Requirements` entry carries ≥1 `Given / When / Then` scenario; a script
(extend `openup-board.py`/readiness or a `.claude/scripts/` check invoked by
`/openup-assess-completeness`) validates the structure deterministically. Writing
the scenario is where vague requirements break down. Apply on standard + full
tracks; skip quick.

- **Files**: `docs-eng-process/templates/task-spec.md`,
  `.claude/skills/openup-artifacts/create-task-spec/SKILL.md`,
  `.claude/rubrics/task-spec-rubric.md`,
  `.claude/scripts/` (structure check), `assess-completeness` wiring.
- **Verify**: a requirement with no scenario fails the check; adding a valid
  Given/When/Then passes it.
- **Depends on**: T-019.

### T-021 (E) — Implementation-vs-spec verify step in `/openup-complete-task` `MED / LOW`
OpenSpec `/opsx:verify` equivalent: before marking done, grade each requirement
(and its scenarios, if T-020 landed) ✅/❌ against the actual diff — same
per-criterion idiom as the rubrics. Sharpen the task-spec `## Verification`
execution rather than add an artifact.

- **Files**: `.claude/skills/openup-workflow/complete-task/SKILL.md`.
- **Verify**: complete a task whose diff omits one requirement; confirm the step
  flags it ❌ and blocks "done."
- **Depends on**: T-020 (optional — grades scenarios if present).

---

## Dependencies

```
T-015 (C) ──► T-016 (F) ──► T-017 (G)        [the core loop: clarity → self-brief → compose]
T-018 (D)   independent
T-019 (A) ──► T-020 (B) ──► T-021 (E)        [spec self-sufficiency + verify]
```

T-015 → T-016 → T-017 is the headline path (~3 sessions) that realizes "read the
next task and execute." T-018 can start anytime. T-019/T-020/T-021 deepen spec
quality and close the verify gap.

---

## Out of Scope

- OpenSpec artifact names (`proposal.md`/`specs/`/`tasks.md`), forkable schemas,
  npm CLI, tool-portability for 25+ assistants — unchanged rejections from the
  2026-05-13 plan.
- `/opsx:ff` (covered by start-iteration + plan-feature) and `/opsx:onboard`
  (covered by `/openup-init`).
- Removing T-009's parallelism machinery — it is re-scoped as the per-lane
  enabler, not deleted.
- Multiple teammates inside one task — explicitly rejected in favor of one agent
  per lane with sequential role-hats.

---

## Open Questions

1. `.openup/board.json` committed (shared across lanes/machines) or local-only
   with the script as sync point? Leases argue committed; regeneration-on-read
   argues it barely matters.
2. `openup-board.py` as a `Stop`/`PostToolUse` hook refresh, or only inside
   `/openup-next`? Hook = always fresh; skill-only = simpler.
3. Does T-016's cold-start block go verbatim into `*-compact.md` variants or as a
   one-line pointer to the full role file?
4. T-020 scenario requirement on `standard` track or `full` only? (Lean:
   standard + full, skip quick.)
5. Does T-017's `state.json` keep any within-cycle role beyond the lease, or is
   the Operations checkbox + board enough to resume after a mid-cycle crash?

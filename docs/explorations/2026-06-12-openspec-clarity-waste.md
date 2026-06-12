# Exploration: OpenSpec ideas for reducing waste from unclear objectives

**Started:** 2026-06-12
**Question:** Which OpenSpec primitives, not yet adopted by OpenUP, would reduce
development waste caused by unclear objectives and misunderstandings between
the requester and the implementing agent?

## Context

This is a follow-up to [2026-05-13-openspec-ideas-for-openup.md](../plans/2026-05-13-openspec-ideas-for-openup.md),
re-focused on a single goal: **waste reduction from intent ambiguity**. Since
that plan was written, Process v2 (T-004…T-011) absorbed most of it:

| 2026-05-13 item | Status today |
|---|---|
| #1 Readiness DAG | ✅ done — T-008, `/openup-readiness` + coordination frontmatter |
| #2 `project-config.yaml` context/rules injection | ❌ **not implemented** — no references anywhere in skills or docs-eng-process |
| #3 Per-change folders | ✅ done — T-007, `docs/changes/T-NNN/` (Ring 2) |
| #4 Archive flow | ✅ done — `docs/changes/archive/` |
| #5 Explore mode | ✅ done — this file is written through it |
| (related) T-002 `/openup-sync-spec` | ✅ done — 2026-06-11 |

So the question is no longer "what should we borrow" wholesale — it's what
remains in OpenSpec (including its current OPSX iteration: `/opsx:propose`,
`/opsx:verify`, delta-specs, structural validation) that targets the two
moments where ambiguity waste actually occurs:

1. **Before work starts** — intent never pinned down; the agent builds a
   plausible-but-wrong thing.
2. **During/after work** — ambiguity discovered mid-flight is resolved
   silently by the agent; spec and code drift without anyone deciding.

## Notes

### Where OpenUP already stands on clarity

- **Task spec (REASONS canvas)** is strong on *scope* alignment: Story +
  INVEST, "Scope boundaries", "Do not touch" (explicit anti-scope), Safeguards
  with no-go zones. This is better than OpenSpec's proposal at preventing
  scope creep.
- **Use-case rubric** enforces flows, alternates, exceptions — good behavioral
  coverage at the *use-case* level.
- **Weak point 1:** task-spec `## Requirements` are "numbered, testable
  assertions" — testability is *asserted*, never *demonstrated*. Nothing forces
  a requirement to be concrete enough that two readers parse it identically.
- **Weak point 2:** requirements are written fresh, not as a **delta against
  Ring 1 product truth**. A reviewer can't see "this changes existing behavior
  X" vs "this adds new behavior Y" without doing the diff in their head — which
  is exactly where misunderstandings hide ("I thought we were keeping X").
- **Weak point 3:** `/openup-request-input` exists (and its `fit.great`
  includes "ambiguous requirements"), but **no authoring skill is required to
  use it**. Neither `create-task-spec` nor `plan-feature` mention ambiguity,
  clarification, or request-input. An agent that guesses wrong never hits a
  gate.

### What OpenSpec does at those two moments

- **Pre-work:** proposal = "Why / What changes / Impact" reviewed by the human
  *before* any artifact is built; requirements written as **deltas**
  (`ADDED` / `MODIFIED` / `REMOVED` against living specs); every requirement
  must carry ≥1 `#### Scenario:` in Given/When/Then; `openspec validate`
  checks this structure deterministically; agent instructions say "ask
  clarifying questions when the request is ambiguous" rather than guess.
- **Post-work:** `/opsx:verify` checks the implementation against the
  artifacts; archive folds deltas back into the living `specs/` truth.

## Options Considered

Five candidate adoptions, graded for the stated goal:

- **Option A — Behavior-delta section in the task spec** (HIGH value / MED effort).
  Add a `## Behavior Delta` section to `docs-eng-process/templates/task-spec.md`:
  requirements grouped **Added / Modified / Removed**, each Modified/Removed
  entry naming the Ring 1 artifact + section it changes
  (`docs/product/use-cases/UC-3 §main-flow`). Pro: misunderstandings about
  *existing* behavior become visible at review time; gives `/openup-sync-spec`
  an exact list of Ring-1 artifacts to update instead of inferring. Con: only
  pays off when Ring 1 is populated; meaningless for greenfield tasks (make the
  section "n/a — all Added" in that case). Mirrors the existing
  Add/Modify/Do-not-touch idiom the Structure section already uses for *files*.

- **Option B — Scenario-per-requirement + deterministic validation** (HIGH value / MED effort).
  Every entry in `## Requirements` must carry at least one
  `Given / When / Then` scenario; a small script (extend
  `/openup-readiness` or a `.claude/scripts/` check invoked by
  `/openup-assess-completeness`) validates the structure deterministically —
  Process v2's own principle: "if a step is deterministic, the harness does
  it." Pro: writing the scenario is where vague requirements break down
  ("When the user does X — *which* X?"); the misunderstanding surfaces before
  code. Con: ceremony for quick-track tasks — apply on standard/full tracks
  only.

- **Option C — Mandatory ambiguity gate in spec authoring** (HIGH value / LOW effort).
  Add a numbered step to `create-task-spec` and `plan-feature`: before
  drafting, list open questions; classify each as *blocking* (answer changes
  scope/requirements) or *non-blocking* (note the assumption inline). Blocking
  → invoke `/openup-request-input` and stop; non-blocking → record as
  `**Assumption:**` lines in Analysis Context so the requester can veto them at
  review. Pro: cheapest item; directly converts silent guesses into visible,
  vetoable assumptions. Con: relies on prose instruction (no hook) — but it
  lives inside a skill, the layer that held up in the Kaze audit.

- **Option D — `docs/project-config.yaml`** (MED value / LOW effort).
  The one surviving item from the 2026-05-13 plan, already fully specified
  there (item #2). A canonical home for project facts (stack, domain,
  compliance) injected as `<project-context>` / `<project-rules>` into every
  `/openup-create-*` prompt. Pro: removes a whole class of misunderstanding —
  "the agent didn't know a fact that's true here but not everywhere." Con:
  none new; it was rated MED/LOW then and nothing changed.

- **Option E — Implementation-vs-spec verify step in `/openup-complete-task`** (MED value / LOW effort).
  OpenSpec's `/opsx:verify` equivalent: before marking done, grade each
  requirement (and its scenarios, if Option B lands) ✅/❌ against the actual
  diff — same per-criterion idiom as the rubrics. Pro: catches "built the
  wrong thing" before it's archived as done. Con: partially overlaps the
  task-spec's own `## Verification` section; implement as a sharpening of
  that section's execution, not a new artifact.

**Ruled out** (unchanged from 2026-05-13, still correct): OpenSpec artifact
names, forkable schemas, npm CLI, tool-portability. Also ruled out from the
current OPSX set: `/opsx:ff` (covered by `/openup-start-iteration` +
plan-feature) and `/opsx:onboard` (covered by `/openup-init`).

### Suggested sequencing

C (one session, immediate) → D (one session, already specified) →
A (feeds sync-spec; do before B) → B (validation builds on A's structure) →
E (half session, folds into complete-task).

C+D+A together address "objectives not clear before work"; B+E address
"misunderstanding not caught during/after work."

## 2026-06-12 (later) — Principle: roles self-brief from `docs/`, no custom instructions

User-stated design principle, added mid-exploration: **each OpenUP role should
be able to continue work from information already in `docs/` — status from
roadmap/plans/logs, *what* from vision/use-cases/specs, *how* from OpenUP
guidelines and elaboration outputs — without receiving custom instructions.**
The docs ARE the briefing; a delegation should reduce to "role + task ID."

### How far OpenUP is from this today

- **Closest to the ideal:** the developer teammate already says "read
  `docs/project-status.md`, then `docs/changes/T-XXX/plan.md` — your
  authoritative input." The Three Rings rule defines what to load. The
  readiness DAG makes "what's next" a query.
- **Furthest from the ideal:** the PM Delegation Brief Format
  (`.claude/teammates/project-manager.md`) instructs the PM to hand each
  specialist scope + context-docs list + deliverable + done-when criteria.
  Every one of those is (or should be) derivable: scope = task-spec
  Story/Scope boundaries; context docs = coordination frontmatter +
  role-scoped ring rule; deliverable = task-spec Structure/Operations;
  done-when = rubric + task-spec Verification. The brief is redundant
  *exactly when the spec is complete* — and a custom patch over the spec's
  gaps when it isn't. Custom briefings are therefore a **symptom of
  incomplete specs**, which ties this principle directly to Options A/B/C.
- **Uneven:** not all teammate files have the developer's deterministic
  cold-start reading list; per-role "how" sources (architecture notebook,
  conventions, test plan) are referenced inconsistently across roles.

### Option F — Self-briefing roles: pointer-only delegation (HIGH value / LOW–MED effort)

Two coordinated edits:

1. **Cold-start reading list per role.** Give every teammate file a uniform
   "On start, read:" block — status (`project-status.md` + roadmap entry),
   what (`docs/changes/T-NNN/` + linked Ring 1 artifacts), how (role-relevant
   guideline docs: architect → architecture notebook; tester → test plan;
   developer → conventions + arch notebook). Role-scoped rings, stated once
   in the role file instead of re-decided per briefing.
2. **Collapse the PM brief to a pointer + delta.** Replace the four-part
   brief format with: `[ROLE]: T-NNN. Deltas: <only what the docs don't say —
   usually nothing>`. If the PM finds itself writing scope or done-when into
   a brief, that is a signal the task spec is incomplete → fix the spec
   (fix-spec-first), don't patch it with prompt text.

Pro: removes the largest remaining source of per-session custom instructions;
makes brief-writing cost ~zero; turns "spec was incomplete" from a silent
prompt-patch into a visible spec edit. Con: depends on spec completeness —
sequence after C (ambiguity gate) so specs carry assumptions explicitly;
A/B strengthen it further but aren't preconditions.

### Effect on sequencing

C and F are mutually reinforcing and both cheap: C makes specs complete
enough to brief from; F removes the briefing layer that was compensating.
Revised order: **C → F → D → A → B → E.**

## 2026-06-12 (later still) — Principle: sequential execution, repo-persisted handover

Second user-stated principle: **team-based work produces noisy handovers and
parallel agents are not actually wanted.** Preference: sequential execution
with clean handovers based on information persisted in the repo. The ideal
operating mode is a loop whose body is one simple instruction — *"read the
next task and execute"* — with no per-cycle human authoring.

This is OpenSpec's `/opsx:continue` idea, which the 2026-05-13 plan noted
("deterministically picks the next READY node") but adopted only the *state*
half of (the readiness DAG), not the *executor* half.

### What this changes in the framework's posture

- **Teams demote from default to opt-in.** Today `CLAUDE.openup.md` says
  teams are "active by default" and `/openup-start-iteration` deploys one as
  mandatory step 3. Under this principle the default is one agent assuming
  roles *sequentially* (analyst hat → developer hat → tester hat), with the
  role transition recorded in repo artifacts, not in inter-agent messages.
  Teams remain available for `full`-track work that genuinely needs
  independent review — opt-in, not ambient.
- **Handover channel = the repo, exclusively.** Rule: *no information needed
  to continue the work may live only in a conversation.* The Ring 2 change
  folder (`plan.md`, `design.md`, `test-notes.md`), `.openup/state.json`,
  the run log, and `/openup-create-handoff` output are the handover. Teammate
  message traffic is at most a notification that the repo changed.
- **Parallelism is per-*lane*, not per-role.** (User refinement, same day.)
  Parallel work IS wanted — but across **disjoint work streams** (a new
  feature in one lane, an unrelated refactor in another), never as multiple
  teammates inside one task. The unit of parallelism is the independent
  task/lane; within a lane, execution is strictly sequential with
  repo-persisted handover.
- **T-009's machinery is the lane enabler, not dead weight.** Worktree-per-
  task + lease claims + collision pre-flight are exactly what makes two
  concurrent lanes safe: the collision pre-flight (already part of
  `/openup-readiness`'s collision set = READY ∪ IN-PROGRESS) decides whether
  a second lane may open; the lease marks the task claimed; the worktree
  isolates the lane's files. What changes is the *framing*: one agent per
  lane, lanes proven disjoint before opening — not N teammates on one task.

### What already exists for the loop (the gap is composition)

| Loop step | Existing piece |
|---|---|
| "what's next?" | `/openup-readiness` — READY/BLOCKED/collision report |
| "brief myself" | Option F cold-start lists + Ring 1 + change folder |
| "execute under right ceremony" | graded tracks (T-010) + track skills |
| "persist the handover" | change folder + `/openup-log-run` + `/openup-create-handoff` + state.json |
| "mark done, archive" | `/openup-complete-task` + archive flow |
| **compose the above** | **missing** |

### Option G — `/openup-next`: sequential continue-loop entry point (HIGH value / MED effort)

One skill that makes "read the next task and execute" literally sufficient:

1. Run readiness; pick the single best READY task **that does not collide
   with any in-progress lane** (priority, then DAG depth; readiness's
   collision set is the gate). If nothing is READY-and-collision-free, print
   why and stop cleanly — a no-op cycle is a valid result. Claim the task
   (lease) and work in its worktree, so a second `/openup-next` loop in
   another session naturally picks a disjoint task — that is how cross-lane
   parallelism happens, with no coordination protocol beyond the repo.
2. Self-brief per Option F (role implied by the task's next ready artifact:
   spec missing → analyst hat; spec ready → developer hat; impl done →
   tester hat).
3. Execute under the task's track ceremony (quick/standard/full).
4. Persist: spec deltas, design.md decisions, run log, state.json; finish
   via `/openup-complete-task` or write a `/openup-create-handoff` brief if
   stopping mid-task (the *only* two legal exits).
5. End the session. The outer loop (Claude Code `/loop`, cron, or a human
   re-invoking) provides repetition; the skill owns exactly one cycle.

### G's data layer — the execution board (user refinement, same day)

Requirement: a cycle must not "read many docs and think about who/what/how."
Selection and continuation should be a **lookup against one simple-to-parse
file** that supports many active items (lanes), and every cycle must update
it on exit so the next cycle knows how to continue.

Two coordinated pieces:

1. **`.openup/board.json` — the materialized queue (one file, many lanes).**
   A machine-readable array, one entry per active/ready task:

   ```json
   {
     "generated_at": "<iso>",
     "items": [
       {
         "task": "T-021",
         "title": "…",
         "track": "standard",
         "state": "in-progress",
         "lease": {"by": "session-abc", "since": "<iso>"},
         "hat": "developer",
         "next_action": "Operations step 4 of 7: <verbatim step text>",
         "plan": "docs/changes/T-021/plan.md",
         "collides_with": [],
         "depends_ok": true
       }
     ]
   }
   ```

   Crucially the board is **derived, never authored**: a deterministic script
   (`.claude/scripts/openup-board.py`) regenerates it from the existing
   sources of truth — change-folder frontmatter, roadmap, leases, checklist
   state (below). The model never edits the board; it runs the script and
   reads `items[0]` that is collision-free and unleased. This follows
   Process v2's own rule ("if a step is deterministic, the harness does it")
   and kills the staleness risk a hand-maintained queue would have.

2. **Within-task progress = checkboxes in the spec's Operations section.**
   The task-spec template's `## Operations` is already an ordered step list;
   change the convention from `1. <step>` to `- [ ] <step>`. A cycle checks
   off the steps it completed before exiting — that single edit is the
   within-task handover, and it is trivially parseable (the board script
   derives `next_action` from the first unchecked box, and `hat` from which
   artifact/phase the unchecked work belongs to). This is OpenSpec's
   `tasks.md` checklist pattern, grafted onto the existing REASONS spec
   instead of adding a new artifact.

The cycle then becomes mechanical at both ends:
**refresh board → take top item → do `next_action` → tick boxes (+ design.md
notes if decisions were made) → refresh board → exit.** Reading stays scoped
to the one change folder plus whatever Ring 1 artifacts the spec links —
never "scan docs/ and decide."

Pro: collapses the PM-orchestration overhead to zero for the common case;
makes progress resumable from any cold session; the noisy-handover problem
disappears because there is no *receiver* mid-task — the next cycle reads
the repo. Con: one-cycle-one-task assumes specs are executable cold —
sequence after C and F; and `CLAUDE.openup.md`'s team-by-default language
must be revised in the same change or the skill contradicts the guidelines.

### Effect on sequencing (revised again)

**C → F → G → D → A → B → E.** C makes specs unambiguous, F makes roles
self-briefing, G composes them into the loop; D/A/B deepen spec
self-sufficiency; E closes the verify gap at task completion.

## Open Questions

- Should Option B's scenario requirement apply to `standard` track or only
  `full`? (Lean: standard+full, skip quick.)
- Does Option A's Behavior Delta live in `plan.md` (Ring 2) or in the task
  spec template — or are those now the same file under `docs/changes/T-NNN/`?
  Needs a look at how T-007 reconciled `task-spec.md` with `plan.md`.
- Option E vs the existing rubric pass in `/openup-complete-task` (full
  track) — extension or duplication? Check complete-task's current steps
  before scoping.
- Option F: do compact teammate variants (`*-compact.md`) get the same
  cold-start block, or a one-line pointer to the full role file's list?
- Option G: how does role-hat sequencing interact with the mandatory
  "deploy team as step 3" gate in `/openup-start-iteration` — does the gate
  become track-conditional (full only)?
- Option G: what does state.json record between hats within one cycle, so a
  crash mid-cycle resumes at the right hat? (Largely answered by the board +
  Operations checkboxes — remaining question is whether state.json keeps any
  role beyond the lease.)
- Board: is `.openup/board.json` committed (shared across machines/lanes) or
  local-only with the script as the sync point? Leases argue for committed;
  regeneration-on-read argues it barely matters.
- Board: does the script live as a `PostToolUse`/`Stop` hook refresh, or
  only inside `/openup-next`? Hook = always fresh; skill-only = simpler.

## Where this goes next

→ iteration — promote to a roadmap entry "Clarity, self-briefing, and the
sequential continue-loop" with seven candidate tasks (C, F, G, D, A, B, E in
that order); C and F are each ~1 session and unblock G, which is the
headline deliverable ("read the next task and execute" becomes sufficient).

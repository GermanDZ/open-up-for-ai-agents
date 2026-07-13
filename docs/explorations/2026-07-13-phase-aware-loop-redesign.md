# Exploration: making the loop follow OpenUP — gap analysis and redesign

**Started:** 2026-07-13
**Question:** Our automated loop runs a simplified explore→plan→execute cycle
that ignores the OpenUP lifecycle. What has to change in our tools and skills
so the loop *follows the process* — starting each cycle from the product's
current phase, running real iterations composed of per-role activities, and
gating phase transitions the way OpenUP does — instead of the LLM re-inventing
a process every run?
**Inputs:** [2026-07-13-openup-kb-process-model.md](2026-07-13-openup-kb-process-model.md)
(the authoritative model), plus a full audit of the current skills/scripts.
**Follow-on to:** [2026-07-13-openup-agent-live-run-feedback.md](2026-07-13-openup-agent-live-run-feedback.md)

## 1. The gap, precisely

OpenUP is a **three-layer state machine**:

| Layer | OpenUP | Our automation today |
|---|---|---|
| Project lifecycle | 4 phases, each ending at a milestone with a stakeholder go/no-go (LCO → LCA → IOC → PR); risk↓ value↑ ordering | `phase` is a static enum in `.openup/state.json`, set by a human editing `docs/project-status.md`; never read to gate work, never advanced by the loop |
| Iteration lifecycle | Plan Iteration (1–5 objectives from risk+value, committed work items, evaluation criteria) → Manage → **Assess Results** (demo, retro, milestone review at phase end) | "iteration" ≈ one task; `/openup-start-iteration` wraps a single task spec; there is no assess step — `/openup-complete-task` closes the lane and the loop moves on |
| Micro-increment | Work item, ½–2 days, tracked on the Work Items List | ✅ this layer we do well: lanes, Operations checkboxes, leases, collision detection, the derived board |

Audit facts backing this (templates pack + scripts):

- `openup-next/SKILL.md` resolves `{resume | pick | promote | noop}` via
  `openup-board.py resolve`. Phase appears **once**, in the no-op branch, as an
  advisory message suggesting a human run `/openup-phase-review`.
- `openup-board.py` builds the board from change-folder frontmatter, leases,
  and checkbox state — **no phase input anywhere**. `openup-roadmap.py
  cmd_next` picks the first eligible pending row in document order — **zero
  occurrences of "phase"**.
- The four phase skills (`/openup-inception` … `/openup-transition`) and
  `/openup-phase-review` are human-facing guidance docs; nothing in the loop
  invokes them.
- `/openup-orchestrate` decomposes a goal by role ad hoc — not by the phase's
  activity composition.
- The artifact skills (create-vision, create-use-case, create-architecture-
  notebook, create-test-plan, create-risk-list, create-iteration-plan) exist
  per role but **nothing sequences them per phase**; they run only when a
  human writes a roadmap row that happens to name them.
- The outer drivers (`scripts/openup-loop.sh`, `/loop /openup-next`,
  `scripts/openup-agent.py`) just repeat `next` until a DONE sentinel —
  goal-blind and phase-blind by design (fine: the intelligence belongs below
  them).

Net effect: the loop is a **flat task queue**. Whatever process happens on top
of it is re-invented by the model each session — exactly the failure mode the
framework exists to prevent.

## 2. Design principles for the fix

1. **Same philosophy as the board: derive, don't author.** Phase and iteration
   state must come from deterministic scripts reading repo facts (artifact
   presence/status, milestone decision records, roadmap state) — never from
   the model's judgment mid-loop. The model does the *work inside* a step; the
   *choice of step* is mechanical.
2. **Humans own the go/no-go.** Milestone reviews are stakeholder decisions.
   The loop prepares the evidence and **pauses** (T-074 `/openup-request-input`
   machinery); it never advances a phase on its own. Transition is entirely
   human-gated.
3. **Tailoring is data, not prose.** Each project declares its Development
   Case (OpenUP's own name for this) in config; the same engine runs a
   quick project, an MVP, and a full product with different parameters.
4. **Keep the micro-increment layer as is.** Lanes, leases, write-fence,
   collision detection, two legal exits — all unchanged. We are adding the two
   missing outer layers, not rebuilding the inner one.

## 3. Proposed architecture

### 3.1 Lifecycle state — new derived view + decision records

- **`scripts/openup-lifecycle.py status`** (new, deterministic): computes the
  current phase and per-milestone criteria state. Inputs: which work-product
  instances exist and their `status:` frontmatter (vision, use cases, risk
  list, architecture notebook, test plan — we already have typed traceability
  frontmatter from T-038), roadmap rows, archived change folders, and
  **milestone decision records**.
- **Milestone decision records** — `docs/product/milestones/<phase>-<cycle>.md`,
  authored only via `/openup-phase-review`, recording the stakeholder's
  go/no-go answer + evidence links. The *record* is the source of truth for
  "phase advanced"; `lifecycle.py` merely reads it. A `cycle` counter supports
  going back to Construction after (partial) Transition — OpenUP's "start
  another development cycle".
- `phase` in `.openup/state.json` becomes a cache of `lifecycle.py status`,
  stamped at iteration start — no longer hand-set via `project-status.md`.

### 3.2 Development Case — tailoring as config

Extend `docs/project-config.yaml` (already the project-rules home) with a
`process:` section, defaulted by archetype:

```yaml
process:
  archetype: product        # quick | mvp | product  (sets the defaults below)
  phases:
    inception:    { iterations: 1, artifacts: [vision, use-case-outline, risk-list] }
    elaboration:  { iterations: auto, artifacts: [architecture-notebook, detailed-use-cases, test-plan],
                    exit: architecture-validated }   # tested skeleton, not a doc
    construction: { iterations: many, parallel: true }
    transition:   { gate: human }
  milestone_review: human   # human | auto-assess (auto allowed only for minor milestones)
```

- `quick` archetype ≈ today's quick track generalized: near-empty Inception,
  Elaboration skipped, one Construction iteration.
- `mvp`: one lean Inception, one thin Elaboration (architecture = a validated
  walking skeleton), single Construction run.
- `product`: Elaboration sized to technical risk — `iterations: auto` means
  "keep planning Elaboration iterations while architecturally-significant
  risks remain open on the risk list", which is exactly the KB rule.
- This *is* OpenUP's Development Case
  (`project_process_tailoring/guidances/concepts/development-case.md`) made
  machine-readable. Framework rubric → project rules precedence already
  defined in `docs-eng-process/project-config.md` extends naturally.

### 3.3 Phase → activity → skill map — the process as data

New `docs-eng-process/process-map.yaml` (framework-owned, vendored like the
KB), encoding §4 of the KB distillation:

```yaml
inception:    [initiate-project, agree-technical-approach, identify-refine-requirements, plan-manage-iteration]
elaboration:  [identify-refine-requirements, develop-architecture, develop-solution-increment, test-solution, plan-manage-iteration]
construction: [identify-refine-requirements, develop-solution-increment, test-solution, plan-manage-iteration]
transition:   [ongoing-tasks, develop-solution-increment, test-solution, plan-manage-iteration]
activities:
  identify-refine-requirements: { role: analyst,   skills: [openup-create-use-case, openup-detail-use-case] }
  develop-architecture:         { role: architect, skills: [openup-create-architecture-notebook] }
  develop-solution-increment:   { role: developer, skills: [openup-tdd-workflow] }
  test-solution:                { role: tester,    skills: [openup-create-test-plan] }
  ...
```

Consequence: **iteration planning can generate phase-appropriate lanes.** In
Inception the planner emits vision/use-case/risk-list lanes with `hat:
analyst` without a human hand-writing those roadmap rows; in Elaboration it
emits architecture + skeleton-increment + test lanes; in Construction the
familiar dev/test lanes. The four phase skills stop being parallel manual
guidance and become thin fronts over this map (or are folded into the
planner and kept as documentation).

### 3.4 The loop — new resolve order (the heart of the change)

`openup-next` keeps its shape (one cycle per invocation, deterministic
resolve, two legal exits) but the resolver becomes lifecycle-aware. New
precedence, wrapping today's logic:

```
0. lifecycle.py status                → current phase, cycle, milestone criteria state
1. resume                             → unchanged (mid-lane work continues)
2. pick                               → unchanged, but only lanes belonging to the ACTIVE iteration
3. iteration exhausted (all committed work items done)
                                      → path: assess-iteration
                                        run Assess Results: evaluation criteria check, demo notes,
                                        feed new work items back, retrospective;
                                        if phase exit criteria met per Development Case
                                        → path: milestone-review (pause: /openup-request-input,
                                          human go/no-go; on GO record decision, advance phase)
4. no active iteration                → path: plan-iteration
                                        run Plan Iteration for the CURRENT phase:
                                        objectives (1–5) from risk list + PM value order + phase
                                        objectives; commit work items (generate lanes from the
                                        process map); define evaluation criteria
5. noop                               → truly nothing to do (awaiting human input or product done)
```

- The **promote** path dissolves into `plan-iteration`: promoting single
  roadmap rows one at a time is replaced by committing a set of work items to
  a real iteration. (Quick archetype degenerates gracefully: an iteration of
  one work item ≈ today's behavior.)
- `openup-agent.py` procedures gain the matching new paths
  (`plan-iteration`, `assess-iteration`, `milestone-review`); the drivers
  themselves stay dumb.
- The DONE sentinel changes meaning from "roadmap empty" to "milestone-review
  pending human input" or "PR milestone accepted".

### 3.5 Iteration as a first-class unit

- The **iteration-plan instance** (already a typed work product,
  `/openup-create-iteration-plan`) becomes the loop's contract: objectives,
  committed work-item ids (references to lanes — the Work Items List is the
  roadmap + change folders, as today), evaluation criteria, assessment
  section. Low-ceremony per KB: one page.
- `.openup/state.json` grows `iteration_id` (pointer to the plan instance) and
  keeps per-lane fields as today; `openup-state.schema.json` versioned to
  schema 2.
- New skill **`/openup-assess-iteration`** (or an upgraded
  `/openup-retrospective`): runs Assess Results — checks evaluation criteria,
  demos only completed acceptance-tested work, feeds discovered work back into
  the roadmap, writes the assessment into the iteration plan, and triggers
  `/openup-phase-review` when the Development Case says the phase should be
  done. This is the piece that makes the loop *converge* instead of just
  draining a queue.

### 3.6 The user's scenarios, expressed in this design

- **Quick project / fast inception** → `archetype: quick`: Inception = one
  auto-assessed short iteration (or none), straight to Construction.
- **MVP** → `archetype: mvp`: single thin Elaboration whose exit is a
  *validated walking skeleton*, then one Construction phase.
- **Normal product** → `elaboration.iterations: auto`: Elaboration continues
  while architecturally-significant risks remain open — sized by technical
  challenge, exactly the KB rule.
- **Transition human-gated; return to Construction** → `transition.gate:
  human` + milestone records with a `cycle` counter: a "not yet" or a
  post-release feature idea starts Construction iterations in cycle N+1
  without pretending the product never shipped.
- **Many Construction iterations; small tasks join the current one** → small
  work items are appended to the Work Items List and pulled in either by the
  active iteration's Manage step (Ongoing Tasks / Request Change) or at the
  next plan-iteration; no ceremony beyond a roadmap row.
- **New ideas → lean re-inception** → `/openup-plan-feature` evolves into a
  *feature-scoped* Identify-and-Refine-Requirements (+ optional
  Envision-Architecture) activity: it revises the vision/use-case/risk
  artifacts (fix-spec-first, through their skills) and lands work items on the
  list — a mini-Inception/Elaboration that composes with the running
  Construction phase instead of restarting the lifecycle.
- **Parallel Construction iterations for low-dependency features** → lift the
  existing lane collision machinery one level: allow N concurrent iterations
  whose committed work items have disjoint `touches` and use-case
  dependencies. `board.py` already computes collisions; the planner just
  partitions work items into non-colliding clusters. (This also matches the
  live-run finding F5: worktree-per-lane.)

## 4. What changes, per artifact (summary table)

| Artifact | Change |
|---|---|
| `scripts/openup-lifecycle.py` | NEW — derived phase/milestone status; same never-hand-edit rule as board |
| `docs/product/milestones/` | NEW — milestone decision records (human go/no-go), written by `/openup-phase-review` |
| `docs/project-config.yaml` `process:` | NEW section — Development Case (archetype + per-phase tailoring) |
| `docs-eng-process/process-map.yaml` | NEW — phase→activity→role→skill map (KB §3/§4 as data) |
| `scripts/openup-board.py` / `openup-roadmap.py` | resolve becomes lifecycle-aware; promote → plan-iteration; iteration-scoped pick |
| `openup-next` skill + `procedures/openup-next.md` | new paths: plan-iteration, assess-iteration, milestone-review |
| `/openup-start-iteration` | becomes Plan Iteration proper: phase objectives + risk/value-driven work-item commitment, generates lanes from the map |
| `/openup-create-iteration-plan` | instance becomes the loop contract (objectives, work items, evaluation criteria, assessment) |
| `/openup-assess-iteration` | NEW (or upgraded `/openup-retrospective`) — Assess Results incl. phase-end trigger |
| `/openup-phase-review` | wired in: invoked by the loop at phase end, pauses via `/openup-request-input`, writes the milestone record |
| Phase skills (`/openup-inception` etc.) | become thin fronts over the process map / docs; no longer a parallel manual process |
| `/openup-orchestrate` | decomposes by the phase's activity composition instead of ad-hoc roles |
| `.openup/state.json` | schema 2: `iteration_id`, `cycle`; `phase` becomes derived cache |
| `openup-agent.py` procedures | matching new procedure files; drivers unchanged |

## 5. Suggested delivery slicing (each its own task/PR)

1. **T-A `openup-lifecycle.py status` + milestone records** — read-only
   derived view; wire `phase` in state to it. No behavior change to the loop
   yet (status is advisory). Small, unblocks everything.
2. **T-B Development Case config** — `process:` section + archetype defaults +
   validation in `check-docs.py`/`openup-doctor`.
3. **T-C process-map.yaml + phase-aware plan-iteration** —
   `/openup-start-iteration` becomes Plan Iteration; planner generates
   phase-appropriate lanes. Biggest slice.
4. **T-D assess-iteration + milestone-review wiring** — the convergence step;
   `/openup-request-input` pause at milestones; resolve paths added to
   `openup-next` + procedures.
5. **T-E parallel iterations** — non-colliding iteration clusters; depends on
   worktree-per-lane (live-run F5).

Risks / open questions:
- **Ceremony creep for quick work** — mitigation: the quick archetype must
  degenerate to today's `/openup-quick-task` cost, measured in tokens, or the
  design fails its own token-efficiency protocol.
- **Criteria detection fidelity** — `lifecycle.py` can verify artifact
  existence/status mechanically, but "architecture validated" means a tested
  skeleton, not a notebook; the milestone record (human) carries that
  judgment. Keep the script honest about what it can and cannot assess.
- **Board/lane vocabulary vs work items** — we overload "task", "lane",
  "iteration" today; schema 2 should fix names once (work item = lane =
  change folder; iteration = committed set of work items).
- **manifest.json** — if we want exact intra-activity task ordering, parse the
  KB's `manifest.json` (1.5 MB) once into the process map rather than trusting
  the stripped diagrams.

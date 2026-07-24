# Exploration: the authoritative OpenUP process model (KB distillation)

**Started:** 2026-07-13
**Question:** What does the vendored OpenUP knowledge base actually define as the
process — phases, milestones, iteration lifecycle, per-phase role workflows,
tailoring — so we can measure our automation against it instead of re-inventing
a loop each run?
**Source:** all paths relative to `docs-eng-process/openup-knowledge-base/`.
**Companion:** [2026-07-13-phase-aware-loop-redesign.md](2026-07-13-phase-aware-loop-redesign.md)
(the gap analysis and redesign this distillation feeds).

## 1. The three layers of OpenUP

Canonical statement in `guides/base/guidances/supportingmaterials/introduction-to-openup.md`:
"OpenUP layers: micro-increments, iteration lifecycle and project lifecycle."

- **Micro-increments (personal level).** Short units of work, hours to a few
  days, each specified/tracked by a **work item**; change sets are the physical
  output. "An extremely short feedback loop that drives adaptive decisions
  within each iteration."
  (`practice-management/iterative_dev/guidances/concepts/micro-increments.md`)
- **Iteration lifecycle (team level).** "Planned, time-boxed intervals typically
  measured in weeks... structures how micro-increments are applied to deliver
  stable, cohesive builds." Result = a demoable or shippable build; the team
  pulls fine-grained tasks from a work-items list.
  (`practice-management/iterative_dev/guidances/concepts/iteration-lifecycle.md`)
- **Project lifecycle (stakeholder level).** Four phases — Inception,
  Elaboration, Construction, Transition — giving stakeholders "visibility,
  synchronization points, and decision points... go or no-go decisions."
  (`practice-management/risk_value_lifecycle/guidances/concepts/project-lifecycle.md`)

**Mapping to our repo:** micro-increment ≈ lane / Operations checkbox;
iteration ≈ what `/openup-start-iteration` *should* manage (today it wraps one
task); project lifecycle ≈ the `phase` field that today is a static label.

## 2. Phases, objectives, milestones, exit criteria

Each phase "has a defined set of goals, a particular iteration style, and
customized tasks and work products," ends at a milestone that answers a
stakeholder question, and the two drivers across the lifecycle are **risk
reduction** and **value creation**. If the milestone answer is No, the phase is
extended (usually one more iteration) or the project is cancelled.
(`.../concepts/project-lifecycle.md`, `.../concepts/phase-milestones.md`)

| Phase | Objectives | Milestone | Exit question |
|---|---|---|---|
| Inception | understand what to build (vision, scope, stakeholders); identify key functionality; ≥1 feasible solution/candidate architecture; high-level cost/schedule/risk | **Lifecycle Objectives (LCO)** | "Do we agree on scope and objectives, and should the project proceed?" |
| Elaboration | detail requirements; **design, implement, validate and baseline an executable architecture**; mitigate essential risks; reliable estimates | **Lifecycle Architecture (LCA)** | "Do we agree on the executable architecture; is value so far + remaining risk acceptable?" — achieved when the architecture is *validated* (tested skeleton, key interfaces implemented) |
| Construction | iteratively develop the complete product on the baselined architecture; minimize cost, achieve parallelism | **Initial Operational Capability (IOC)** | "Is the product close enough to release to switch focus to tuning/polish/deployment?" — all functionality developed, alpha testing done, ready for beta |
| Transition | beta test against user expectations; stakeholder concurrence that deployment is complete; lessons learned | **Product Release (PR)** | "Is the application ready to release?" — customer reviews and accepts deliverables |

Sources: `practice-management/risk_value_lifecycle/guidances/concepts/{inception,elaboration,construction,transition}-phase-10.md`,
`.../phase-milestones.md`. (The `process/base/deliveryprocesses/*-milestone.md`
files exist but their Required Results fields were emptied by the HTML→md
conversion; the prose above is the substance.)

**Typical iteration counts (tailoring signal):** Inception — default **one
short iteration** ("avoid analysis paralysis"), more only for large/
unprecedented/high-risk scope. Elaboration — depends on how unprecedented the
tech is; first iteration builds and tests a few critical scenarios to pin the
architecture. Construction — usually the most (1 simple, 2 substantial, 3+
large). Transition — one bug-fix iteration for a simple system to many for a
complex one.

**Milestone mechanics:** the end-of-phase review is not a separate ceremony —
it is a step inside the iteration's **Assess Results** task ("Perform a
retrospective (end of phase)", `practice-management/iterative_dev/tasks/assess-results-1.md`).

## 3. The iteration lifecycle: plan → manage → assess

Three collaboration tasks define an iteration (primary performer Project
Manager; Analyst/Architect/Developer/Stakeholder/Tester participate).
(`practice-management/iterative_dev/guidances/practices/iterative-development.md`)

1. **Plan Iteration** (`tasks/plan-iteration-1.md`): prioritize the work-items
   list; define **1–5 high-level iteration objectives** (drawn from unmitigated
   risk + highest-priority value); review risks; team commits work items and
   breaks them into ½–2-day tasks; define **evaluation criteria**; refine
   scope. In: Work Items List (mandatory). Out: Iteration Plan, Risk List,
   Work Items List. Guideline: `guidances/guidelines/iteration-planning.md`.
2. **Manage Iteration** (`tasks/manage-iteration-1.md`): track progress,
   handle exceptions, revisit the Risk List at least once per iteration,
   **descope to protect a useful increment** when falling behind.
3. **Assess Results** (`tasks/assess-results-1.md`): verify objectives and
   evaluation criteria met; demo **only completed, acceptance-tested work**;
   feed new work/defects back into the Work Items List; retrospective; when
   the iteration ends a phase, this is where the **milestone review** happens.
   Guideline: `guidances/guidelines/iteration-assessment.md`.

**Iteration Plan artifact** is deliberately low-ceremony — "a whiteboard" or a
one-page doc; "not required if... the scope of the project and each iteration
is sufficiently small as to be handled informally."
(`practice-management/iterative_dev/workproducts/iteration-plan-4.md`)

## 4. Per-phase activity composition (what an iteration runs, by phase)

OpenUP composes each phase-iteration from a fixed vocabulary of **activities**
(capability patterns). The objective→activity mapping survives in the numbered
capability-pattern variants:

- **Inception iteration** (`process/base/capabilitypatterns/inception-phase-iteration-2.md`):
  Initiate Project · Agree on Technical Approach · Identify and Refine
  Requirements · Plan and Manage Iteration.
- **Elaboration iteration** (`.../elaboration-phase-iteration-3.md`):
  Identify and Refine Requirements · **Develop the Architecture** · Develop
  Solution Increment · Test Solution · Plan and Manage Iteration — "most
  activities during a typical Elaboration iteration happen in parallel."
- **Construction iteration** (`.../construction-phase-iteration-1.md`):
  Identify and Refine Requirements · Develop Solution Increment · Test
  Solution · Plan and Manage Iteration.
- **Transition iteration** (`.../transition-phase-iteration-2.md`):
  Ongoing Tasks · Develop Solution Increment · Test Solution · Plan and
  Manage Iteration.

Activity meanings: **Plan and Manage Iteration** wraps §3.
**Identify and Refine Requirements** = detail use cases / scenarios /
system-wide requirements (Analyst). **Develop the Architecture** =
Elaboration-specific (Architect). **Develop Solution Increment** = design,
implement, test, integrate one requirement (Developer). **Test Solution** =
system-perspective testing (Tester). **Ongoing Tasks** = event-driven,
unplanned work, chiefly Request Change — "does not appear on the project plan,
iteration plan, or work items list."
(`process/base/capabilitypatterns/*.md`)

**Atomic role tasks** the activities decompose into:

- Analyst: Identify and Outline Requirements · Detail Use-Case Scenarios ·
  Detail System-Wide Requirements
  (`practice-technical/use_case_driven_dev/tasks/`); Develop Technical Vision
  (`practice-technical/shared_vision/tasks/`).
- Architect: Envision the Architecture · Refine the Architecture
  (`practice-technical/evolutionary_arch/tasks/`).
- Developer (the Develop Solution Increment inner loop): Design the Solution →
  Implement Developer Tests → Implement Solution → Run Developer Tests →
  Integrate and Create Build
  (`practice-technical/evolutionary_design/tasks/`,
  `practice-technical/test_driven_development/tasks/`,
  `practice-technical/continuous_integration/tasks/`).
- Tester: Create Test Cases → Implement Tests → Run Tests
  (`practice-technical/concurrent_testing/tasks/`).
- Project Manager: Plan Iteration · Manage Iteration · Assess Results
  (`practice-management/iterative_dev/tasks/`); Plan Project
  (`practice-management/release_planning/tasks/`).

Caveat: the exact intra-activity work-breakdown (ordering, RACI) lived in EPF
activity-diagram images stripped by the conversion; `manifest.json` (1.5 MB at
the KB root) encodes the full breakdown if we ever need it machine-readable.

## 5. Tailoring: the process is per-project by design

- **Minimal, complete, extensible** — OpenUP as shipped is a valid whole
  process; tailoring adds/renames roles, tasks, work products, lifecycles.
  "Thinking about design is more important than documenting the design."
  (`guides/base/guidances/supportingmaterials/minimal-complete-and-extensible.md`)
- **Process tailoring vs instantiation** — tailoring decides which work
  products and tasks are in/out, **what state each work product must reach at
  each milestone**, review/approval formality, reporting; instantiation binds
  people and storage.
  (`practice-management/project_process_tailoring/guidances/guidelines/tailoring-a-process-for-a-project.md`)
- **The Development Case** is the named artifact recording how a project
  deviates from published OpenUP (roles applied, artifacts added/dropped,
  review formality per milestone).
  (`practice-management/project_process_tailoring/guidances/concepts/development-case.md`)
- Built-in lean defaults: one short Inception iteration; Iteration Plan
  droppable for small scope; simple projects = 1 Construction + 1 Transition
  iteration.

**Mapping to our repo:** the Development Case is exactly what a `process:`
section in `docs/project-config.yaml` should hold — phase/iteration budgets,
required artifact set per milestone, review formality (auto vs human gate).

## 6. Direct implications for our automation (headline)

The KB model is a **three-layer state machine**: phase (milestone-gated,
human go/no-go) ⊃ iteration (plan → execute → assess, objectives drawn from
risk + value) ⊃ micro-increment (work item / lane). Our current loop
implements only the innermost layer and flattens the other two into a static
label and an endless queue. The gap analysis and redesign live in
[2026-07-13-phase-aware-loop-redesign.md](2026-07-13-phase-aware-loop-redesign.md).

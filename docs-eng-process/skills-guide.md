# OpenUP Skills Guide

This guide documents all OpenUP skills available for automating workflow operations.

## What are Skills?

Skills are reusable workflow operations that can be invoked using the `/` command in Claude Code. They encapsulate common OpenUP processes, ensuring consistency and reducing manual effort.

**Key Features of OpenUP Skills:**
- **Discoverable**: Each skill includes "When to Use" and "When NOT to Use" guidance
- **Verifiable**: Success criteria checklists ensure proper completion
- **Connected**: Cross-references to related skills and documentation
- **Robust**: Error handling and troubleshooting for common issues
- **Multi-file structure**: Complex skills use progressive disclosure

## Using Skills

Invoke a skill by typing `/` followed by the skill name:

```
/openup-skill-name argument1: value1 argument2: value2
```

Skills can also be invoked without arguments if they're optional:

```
/openup-skill-name
```

## Skill Naming Convention

All OpenUP skills use the `openup-` namespace prefix to avoid conflicts:
- Phase skills: `openup-inception`, `openup-elaboration`, etc.
- Artifact skills: `openup-create-vision`, `openup-create-use-case`, etc.
- Workflow skills: `openup-start-iteration`, `openup-complete-task`, etc.

## Skill Reference

> Generated from the skill files by `scripts/check-skills-guide.py` — do not
> hand-edit between the markers. Each entry is sourced from its
> `.claude-templates/skills/<name>/SKILL.md` frontmatter and body; to change an
> entry, edit that SKILL.md and run `python3 scripts/check-skills-guide.py --write`.

<!-- BEGIN GENERATED: skill-reference (scripts/check-skills-guide.py) -->
## Phase Skills

Phase skills guide you through each OpenUP phase, providing context-specific activities and completion criteria.

### /openup-construction

Initialize and manage Construction phase activities - build the system incrementally

**Model**: `haiku`

**When to Use**

Use this skill when:
- Elaboration is complete and architecture baseline is established
- Ready to build the system iteratively
- Implementing features incrementally
- Preparing for beta testing
- Checking if Construction phase is complete
- Getting guidance on next steps in Construction

**When NOT to Use**

Do NOT use this skill when:
- Architecture is not yet stable (use `/openup-elaboration`)
- System is ready for deployment (use `/openup-transition`)
- Need to create specific artifacts (use artifact skills)
- Looking for iteration planning (use `/openup-create-iteration-plan`)

**Success Criteria**

After using this skill, verify:
- [ ] Phase status is clearly understood (initiated, in-progress, or complete)
- [ ] Implementation progress is tracked
- [ ] Test coverage is adequate
- [ ] Next iteration tasks are identified
- [ ] Beta readiness is assessed

**Arguments**:
- `activity` (optional) — Specific activity to perform (initiate, check-status, next-steps)

**See Also**: `openup-complete-task` · `openup-create-test-plan` · `openup-elaboration` · `openup-transition`

### /openup-elaboration

Initialize and manage Elaboration phase activities - establish architecture baseline

**Model**: `haiku`

**When to Use**

Use this skill when:
- Inception is complete and need to establish architecture baseline
- Need to design and validate system architecture
- Resolving high-risk technical elements
- Implementing architectural prototypes
- Checking if Elaboration phase is complete
- Getting guidance on next steps in Elaboration

**When NOT to Use**

Do NOT use this skill when:
- Still defining project vision and scope (use `/openup-inception`)
- Architecture is stable and ready for incremental build (move to Construction)
- Need to create specific artifacts (use artifact skills)
- Looking for iteration planning (use `/openup-create-iteration-plan`)

**Success Criteria**

After using this skill, verify:
- [ ] Phase status is clearly understood (initiated, in-progress, or complete)
- [ ] Architecture notebook is created or updated
- [ ] Technical risks are identified and mitigated
- [ ] Critical use cases are detailed
- [ ] Next steps are clearly defined

**Arguments**:
- `activity` (optional) — Specific activity to perform (initiate, check-status, next-steps)

**See Also**: `openup-create-architecture-notebook` · `openup-shared-vision` · `openup-create-use-case` · `openup-detail-use-case` · `openup-inception` · `openup-construction`

### /openup-inception

Initialize and manage Inception phase activities - define scope, vision, and feasibility

**Model**: `haiku`

**When to Use**

Use this skill when:
- Starting a new project and need to define scope and vision
- Need to identify key stakeholders and risks
- Preparing to move from idea to validated business case
- Checking if Inception phase is complete
- Getting guidance on next steps in Inception

**When NOT to Use**

Do NOT use this skill when:
- Currently in Elaboration, Construction, or Transition phase (use appropriate phase skill)
- Need to create specific artifacts like vision documents or use cases (use artifact skills)
- Already have clear vision and architecture baseline (move to Elaboration)
- Looking for iteration planning (use `/openup-create-iteration-plan`)

**Success Criteria**

After using this skill, verify:
- [ ] Phase status is clearly understood (initiated, in-progress, or complete)
- [ ] Key artifacts are identified or created (vision, risk list, roadmap)
- [ ] Next steps are clearly defined
- [ ] Stakeholders and risks are documented

**Arguments**:
- `activity` (optional) — Specific activity to perform (initiate, check-status, next-steps)

**See Also**: `openup-create-vision` · `openup-shared-vision` · `openup-create-risk-list` · `openup-elaboration` · `openup-start-iteration`

### /openup-transition

Initialize and manage Transition phase activities - deploy to users

**Model**: `haiku`

**When to Use**

Use this skill when:
- Construction is complete and system is ready for deployment
- Preparing for beta or production release
- Conducting final testing and user acceptance
- Training users and support staff
- Checking if Transition phase is complete
- Getting guidance on next steps in Transition

**When NOT to Use**

Do NOT use this skill when:
- Still implementing features (use `/openup-construction`)
- System is not stable enough for testing (continue Construction)
- Need to create specific artifacts (use artifact skills)
- Looking for deployment procedures (use DevOps/ops documentation)

**Success Criteria**

After using this skill, verify:
- [ ] Phase status is clearly understood (initiated, in-progress, or complete)
- [ ] Deployment readiness is assessed
- [ ] Support materials are prepared
- [ ] User acceptance is documented
- [ ] Release decision is clear

**Arguments**:
- `activity` (optional) — Specific activity to perform (initiate, check-status, next-steps)

**See Also**: `openup-phase-review` · `openup-create-test-plan` · `openup-construction` · `openup-log-run`

## Artifact Skills

Artifact skills create OpenUP work products from templates.

### /openup-create-architecture-notebook

Generate or update architecture documentation from template

**Model**: `sonnet`

**When to Use**

Use this skill when:
- Starting Elaboration phase and need to document architecture
- Making significant architectural decisions
- Need to document system design and constraints
- Establishing architecture baseline
- Reviewing or updating existing architecture

**When NOT to Use**

Do NOT use this skill when:
- In Inception phase before architecture is defined (use `/openup-create-vision`)
- Need detailed component design (use design documents)
- Looking for implementation details (use code documentation)
- Architecture notebook exists and only minor updates needed (edit directly)

**Success Criteria**

After using this skill, verify:
- [ ] Architecture notebook exists at `docs/architecture-notebook.md`
- [ ] System name and context are defined
- [ ] Key architectural decisions are documented
- [ ] Architectural constraints are listed
- [ ] Quality attributes are specified
- [ ] Subsystem/component decomposition is documented

**Arguments**:
- `system_name` (required) — Name of the system
- `architectural_concerns` (optional) — Key architectural concerns to address

**See Also**: `openup-elaboration` · `openup-create-vision` · `openup-create-risk-list`

### /openup-create-documentation

Generate human-readable documentation from code and artifacts

**Model**: `sonnet`

**Arguments**:
- `doc_type` (required) — Type of documentation (user-guide, api-reference, troubleshooting, tutorial)
- `feature` (required) — Feature or component to document
- `output_path` (optional) — Output path for documentation (optional, defaults to docs/user-guides/)

**See Also**: `openup-create-use-case` · `openup-detail-use-case`

### /openup-create-iteration-plan

Plan iteration based on current state and roadmap

**Model**: `sonnet`

**When to Use**

Use this skill when:
- Starting a new iteration and need to plan work
- In Construction phase planning iterations
- Need to select tasks from roadmap for iteration
- Assigning tasks to team members
- Defining iteration success criteria

**When NOT to Use**

Do NOT use this skill when:
- Looking to start iteration (use `/openup-start-iteration`)
- Need to create roadmap (use project management)
- Iteration plan exists and only minor updates needed (edit directly)
- In Inception phase (use phase activities instead)

**Success Criteria**

After using this skill, verify:
- [ ] Iteration plan file exists
- [ ] Iteration goal is clearly defined
- [ ] Tasks are selected from roadmap
- [ ] Task assignments are made
- [ ] Success criteria are specified
- [ ] Iteration timeline is stated

**Arguments**:
- `iteration_number` (optional) — Iteration number to plan

**See Also**: `openup-start-iteration` · `openup-complete-task` · `openup-construction`

### /openup-create-risk-list

Create or update risk assessment document from template

**Model**: `sonnet`

**When to Use**

Use this skill when:
- Starting a new project and need to identify risks
- In Inception phase documenting major risks
- New risks emerge during project
- Need to update risk probability or impact
- Planning risk mitigation strategies

**When NOT to Use**

Do NOT use this skill when:
- Risk list exists and only minor updates needed (edit directly)
- Looking for issue tracking (use issue tracker)
- Risks have been realized and are now issues (manage as issues)
- Need detailed risk analysis (use risk management process)

**Success Criteria**

After using this skill, verify:
- [ ] Risk list exists at `docs/risk-list.md`
- [ ] Risks are documented with descriptions
- [ ] Probability and impact are assessed
- [ ] Mitigation strategies are defined
- [ ] Risk owners are assigned

**Arguments**:
- `risks` (optional) — JSON array of risks to add (optional)

**See Also**: `openup-inception` · `openup-create-vision` · `openup-create-architecture-notebook`

### /openup-create-task-spec

Produce a REASONS-Canvas task spec from a roadmap line or feature description, ready for developer-role consumption

**Model**: `sonnet`

**When to Use**

Use this skill when:
- A roadmap task is about to enter implementation and has no spec yet.
- A plan item needs to be decomposed before assignment.
- Existing in-progress work needs a retroactive spec for handoff.

**When NOT to Use**

Do NOT use this skill when:
- The change is a trivial typo / config tweak — use `/openup-quick-task`.
- The task spec already exists at `docs/changes/T-XXX/plan.md` — update via this
  skill (re-run), do not hand-edit (per the spec-first rule in `CLAUDE.openup.md`).
- You're at the *idea* stage and don't yet have requirements — run
  `/openup-plan-feature` first.

**Success Criteria**

After this skill completes, ALL of these must be true:
- [ ] File exists at `docs/changes/T-XXX/plan.md` matching the template at
      `docs-eng-process/templates/task-spec.md`.
- [ ] Front-matter is fully populated (`id`, `title`, `status`, `priority`, `estimate`).
- [ ] Status is `ready` (not `proposed`) — the rubric grades to all-✅.
- [ ] All thirteen rubric criteria in `.claude/rubrics/task-spec-rubric.md` are ✅.
- [ ] Every requirement carries a Given/When/Then scenario (standard/full tracks):
      `python3 scripts/openup-spec-scenarios.py check docs/changes/T-XXX/plan.md` exits 0.
- [ ] `docs/roadmap.md` references the new task with a status entry.

**Fit**:
- Great fit: decomposing iteration-plan tasks into executable specs, formalizing ad-hoc work before coding starts
- OK fit: retrofitting specs onto in-progress work that lacks one
- Poor fit: trivial doc-only edits (overhead exceeds value), exploratory spikes

**Arguments**:
- `task_id` (optional) — Task ID (T-XXX). Reserves the next free ID via `openup-claims.py reserve-id` if not provided.
- `title` (optional) — One-line task title. Required if task_id is new; reads from roadmap if existing.
- `source` (optional) — Where the task comes from: 'roadmap' (default), 'plan' (with plan path), or 'adhoc'.
- `plan_ref` (optional) — Path + section to the originating plan, e.g. 'docs/plans/2026-04-28-foo.md#3

**See Also**: `openup-create-iteration-plan` · `openup-assess-completeness` · `openup-orchestrate`

### /openup-create-test-plan

Generate test cases and test plan from use cases and requirements

**Model**: `sonnet`

**When to Use**

Use this skill when:
- Need to create test cases for features or use cases
- In Elaboration or Construction phase planning tests
- Starting testing for a new feature
- Need to document test procedures
- Creating test scripts for automation

**When NOT to Use**

Do NOT use this skill when:
- Looking to execute tests (use test runner)
- Need to debug test failures (use debugging tools)
- Test plan exists and only minor updates needed (edit directly)
- Looking for test reports (use test reporting)

**Success Criteria**

After using this skill, verify:
- [ ] Test cases exist in `docs/test-cases/`
- [ ] Test scripts exist in `docs/test-scripts/`
- [ ] Test coverage includes happy path, edge cases, error conditions, and integration points
- [ ] Expected results are defined
- [ ] Test procedures are documented

**Arguments**:
- `scope` (required) — What to test (e.g., specific feature, use case)

**See Also**: `openup-create-use-case` · `openup-construction` · `openup-phase-review`

### /openup-create-use-case

Create a use case specification from template

**Model**: `sonnet`

**When to Use**

Use this skill when:
- Need to document user interactions with the system
- In Inception or Elaboration phase defining requirements
- Capturing functional requirements from user perspective
- Need to specify preconditions, flows, and postconditions
- Creating test scenarios from requirements

**When NOT to Use**

Do NOT use this skill when:
- Need non-functional requirements (use architecture notebook)
- Looking for technical specifications (use design documents)
- Documenting internal system behavior (use technical design)
- Use case already exists (update existing file)

**Success Criteria**

After using this skill, verify:
- [ ] Use case file exists in `docs/use-cases/`
- [ ] Use case name and primary actor are defined
- [ ] Basic flow is documented
- [ ] Alternative flows are identified
- [ ] Pre/postconditions are specified

**Arguments**:
- `use_case_name` (required) — Name of the use case
- `primary_actor` (required) — The primary actor for this use case
- `description` (required) — Brief description of what the use case accomplishes

**See Also**: `openup-create-vision` · `openup-detail-use-case` · `openup-create-test-plan` · `openup-elaboration`

### /openup-create-vision

Generate a vision document from template

**Model**: `sonnet`

**When to Use**

Use this skill when:
- Starting a new project and need to define the vision
- In Inception phase and need to document project scope
- Stakeholders need a clear understanding of project goals
- Need to define problem statement and proposed solution
- Creating initial project artifacts

**When NOT to Use**

Do NOT use this skill when:
- Vision document already exists (update it directly or use revision process)
- Need detailed requirements (use use case skills instead)
- Looking for technical architecture (use `/openup-create-architecture-notebook`)
- In later phases (Elaboration+) when vision should be stable

**Success Criteria**

After using this skill, verify:
- [ ] Vision document exists at `docs/vision.md`
- [ ] Project name and problem statement are filled in
- [ ] Proposed solution overview is present
- [ ] Stakeholders are identified
- [ ] Key features are listed
- [ ] Success criteria are defined

**Arguments**:
- `project_name` (required) — Name of the project
- `problem_statement` (required) — Brief description of the problem to be solved

**See Also**: `openup-inception` · `openup-create-use-case` · `openup-create-risk-list`

### /openup-detail-use-case

Transform a high-level use case into detailed scenarios with test cases

**Model**: `sonnet`

**When to Use**

Use this skill when:
- A high-level use case exists but lacks detailed scenarios
- Need to document happy paths, alternative flows, and error cases
- Ready to create Gherkin acceptance criteria for automation
- Preparing to generate test cases from use cases
- In Elaboration phase when detailing requirements

**When NOT to Use**

Do NOT use this skill when:
- The use case doesn't exist (use `/openup-create-use-case` first)
- The use case is already fully detailed with scenarios
- Just need to create a new use case from scratch
- Working on non-functional requirements (use architecture notebook)

**Success Criteria**

After using this skill, verify:
- [ ] Use case is updated with detailed scenarios
- [ ] Happy path, alternative paths, and error paths are documented
- [ ] Gherkin acceptance criteria are written for each scenario
- [ ] Test cases are generated (if generate_tests=true)
- [ ] All actors are identified (primary and secondary)
- [ ] Preconditions and postconditions are clear

**Arguments**:
- `use_case_name` (required) — Name of the use case to detail (file name without .md)
- `generate_tests` (optional) — Generate test cases from scenarios (true/false, default: true)

**See Also**: `openup-create-use-case` · `openup-create-test-plan` · `openup-elaboration`

### /openup-shared-vision

Create shared technical vision for team alignment

**Model**: `sonnet`

**When to Use**

Use this skill when:
- Vision document exists but needs technical elaboration
- Need to define IN/OUT scope clearly
- Starting Elaboration phase and need technical alignment
- Team members have different understanding of technical direction
- Need to document key technical decisions and constraints

**When NOT to Use**

Do NOT use this skill when:
- No vision document exists (use `/openup-create-vision` first)
- In late Construction or Transition phases (should already exist)
- Only need architecture details (use `/openup-create-architecture-notebook`)
- Vision is already well-defined and understood

**Success Criteria**

After using this skill, verify:
- [ ] Technical objectives are clearly documented
- [ ] IN/OUT scope is well-defined
- [ ] Technical assumptions and constraints are listed
- [ ] Key technical decisions have rationale
- [ ] Open questions are tracked for elaboration
- [ ] Document is linked from main vision

**Arguments**:
- `technical_objectives` (optional) — Key technical objectives to address (comma-separated)
- `scope_focus` (optional) — Focus area for IN/OUT scope definition

**See Also**: `openup-create-vision` · `openup-create-architecture-notebook` · `openup-elaboration`

## Workflow Skills

Workflow skills automate common workflow operations.

### /openup-assess-completeness

Rubric-based readiness assessment before task completion or phase transition

**Model**: `inherit`

**Fit**:
- Great fit: pre-merge quality gate, phase transitions, artifact rubric grading
- OK fit: mid-iteration sanity checks on partially-built artifacts
- Poor fit: pure code changes with no rubric to grade against, exploratory work

**Arguments**:
- `scope` (optional) — Assessment scope (task, iteration, phase)
- `artifact` (optional) — Work product type to assess against its rubric (use-case, architecture-notebook, iteration-plan, test-plan, vision). Auto-detected if not provided.
- `strict` (optional) — Fail on any missing items (true/false, default: false)

**See Also**: `openup-complete-task` · `openup-retrospective` · `openup-phase-review`

### /openup-assess-iteration

Run OpenUP Assess Results at iteration end — check evaluation criteria, demo only completed acceptance-tested work, feed discovered work back, and trigger the milestone review at a phase boundary

**Model**: `sonnet`

**When NOT to Use**

- A single lane finished → `/openup-complete-task` (this assesses the *whole
  iteration*, after all its lanes are complete).
- The iteration still has unfinished work items → keep working them (`resolve`
  would return `pick`/`resume`, not `assess-iteration`).
- Whole-project reflection / cadence retro → `/openup-retrospective` (this skill
  *composes* it for the retro half — see step 5 — rather than replacing it).

**Success Criteria**

- [ ] The iteration-plan instance's **evaluation criteria** are each graded met /
      unmet against repo evidence.
- [ ] The demo scope lists **only completed, acceptance-tested** work items;
      anything incomplete or untested is excluded and re-queued.
- [ ] Discovered work / defects are enqueued as pending roadmap items.
- [ ] An **`## Assessment`** section is written into the iteration-plan instance
      (the assessed marker `resolve` reads to stop re-offering this path).
- [ ] If the Development Case marks the phase's exit criteria met, the next move
      named is `/openup-phase-review` — the phase is **not** advanced here.

**Fit**:
- Great fit: closing a phase-aware iteration, the loop's convergence step, deciding whether a phase is ready for its milestone
- OK fit: a human manually assessing an iteration mid-program
- Poor fit: single-task wrap-ups (use /openup-complete-task), the whole-project retro (use /openup-retrospective), planning the next iteration (use /openup-start-iteration)

**Arguments**:
- `iteration_id` (optional) — The minted iteration to assess (e.g. C3). Optional — the board's assess-iteration decision supplies it; omit to assess the active iteration.

**See Also**: `openup-next` · `openup-phase-review` · `openup-retrospective` · `openup-create-iteration-plan`

### /openup-complete-task

Mark a task as complete, update roadmap, commit changes, and prepare traceability logs

**Model**: `inherit`

**Success Criteria**

After this skill completes, ALL of these must be true:

- [ ] **BLOCKING**: Every spec requirement is graded ✅ against the actual diff (step 1a) — no requirement is unmet, and any ❌ blocks "done"
- [ ] **BLOCKING (standard/full)**: The spec's Success Measure instrumentation exists in the diff or demonstrably pre-exists (step 1b) — or the section is an argued `n/a`
- [ ] **BLOCKING (flagged features)**: A flag-removal task row exists in the roadmap Maintenance table (step 4a) — every flag enqueues its own removal
- [ ] All changes are committed (no uncommitted changes remain)
- [ ] Commit messages follow canonical format: `type(scope): description [T-XXX]`
- [ ] **BLOCKING**: Branch is rebased onto the current trunk and the write-fence
      passes (`openup-fence.py check` exit 0) — no out-of-lane files, no stale views
- [ ] **BLOCKING (T-038)**: `python3 scripts/check-docs.py` exits 0 — every
      authored work-product instance has valid frontmatter, resolvable trace
      refs, and resolvable relative links
- [ ] Iteration note written as a sharded file under `docs/status-notes/`
- [ ] Roadmap + project status regenerated via `scripts/sync-status.py` (never hand-edited)
- [ ] Traceability logs are created with commit SHAs
- [ ] Iteration learnings entry appended to `.claude/memory/iteration-learnings.md`
- [ ] Iteration gates pass (`openup-state.py check-gates`) and state is archived
- [ ] PR is created (unless `create_pr` was explicitly `"false"`)

**Fit**:
- Great fit: finishing a roadmap-tracked task, ending an iteration cleanly
- OK fit: closing out ad-hoc work that needs commit + roadmap update
- Poor fit: mid-task checkpoints, abandoning work-in-progress

**Arguments**:
- `task_id` (required) — The task ID to mark as complete (e.g., T-001)
- `commit_message` (optional) — Custom commit message (optional, auto-generates if not provided)
- `create_pr` (optional) — Create a pull request after completing the task (default: true — set to 'false' to skip)

**See Also**: `openup-create-pr` · `openup-log-run` · `openup-start-iteration`

### /openup-create-handoff

Produce a handoff brief (acceptance criteria, test cases, troubleshooting, open questions) for a change, so the next owner can pick it up cold

**Model**: `haiku`

**Fit**:
- Great fit: pausing mid-task for another owner, end-of-iteration handoff, "someone else finishes this" moments
- OK fit: recording how to exercise a finished feature before completion, capturing open questions surfaced during work
- Poor fit: the durable run log (use openup-log-run), the spec itself (that is the change-folder plan.md)

**Arguments**:
- `task_id` (required) — The task ID whose change folder to summarize (e.g., T-011). Required.
- `audience` (optional) — Optional. Who is receiving the handoff (e.g. 'next session', 'tester', 'reviewer') — tunes emphasis. Defaults to the next agent/owner.

**See Also**: `openup-complete-task` · `openup-log-run` · `openup-readiness`

### /openup-create-pr

Create a pull request with proper description linking to roadmap task context

**Model**: `sonnet`

**Fit**:
- Great fit: shipping a finished task, opening a review-ready PR
- OK fit: WIP / draft PRs for early feedback
- Poor fit: pre-merge to local-only branches, work not yet committed

**Arguments**:
- `task_id` (optional) — The task ID from roadmap (e.g., T-001). Auto-detected from branch name if not provided.
- `branch` (optional) — The branch to create PR from. Uses current branch if not provided.
- `title` (optional) — Custom PR title. Auto-generated from task if not provided.
- `base` (optional) — Base branch to merge into (e.g., main, develop). Auto-detected if not provided.

**See Also**: `openup-complete-task` · `openup-start-iteration`

### /openup-cycle

Execute an already-claimed lane's Operations boxes with script/judgment classification — script steps run directly with zero self-brief, judgment steps self-brief and execute. Handles only pick/resume; every other resolve path routes to /openup-next.

**Model**: `inherit`

**Success Criteria**

After this skill completes, ALL of these must be true:
- [ ] `openup-board.py resolve` was called once. If `.path` is not `pick` or
      `resume`, the cycle routed to `/openup-next` and stopped — it did not
      attempt to plan, assess, or replenish.
- [ ] A `resume` carrying `resumable_input` folded the answer into the spec via
      `/openup-create-task-spec` (fix-spec-first) before any box ran.
- [ ] Every Operations box that ran was gated (fence + check-docs) before its
      checkbox was ticked; a gate failure left the box unticked and stopped the
      cycle.
- [ ] The cycle exited through `/openup-complete-task` or
      `/openup-create-handoff` — never a raw commit, never a third path.

**Fit**:
- Great fit: advancing a lane whose Operations boxes are mostly mechanical script calls, an outer loop repeating pure delivery cycles once planning is done, minimizing self-brief overhead on gate/sync/scaffold-heavy lanes
- OK fit: a lane with a mix of script and judgment boxes
- Poor fit: no active lane and nothing pickable — use /openup-next (needs plan-iteration), an iteration needing assess-iteration or milestone-review — use /openup-next, a stuck backlog needing consent-gated replenishment — use /openup-next

**Arguments**:
- `task_id` (optional) — Optional. Force a specific lane instead of the board's top pick (must still be pickable). Omit to take the top READY collision-free lane.

**See Also**: `openup-next` · `openup-start-iteration` · `openup-complete-task` · `openup-create-handoff` · `openup-create-task-spec`

### /openup-deploy-team

Deploy an OpenUP agent team to work on the current iteration

**Model**: `haiku`

**When to Use**

Use this skill **after** `/openup-start-iteration` has completed:
- Iteration is initialized
- Branch is created
- Project status is updated
- Roadmap has the task

Then use this skill to deploy the team.

**When NOT to Use**

Do NOT use this skill:
- Before `/openup-start-iteration` has been called
- Without knowing the iteration goal
- For non-OpenUP work

**Arguments**:
- `team_type` (optional) — Type of team to create (feature, investigation, construction, elaboration, inception, transition, planning, full)
- `roles` (optional) — Specific roles to include (analyst, architect, developer, tester, project-manager). Comma-separated.

**See Also**: `openup-start-iteration` · `openup-complete-task` · `Team configurations`

### /openup-doctor

Read-only project health check — framework/manifest drift, .openup/state.json integrity, and aggregation of existing --check validators

**Model**: `haiku`

**Fit**:
- Great fit: "downstream maintainer asking is my OpenUP install current and unmodified", "pre-flight health check on a fresh clone or in CI without the git hooks", "diagnosing a corrupt/misnamed .openup/state.json footgun"
- OK fit: "a quick is-this-project-well-formed sweep before starting work"
- Poor fit: "fixing anything (doctor is strictly diagnostic — fixes live in sync-from-framework.sh / the owning generators)", "what can I work on next (that is /openup-readiness)"

**Arguments**:
- `framework_path` (optional) — Optional. Path to a framework baseline clone. Enables byte-level CLI drift detection; without it doctor degrades to version-only (offline).

**See Also**: `openup-readiness`

### /openup-explore

Sanctioned pre-iteration mode — think through ideas, investigate problems, sketch options before committing to delivery

**Model**: `inherit`

**When to Use**

- Investigating whether a problem is real before scoping a fix
- Comparing two or three approaches before picking one
- Reading an external framework / codebase and capturing what's worth borrowing
- Drafting an RFC-style argument that may not survive review

**When NOT to Use**

- Known small change → `/openup-quick-task`
- Scoped delivery work → `/openup-start-iteration`
- Anything that produces code intended to ship (exploration code is throwaway)

**Success Criteria**

- [ ] File exists at `docs/explorations/YYYY-MM-DD-<slug>.md`
- [ ] A `### Product-manager challenge pass` section exists, and every
      challenge in it is either accepted into the notes or explicitly
      rejected with a reason (no team was deployed to produce it — role
      hat only)
- [ ] File ends with a "Where this goes next" section naming exactly one
      disposition: `→ iteration`, `→ quick-task`, or `→ dropped`
- [ ] If disposition is `→ iteration` or `→ quick-task`, the follow-up is
      named in one sentence
- [ ] If disposition is `→ dropped`, the reason is stated

**Fit**:
- Great fit: is this problem real?, comparing approaches before scoping, ruling out designs, evaluating external frameworks
- OK fit: reproducing an ambiguous bug before filing it, drafting RFC-style notes that may or may not lead to work
- Poor fit: known small change (use /openup-quick-task), scoped delivery work (use /openup-start-iteration), running experiments that produce code intended to ship

**Arguments**:
- `slug` (required) — Short kebab-case slug for the exploration topic (e.g. "openspec-borrow-analysis"). Used in the filename.
- `append` (optional) — If true, append to today's existing exploration file with this slug instead of creating a new one (default: false)

**See Also**: `openup-start-iteration` · `openup-quick-task`

### /openup-fan-out

Dispatch one background subagent per collision-free READY lane, then collect their ≤6-bullet summaries. The caller's interactive session remains free. Requires T-060 heartbeat+reaper and T-059 sentinel output.

**Model**: `inherit`

**When to Use**

- Board has ≥2 READY lanes with disjoint `touches` surfaces.
- You want background parallelism without tying up your interactive session.
- You want wall-clock time ≈ `max(cycle_time)` rather than `sum(cycle_times)`.

**When NOT to Use**

- Only one READY lane exists → use `/openup-next` directly.
- Lanes share surfaces → the board already serializes them; fan-out cannot help.
- You want step-by-step visibility in your session → use `/openup-next` interactively.
- You need to watch each step for a correctness review → fan-out transcripts are isolated.

**Success Criteria**

- [ ] `reap --dry-run` was run and any stale claims were confirmed and reaped.
- [ ] `top-n` was called to get the collision-free partition; exit 3 was handled as a
      clean stop.
- [ ] One background Agent was dispatched per lane with `task_id:` forced and
      NO `isolation: "worktree"`.
- [ ] Summaries were collected from all subagents; crashed lanes were flagged.
- [ ] The parent session received a ≤6-bullet summary per lane.
- [ ] Total tokens consumed by the parent session (reap + top-n + dispatch +
      collect) stayed under 10k (subagent transcripts are isolated).

**Arguments**:
- None

**See Also**: `openup-next` · `parallel-lanes.md`

### /openup-init

One-command project setup for OpenUP - interactive initialization wizard

**Model**: `inherit`

**When to Use**

Use this skill when:
- Starting a new OpenUP project
- Setting up OpenUP in an existing repository
- Need quick project initialization without manual steps

**When NOT to Use**

Do NOT use this skill when:
- Project is already initialized (use phase skills instead)
- Need to customize individual components (manual setup recommended)

**Success Criteria**

After using this skill, verify:
- [ ] Project structure is created
- [ ] Initial documents are generated
- [ ] Agent teams are configured (if enabled)
- [ ] Git is initialized (if needed)

**Arguments**:
- `project_name` (optional) — The project name (optional, will prompt if not provided)
- `project_type` (optional) — Type of project: web, api, library, mobile (optional, will prompt if not provided)
- `skip_teams` (optional) — Skip agent team setup (default: false)

**See Also**: `openup-inception` · `openup-create-vision` · `Agent Teams Setup`

### /openup-log-run

Create traceability logs (markdown + JSONL) for the current agent run

**Model**: `haiku`

**Fit**:
- Great fit: end-of-session wrap-up after commits, audit-required workflows
- OK fit: mid-session checkpoints when commits exist
- Poor fit: pre-commit runs (no SHAs to log), trivial sessions handled by hooks

**Arguments**:
- `run_id` (optional) — Unique identifier for this run (optional, auto-generates if not provided)

**See Also**: `openup-complete-task` · `openup-start-iteration`

### /openup-next

Run ONE OpenUP delivery cycle — resume the active iteration if one stopped mid-work, else claim the top READY lane, else promote the next pending roadmap task and start it. Always advances; only no-ops when nothing is left to do. The sequential continue-loop.

**Model**: `inherit`

**Success Criteria**

After this skill completes, ALL of these must be true:
- [ ] `openup-board.py resolve` was called once to decide the cycle; on a
      `resume` with `resumable_input`, the answered lane was resumed (answers
      folded into the spec, lane un-suspended, request archived) before a new
      lane was claimed.
- [ ] Exactly one lane was advanced this cycle — by **resuming** the active
      iteration, **claiming** a READY lane, or **promoting** the next pending
      roadmap task into a new lane and starting it — OR the skill stopped cleanly
      because there was genuinely nothing to do (no lane pickable AND no pending
      roadmap task to promote).
- [ ] The Operations checkboxes for completed steps are ticked in the lane's
      `plan.md`.
- [ ] The cycle exited through `/openup-complete-task` **or**
      `/openup-create-handoff` — never a raw commit, never a third path.
- [ ] No information required to resume lives only in the conversation.

**Fit**:
- Great fit: driving delivery one session at a time, an outer /loop or cron repeatedly advancing the roadmap, "just do the next thing", resuming a mid-cycle task, promoting the next roadmap line into a workable lane
- OK fit: starting the very next iteration from a roadmap that has no change folders yet
- Poor fit: picking a SPECIFIC task out of PM order (use /openup-start-iteration directly), open-ended exploration with no roadmap line (use /openup-explore)

**Arguments**:
- `task_id` (optional) — Optional. Force a specific lane instead of the board's top pick (must still be pickable). Omit to take the top READY collision-free lane.

**See Also**: `openup-start-iteration` · `openup-complete-task` · `openup-create-handoff` · `openup-readiness` · `openup-request-input`

### /openup-orchestrate

Run a full orchestrated iteration — PM decomposes the goal, delegates to specialist roles, collects outputs, and synthesizes results

**Model**: `inherit`

**Fit**:
- Great fit: complex multi-role tasks, architecture+impl+test cycles, anything benefiting from role isolation
- OK fit: medium tasks where decomposition aids token-efficiency
- Poor fit: trivial changes, single-role work, hotfixes — heavyweight overkill

**Arguments**:
- `task_id` (required) — The task ID to orchestrate (must match a task in docs/roadmap.md)
- `team` (optional) — Team type to use (feature, construction, elaboration, inception, transition, investigation, planning, full). Auto-selected from phase if not provided.
- `dry_run` (optional) — Preview the orchestration plan without spawning teammates (true/false, default: false)

**See Also**: `openup-start-iteration` · `openup-assess-completeness` · `openup-complete-task` · `openup-deploy-team`

### /openup-phase-review

Run the phase milestone go/no-go — prepare derived evidence, pause for the human decision via an input-request, and record the milestone (never advance the phase itself)

**Model**: `inherit`

**When NOT to Use**

- Just starting a phase → the phase skill (`/openup-inception` …).
- A lane finished / iteration to assess → `/openup-complete-task` /
  `/openup-assess-iteration` (assess-iteration is what *precedes* and triggers
  this at a phase boundary).
- The phase is clearly not done → keep delivering; `resolve` returns
  `plan-iteration`, not `milestone-review`, until the roadmap is drained and the
  exit criteria are met.

**Success Criteria**

- [ ] The phase + cycle and per-criterion state are read from
      `openup-lifecycle.py status` (derived, not hand-judged).
- [ ] A milestone **input-request** carries the go/no-go to the human; the loop
      exits DONE ("milestone-review pending human input") while it is unanswered.
- [ ] On an answered **GO**, `docs/product/milestones/<phase>-<cycle>.md` is
      written; the phase is **not** set directly.
- [ ] On **NO-GO / CONDITIONAL**, the decision is recorded and the follow-on work
      is re-queued (Construction resumes in `cycle`+1 on NO-GO).
- [ ] The request is archived after it is processed.

**Fit**:
- Great fit: end-of-phase milestone go/no-go, the loop's milestone-review pause, recording a stakeholder LCO/LCA/IOC/PR decision
- OK fit: a human mid-phase sanity check on completion criteria
- Poor fit: within-iteration progress checks, single-task decisions, planning the next iteration (use /openup-start-iteration)

**Arguments**:
- `phase` (optional) — The phase to review (optional — derived from openup-lifecycle.py when omitted)

**See Also**: `openup-assess-iteration` · `openup-request-input` · `openup-next`

### /openup-plan-feature

Generate iteration plan and roadmap entry for a feature idea

**Model**: `sonnet`

**When to Use**

Use this skill when:
- You have a new feature idea and need a detailed implementation plan
- You want to add a feature to the roadmap with a plan document
- You need to explore the codebase to understand what a feature will touch before coding
- Planning an iteration task from a high-level description

**When NOT to Use**

Do NOT use this skill when:
- The feature already has an iteration plan (edit it directly)
- You need to start implementing (use `/openup-start-iteration`)
- The task is a quick fix or bug fix (use `/openup-quick-task`)
- You only need to update the roadmap without a plan (edit `docs/roadmap.md` directly)

**Success Criteria**

After using this skill, verify:
- [ ] Iteration plan file exists at `docs/iteration-plans/{task_id}-{slug}.md`
- [ ] Plan includes Current State with actual code excerpts from the codebase
- [ ] Plan includes Proposed Design with concrete code examples
- [ ] Plan includes Acceptance Criteria, Dependencies, and Key Files
- [ ] Roadmap entry exists in `docs/roadmap.md` with correct format
- [ ] PR is created (if `create_pr` is true)

**Fit**:
- Great fit: turning a fresh feature idea into a roadmap entry + plan
- OK fit: re-planning when scope shifts mid-flight
- Poor fit: already-scoped tasks with a plan (skip to start-iteration), trivial fixes

**Arguments**:
- `topic` (required) — The feature idea or requirements to plan (e.g., "Add PDF export for chat conversations")
- `task_id` (optional) — Override the task ID (e.g., C3-004). Reserved via `openup-claims.py reserve-id` if not provided.
- `priority` (optional) — Task priority — critical, high, or medium (default medium)
- `validate` (optional) — Spawn analyst + architect team to review the plan before finalizing (default false)
- `create_pr` (optional) — Create branch, commit, push, and open a PR (default true)

**See Also**: `openup-start-iteration` · `openup-create-iteration-plan` · `openup-complete-task` · `openup-create-pr`

### /openup-quick-task

Fast iteration mode for small changes - simplified workflow with minimal overhead

**Model**: `inherit`

**When to Use**

Use Quick Task for:
- Small bug fixes (< 50 lines changed)
- Documentation updates
- Configuration changes
- Quick experiments
- Hot fixes

**When NOT to Use**

Do NOT use for:
- New features (use standard workflow)
- Major refactoring (use `/openup-start-iteration`)
- Tasks requiring architecture review (use full team)
- Multi-hour development work

**Success Criteria**

- [ ] Task completed
- [ ] Changes verified
- [ ] Branch created (if not skipped)
- [ ] Committed (if not skipped)
- [ ] Logged (if not skipped)

**Fit**:
- Great fit: typo fixes, doc updates, single-file config tweaks, hotfixes
- OK fit: small bug fixes under ~50 LOC, single-component refactors
- Poor fit: new features, multi-role work, architectural changes, anything needing a rubric

**Arguments**:
- `task` (required) — Brief description of the task to complete
- `task_id` (optional) — Roadmap task ID (optional, creates task if not provided)
- `skip_branch` (optional) — Skip branch creation (default: false)
- `skip_commit` (optional) — Skip auto-commit (default: false)
- `skip_logging` (optional) — Skip traceability logging (default: false)

**See Also**: `openup-start-iteration` · `openup-complete-task` · `openup-tdd-workflow`

### /openup-readiness

Compute the change-folder dependency DAG and print READY/BLOCKED/collision report for PM intake

**Model**: `haiku`

**Fit**:
- Great fit: PM intake "what can I start next", dependency-reason lookups, collision pre-flight before claiming
- OK fit: mid-iteration "is T-NNN unblocked yet" checks
- Poor fit: editing frontmatter (this skill is read-only), live worktree-claim enforcement (that is T-009)

**Arguments**:
- `task_id` (optional) — Optional. If given, report only this task's readiness and the reason chain; otherwise report all tasks.

**See Also**: `openup-start-iteration` · `openup-complete-task`

### /openup-request-input

Create an input request document for asynchronous stakeholder communication

**Model**: `haiku`

**Fit**:
- Great fit: blocked tasks needing a human decision, ambiguous requirements
- OK fit: scope/priority clarifications mid-iteration
- Poor fit: questions with obvious answers, internal-only decisions, urgent same-session needs

**Arguments**:
- `title` (required) — Descriptive title for the request
- `questions` (required) — JSON array of questions (type, question_text, options for multiple-choice)
- `context` (required) — Additional context about what the agent is doing
- `related_task` (optional) — Optional roadmap task ID (e.g., T-001)

**See Also**: `openup-start-iteration` · `openup-complete-task`

### /openup-retrospective

Generate iteration retrospective with feedback and action items

**Model**: `sonnet`

**Fit**:
- Great fit: end-of-iteration reflection, capturing patterns to feed forward
- OK fit: mid-iteration when blockers pile up and a reset is needed
- Poor fit: single-task wrap-ups (use complete-task notes), trivial iterations

**Arguments**:
- `iteration_number` (optional) — Iteration to review (optional, defaults to current)
- `include_metrics` (optional) — Include git metrics (true/false, default: true)

**See Also**: `openup-start-iteration` · `openup-complete-task` · `openup-assess-completeness` · `openup-create-iteration-plan`

### /openup-start-iteration

Begin a new OpenUP iteration with proper phase context and task selection

**Model**: `haiku`

**Success Criteria**

After this skill completes, ALL of these must be true:

- [ ] **BLOCKING (full track only, when a team is requested)**: If the `full` track (or an explicit `team:` / `deploy_team: true`) calls for a team, it is deployed and coordinating before implementation begins. `quick` and `standard` default to solo sequential work — no team required.
- [ ] Project status is updated with new iteration
- [ ] **BLOCKING**: `git rev-parse --abbrev-ref HEAD` returns a non-trunk branch name. If it returns trunk, stop and report — do not proceed.
- [ ] Iteration goal is defined
- [ ] Answered input requests are processed
- [ ] Log entry is created
- [ ] `.openup/state.json` created

**Fit**:
- Great fit: feature work, multi-step tasks, anything needing a deployed team
- OK fit: single-component changes that benefit from explicit iteration framing
- Poor fit: typo fixes, hotfixes, exploratory spikes, throwaway scripts

**Arguments**:
- `iteration_number` (optional) — The iteration number (optional, auto-increments if not provided)
- `goal` (optional) — The iteration goal (optional, reads from project-status if not provided)
- `task_id` (required) — The task ID from roadmap to work on (required for task-based branching)
- `track` (optional) — Ceremony track (quick|standard|full). Optional — auto-selected from scope when omitted. quick = docs/config/typo/≤~50 LOC single file (state + auto-log only, no plan gate, no team, no readiness); standard = single-feature (plan gate + scribe + /openup-readiness, solo by default — team opt-in); full = multi-role/architectural (standard + team default-on, opt-out + rubric at complete-task). See tracks.md.
- `team` (optional) — Team type to automatically deploy after initialization (feature, investigation, construction, elaboration, inception, transition, planning, full, or none)
- `deploy_team` (optional) — Whether to deploy a team after iteration initialization (true/false/auto, default: auto — deploy only on the full track; skip on quick/standard. Pass 'true' to force a team, 'false' to force solo)
- `worktree` (optional) — Whether to create an isolated git worktree for this task (true/false, default: true — pass 'false' for a legacy in-place checkout). See T-009 / parallel-work.md.

**See Also**: `openup-next` · `openup-complete-task` · `openup-create-iteration-plan`

### /openup-sync-spec

Back-propagate pure refactors to stale artifacts; classify the diff, refuse behaviour-changes, propose targeted edits for approval (read-only by default)

**Model**: `inherit`

**Success Criteria**

After this skill runs, ALL of these must be true:

- [ ] The diff was classified REFACTOR or BEHAVIOUR-CHANGE by the documented heuristic.
- [ ] A BEHAVIOUR-CHANGE (or ambiguous) verdict produced the refusal + routing and
      wrote nothing.
- [ ] For a REFACTOR, only sections naming changed files/symbols were flagged; no whole
      document was regenerated.
- [ ] No artifact was written without explicit user approval.
- [ ] `last-synced` was bumped to `HEAD` **only** on artifacts whose edits were applied
      this run, in the same approved scribe batch as the section edits.
- [ ] Never-synced artifacts were reported (no auto-edit) unless the user asked to set a
      baseline.

**Fit**:
- Great fit: reconciling artifacts after a rename/extract/move refactor, "did my cleanup leave the spec stale", detecting + routing behaviour-changes back to spec-first
- OK fit: setting a fresh last-synced baseline on a never-synced artifact, single-artifact sync after a targeted diff
- Poor fit: authoring new behaviour spec-first (use the originating /openup-create-* skill), wholesale doc regeneration, applying writes without user approval

**Arguments**:
- `since` (optional) — Optional. Diff baseline — a git ref or \"last commit\". Defaults to each artifact's own last-synced front-matter SHA; falls back to never-synced handling when unset.
- `artifact` (optional) — Optional. Restrict the run to one artifact type (use-case-specification | architecture-notebook | iteration-plan | task-spec). Defaults to all four candidates.

**See Also**: `openup-complete-task` · `openup-readiness`

### /openup-tdd-workflow

Guide Test-Driven Development cycle adapted for AI agents with a pragmatic approach

**Model**: `inherit`

**Success Criteria**

- [ ] Tests are written (preferably before implementation)
- [ ] Implementation makes tests pass
- [ ] Code is reasonably clean and functional
- [ ] Tests pass before commit

**Fit**:
- Great fit: well-specified features with a clear test surface, regression bug fixes (start with failing repro)
- OK fit: refactors with strong existing test coverage
- Poor fit: exploratory spikes, prototyping, UI-only tweaks, throwaway scripts

**Arguments**:
- `phase` (optional) — TDD phase (red, green, refactor, full)
- `feature` (required) — Feature or component to implement

**See Also**: `openup-create-test-plan` · `openup-complete-task` · `openup-detail-use-case`
<!-- END GENERATED: skill-reference -->

## Executable Scripts

OpenUP skills include executable Python scripts for common operations:

### parse-project-status.py

Extract phase, iteration, and goals from project-status.md.

```bash
python docs-eng-process/.claude-templates/skills/scripts/parse-project-status.py
```

### parse-roadmap.py

Extract task information from roadmap.md.

```bash
python docs-eng-process/.claude-templates/skills/scripts/parse-roadmap.py
python docs-eng-process/.claude-templates/skills/scripts/parse-roadmap.py --task T-005
```

### validate-commit.py

Verify git commit success and return commit information.

```bash
python docs-eng-process/.claude-templates/skills/scripts/validate-commit.py
```

### detect-trunk.py

Detect trunk branch name using git commands.

```bash
python docs-eng-process/.claude-templates/skills/scripts/detect-trunk.py
```

## Skill Composition

Skills can be combined for complex workflows. For example:

```
/openup-start-iteration goal: "Implement user authentication"
Create an OpenUP agent team for feature implementation.
/openup-complete-task task_id: T-005 create_pr: true
/openup-log-run
```

## Skill Index

Every available skill, grouped. Generated by `scripts/check-skills-guide.py`.

<!-- BEGIN GENERATED: skill-index (scripts/check-skills-guide.py) -->
| Skill | Group | What it does |
|-------|-------|--------------|
| `/openup-construction` | Phase | Initialize and manage Construction phase activities - build the system incrementally |
| `/openup-elaboration` | Phase | Initialize and manage Elaboration phase activities - establish architecture baseline |
| `/openup-inception` | Phase | Initialize and manage Inception phase activities - define scope, vision, and feasibility |
| `/openup-transition` | Phase | Initialize and manage Transition phase activities - deploy to users |
| `/openup-create-architecture-notebook` | Artifact | Generate or update architecture documentation from template |
| `/openup-create-documentation` | Artifact | Generate human-readable documentation from code and artifacts |
| `/openup-create-iteration-plan` | Artifact | Plan iteration based on current state and roadmap |
| `/openup-create-risk-list` | Artifact | Create or update risk assessment document from template |
| `/openup-create-task-spec` | Artifact | Produce a REASONS-Canvas task spec from a roadmap line or feature description, ready for developer-role consumption |
| `/openup-create-test-plan` | Artifact | Generate test cases and test plan from use cases and requirements |
| `/openup-create-use-case` | Artifact | Create a use case specification from template |
| `/openup-create-vision` | Artifact | Generate a vision document from template |
| `/openup-detail-use-case` | Artifact | Transform a high-level use case into detailed scenarios with test cases |
| `/openup-shared-vision` | Artifact | Create shared technical vision for team alignment |
| `/openup-assess-completeness` | Workflow | Rubric-based readiness assessment before task completion or phase transition |
| `/openup-assess-iteration` | Workflow | Run OpenUP Assess Results at iteration end — check evaluation criteria, demo only completed acceptance-tested work, feed discovered work back, and trigger the milestone review at a phase boundary |
| `/openup-complete-task` | Workflow | Mark a task as complete, update roadmap, commit changes, and prepare traceability logs |
| `/openup-create-handoff` | Workflow | Produce a handoff brief (acceptance criteria, test cases, troubleshooting, open questions) for a change, so the next owner can pick it up cold |
| `/openup-create-pr` | Workflow | Create a pull request with proper description linking to roadmap task context |
| `/openup-cycle` | Workflow | Execute an already-claimed lane's Operations boxes with script/judgment classification — script steps run directly with zero self-brief, judgment steps self-brief and execute. Handles only pick/resume; every other resolve path routes to /openup-next. |
| `/openup-deploy-team` | Workflow | Deploy an OpenUP agent team to work on the current iteration |
| `/openup-doctor` | Workflow | Read-only project health check — framework/manifest drift, .openup/state.json integrity, and aggregation of existing --check validators |
| `/openup-explore` | Workflow | Sanctioned pre-iteration mode — think through ideas, investigate problems, sketch options before committing to delivery |
| `/openup-fan-out` | Workflow | Dispatch one background subagent per collision-free READY lane, then collect their ≤6-bullet summaries. The caller's interactive session remains free. Requires T-060 heartbeat+reaper and T-059 sentinel output. |
| `/openup-init` | Workflow | One-command project setup for OpenUP - interactive initialization wizard |
| `/openup-log-run` | Workflow | Create traceability logs (markdown + JSONL) for the current agent run |
| `/openup-next` | Workflow | Run ONE OpenUP delivery cycle — resume the active iteration if one stopped mid-work, else claim the top READY lane, else promote the next pending roadmap task and start it. Always advances; only no-ops when nothing is left to do. The sequential continue-loop. |
| `/openup-orchestrate` | Workflow | Run a full orchestrated iteration — PM decomposes the goal, delegates to specialist roles, collects outputs, and synthesizes results |
| `/openup-phase-review` | Workflow | Run the phase milestone go/no-go — prepare derived evidence, pause for the human decision via an input-request, and record the milestone (never advance the phase itself) |
| `/openup-plan-feature` | Workflow | Generate iteration plan and roadmap entry for a feature idea |
| `/openup-quick-task` | Workflow | Fast iteration mode for small changes - simplified workflow with minimal overhead |
| `/openup-readiness` | Workflow | Compute the change-folder dependency DAG and print READY/BLOCKED/collision report for PM intake |
| `/openup-request-input` | Workflow | Create an input request document for asynchronous stakeholder communication |
| `/openup-retrospective` | Workflow | Generate iteration retrospective with feedback and action items |
| `/openup-start-iteration` | Workflow | Begin a new OpenUP iteration with proper phase context and task selection |
| `/openup-sync-spec` | Workflow | Back-propagate pure refactors to stale artifacts; classify the diff, refuse behaviour-changes, propose targeted edits for approval (read-only by default) |
| `/openup-tdd-workflow` | Workflow | Guide Test-Driven Development cycle adapted for AI agents with a pragmatic approach |
<!-- END GENERATED: skill-index -->

## References

- Skills are located in: `docs-eng-process/.claude-templates/skills/`
- Templates are located in: `docs-eng-process/templates/`
- Executable scripts are in: `docs-eng-process/.claude-templates/skills/scripts/`
- Agent Workflow: `docs-eng-process/agent-workflow.md`
- Graded ceremony tracks (quick / standard / full): [`docs-eng-process/tracks.md`](tracks.md) — how `/openup-start-iteration` and `/openup-quick-task` pick a track and what ceremony each applies.
- Anthropic Agent Skills Framework: https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills

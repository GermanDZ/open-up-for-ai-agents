# Agent Workflow - Complete Operating Procedures

**⚠️ STRICT PROCESS: This document defines mandatory procedures for AI agents. Follow these procedures exactly. If the process blocks progress, log the issue in `docs/` and proceed only as allowed by the workflow.**

## Table of Contents

1. [Start-of-Run SOP](#start-of-run-sop)
2. [Role-Based Execution SOP](#role-based-execution-sop)
3. [Self-Critique SOP (Planning & Specification)](#self-critique-sop-planning--specification)
4. [User Communication SOP](#user-communication-sop)
5. [Asynchronous Input SOP](#asynchronous-input-sop)
6. [Branching SOP](#branching-sop)
7. [Docs Update SOP](#docs-update-sop)
8. [Traceability Logging SOP](#traceability-logging-sop)
9. [End-of-Run SOP](#end-of-run-sop)
10. [Project Status Definition](#project-status-definition)
11. [Skills and Teams Integration](#skills-and-teams-integration)

---

## Start-of-Run SOP

**Every agent run MUST begin with these steps in order:**

### Step 0: Check for Answered Input Requests

Before proceeding with normal workflow, check for answered input requests:

- Check `docs/input-requests/` directory for files with `status: answered` in frontmatter
- If answered requests exist:
  1. Process them in chronological order (oldest first)
  2. Read all answers from each request
  3. Use the information to continue the related task
  4. Update the request's `status` to `processed` in frontmatter
  5. Move the file to `docs/input-requests/archive/`
  6. Log the processing in the agent-run log
- After processing all answered requests, continue with normal start-of-run steps

**Note**: If the user explicitly asks to process input requests (e.g., "Continue with input-requests"), prioritize this step and process all answered requests before selecting new tasks.

### Step 1: Read Project Status and Learnings

Read `docs/project-status.md` to establish context:

- Extract `phase` (inception | elaboration | construction | transition)
- Extract `iteration` (current iteration number)
- Extract `iteration_goal` (what this iteration should achieve)
- Extract `status` (not-started | in-progress | blocked | completed)

Also read `.claude/memory/iteration-learnings.md` if it exists — scan for gotchas, decisions, and conventions from past iterations that apply to the current task. This is your institutional memory; don't repeat mistakes or redo decisions already made.

**If `status == blocked`**:
- Report all blockers to the user
- Request guidance before proceeding
- Do not proceed until blockers are resolved or explicitly overridden

**If `status == completed`**:
- Check if next phase should be started
- Propose phase transition to user
- **Do NOT automatically advance phase** (requires human approval)

### Step 2: Check for Pending Plans

If `docs/plans/` exists, check for plan files that have been saved but not yet started:

- Look for entries in `docs/roadmap.md` with `status: planned` that link to a file in `docs/plans/`
- For any such entry, **read the linked plan file** — it contains the full implementation plan created in a prior session
- When starting work on a planned task, treat the plan file as the authoritative spec: the decomposition, approach, and file list are already decided — do not re-plan

This is the mechanism for cross-session continuity: plan in one session, implement in another without losing context.

### Step 3: Read Roadmap and Select Task

Read `docs/roadmap.md` and select the next task:

- Filter tasks by `status == pending`
- If multiple possible targets and not specified: choose the **highest priority** task
- Priority tie-breakers (in order):
  1. Tasks explicitly marked as high priority
  2. Tasks blocking other work
  3. Tasks aligned with current `iteration_goal`
  4. Tasks with earliest due date
  5. First task in the list

### Step 4: Verify Phase Context

Ensure the selected task aligns with:
- Current `phase` from `docs/project-status.md`
- Current `iteration_goal` from `docs/project-status.md`

If the task doesn't fit:
- Log as out-of-scope in the agent-run log
- Request user approval or defer to backlog
- Do not proceed without explicit approval

### Step 4.5: Select Workflow Depth (Task-Size Gate)

Before branch/task execution, choose the lightest valid workflow:

- **Tiny, low-risk changes** (small docs/config/bug fix): use `/openup-quick-task` when allowed by project policy
- **Normal implementation tasks**: use `/openup-complete-task` for integrated commit + docs + logging
- **Iteration/phase-level work**: use full SOP + phase skills

**Goal**: reduce overhead while preserving required traceability for the scope of work.

### Step 5: Create Branch (if needed)

**MANDATORY**: Before starting any work, ensure you are on an appropriate branch. Never work directly on trunk. New tasks must start on a clean branch (either trunk or a branch that has been merged to trunk).

1. **Detect trunk branch** using this algorithm:
   - Prefer `origin/HEAD` if present locally
   - Else fall back to `main`
   - Else fall back to `master`
   - Else use current branch

2. **Check branch lifecycle** (see [Branching SOP](#branching-sop) for details):
   - If `current branch == trunk`: Proceed to step 3 to create a new branch
   - If `current branch != trunk`: Check for unmerged commits using `git log <trunk>..HEAD --oneline`
     - **If unmerged commits exist**: 
       - **If origin is configured**: Create pull request and wait for user confirmation that PR is merged
       - **If origin is not configured**: Ask user to confirm merge to trunk before proceeding
       - **Do NOT proceed** with new task until branch is merged or user explicitly overrides
     - **If no unmerged commits or after merge/PR confirmation**: Proceed to step 3 to create a new branch

3. **Create a new branch for the new task**:
   - Use descriptive branch name following project conventions (typically `feature/`, `fix/`, `refactor/`, etc.)
   - Include task ID or brief description in branch name (e.g., `feature/T-001-login-endpoint`)
   - Create branch: `git checkout -b <branch-name>`

4. **Record branch information**:
   - Note the branch name and trunk detection result for inclusion in traceability logs
   - Always record what was detected as trunk in the run log
   - Record any merge/PR actions taken during branch lifecycle check

**CRITICAL**: Do not proceed to Role-Based Execution until you are on a non-trunk branch that has been merged to trunk (or is trunk itself, from which you've created a new branch). All work must happen on a feature branch, never directly on trunk.

**See [Branching SOP](#branching-sop) for detailed branch lifecycle management, naming conventions, and rules.**

---

## Role-Based Execution SOP

Agents assume different OpenUP roles as needed to complete work. Roles may switch during a run.

### Role Selection

After selecting a task, explicitly choose the initial role(s) based on phase + task type:

- **ProductOwner/Analyst** - for scope, requirements, prioritization
- **Architect** - for architecture decisions and constraints
- **Developer** - for implementation
- **Tester** - for test strategy and validation
- **ProjectManager** - for planning/tracking updates

### Role Usage Types

Distinguish between:

- **Primary role**: Main role responsible for the current task's outputs (this defines the task boundary)
- **Consulting role**: Brief consultation of another role's guidance (no new task boundary)

### Task Boundary Rules

- A new **task** starts when the agent changes the **primary role** *and* intends to modify code or project artifacts (including `/docs`)
- Consulting-role switches do **not** require a new task or a new commit when no code/artifacts are modified; they must be noted in the task log as consultation

### Task Planning

Each task must be planned before execution:

- Define objective
- Define expected outputs (including `/docs` updates)
- Define completion criteria
- Ensure the task supports the current phase + iteration goals

### Commit Policy Per Task

**⚠️ CRITICAL**: Commit DURING implementation, not just at the end.

**Do NOT save all changes for one big commit at the end.** Instead:

1. **Commit after each meaningful unit of work** — a new function, a passing test, a config change, a doc update
2. **Use the canonical commit format** from `docs-eng-process/conventions.md`:
   ```
   type(scope): brief description [T-XXX]
   ```
3. **At task end**, commit any remaining uncommitted changes, then verify with `git status --porcelain` that nothing is left

**MANDATORY**: Uncommitted changes mean the task is NOT complete. Before declaring a task finished, `git status --porcelain` must return empty.

**See [End-of-Run SOP](#end-of-run-sop) for the complete mandatory procedure that must be followed before stopping.**

### Role Switching

When switching roles, the agent must:

- State the active role to the user before executing work in that role
- Keep changes aligned with the phase + iteration goals

### OpenUP Role References

Role definitions are available in the vendored knowledge base:

- [Analyst](openup-knowledge-base/core/role/roles/analyst-6.md)
- [Product Owner](openup-knowledge-base/core/role/roles/product-owner-2.md)
- [Architect](openup-knowledge-base/core/role/roles/architect-6.md)
- [Developer](openup-knowledge-base/core/role/roles/developer-11.md)
- [Tester](openup-knowledge-base/core/role/roles/tester-5.md)
- [Project Manager](openup-knowledge-base/core/role/roles/project-manager-4.md)

---

## Self-Critique SOP (Planning & Specification)

> **Moved to [`sops/self-critique.md`](sops/self-critique.md).** Extracted so skills that apply this SOP load just the procedure instead of this whole operating-procedures document.
> The full procedure now lives in that file; this heading is kept so existing in-document links still resolve.

---

## User Communication SOP

**Before making substantive changes**, explain to the user:

1. **Current phase** (from `docs/project-status.md`)
2. **Iteration goals** for this run (derived from the selected roadmap task(s) and phase intent)

**During execution**:

- Ensure all changes made during the run clearly support the stated phase + iteration goals
- If a needed change does not fit, treat it as out-of-scope unless explicitly approved
- Log the decision in `docs/` + the agent-run log

---

## Asynchronous Input SOP

> **Moved to [`sops/async-input.md`](sops/async-input.md).** Extracted so skills that apply this SOP load just the procedure instead of this whole operating-procedures document.
> The full procedure now lives in that file; this heading is kept so existing in-document links still resolve.

---

## Branching SOP

> **Moved to [`sops/branching.md`](sops/branching.md).** Extracted so skills that apply this SOP load just the procedure instead of this whole operating-procedures document.
> The full procedure now lives in that file; this heading is kept so existing in-document links still resolve.

---

## Docs Update SOP

Always update `/docs` artifacts to reflect work done:

- Update `docs/project-status.md` (Active Work Items table, `last_updated`, `updated_by`)
- Update `docs/roadmap.md` (task status changes)
- Update phase notes (`docs/phases/{phase}/notes.md` or discipline-specific notes)
- Create/update decision records in `docs/` if architectural decisions were made

**Note**: Agents must ask permission before updating roadmap or project-status files. These are state documents that require human oversight.

---

## Traceability Logging SOP

> **Moved to [`sops/traceability-logging.md`](sops/traceability-logging.md).** Extracted so skills that apply this SOP load just the procedure instead of this whole operating-procedures document.
> The full procedure now lives in that file; this heading is kept so existing in-document links still resolve.

---

## End-of-Run SOP

**⚠️ MANDATORY: Every agent run MUST complete these steps before stopping. A task is NOT complete until all steps are finished.**

**Every agent run MUST end with these steps in order:**

### Step 1: Commit All Changes

**REQUIRED**: All changes made during the task must be committed to git before proceeding.

1. **Stage all changes**: `git add -A` (or selectively stage specific files)
2. **Create commit**: `git commit -m "<descriptive commit message>"`
   - Include task ID/description in the commit message
   - Make the commit message descriptive of what was accomplished
3. **Verify commit exists**: `git log -1 --oneline` to confirm the commit was created
4. **Record commit SHA**: Note the commit SHA for inclusion in traceability logs

**CRITICAL**: If there are any uncommitted changes, the task is NOT complete. Do NOT proceed to the next step until `git status --porcelain` shows no changes.

### Step 2: Verify No Uncommitted Changes

**REQUIRED**: Verify that all changes are committed:

- Run `git status --porcelain`
- If any output is shown, there are uncommitted changes - return to Step 1
- Only proceed when `git status --porcelain` returns empty (no output)

**MANDATORY**: You MUST NOT declare a task finished or stop the run if there are uncommitted changes. Uncommitted changes mean the task execution history is not persisted.

### Step 3: Create Traceability Logs

**REQUIRED**: Create both markdown and JSONL logs (see [Traceability Logging SOP](#traceability-logging-sop)):

1. Create markdown log at `docs/agent-logs/YYYY/MM/DD/<timestamp>-<agent>-<branch>.md`
2. Append JSONL entry to `docs/agent-logs/agent-runs.jsonl`
3. **Include commit SHAs**: The `commits` field in the JSONL must contain the actual commit SHAs from Step 1
4. Verify the logs reference the commits that were just created

### Step 4: Update Documentation

**REQUIRED**: Update project documentation to reflect completed work:

- Update phase notes in `docs/phases/{phase}/notes.md`
- If permission was granted: update `docs/project-status.md` (Active Work Items table, `last_updated`, `updated_by`)
- If permission was granted: update `docs/roadmap.md` (mark task as completed)
- Create/update decision records if architectural decisions were made

### Step 5: Final Verification

Before stopping, verify:

- [ ] All changes are committed (Step 1 complete)
- [ ] No uncommitted changes exist (Step 2 verified)
- [ ] Traceability logs created with commit SHAs (Step 3 complete)
- [ ] Documentation updated (Step 4 complete)
- [ ] Task is marked as complete in roadmap (if permission granted)

### Output Size Discipline (All Steps)

During end-of-run execution, keep command output compact:

- Prefer command summaries over full stdout dumps
- For noisy tools, report counts, failure summary, and a short tail excerpt
- Avoid re-running state checks unless new information is expected

**ONLY after all steps are complete**: Inform the user that the task is finished and stop. Do not proceed to additional tasks in this run.

### Failure to Complete End-of-Run SOP

If an agent stops without completing the End-of-Run SOP:

- The task execution history is lost (not persisted in git)
- Traceability is broken (logs may reference non-existent commits)
- The task should be considered incomplete
- Future agents will not have a complete history of work performed

**Therefore, completing the End-of-Run SOP is not optional - it is a mandatory requirement for task completion.**

---

## Project Status Definition

### Purpose

`docs/project-status.md` is the canonical source of truth for the project's current state. AI agents must read it at the start of every run to establish context (phase + iteration goals) before selecting tasks.

### Location

`docs/project-status.md`

### Template Structure

```markdown
---
project_name: "[Project Name]"
phase: inception # inception | elaboration | construction | transition
iteration: 1
iteration_goal: "Define project vision and identify key risks"
status: in-progress # not-started | in-progress | blocked | completed

phase_started: 2026-01-13
phase_target_end: 2026-01-27
iteration_started: 2026-01-13
iteration_target_end: 2026-01-20

blockers: []
# - description: "Waiting for stakeholder review of vision document"
#   since: 2026-01-15
#   owner: "product-owner"

last_updated: 2026-01-13
updated_by: "human | <agent-run-id>"
---

# Project Status

This file is the canonical source for current project state. AI agents read this at the start of every run.

## Current Focus

Brief description of what the team/agents should focus on right now.

Example: "Complete vision document and initial risk assessment. Prepare for Lifecycle Objectives Milestone review."

## Active Work Items

Reference to specific tasks currently in progress. Link to roadmap for details.

| ID    | Task                  | Role            | Status      | Notes                        |
| ----- | --------------------- | --------------- | ----------- | ---------------------------- |
| T-001 | Draft vision document | Analyst         | in-progress | First draft ready for review |
| T-002 | Identify top 10 risks | Project Manager | not-started | Blocked by T-001             |

See [roadmap.md](roadmap.md) for full backlog.

## Recent Decisions

Quick reference to decisions made this iteration. Links to full decision records.

- **2026-01-13**: Selected Python + FastAPI for backend ([ADR-001](decisions/adr-001-backend-stack.md))
- **2026-01-12**: Confirmed 4-week inception phase

## Phase Completion Criteria

Checklist for current phase milestone. When all items are checked, phase is ready for review.

### Inception - Lifecycle Objectives Milestone

- [ ] Vision document approved by stakeholders
- [ ] Key use cases identified (20-30% detailed)
- [ ] Major risks documented with mitigation strategies
- [ ] Initial project plan with cost/schedule estimates
- [ ] Business case demonstrates viability
- [ ] Stakeholder agreement to proceed

See [phase milestones reference](openup-knowledge-base/practice-management/risk_value_lifecycle/guidances/concepts/phase-milestones.md) for details.

## Notes

Any additional context agents or team members should know.
```

### Field Definitions

- `project_name` (required): human-readable project identifier
- `phase` (required): inception | elaboration | construction | transition
- `iteration` (required): iteration number within the phase
- `iteration_goal` (required): one-line summary of what this iteration should achieve
- `status` (required): not-started | in-progress | blocked | completed
- `phase_started`, `phase_target_end`, `iteration_started`, `iteration_target_end` (required): dates
- `blockers` (optional unless `status == blocked`): list of blockers with `description`, `since`, `owner`
- `last_updated`, `updated_by` (required)

### Agent Behavior

**At run start**:
- Read `docs/project-status.md`
- Extract: phase, iteration, iteration_goal, status
- If `status == blocked`: report blockers; request guidance before proceeding
- If `status == completed`: propose next phase transition; require human confirmation (do not auto-advance)
- Use phase + iteration_goal to filter/select tasks from `docs/roadmap.md`

**During run**:
- Ensure all work aligns with `iteration_goal`
- If work doesn't fit the current iteration: log as out-of-scope; request user approval or defer to backlog

**At run end**:
- Update "Active Work Items" table
- Update `last_updated` and `updated_by`
- If phase completion criteria are met: notify user that a phase review is needed; do not auto-advance phase

### Status Transitions

- not-started → in-progress → completed
- in-progress → blocked → in-progress

**Policy**: Only humans can mark a phase "completed" or resolve "blocked". Agents may propose the change but must wait for approval.

---

## Skills and Teams Integration

OpenUP workflow procedures integrate with Claude Code's Skills and Agent Teams capabilities for automation and collaboration.

### Skills

Skills encapsulate common workflow operations. Use skills to automate repetitive tasks:

**Workflow Skills** (automate SOP steps):
- `/start-iteration` - Automates Start-of-Run SOP; **deploys team by default** (auto-selected from phase)
- `/complete-task` - Automates End-of-Run SOP; saves iteration learnings to `.claude/memory/`
- `/orchestrate` - PM orchestrates a full iteration: decomposes goal, delegates to specialists, synthesizes
- `/request-input` - Automates Asynchronous Input SOP
- `/phase-review` - Checks phase completion criteria
- `/log-run` - Automates Traceability Logging SOP
- `/assess-completeness` - Rubric-based quality gate for work products and iterations

**Phase Skills** (guide phase-specific work):
- `/inception` - Guides Inception phase activities
- `/elaboration` - Guides Elaboration phase activities
- `/construction` - Guides Construction phase activities
- `/transition` - Guides Transition phase activities

**Artifact Skills** (create work products):
- `/create-vision` - Creates vision document
- `/create-use-case` - Creates use case specification
- `/create-architecture-notebook` - Creates architecture documentation
- `/create-risk-list` - Creates risk assessment
- `/create-iteration-plan` - Creates iteration plan
- `/create-test-plan` - Creates test cases and scripts

See [Skills Guide](skills-guide.md) for complete skill documentation.

### Agent Teams

Agent Teams enable role-based collaboration. **Teams are active by default** — `/start-iteration` deploys the appropriate team automatically unless explicitly opted out with `deploy_team: false`.

**Available Roles**:
- **analyst** - Requirements, stakeholder communication
- **architect** - Architecture design, technical decisions
- **developer** - Implementation, unit testing
- **project-manager** - Planning, coordination, **orchestration**
- **tester** - Test planning, execution

**Team Configurations**:
- **Phase teams**: Inception, Elaboration, Construction, Transition (auto-selected by phase)
- **Task teams**: Feature, Investigation, Planning, Full Team (override with `team:` argument)

See [Teams Guide](teams-guide.md) for complete team documentation.

### Orchestrator Pattern

The Project Manager acts as an **orchestrator** that coordinates specialist agents. This maps to the coordinator + specialist pattern:

1. **PM decomposes** the iteration goal into role-appropriate subtasks
2. **PM delegates** with focused briefs (task, context, deliverable, done-when criteria)
3. **Specialists work** in their own isolated context — each gets only what they need
4. **PM synthesizes** all outputs and verifies against acceptance criteria

Use `/orchestrate task_id: T-XXX` to run a full orchestrated iteration.

### Using Skills with Teams

Skills and teams work together. Example workflows:

**Iteration Start with Team (default)**:
```
/openup-start-iteration task_id: T-007
# Team is auto-deployed based on current phase — no extra step needed
```

**Fully Orchestrated Iteration**:
```
/openup-start-iteration task_id: T-007
/openup-orchestrate task_id: T-007
# PM coordinates analyst + architect + developer + tester, synthesizes result
/openup-complete-task task_id: T-007
```

**Skip Team Deployment**:
```
/openup-start-iteration task_id: T-007 deploy_team: false
# Single-agent execution for small, single-role tasks
```

**Phase Review with Team**:
```
/phase-review
# Team should already be active from the last start-iteration
```

### Skills that Reference SOPs

| Skill | References SOP |
|-------|----------------|
| `/start-iteration` | Start-of-Run SOP; auto-deploys team |
| `/complete-task` | End-of-Run SOP, Traceability Logging SOP; saves learnings |
| `/orchestrate` | PM Orchestrator Protocol; coordinates full team iteration |
| `/assess-completeness` | Uses rubrics from `.claude/rubrics/`; iterates until satisfied |
| `/request-input` | Asynchronous Input SOP |
| `/log-run` | Traceability Logging SOP, End-of-Run SOP |

### Quality Hooks

Optional quality enforcement hooks can be configured in `.claude/settings.json`:

- **Pre-commit**: Verifies required documentation exists
- **Post-edit**: Prompts for documentation updates
- **Stop**: Verifies completion criteria before stopping

Example configuration: `docs-eng-process/.claude-templates/settings.json.example`

---

## Additional Resources

- [How to Work](how-to-work.md) - Minimal orientation
- [Getting Started](getting-started.md) - Project initialization guide
- [OpenUP Knowledge Base](openup-knowledge-base/) - Complete process reference
- [Skills Guide](skills-guide.md) - Skills documentation
- [Teams Guide](teams-guide.md) - Teams documentation

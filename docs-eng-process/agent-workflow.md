# Agent Workflow - Complete Operating Procedures

**⚠️ STRICT PROCESS: This document defines mandatory procedures for AI agents. Follow these procedures exactly. If the process blocks progress, log the issue in `docs/` and proceed only as allowed by the workflow.**

## Table of Contents

1. [Start-of-Run SOP](#start-of-run-sop)
2. [Role-Based Execution SOP](#role-based-execution-sop)
3. [User Communication SOP](#user-communication-sop)
4. [Branching SOP](#branching-sop)
5. [Docs Update SOP](#docs-update-sop)
6. [Traceability Logging SOP](#traceability-logging-sop)
7. [Project Status Definition](#project-status-definition)

---

## Start-of-Run SOP

**Every agent run MUST begin with these steps in order:**

### Step 1: Read Project Status

Read `docs/project-status.md` to establish context:

- Extract `phase` (inception | elaboration | construction | transition)
- Extract `iteration` (current iteration number)
- Extract `iteration_goal` (what this iteration should achieve)
- Extract `status` (not-started | in-progress | blocked | completed)

**If `status == blocked`**:
- Report all blockers to the user
- Request guidance before proceeding
- Do not proceed until blockers are resolved or explicitly overridden

**If `status == completed`**:
- Check if next phase should be started
- Propose phase transition to user
- **Do NOT automatically advance phase** (requires human approval)

### Step 2: Read Roadmap and Select Task

Read `docs/roadmap.md` and select the next task:

- Filter tasks by `status == pending`
- If multiple possible targets and not specified: choose the **highest priority** task
- Priority tie-breakers (in order):
  1. Tasks explicitly marked as high priority
  2. Tasks blocking other work
  3. Tasks aligned with current `iteration_goal`
  4. Tasks with earliest due date
  5. First task in the list

### Step 3: Verify Phase Context

Ensure the selected task aligns with:
- Current `phase` from `docs/project-status.md`
- Current `iteration_goal` from `docs/project-status.md`

If the task doesn't fit:
- Log as out-of-scope in the agent-run log
- Request user approval or defer to backlog
- Do not proceed without explicit approval

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

- All changes made during a task must be committed in **at least one atomic commit**
- If a task is split into multiple steps, each step may be a separate commit (still atomic per step)

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

## User Communication SOP

**Before making substantive changes**, explain to the user:

1. **Current phase** (from `docs/project-status.md`)
2. **Iteration goals** for this run (derived from the selected roadmap task(s) and phase intent)

**During execution**:

- Ensure all changes made during the run clearly support the stated phase + iteration goals
- If a needed change does not fit, treat it as out-of-scope unless explicitly approved
- Log the decision in `docs/` + the agent-run log

---

## Branching SOP

### Trunk Detection

Detect trunk branch (varies per repo) using this algorithm:

1. Prefer `origin/HEAD` if present locally
2. Else fall back to `main`
3. Else fall back to `master`
4. Else use current branch

**Always record what was detected** as trunk in the run log.

### Branch Creation Rules

- **If current branch == trunk**: Create a new branch for the work
- **If current branch != trunk**: Do **not** create a new branch; work on current branch

### Branch Naming

Follow project conventions (typically `feature/`, `fix/`, `refactor/`, etc.)

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

**Always write run logs** for every agent execution.

### Markdown Log

Create: `docs/agent-logs/YYYY/MM/DD/<timestamp>-<agent>-<branch>.md`

Include:
- Run metadata (branch, trunk, timestamps)
- Roles assumed and any role switches
- Tasks performed (one per primary-role task boundary)
- Consulting-role usage within tasks
- Key decisions/assumptions + links to relevant docs
- Initial instructions/prompt (verbatim)
- Start/end timestamps

### JSONL Index

Append to: `docs/agent-logs/agent-runs.jsonl`

**Schema** (one JSON object per line):

```json
{
  "run_id": "2026-01-13T14:30:00Z-claude-feature/xyz",
  "agent": "claude",
  "branch": "feature/xyz",
  "trunk": "main",
  "start": "2026-01-13T14:30:00Z",
  "end": "2026-01-13T15:45:00Z",
  "phase": "construction",
  "iteration_goals": ["Deliver login endpoint with tests", "Update roadmap and notes"],
  "prompt_hash": "sha256:abc...",
  "md_log_path": "docs/agent-logs/2026/01/13/2026-01-13T14-30-00Z-claude-feature-xyz.md",
  "tasks": [
    {
      "role": "developer",
      "objective": "Implement login endpoint",
      "start": "2026-01-13T14:35:00Z",
      "end": "2026-01-13T15:10:00Z",
      "commits": ["abc1234", "def5678"],
      "docs_updated": ["docs/phases/construction/notes.md"],
      "consulting_roles": ["architect"]
    }
  ],
  "decisions": ["docs/decisions/adr-001-backend-stack.md"],
  "notes": "Brief run summary / anomalies"
}
```

**Required fields**:
- `run_id`, `agent`, `branch`, `trunk`, `start`, `end`, `phase`, `iteration_goals`, `prompt_hash`, `md_log_path`, `tasks`
- `tasks[]`: `role`, `objective`, `start`, `end`, `commits`, `docs_updated`, `consulting_roles`

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

## Additional Resources

- [How to Work](how-to-work.md) - Minimal orientation
- [Getting Started](getting-started.md) - Project initialization guide
- [OpenUP Knowledge Base](openup-knowledge-base/) - Complete process reference

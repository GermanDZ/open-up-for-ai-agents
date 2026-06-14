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

> **Moved to [`sops/start-of-run.md`](sops/start-of-run.md).** Extracted so skills that apply this SOP load just the procedure instead of this whole operating-procedures document.
> The full procedure now lives in that file; this heading is kept so existing in-document links still resolve.

---

## Role-Based Execution SOP

> **Moved to [`sops/role-based-execution.md`](sops/role-based-execution.md).** Extracted so skills that apply this SOP load just the procedure instead of this whole operating-procedures document.
> The full procedure now lives in that file; this heading is kept so existing in-document links still resolve.

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

> **Moved to [`sops/end-of-run.md`](sops/end-of-run.md).** Extracted so skills that apply this SOP load just the procedure instead of this whole operating-procedures document.
> The full procedure now lives in that file; this heading is kept so existing in-document links still resolve.

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

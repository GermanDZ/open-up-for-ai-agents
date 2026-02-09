# Agent Workflow - Complete Operating Procedures

**⚠️ STRICT PROCESS: This document defines mandatory procedures for AI agents. Follow these procedures exactly. If the process blocks progress, log the issue in `docs/` and proceed only as allowed by the workflow.**

## Table of Contents

1. [Start-of-Run SOP](#start-of-run-sop)
2. [Role-Based Execution SOP](#role-based-execution-sop)
3. [User Communication SOP](#user-communication-sop)
4. [Asynchronous Input SOP](#asynchronous-input-sop)
5. [Branching SOP](#branching-sop)
6. [Docs Update SOP](#docs-update-sop)
7. [Traceability Logging SOP](#traceability-logging-sop)
8. [End-of-Run SOP](#end-of-run-sop)
9. [Project Status Definition](#project-status-definition)
10. [Skills and Teams Integration](#skills-and-teams-integration)

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

### Step 4: Create Branch (if needed)

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

**⚠️ CRITICAL**: Committing changes is not optional - it is a mandatory requirement for task completion.

- All changes made during a task must be committed in **at least one atomic commit**
- If a task is split into multiple steps, each step may be a separate commit (still atomic per step)
- **MANDATORY**: When confirming a task is finished, you MUST commit all changes to git before stopping. Do not leave uncommitted changes.
- **MANDATORY**: Uncommitted changes mean the task is NOT complete. Task execution history is only persisted when changes are committed.
- **MANDATORY**: Before declaring a task finished, verify with `git status --porcelain` that no uncommitted changes exist.

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

When an agent needs user input, it may create an **Input Request Document** instead of asking questions interactively. This enables asynchronous communication and allows documents to be shared via email for stakeholder input.

### When to Create an Input Request Document

Agents should create an input request document when:

- The question requires stakeholder consultation (not just the current user)
- Multiple related questions need to be answered together
- The user explicitly requests async communication
- The input may take time to gather (e.g., business decisions, approvals)
- The question could benefit from being shared via email
- The input is needed to unblock work but the user may not be immediately available

### When to Use Interactive Chat Instead

Use interactive chat for:

- Quick clarifications (yes/no, simple choices)
- Urgent blockers that need immediate resolution
- Follow-up questions during active work
- Single, straightforward questions that don't require stakeholder input

### Creating an Input Request Document

1. **Copy the template**: Copy `docs-eng-process/templates/input-request.md` to `docs/input-requests/`
2. **Name the file**: Use format `<YYYY-MM-DD>-<short-topic>.md` (e.g., `2026-01-13-vision-scope.md`)
3. **Fill the frontmatter**:
   - `title`: Descriptive title for the request
   - `created`: Current timestamp in ISO 8601 format
   - `created_by`: Agent identifier (e.g., "claude")
   - `status`: Set to `pending`
   - `run_id`: Current run identifier
   - `related_task`: Optional roadmap task ID (e.g., "T-001")
   - `expires`: Optional expiration date for time-sensitive requests
4. **Write the Context section**: Explain what the agent is doing and why input is needed
5. **Add Questions**: Use the structured question format:
   - **Type**: `multiple-choice`, `text`, or `reference`
   - **Question**: The actual question text
   - For `multiple-choice`: Provide checkbox options with short identifiers
   - For `text`: Include an example answer
   - For `reference`: Specify that it accepts file paths or URLs
   - **Answer**: Empty section for user to fill
6. **Include Instructions**: Explain how to fill and resume
7. **Notify the user**: Inform them that an input request document has been created and where to find it

### Question Format Standards

**Multiple-choice questions**:
```markdown
### Q1: [Question Title]

**Type**: multiple-choice

**Question**: [The actual question text]

- [ ] `option-a` - Option A description
- [ ] `option-b` - Option B description
- [ ] `option-c` - Option C description
- [ ] `other` - Other (specify below)

**Answer**: 
<!-- Check one option above or specify here -->
```

**Text questions**:
```markdown
### Q2: [Question Title]

**Type**: text

**Question**: [The actual question text]

**Example**: "[Example answer to guide the user]"

**Answer**: 
<!-- Write your answer here -->
```

**Reference questions**:
```markdown
### Q3: [Question Title]

**Type**: reference

**Question**: [The actual question text]

**Accepts**: Path to a file (relative to repo root) or URL containing the answer

**Answer**: 
<!-- Provide path or URL, or write "None" -->
```

### Processing Completed Requests

When processing an answered input request:

1. **Read the document**: Parse the frontmatter and all question answers
2. **Validate answers**: Ensure all required questions have answers
3. **Use the information**: Apply the answers to continue the related task
4. **Update status**: Change `status` from `answered` to `processed` in frontmatter
5. **Archive**: Move the file to `docs/input-requests/archive/`
6. **Log**: Record the processing in the agent-run log, including which task was unblocked

### Document Location

- **Active requests**: `docs/input-requests/`
- **Processed requests**: `docs/input-requests/archive/`
- **Template**: `docs-eng-process/templates/input-request.md`

### Status Lifecycle

- `pending` → User fills out the document
- `answered` → User updates status and saves (agent processes this)
- `processed` → Agent has processed the answers and archived the document

---

## Branching SOP

**Note**: This procedure is executed as part of [Start-of-Run SOP](#start-of-run-sop) Step 4, which happens **before any work begins**. Branch creation is mandatory if you are on trunk, and branches with unmerged commits must be merged to trunk before starting new tasks.

### Trunk Detection

Detect trunk branch (varies per repo) using this algorithm:

1. Prefer `origin/HEAD` if present locally
2. Else fall back to `main`
3. Else fall back to `master`
4. Else use current branch

**Always record what was detected** as trunk in the run log.

### Branch Lifecycle Check

**MANDATORY**: Before starting a new task, check if the current branch has unmerged commits. New tasks must start on a clean branch (either trunk or a branch that has been merged to trunk).

1. **If current branch == trunk**: Proceed to [Branch Creation Rules](#branch-creation-rules) to create a new branch for the work.

2. **If current branch != trunk**: Check for unmerged commits:
   - Run: `git log <trunk>..HEAD --oneline` to detect commits not in trunk
   - If commits exist (output is non-empty):
     - **If origin remote is configured** (`git remote get-url origin` succeeds):
       - Inform user: "Current branch has unmerged commits. Creating pull request with task context..."
       - Invoke `/create-pr` skill to create PR with proper description linking to roadmap task context:
         - Extract task_id from branch name (e.g., `feature/T-001-xyz` → `T-001`)
         - Generate PR description from `docs/roadmap.md` task entry
         - Push branch to origin: `git push -u origin <current-branch>`
         - Create PR using platform-specific tooling (GitHub `gh`, GitLab `glab`)
       - Wait for user confirmation: "PR has been merged to trunk" or "PR is ready for review"
       - **Do NOT proceed** with new task until PR is merged or user explicitly confirms to continue
     - **If origin remote is not configured**:
       - Ask user: "Current branch has unmerged commits. Merge to trunk before continuing? (yes/no)"
       - If user confirms "yes":
         - Switch to trunk: `git checkout <trunk>`
         - Merge branch: `git merge <previous-branch>`
         - Delete merged branch: `git branch -d <previous-branch>`
         - Proceed to create new branch for new task
       - If user confirms "no" or does not approve:
         - Stop and wait for user to handle merge manually
         - **Do NOT proceed** with new task until merge is complete
   - If no commits exist (output is empty) or after merge/PR confirmation:
     - Proceed to [Branch Creation Rules](#branch-creation-rules) to create a new branch for the new task

**CRITICAL**: Do not start a new task on a branch that has unmerged commits. This ensures clean branch history and prevents work from being lost.

### Branch Creation Rules

- **If current branch == trunk**: **MANDATORY** - Create a new branch for the work before starting any work
- **If current branch != trunk AND has been merged to trunk** (no unmerged commits): **MANDATORY** - Create a new branch for the new task
- **If current branch != trunk AND has unmerged commits**: **BLOCKED** - Handle merge/PR first (see [Branch Lifecycle Check](#branch-lifecycle-check))

**CRITICAL**: Branch creation happens BEFORE Role-Based Execution begins. Never start working before ensuring you are on an appropriate branch that has been merged to trunk (or is trunk itself).

### Branch Naming

Follow project conventions (typically `feature/`, `fix/`, `refactor/`, etc.)

- Include task ID or brief description when possible (e.g., `feature/T-001-login-endpoint`)
- Use descriptive names that indicate the work being done
- Keep branch names concise but informative

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

**⚠️ MANDATORY PREREQUISITE**: Commits must exist before creating logs. The `commits` field in logs must reference actual commit SHAs that exist in the git repository. Do not create logs until all changes are committed (see [End-of-Run SOP](#end-of-run-sop) Step 1).

### Markdown Log

Create: `docs/agent-logs/YYYY/MM/DD/<timestamp>-<agent>-<branch>.md`

Include:
- Run metadata (branch, trunk, timestamps)
- Roles assumed and any role switches
- Tasks performed (one per primary-role task boundary)
- **Commit SHAs**: List all commits created during this run
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

**MANDATORY**: The `commits` field must contain actual commit SHAs that exist in the repository. 

**Validation before logging**:
1. Verify commits exist: `git log --oneline` should show the commits you plan to reference
2. Verify no uncommitted changes: `git status --porcelain` should be empty
3. Only after both checks pass, create the logs with commit SHAs

**If no commits exist**: Do not create logs. Return to [End-of-Run SOP](#end-of-run-sop) Step 1 to commit changes first.

**See [End-of-Run SOP](#end-of-run-sop) for the complete mandatory procedure that must be followed before creating logs.**

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
- `/start-iteration` - Automates Start-of-Run SOP for iteration initialization
- `/complete-task` - Automates End-of-Run SOP for task completion
- `/request-input` - Automates Asynchronous Input SOP
- `/phase-review` - Checks phase completion criteria
- `/log-run` - Automates Traceability Logging SOP

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

Agent Teams enable role-based collaboration. Teams automatically follow role-based instructions and the SOPs defined in this document:

**Available Roles**:
- **analyst** - Requirements, stakeholder communication
- **architect** - Architecture design, technical decisions
- **developer** - Implementation, unit testing
- **project-manager** - Planning, coordination
- **tester** - Test planning, execution

**Team Configurations**:
- **Phase teams**: Inception, Elaboration, Construction, Transition
- **Task teams**: Feature, Investigation, Planning, Full Team

See [Teams Guide](teams-guide.md) for complete team documentation.

### Using Skills with Teams

Skills and teams work together. Example workflows:

**Iteration Start with Team**:
```
/start-iteration goal: "Implement user authentication"
Create an OpenUP agent team for construction phase.
```

**Feature Implementation with Team**:
```
Create an OpenUP feature team.
/complete-task task_id: T-005
/log-run
```

**Phase Review with Team**:
```
/phase-review
Create an OpenUP team for phase review preparation.
```

### Skills that Reference SOPs

| Skill | References SOP |
|-------|----------------|
| `/start-iteration` | Start-of-Run SOP |
| `/complete-task` | End-of-Run SOP, Traceability Logging SOP |
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

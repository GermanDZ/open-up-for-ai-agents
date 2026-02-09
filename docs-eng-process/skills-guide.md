# OpenUP Skills Guide

This guide documents all OpenUP skills available for automating workflow operations.

## What are Skills?

Skills are reusable workflow operations that can be invoked using the `/` command in Claude Code. They encapsulate common OpenUP processes, ensuring consistency and reducing manual effort.

## Using Skills

Invoke a skill by typing `/` followed by the skill name:

```
/skill-name argument1: value1 argument2: value2
```

Skills can also be invoked without arguments if they're optional:

```
/skill-name
```

## Phase Skills

Phase skills guide you through each OpenUP phase, providing context-specific activities and completion criteria.

### /inception

Initialize and manage Inception phase activities.

**Purpose**: Define scope, vision, and feasibility

**Arguments**:
- `activity` (optional): `initiate`, `check-status`, or `next-steps`

**Example**:
```
/inception activity: initiate
```

**What it does**:
- Reads project status to confirm Inception phase
- For `initiate`: Creates vision document, risk list, initial roadmap
- For `check-status`: Reviews completion criteria and progress
- For `next-steps`: Suggests next tasks based on current state

**Completion Criteria**:
- Vision document approved
- Key use cases identified (20-30%)
- Major risks documented
- Initial project plan with estimates
- Business case demonstrates viability
- Stakeholder agreement to proceed

### /elaboration

Initialize and manage Elaboration phase activities.

**Purpose**: Establish architecture baseline

**Arguments**:
- `activity` (optional): `initiate`, `check-status`, or `next-steps`

**Example**:
```
/elaboration activity: initiate
```

**What it does**:
- Reads project status to confirm Elaboration phase
- For `initiate`: Creates architecture notebook, refines risk list
- For `check-status`: Reviews completion criteria and progress
- For `next-steps`: Suggests next tasks based on current state

**Completion Criteria**:
- Architecture notebook completed
- Critical use cases detailed (80%)
- Technical risks identified and mitigated
- Prototypes validate architectural decisions
- Project plan refined with accurate estimates
- Stakeholder agreement on architecture

### /construction

Initialize and manage Construction phase activities.

**Purpose**: Build the system incrementally

**Arguments**:
- `activity` (optional): `initiate`, `check-status`, or `next-steps`

**Example**:
```
/construction activity: next-steps
```

**What it does**:
- Reads project status to confirm Construction phase
- For `initiate`: Updates roadmap with construction tasks
- For `check-status`: Reviews completion criteria and progress
- For `next-steps`: Suggests next tasks based on current state

**Completion Criteria**:
- Product stable enough for beta testing
- Alpha test results documented
- Critical issues resolved
- User documentation adequate
- Stakeholder agreement to deploy to beta users

### /transition

Initialize and manage Transition phase activities.

**Purpose**: Deploy to users

**Arguments**:
- `activity` (optional): `initiate`, `check-status`, or `next-steps`

**Example**:
```
/transition activity: initiate
```

**What it does**:
- Reads project status to confirm Transition phase
- For `initiate`: Creates deployment checklist
- For `check-status`: Reviews completion criteria and progress
- For `next-steps`: Suggests next tasks based on current state

**Completion Criteria**:
- Product ready for release
- All acceptance tests pass
- Deployment documentation complete
- Support materials ready
- Stakeholder sign-off obtained

## Artifact Skills

Artifact skills create OpenUP work products from templates.

### /create-vision

Generate a vision document from template.

**Arguments**:
- `project_name` (required): Name of the project
- `problem_statement` (required): Brief description of the problem

**Example**:
```
/create-vision project_name: "TaskManager" problem_statement: "Teams need a better way to track and prioritize work"
```

**Output**: `docs/vision.md` with filled-in sections

### /create-use-case

Create a use case specification from template.

**Arguments**:
- `use_case_name` (required): Name of the use case
- `primary_actor` (required): The primary actor
- `description` (required): Brief description

**Example**:
```
/create-use-case use_case_name: "Create Task" primary_actor: "User" description: "User creates a new task in the system"
```

**Output**: `docs/use-cases/<use-case-name>.md`

### /create-architecture-notebook

Generate or update architecture documentation.

**Arguments**:
- `system_name` (required): Name of the system
- `architectural_concerns` (optional): Key concerns to address

**Example**:
```
/create-architecture-notebook system_name: "TaskManager" architectural_concerns: "scalability, security, performance"
```

**Output**: `docs/architecture-notebook.md`

### /create-risk-list

Create or update risk assessment document.

**Arguments**:
- `risks` (optional): JSON array of risks to add

**Example**:
```
/create-risk-list risks: '[{"description": "Database scaling", "probability": "high", "impact": "high"}]'
```

**Output**: `docs/risk-list.md`

### /create-iteration-plan

Plan iteration based on current state and roadmap.

**Arguments**:
- `iteration_number` (optional): Iteration number to plan

**Example**:
```
/create-iteration-plan iteration_number: 3
```

**Output**: `docs/phases/<phase>/iteration-<n>-plan.md`

### /create-test-plan

Generate test cases and scripts from use cases and requirements.

**Arguments**:
- `scope` (required): What to test

**Example**:
```
/create-test-plan scope: "user authentication"
```

**Output**: Test cases in `docs/test-cases/` and test scripts in `docs/test-scripts/`

## Workflow Skills

Workflow skills automate common workflow operations.

### /start-iteration

Begin a new iteration with proper phase context and task selection.

**Arguments**:
- `iteration_number` (optional): The iteration number
- `goal` (optional): The iteration goal

**Example**:
```
/start-iteration iteration_number: 2 goal: "Complete user authentication"
```

**What it does**:
1. Reads project status
2. Checks for answered input requests
3. Creates new branch
4. Updates iteration in project-status.md
5. Logs initialization

**Output**: Summary of phase, iteration, goal, branch, and recommended tasks

### /complete-task

Mark a task as complete, update roadmap, commit changes, and prepare logs.

**Arguments**:
- `task_id` (required): Task ID (e.g., T-001)
- `commit_message` (optional): Custom commit message

**Example**:
```
/complete-task task_id: T-003
```

**What it does**:
1. Verifies task completion
2. Commits all changes
3. Verifies no uncommitted changes
4. Updates roadmap
5. Updates project status
6. Creates traceability logs

**Output**: Task completed, commit SHA, files changed, log locations

**IMPORTANT**: Must be called AFTER all changes are committed.

### /request-input

Create an input request document for asynchronous stakeholder communication.

**Arguments**:
- `title` (required): Descriptive title
- `questions` (required): JSON array of questions
- `context` (required): Additional context
- `related_task` (optional): Roadmap task ID

**Example**:
```
/request-input title: "Vision Scope" context: "Need to clarify project scope" questions: '[{"type": "text", "question": "What are the core features?"}]'
```

**What it does**:
1. Creates input request file
2. Fills in frontmatter and context
3. Formats questions properly
4. Includes instructions for user
5. Notifies user of file location

**Output**: File path, number of questions, instructions

### /phase-review

Check phase completion criteria and prepare for phase review.

**Arguments**:
- `phase` (optional): Phase to review

**Example**:
```
/phase-review
```

**What it does**:
1. Reads current project status
2. Checks phase completion criteria
3. Generates phase review summary
4. Creates review presentation outline
5. Notifies user of any incomplete criteria

**Output**: Completion checklist status, work products, review summary

### /log-run

Create traceability logs for the current agent run.

**Arguments**:
- `run_id` (optional): Unique identifier

**Example**:
```
/log-run
```

**What it does**:
1. Generates run ID
2. Collects run metadata
3. Reads project context
4. Creates markdown log
5. Appends JSONL entry
6. Verifies logs

**Output**: Markdown log path, JSONL confirmation, commits logged

**IMPORTANT**: Must be called AFTER all changes are committed.

## Skill Composition

Skills can be combined for complex workflows. For example:

```
/start-iteration goal: "Implement user authentication"
Create an OpenUP agent team for feature implementation.
/complete-task task_id: T-005
/log-run
```

## When to Use Each Skill

| Situation | Use This Skill |
|-----------|----------------|
| Starting a new phase | `/inception`, `/elaboration`, `/construction`, `/transition` |
| Checking phase progress | `/phase activity: check-status` |
| Need project vision | `/create-vision` |
| Defining requirements | `/create-use-case` |
| Architecture work needed | `/create-architecture-notebook` |
| Identifying risks | `/create-risk-list` |
| Planning iteration | `/create-iteration-plan` |
| Starting iteration | `/start-iteration` |
| Finishing task | `/complete-task` |
| Need stakeholder input | `/request-input` |
| Phase nearly complete | `/phase-review` |
| Ending agent run | `/log-run` |
| Testing needed | `/create-test-plan` |

## References

- Skills are located in: `docs-eng-process/.claude-templates/skills/`
- Templates are located in: `docs-eng-process/templates/`
- Agent Workflow: `docs-eng-process/agent-workflow.md`

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

## Phase Skills

Phase skills guide you through each OpenUP phase, providing context-specific activities and completion criteria.

### /openup-inception

Initialize and manage Inception phase activities.

**Purpose**: Define scope, vision, and feasibility

**When to Use**:
- Starting a new project and need to define scope and vision
- Need to identify key stakeholders and risks
- Preparing to move from idea to validated business case
- Checking if Inception phase is complete

**When NOT to Use**:
- Currently in later phases (use appropriate phase skill)
- Need to create specific artifacts (use artifact skills)
- Already have clear vision and architecture baseline

**Arguments**:
- `activity` (optional): `initiate`, `check-status`, or `next-steps`

**Example**:
```
/openup-inception activity: initiate
```

**Success Criteria**:
- [ ] Phase status is clearly understood
- [ ] Key artifacts are identified or created
- [ ] Next steps are clearly defined
- [ ] Stakeholders and risks are documented

**See Also**: `openup-create-vision`, `openup-create-risk-list`, `openup-elaboration`

### /openup-elaboration

Initialize and manage Elaboration phase activities.

**Purpose**: Establish architecture baseline

**When to Use**:
- Inception is complete and need to establish architecture baseline
- Need to design and validate system architecture
- Resolving high-risk technical elements

**When NOT to Use**:
- Still defining project vision and scope
- Architecture is stable and ready for incremental build

**Arguments**:
- `activity` (optional): `initiate`, `check-status`, or `next-steps`

**Example**:
```
/openup-elaboration activity: initiate
```

**Success Criteria**:
- [ ] Phase status is clearly understood
- [ ] Architecture notebook is created or updated
- [ ] Technical risks are identified and mitigated
- [ ] Critical use cases are detailed

**See Also**: `openup-create-architecture-notebook`, `openup-create-use-case`, `openup-inception`

### /openup-construction

Initialize and manage Construction phase activities.

**Purpose**: Build the system incrementally

**When to Use**:
- Elaboration is complete and architecture baseline is established
- Ready to build the system iteratively
- Implementing features incrementally

**When NOT to Use**:
- Architecture is not yet stable
- System is ready for deployment

**Arguments**:
- `activity` (optional): `initiate`, `check-status`, or `next-steps`

**Example**:
```
/openup-construction activity: next-steps
```

**Success Criteria**:
- [ ] Phase status is clearly understood
- [ ] Implementation progress is tracked
- [ ] Test coverage is adequate
- [ ] Next iteration tasks are identified

**See Also**: `openup-complete-task`, `openup-create-test-plan`, `openup-elaboration`

### /openup-transition

Initialize and manage Transition phase activities.

**Purpose**: Deploy to users

**When to Use**:
- Construction is complete and system is ready for deployment
- Preparing for beta or production release
- Conducting final testing and user acceptance

**When NOT to Use**:
- Still implementing features
- System is not stable enough for testing

**Arguments**:
- `activity` (optional): `initiate`, `check-status`, or `next-steps`

**Example**:
```
/openup-transition activity: initiate
```

**Success Criteria**:
- [ ] Phase status is clearly understood
- [ ] Deployment readiness is assessed
- [ ] Support materials are prepared
- [ ] User acceptance is documented

**See Also**: `openup-phase-review`, `openup-create-test-plan`, `openup-construction`

## Artifact Skills

Artifact skills create OpenUP work products from templates.

### /openup-create-vision

Generate a vision document from template.

**When to Use**:
- Starting a new project and need to define the vision
- In Inception phase and need to document project scope
- Stakeholders need a clear understanding of project goals

**When NOT to Use**:
- Vision document already exists
- Need detailed requirements (use use case skills)
- Looking for technical architecture

**Arguments**:
- `project_name` (required): Name of the project
- `problem_statement` (required): Brief description of the problem

**Example**:
```
/openup-create-vision project_name: "TaskManager" problem_statement: "Teams need a better way to track and prioritize work"
```

**Success Criteria**:
- [ ] Vision document exists at `docs/vision.md`
- [ ] Project name and problem statement are filled in
- [ ] Stakeholders are identified
- [ ] Key features are listed

**See Also**: `openup-inception`, `openup-create-use-case`, `openup-create-risk-list`

### /openup-create-use-case

Create a use case specification from template.

**When to Use**:
- Need to document user interactions with the system
- In Inception or Elaboration phase defining requirements
- Capturing functional requirements from user perspective

**When NOT to Use**:
- Need non-functional requirements
- Looking for technical specifications
- Use case already exists

**Arguments**:
- `use_case_name` (required): Name of the use case
- `primary_actor` (required): The primary actor
- `description` (required): Brief description

**Example**:
```
/openup-create-use-case use_case_name: "Create Task" primary_actor: "User" description: "User creates a new task in the system"
```

**Success Criteria**:
- [ ] Use case file exists in `docs/use-cases/`
- [ ] Use case name and primary actor are defined
- [ ] Basic flow is documented
- [ ] Alternative flows are identified

**See Also**: `openup-create-vision`, `openup-create-test-plan`, `openup-elaboration`

### /openup-create-architecture-notebook

Generate or update architecture documentation.

**When to Use**:
- Starting Elaboration phase and need to document architecture
- Making significant architectural decisions
- Need to document system design and constraints

**When NOT to Use**:
- In Inception phase before architecture is defined
- Need detailed component design
- Architecture notebook exists and only minor updates needed

**Arguments**:
- `system_name` (required): Name of the system
- `architectural_concerns` (optional): Key concerns to address

**Example**:
```
/openup-create-architecture-notebook system_name: "TaskManager" architectural_concerns: "scalability, security, performance"
```

**Success Criteria**:
- [ ] Architecture notebook exists at `docs/architecture-notebook.md`
- [ ] System name and context are defined
- [ ] Key architectural decisions are documented
- [ ] Architectural constraints are listed

**See Also**: `openup-elaboration`, `openup-create-vision`, `openup-create-risk-list`

### /openup-create-risk-list

Create or update risk assessment document.

**When to Use**:
- Starting a new project and need to identify risks
- In Inception phase documenting major risks
- New risks emerge during project

**When NOT to Use**:
- Risk list exists and only minor updates needed
- Looking for issue tracking
- Risks have been realized and are now issues

**Arguments**:
- `risks` (optional): JSON array of risks to add

**Example**:
```
/openup-create-risk-list risks: '[{"description": "Database scaling", "probability": "high", "impact": "high"}]'
```

**Success Criteria**:
- [ ] Risk list exists at `docs/risk-list.md`
- [ ] Risks are documented with descriptions
- [ ] Probability and impact are assessed
- [ ] Mitigation strategies are defined

**See Also**: `openup-inception`, `openup-create-vision`, `openup-create-architecture-notebook`

### /openup-create-iteration-plan

Plan iteration based on current state and roadmap.

**When to Use**:
- Starting a new iteration and need to plan work
- In Construction phase planning iterations
- Need to select tasks from roadmap for iteration

**When NOT to Use**:
- Looking to start iteration (use `openup-start-iteration`)
- Need to create roadmap
- Iteration plan exists and only minor updates needed

**Arguments**:
- `iteration_number` (optional): Iteration number to plan

**Example**:
```
/openup-create-iteration-plan iteration_number: 3
```

**Success Criteria**:
- [ ] Iteration plan file exists
- [ ] Iteration goal is clearly defined
- [ ] Tasks are selected from roadmap
- [ ] Task assignments are made

**See Also**: `openup-start-iteration`, `openup-complete-task`, `openup-construction`

### /openup-create-test-plan

Generate test cases and scripts from use cases and requirements.

**When to Use**:
- Need to create test cases for features or use cases
- In Elaboration or Construction phase planning tests
- Starting testing for a new feature

**When NOT to Use**:
- Looking to execute tests
- Need to debug test failures
- Test plan exists and only minor updates needed

**Arguments**:
- `scope` (required): What to test

**Example**:
```
/openup-create-test-plan scope: "user authentication"
```

**Success Criteria**:
- [ ] Test cases exist in `docs/test-cases/`
- [ ] Test scripts exist in `docs/test-scripts/`
- [ ] Test coverage includes happy path and edge cases
- [ ] Expected results are defined

**See Also**: `openup-create-use-case`, `openup-construction`, `openup-phase-review`

## Workflow Skills

Workflow skills automate common workflow operations.

### /openup-start-iteration

Begin a new iteration with proper phase context and task selection.

**When to Use**:
- Starting a new iteration in any phase
- Need to create iteration branch
- Ready to begin iteration work

**When NOT to Use**:
- Current iteration is still in progress
- Need to plan iteration without starting
- Looking to complete iteration

**Arguments**:
- `iteration_number` (optional): The iteration number
- `goal` (optional): The iteration goal

**Example**:
```
/openup-start-iteration iteration_number: 2 goal: "Complete user authentication"
```

**Success Criteria**:
- [ ] Project status is updated with new iteration
- [ ] Iteration branch is created
- [ ] Iteration goal is defined
- [ ] Answered input requests are processed

**See Also**: `openup-create-iteration-plan`, `openup-complete-task`, `openup-request-input`

### /openup-complete-task

Mark a task as complete, update roadmap, commit changes, and prepare logs.

**When to Use**:
- A task implementation is complete and ready to commit
- All tests pass for the task
- Documentation has been updated

**When NOT to Use**:
- Still implementing the task
- Tests are failing
- Just need to commit without updating roadmap

**Multi-file Structure**:
- `SKILL.md` - Main entry point
- `commit-procedure.md` - Detailed commit steps
- `traceability-logs.md` - Logging procedures
- `pr-handling.md` - PR creation flow

**Arguments**:
- `task_id` (required): Task ID (e.g., T-001)
- `commit_message` (optional): Custom commit message
- `create_pr` (optional): Create a pull request after completing the task

**Examples**:
```
/openup-complete-task task_id: T-003
/openup-complete-task task_id: T-003 create_pr: true
```

**Success Criteria**:
- [ ] All changes are committed with descriptive message
- [ ] No uncommitted changes remain
- [ ] Roadmap is updated to mark task complete
- [ ] Project status is updated
- [ ] Traceability logs are created with commit SHAs

**See Also**: `openup-create-pr`, `openup-log-run`, `openup-start-iteration`

### /openup-create-pr

Create a pull request with proper description linking to roadmap task context.

**When to Use**:
- Ready to share changes for review
- Need to create PR from current branch
- Want PR description linked to roadmap task

**When NOT to Use**:
- No unmerged commits exist
- Looking to update existing PR
- Need to push branch without PR

**Multi-file Structure**:
- `SKILL.md` - Main entry point
- `detection.md` - State detection procedures
- `generation.md` - PR title and description generation

**Arguments**:
- `task_id` (optional): Task ID from roadmap (e.g., T-001). Auto-detected from branch name if not provided.
- `branch` (optional): Branch to create PR from. Uses current branch if not provided.
- `title` (optional): Custom PR title. Auto-generated from task if not provided.
- `base` (optional): Base branch to merge into. Auto-detected if not provided.

**Examples**:
```
/openup-create-pr task_id: T-005
/openup-create-pr task_id: T-005 base: develop
/openup-create-pr
```

**Success Criteria**:
- [ ] PR is created with proper title and description
- [ ] PR links to roadmap task context
- [ ] PR includes task label for traceability
- [ ] Branch is pushed to remote

**Error Handling**:
- No unmerged commits: Informs user branch is up to date
- No remote configured: Prompts user to add remote
- CLI not installed: Provides installation instructions

**See Also**: `openup-complete-task`, `openup-start-iteration`

### /openup-request-input

Create an input request document for asynchronous stakeholder communication.

**When to Use**:
- The question requires stakeholder consultation
- Multiple related questions need to be answered together
- The input may take time to gather

**When NOT to Use**:
- Question can be answered immediately by user
- Need real-time interaction
- Question is simple and quick to answer

**Arguments**:
- `title` (required): Descriptive title
- `questions` (required): JSON array of questions
- `context` (required): Additional context
- `related_task` (optional): Roadmap task ID

**Example**:
```
/openup-request-input title: "Vision Scope" context: "Need to clarify project scope" questions: '[{"type": "text", "question": "What are the core features?"}]'
```

**Success Criteria**:
- [ ] Input request document exists in `docs/input-requests/`
- [ ] All questions are clearly formatted
- [ ] Context explains why input is needed
- [ ] Instructions for filling and resuming are included

**See Also**: `openup-start-iteration`, `openup-complete-task`

### /openup-phase-review

Check phase completion criteria and prepare for phase review.

**When to Use**:
- Nearing end of a phase and need to check completion
- Preparing for phase review meeting with stakeholders
- Assessing readiness to move to next phase

**When NOT to Use**:
- Just starting a phase
- Need to complete iteration tasks
- Phase is clearly not complete

**Arguments**:
- `phase` (optional): Phase to review

**Example**:
```
/openup-phase-review
```

**Success Criteria**:
- [ ] All phase completion criteria are checked
- [ ] Missing items are clearly identified
- [ ] Phase review summary is generated
- [ ] Recommendations for next phase are provided

**See Also**: `openup-inception`, `openup-elaboration`, `openup-construction`, `openup-transition`

### /openup-log-run

Create traceability logs for the current agent run.

**When to Use**:
- Completing work that should be logged for traceability
- Need to document agent activities for audit trail
- After committing all changes

**When NOT to Use**:
- Changes are not yet committed
- Looking to commit changes
- Run is incomplete and will continue

**Arguments**:
- `run_id` (optional): Unique identifier

**Example**:
```
/openup-log-run
```

**Success Criteria**:
- [ ] Markdown log exists with all required fields
- [ ] JSONL entry is valid and appended
- [ ] Commit SHAs are correctly recorded
- [ ] Log files are in correct directory structure

**IMPORTANT**: Must be called AFTER all changes are committed.

**See Also**: `openup-complete-task`, `openup-start-iteration`

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

## When to Use Each Skill

| Situation | Use This Skill |
|-----------|----------------|
| Starting a new phase | `/openup-inception`, `/openup-elaboration`, `/openup-construction`, `/openup-transition` |
| Checking phase progress | `/openup-{phase} activity: check-status` |
| Need project vision | `/openup-create-vision` |
| Defining requirements | `/openup-create-use-case` |
| Architecture work needed | `/openup-create-architecture-notebook` |
| Identifying risks | `/openup-create-risk-list` |
| Planning iteration | `/openup-create-iteration-plan` |
| Starting iteration | `/openup-start-iteration` |
| Finishing task | `/openup-complete-task` |
| Creating pull request | `/openup-create-pr` |
| Need stakeholder input | `/openup-request-input` |
| Phase nearly complete | `/openup-phase-review` |
| Ending agent run | `/openup-log-run` |
| Testing needed | `/openup-create-test-plan` |

## References

- Skills are located in: `docs-eng-process/.claude-templates/skills/`
- Templates are located in: `docs-eng-process/templates/`
- Executable scripts are in: `docs-eng-process/.claude-templates/skills/scripts/`
- Agent Workflow: `docs-eng-process/agent-workflow.md`
- Anthropic Agent Skills Framework: https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills

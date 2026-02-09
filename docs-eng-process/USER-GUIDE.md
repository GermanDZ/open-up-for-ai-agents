# OpenUP User Guide for Claude Code

**Your complete guide to using OpenUP (Open Unified Process) with AI agent-driven development.**

---

## Table of Contents

- [Part 1: Getting Started](#part-1-getting-started)
- [Part 2: Project Setup](#part-2-project-setup)
- [Part 3: Core Concepts](#part-3-core-concepts)
- [Part 4: Common Workflows (Quick Reference)](#part-4-common-workflows-quick-reference)
- [Part 5: Common Workflows (Detailed)](#part-5-common-workflows-detailed)
- [Part 6: Skills Reference](#part-6-skills-reference)
- [Part 7: Agent Teams Reference](#part-7-agent-teams-reference)
- [Part 8: Configuration](#part-8-configuration)
- [Part 9: Documentation Issues & Fixes](#part-9-documentation-issues--fixes)
- [Part 10: Troubleshooting](#part-10-troubleshooting)

---

## Part 1: Getting Started

### What is OpenUP?

OpenUP (Open Unified Process) is a lean, iterative software development methodology adapted for AI agent-driven development. It provides:

- **Structured phases** - Inception, Elaboration, Construction, Transition
- **Role-based collaboration** - Analyst, Architect, Developer, Tester, Project Manager
- **Traceable artifacts** - Vision documents, roadmaps, architecture notebooks, test plans
- **Agent-driven workflows** - Skills and teams that automate common tasks

### Why Use OpenUP with Claude Code?

- **Consistent process** - Agents follow documented procedures
- **Traceability** - Every decision and commit is logged
- **Collaboration** - Agent teams work together using role-based instructions
- **Quality hooks** - Automated checks ensure documentation stays complete

### System Requirements

- **Claude Code** - Installed and configured (see [Claude Code documentation](https://code.claude.com/docs/en/agent-teams))
- **Git** - For version control and branching
- **Bash** - For running setup scripts
- **Python 3.10+** - Required only for the OpenUP HTML converter (not typical project work)

### Claude Code Brief Refresher

Claude Code features relevant to OpenUP:

| Feature | How to Use | OpenUP Purpose |
|---------|-----------|----------------|
| **Skills** | Type `/skill-name` to invoke | Automate workflow operations |
| **Agent Teams** | Type "Create an OpenUP agent team..." | Role-based collaboration |
| **Edit tools** | Agents automatically use Edit/Write | Modify code and documentation |
| **Bash tool** | Agents automatically run git commands | Branching, committing, PRs |

**Key Navigation** (in-process team mode):
- `Shift+Up/Down` - Cycle through active teammates
- `Shift+Left/Right` - Switch between agent and user view

### Creating Your First Project

**Option 1: Bootstrap Script (Recommended)**

```bash
# From the open-up-for-ai-agents directory
./scripts/bootstrap-project.sh my-project --base-dir ~/projects
cd ~/projects/my-project
```

**Option 2: Manual Copy**

```bash
# Copy template files to your project
cp -r docs-eng-process/* /path/to/your-project/docs-eng-process/
cp AGENTS.md README.md /path/to/your-project/
mkdir -p /path/to/your-project/docs
```

After setup, continue to [Part 2: Project Setup](#part-2-project-setup).

---

## Part 2: Project Setup

### Using the Bootstrap Script

The bootstrap script (`scripts/bootstrap-project.sh`) creates a new project with:

1. **docs-eng-process/** - Engineering process documentation (do not modify)
2. **docs/** - Empty directory for project artifacts
3. **.claude/** - Agent team configuration
4. **.git/** - Initialized git repository

```bash
./scripts/bootstrap-project.sh my-project --base-dir ~/projects
```

**What the script does:**
- Copies essential template files
- Creates git repository with initial commit
- Sets up agent team templates
- Prints next steps

### Initial Project Structure

After bootstrapping, your project structure looks like:

```
my-project/
├── docs-eng-process/          # Engineering process (DO NOT MODIFY)
│   ├── README.md              # Process entry point
│   ├── agent-workflow.md      # Agent SOP
│   ├── skills-guide.md        # Skills documentation
│   ├── teams-guide.md         # Teams documentation
│   ├── templates/             # Document templates
│   └── openup-knowledge-base/ # OpenUP reference
├── docs/                      # Project artifacts (YOUR WORK GOES HERE)
│   ├── project-status.md      # Current state (created during init)
│   ├── roadmap.md             # Task backlog (created during init)
│   ├── vision.md              # Project vision (created during init)
│   ├── risk-list.md           # Risks (created during init)
│   ├── phases/                # Phase-specific documentation
│   │   └── inception/         # Created during init
│   └── agent-logs/            # Execution logs (created by agents)
├── .claude/                   # Claude Code configuration
│   ├── teammates/             # Role instructions
│   ├── teams/                 # Team configurations
│   └── CLAUDE.md              # Project instructions
└── scripts/                   # Utility scripts
```

### Understanding docs/ vs docs-eng-process/

| Directory | Purpose | Should You Modify? |
|-----------|---------|-------------------|
| **docs-eng-process/** | Authoritative engineering process | **NO** - This is the template |
| **docs/** | Project-specific artifacts | **YES** - All your work goes here |

**Rule**: If a file is in `docs-eng-process/`, it's process documentation. If it's in `docs/`, it's your project's work product.

### Running the Initialization Prompts

After bootstrapping, initialize your project using AI agents with the two-prompt flow:

**Step 1: Copy Prompt A from `docs-eng-process/init-prompts.md`**

```
You are initializing a brand-new project using this repo as a template.

Project information:
- Project name: YourProjectName
- One-sentence description: Your description here
- Target users (optional): Your target users

[... rest of Prompt A ...]
```

**Step 2: Copy Prompt B from `docs-eng-process/init-prompts.md`**

After Prompt A completes, run Prompt B for the Vision document Q&A.

**What the prompts create:**
- `docs/project-status.md` - Project state (phase=inception, iteration=1)
- `docs/roadmap.md` - Initial task backlog
- `docs/vision.md` - Project vision (partially filled)
- `docs/risk-list.md` - Risk tracking
- `docs/phases/inception/` - Phase documentation

### Enabling Agent Teams

Agent teams must be enabled before use:

```bash
# Enable in current shell
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# Add to ~/.bashrc or ~/.zshrc for persistence
echo 'export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1' >> ~/.bashrc
```

**Verify agent teams are enabled:**

When you type "Create an OpenUP agent team...", Claude should spawn multiple teammates.

---

## Part 3: Core Concepts

### The Four OpenUP Phases

```
Inception → Elaboration → Construction → Transition
   ↓              ↓               ↓              ↓
Define Scope   Architecture     Build         Deploy
Vision         Baseline        Incrementally
```

| Phase | Focus | Duration | Key Artifacts |
|-------|-------|----------|---------------|
| **Inception** | Define scope, vision, feasibility | Short (1-2 weeks) | Vision, Risk List, Initial Roadmap |
| **Elaboration** | Establish architecture baseline | Medium (2-4 weeks) | Architecture Notebook, Detailed Use Cases |
| **Construction** | Build the system incrementally | Long (multiple iterations) | Code, Tests, Working Software |
| **Transition** | Deploy to users | Variable | Deployment, User Acceptance |

### Project State Documents

#### docs/project-status.md
**Single source of truth** for project state. Contains:
- Current phase and iteration
- Iteration goal
- Project status (not-started, in-progress, blocked, completed)
- Active work items
- Blockers

**Agents read this file at the start of every run.**

#### docs/roadmap.md
Prioritized task backlog. Contains:
- Task IDs (T-001, T-002, etc.)
- Descriptions
- Priorities (high, medium, low)
- Status (pending, in-progress, completed)
- Dependencies

**Agents select tasks from this file based on priority and iteration goals.**

#### docs/vision.md
Project vision document. Created in Inception, refined throughout.

#### docs/risk-list.md
Risk tracking and mitigation strategies.

#### docs/architecture-notebook.md
Architecture decisions and constraints (created in Elaboration).

### Agent Teams and Roles

| Role | Focus | When to Use |
|------|-------|-------------|
| **analyst** | Requirements, stakeholder communication | Inception, feature definition |
| **architect** | Architecture design, technical decisions | Elaboration, technical spikes |
| **developer** | Implementation, unit testing | Construction, bug fixes |
| **project-manager** | Planning, coordination | All phases, planning tasks |
| **tester** | Test planning, execution | Construction, Transition |

**Team patterns:**
- **Phase teams** - Optimized for specific phases (Inception, Elaboration, etc.)
- **Task teams** - Optimized for specific work (Feature, Investigation, Planning)

### Skills Reference

Skills are invoked with `/skill-name`. See [Part 6: Skills Reference](#part-6-skills-reference) for complete reference.

**Quick summary:**
- `/inception`, `/elaboration`, `/construction`, `/transition` - Phase guidance
- `/start-iteration`, `/complete-task`, `/log-run` - Workflow automation
- `/create-vision`, `/create-use-case`, `/create-architecture-notebook` - Artifact creation
- `/create-pr` - Pull request creation with task context

### Branching Strategy

OpenUP uses a simple branching model:

```
trunk (main/master)
  ↑
  └── feature/T-001-description  (work happens here)
  └── fix/T-002-bug-description
```

**Rules:**
1. Never work directly on trunk
2. Create a new branch for each task
3. Merge or create PR before starting new task
4. Use descriptive branch names with task IDs

---

## Part 4: Common Workflows (Quick Reference)

### Workflow Checklists

#### Starting a New Project
- [ ] Run bootstrap script
- [ ] Run Prompt A (project setup)
- [ ] Run Prompt B (Vision Q&A)
- [ ] Review docs/vision.md and docs/roadmap.md
- [ ] Enable agent teams (optional)

#### Adding a Feature Idea
- [ ] Read docs/roadmap.md
- [ ] Document feature or use `/request-input`
- [ ] Update docs/roadmap.md with new task
- [ ] Set priority and status

#### Developing a Planned Feature
- [ ] Read docs/project-status.md and docs/roadmap.md
- [ ] Select task from roadmap
- [ ] Create feature team (optional)
- [ ] Implement following OpenUP workflow
- [ ] Use `/complete-task task_id: T-XXX`
- [ ] Use `/create-pr` for pull request

#### Implementing a Task from Scratch
- [ ] Ensure docs/project-status.md exists
- [ ] Define task in docs/roadmap.md
- [ ] Select appropriate phase and iteration
- [ ] Use `/start-iteration` if needed
- [ ] Create appropriate agent team
- [ ] Implement following OpenUP practices
- [ ] Complete with `/complete-task` and `/log-run`

#### Continuing Work on Roadmap
- [ ] Read docs/project-status.md
- [ ] Read docs/roadmap.md
- [ ] Select next task by priority
- [ ] Use: "Continue with next task from roadmap"
- [ ] Agent handles branch, execution, completion

#### Fixing a Bug
- [ ] Add bug to docs/roadmap.md
- [ ] Create investigation team
- [ ] Team analyzes and fixes
- [ ] Update docs/roadmap.md
- [ ] Use `/complete-task` and `/create-pr`

#### Registering/Tracking Bugs
- [ ] Create bug entry in docs/roadmap.md
- [ ] Include: Task ID, description, priority, status
- [ ] Optionally create input request for details
- [ ] Optionally create test case documenting bug

#### Running an Iteration
- [ ] Use `/start-iteration`
- [ ] Execute tasks from roadmap
- [ ] Update docs/phases/{phase}/notes.md
- [ ] Review iteration completion
- [ ] Plan next iteration

#### Phase Transitions
- [ ] Use `/phase-review`
- [ ] Verify completion criteria
- [ ] Schedule phase review meeting
- [ ] Update docs/project-status.md
- [ ] Begin next phase

---

## Part 5: Common Workflows (Detailed)

### Starting a New Project (from Scratch)

**Prerequisites:** None

**Step-by-step:**

1. **Bootstrap the project:**
   ```bash
   ./scripts/bootstrap-project.sh my-project --base-dir ~/projects
   cd ~/projects/my-project
   ```

2. **Run Prompt A (technical setup):**
   - Copy Prompt A from `docs-eng-process/init-prompts.md`
   - Replace placeholders: `<YOUR_PROJECT_NAME>`, `<ONE_TO_TWO_SENTENCE_DESCRIPTION>`
   - Paste into Claude Code
   - Agent creates: docs structure, initial files

3. **Run Prompt B (Vision Q&A):**
   - Copy Prompt B from `docs-eng-process/init-prompts.md`
   - Paste into Claude Code
   - Agent asks questions in batches
   - Vision document is created incrementally

4. **Review and adjust:**
   - Read `docs/vision.md`
   - Read `docs/roadmap.md`
   - Adjust priorities if needed

5. **Enable agent teams (optional):**
   ```bash
   export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
   ```

**Example prompt to start work:**
```
Continue with the next task from docs/roadmap.md. Follow the OpenUP workflow.
```

**Expected outcome:**
- Project initialized with Inception phase
- Vision document with core sections filled
- Roadmap with initial tasks
- Agent begins executing first task

---

### Adding a Feature Idea

**Prerequisites:**
- Project initialized (docs/roadmap.md exists)

**Step-by-step:**

1. **Read current roadmap:**
   - Open `docs/roadmap.md`
   - Understand existing tasks and priorities

2. **Document the feature:**
   - Option A: Ask agent to document it
     ```
     Add a new task to docs/roadmap.md for [feature description].
     Set priority to high and link to existing use case UC-001 if applicable.
     ```
   - Option B: Use `/request-input` for stakeholder input
     ```
     /request-input title: "Feature Request: [feature name]"
       context: "Need to document this feature idea"
       questions: '[{"type": "text", "question": "What problem does this solve?"}]'
     ```

3. **Update roadmap:**
   - Add task with format: `T-XXX | [description] | [priority] | pending`
   - Include acceptance criteria if known
   - Link to related use cases or create placeholder

4. **Set priority and status:**
   - Priority: high, medium, or low
   - Status: pending (will be updated when work begins)

**Example prompt:**
```
Add a new task to docs/roadmap.md for implementing user authentication.
Description: Users should be able to log in with email/password and social providers.
Priority: high
Create a placeholder use case UC-010 for this feature.
```

**Expected outcome:**
- New task in roadmap with task ID
- Placeholder use case created if specified
- Feature ready for prioritization and planning

---

### Developing a Planned Feature

**Prerequisites:**
- Feature exists in docs/roadmap.md
- docs/project-status.md exists

**Step-by-step:**

1. **Read project state:**
   ```
   Read docs/project-status.md to understand current phase and iteration.
   ```

2. **Select the task from roadmap:**
   - Open `docs/roadmap.md`
   - Find the feature task (e.g., T-005)
   - Note priority and dependencies

3. **Create branch (agent does this):**
   - Agent detects trunk and creates feature branch
   - Format: `feature/T-005-user-authentication`

4. **Create feature team (optional):**
   ```
   Create an OpenUP agent team for implementing user authentication.

   Spawn:
   - analyst: to define acceptance criteria
   - architect: to design the authentication architecture
   - developer: to implement the feature
   - tester: to create and execute tests

   The analyst should first update UC-010 with acceptance criteria,
   then the architect should design the architecture, then the
   developer should implement with tests.
   ```

5. **Agent executes following OpenUP workflow:**
   - Analyst: Updates use case, defines acceptance criteria
   - Architect: Creates/updates architecture notebook
   - Developer: Implements feature with unit tests
   - Tester: Creates test cases, executes tests

6. **Complete task:**
   ```
   /complete-task task_id: T-005
   ```
   This commits changes, updates roadmap, creates logs.

7. **Create pull request:**
   ```
   /create-pr task_id: T-005
   ```

**Example prompt:**
```
Implement task T-005 from the roadmap: User authentication.
Create a feature team and follow the OpenUP workflow.
Use /complete-task when done and create a PR.
```

**Expected outcome:**
- Feature implemented with tests
- Documentation updated (use cases, architecture)
- Changes committed
- Roadmap updated
- Pull request created with task context

---

### Implementing a Task from Scratch

**Prerequisites:**
- Project initialized (docs/project-status.md exists)

**Step-by-step:**

1. **Ensure project is initialized:**
   - Check `docs/project-status.md` exists
   - If not, run initialization prompts first

2. **Define the task:**
   - If task doesn't exist in docs/roadmap.md, add it:
     ```
     Add task T-101 to docs/roadmap.md: Fix login bug where users are not redirected properly.
     Priority: high, Status: pending
     ```

3. **Select appropriate phase and iteration:**
   - Read `docs/project-status.md`
   - Verify current phase matches task type
   - If not, note the phase mismatch

4. **Start new iteration if needed:**
   ```
   /start-iteration iteration_number: 2 goal: "Fix critical login bugs"
   ```

5. **Create appropriate agent team:**
   - For bug: investigation team
   - For feature: feature team
   - For architecture: architect + developer

6. **Agent follows SOP:**
   - Reads project-status.md
   - Selects task from roadmap.md
   - Creates branch
   - Implements following OpenUP practices

7. **Complete and log:**
   ```
   /complete-task task_id: T-101
   /log-run
   ```

**Example prompt:**
```
Implement task T-101: Fix login redirect bug.
This is in the Construction phase. Create an investigation team
to find the root cause and fix it. Complete the task when done.
```

**Expected outcome:**
- Bug fixed with tests
- Root cause documented
- Changes committed
- Task marked complete in roadmap
- Logs created

---

### Continuing Work on the Roadmap

**Prerequisites:**
- docs/roadmap.md exists with pending tasks

**Step-by-step:**

1. **Read project status:**
   - Agent reads `docs/project-status.md`
   - Extracts current phase, iteration, iteration goal

2. **Read roadmap:**
   - Agent reads `docs/roadmap.md`
   - Filters for pending tasks
   - Selects highest priority task

3. **Simple prompt continues work:**
   ```
   Continue with the next task from the roadmap.
   ```

4. **Agent handles:**
   - Branch creation
   - Task execution
   - Completion and logging

5. **Review and merge:**
   - Review pull request when ready
   - Merge to trunk
   - Repeat for next task

**Example prompt:**
```
Continue with the next high-priority task from docs/roadmap.md.
Follow the OpenUP workflow and create a PR when done.
```

**Expected outcome:**
- Next task selected automatically
- Work completed following OpenUP
- PR created for review

---

### Fixing a Bug

**Prerequisites:**
- Project initialized

**Step-by-step:**

1. **Add bug to roadmap (if not already tracked):**
   ```
   Add bug T-201 to docs/roadmap.md:
   Description: API endpoint returns 500 when user has no profile
   Priority: high
   Status: pending
   Related component: User service
   ```

2. **Create investigation team:**
   ```
   Create an OpenUP investigation team for the profile API 500 error.

   Spawn:
   - architect: to analyze the architecture and identify potential causes
   - developer: to find the root cause in the code
   - tester: to reproduce the bug and verify the fix
   ```

3. **Team executes:**
   - Tester: Reproduces bug, documents steps
   - Architect: Analyzes code, identifies root cause
   - Developer: Implements fix with tests

4. **Update roadmap:**
   - Change status to completed
   - Add notes about fix

5. **Complete and create PR:**
   ```
   /complete-task task_id: T-201 create_pr: true
   ```

**Example prompt:**
```
Fix the API 500 error documented in T-201.
Create an investigation team. Find the root cause,
implement a fix with tests, and create a PR.
```

**Expected outcome:**
- Bug reproduced and documented
- Root cause identified
- Fix implemented with regression tests
- PR created with bug context

---

### Registering/Tracking Bugs

**Prerequisites:**
- Project initialized

**Step-by-step:**

1. **Create bug entry in roadmap:**
   - Open `docs/roadmap.md`
   - Add entry following format:

   ```markdown
   ### Bugs

   | ID | Description | Priority | Status | Component |
   |----|-------------|----------|--------|-----------|
   | T-301 | Null pointer exception in checkout flow | high | pending | Payment service |
   | T-302 | UI glitch on mobile Safari | medium | pending | Frontend |
   ```

2. **Include required information:**
   - **Task ID**: Unique identifier (T-XXX)
   - **Description**: What the bug is
   - **Priority**: high, medium, low
   - **Status**: pending (will be updated when fixed)
   - **Related component**: Which service/feature is affected

3. **Optionally create input request:**
   ```
   /request-input title: "Bug T-301 Details"
     context: "Need more information about the null pointer exception"
     questions: '[{"type": "text", "question": "What steps reproduce this bug?"}]'
     related_task: T-301
   ```

4. **Optionally create test case:**
   ```
   /create-test-plan scope: "checkout flow null pointer exception"
   ```

**Example prompt:**
```
Add bug T-301 to docs/roadmap.md:
Description: Checkout flow crashes with null pointer when user has no saved payment methods
Priority: high
Component: Payment service
Create a test case documenting the reproduction steps.
```

**Expected outcome:**
- Bug tracked in roadmap
- Stakeholder input requested if needed
- Test case created for reproduction
- Bug ready to be prioritized and fixed

---

### Running an Iteration

**Prerequisites:**
- docs/project-status.md exists
- docs/roadmap.md has pending tasks

**Step-by-step:**

1. **Start the iteration:**
   ```
   /start-iteration iteration_number: 3 goal: "Complete user profile management"
   ```

2. **Agent does:**
   - Reads project-status.md
   - Checks for answered input requests
   - Creates new branch
   - Updates iteration in project-status.md
   - Logs initialization

3. **Execute tasks:**
   - Select tasks from roadmap aligned with iteration goal
   - Execute following OpenUP workflow
   - Update phase notes as you go

4. **Update phase notes:**
   - Document progress in `docs/phases/{phase}/notes.md`
   - Track decisions and issues

5. **Review iteration completion:**
   - Check if iteration goal achieved
   - Review completed tasks
   - Identify carry-over items

6. **Plan next iteration:**
   ```
   /create-iteration-plan iteration_number: 4
   ```

**Example prompt:**
```
Start iteration 3 with goal: "Complete user profile management".
Then execute the tasks T-010 through T-015 from the roadmap.
Update phase notes as you progress.
```

**Expected outcome:**
- Iteration initialized
- Tasks completed
- Phase notes updated
- Ready for next iteration

---

### Phase Transitions

**Prerequisites:**
- Current phase completion criteria met

**Step-by-step:**

1. **Review phase completion:**
   ```
   /phase-review
   ```

2. **Agent checks:**
   - Reads completion criteria from docs/project-status.md
   - Reviews work products
   - Generates review summary

3. **Schedule phase review meeting:**
   - Share review summary with stakeholders
   - Get sign-off on phase completion

4. **Update project status:**
   - Change phase in docs/project-status.md
   - Reset iteration to 1
   - Set new iteration goal

5. **Begin next phase:**
   ```
   /elaboration activity: initiate
   ```

**Example prompt:**
```
Review the Inception phase for completion.
If all criteria are met, prepare for transition to Elaboration phase.
Do not advance phase until I confirm.
```

**Expected outcome:**
- Phase completion status documented
- Review materials prepared
- Ready for stakeholder review
- Phase can be advanced after approval

---

## Part 6: Skills Reference

### Skills Quick Reference Table

| Skill | Purpose | Arguments | When to Use |
|-------|---------|-----------|-------------|
| `/inception` | Guide Inception phase | `activity: initiate\|check-status\|next-steps` | Starting/working in Inception |
| `/elaboration` | Guide Elaboration phase | `activity: initiate\|check-status\|next-steps` | Starting/working in Elaboration |
| `/construction` | Guide Construction phase | `activity: initiate\|check-status\|next-steps` | Starting/working in Construction |
| `/transition` | Guide Transition phase | `activity: initiate\|check-status\|next-steps` | Starting/working in Transition |
| `/create-vision` | Generate vision document | `project_name`, `problem_statement` | Need vision document |
| `/create-use-case` | Create use case spec | `use_case_name`, `primary_actor`, `description` | Documenting requirements |
| `/create-architecture-notebook` | Generate/update architecture docs | `system_name`, `architectural_concerns` | Architecture work |
| `/create-risk-list` | Create/update risk assessment | `risks` (JSON) | Risk identification |
| `/create-iteration-plan` | Plan iteration | `iteration_number` | Planning iterations |
| `/create-test-plan` | Generate test cases | `scope` | Test planning |
| `/start-iteration` | Begin new iteration | `iteration_number`, `goal` | Starting iteration |
| `/complete-task` | Mark task complete, commit, update | `task_id`, `commit_message`, `create_pr` | Finishing work |
| `/create-pr` | Create pull request with task context | `task_id`, `branch`, `title`, `base` | Ready for review |
| `/request-input` | Create input request document | `title`, `questions`, `context`, `related_task` | Need stakeholder input |
| `/phase-review` | Check phase completion | `phase` | Phase nearing completion |
| `/log-run` | Create traceability logs | `run_id` | Ending agent run |

### When to Use Each Skill

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
| Creating pull request | `/create-pr` |
| Need stakeholder input | `/request-input` |
| Phase nearly complete | `/phase-review` |
| Ending agent run | `/log-run` |
| Testing needed | `/create-test-plan` |

### Skill Examples

#### Phase Skills
```
/inception activity: initiate
/elaboration activity: next-steps
/construction activity: check-status
```

#### Artifact Skills
```
/create-vision project_name: "TaskManager" problem_statement: "Teams need better tracking"
/create-use-case use_case_name: "Create Task" primary_actor: "User" description: "User creates task"
/create-architecture-notebook system_name: "TaskManager" architectural_concerns: "scalability, security"
```

#### Workflow Skills
```
/start-iteration iteration_number: 2 goal: "Implement user authentication"
/complete-task task_id: T-005 create_pr: true
/create-pr task_id: T-005 base: develop
/request-input title: "Feature Scope" context: "Need to clarify scope" questions: '[{"type":"text","question":"What are the core features?"}]'
/phase-review
/log-run
```

---

## Part 7: Agent Teams Reference

### Available Roles

| Role | Focus | Key Work Products | When to Use |
|------|-------|-------------------|-------------|
| **analyst** | Requirements, stakeholder communication | Vision, Use Cases, Requirements | Inception, feature definition |
| **architect** | Architecture design, technical decisions | Architecture Notebook | Elaboration, technical spikes |
| **developer** | Implementation, unit testing | Design, Code, Unit Tests | Construction, bug fixes |
| **project-manager** | Planning, coordination | Project Plan, Iteration Plan, Risk List | All phases, planning |
| **tester** | Test planning, execution | Test Cases, Test Scripts, Test Logs | Construction, Transition |

### Team Configurations

#### Phase-Specific Teams

**Inception Team** (analyst, project-manager, architect as needed)
```
Create an OpenUP agent team for the Inception phase.

Spawn teammates for:
- analyst: to lead requirements gathering and vision definition
- project-manager: to lead planning and coordination
```

**Elaboration Team** (architect, developer, tester, analyst as needed)
```
Create an OpenUP agent team for the Elaboration phase.

Spawn teammates for:
- architect: to lead architecture design
- developer: to implement the architectural baseline
- tester: to validate the architecture through testing
```

**Construction Team** (developer, tester, architect as needed)
```
Create an OpenUP agent team for the Construction phase.

Spawn teammates for:
- developer: to lead implementation
- tester: to lead testing and quality assurance
```

**Transition Team** (tester, developer, project-manager, analyst as needed)
```
Create an OpenUP agent team for the Transition phase.

Spawn teammates for:
- tester: to lead final testing and validation
- developer: to fix bugs and support deployment
- project-manager: to coordinate deployment and release
```

#### Task-Specific Teams

**Full Team** (all roles)
```
Create an OpenUP agent team with all roles: analyst, architect,
developer, project-manager, and tester.

Each teammate should follow their role instructions in
.claude/teammates/{role}.md.
```

**Feature Team** (analyst, architect, developer, tester)
```
Create an OpenUP agent team for feature implementation.

Spawn teammates for:
- analyst: to gather requirements and define acceptance criteria
- architect: to design the feature architecture
- developer: to implement the feature
- tester: to create and execute tests

The analyst should first create use cases, then the architect
should design, then the developer should implement with tests.
```

**Investigation Team** (architect, developer, tester)
```
Create an OpenUP investigation team to investigate [issue description].

Spawn teammates for:
- architect: to analyze the architecture and identify root causes
- developer: to analyze the code and implement the fix
- tester: to reproduce the issue and verify the fix
```

**Planning Team** (project-manager, analyst, architect as needed)
```
Create an OpenUP agent team for iteration planning.

Spawn teammates for:
- project-manager: to lead the planning session
- analyst: to review and prioritize requirements
- architect: to assess technical feasibility
```

### Choosing the Right Team

| Situation | Use This Team |
|-----------|--------------|
| Starting a new project | Inception Team |
| Defining architecture | Elaboration Team |
| Building features | Construction Team |
| Preparing for release | Transition Team |
| Implementing a feature | Feature Team |
| Debugging an issue | Investigation Team |
| Planning iteration | Planning Team |
| Comprehensive work | Full Team |

---

## Part 8: Configuration

### Setting Up Claude Code (Brief Refresher)

Claude Code should already be installed. Key features for OpenUP:

1. **Terminal access** - Agents can run git commands
2. **File editing** - Agents can modify project files
3. **Skills** - Invoke with `/skill-name`
4. **Agent Teams** - Multiple agents collaborate

For full Claude Code documentation, see: https://code.claude.com/docs/en/agent-teams

### Enabling Agent Teams

**Required for team functionality:**

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

**Persist in shell config:**
```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1' >> ~/.bashrc
source ~/.bashrc
```

**Verify enabled:**
When you type "Create an OpenUP agent team...", Claude should spawn multiple teammates.

### Quality Hooks (settings.json)

Optional quality enforcement in `.claude/settings.json`:

**Copy the example:**
```bash
cp docs-eng-process/.claude-templates/settings.json.example .claude/settings.json
```

**What the hooks do:**

| Hook | Trigger | Action |
|------|---------|--------|
| Pre-commit | Before git commit | Check for project-status.md |
| Post-edit | After file edit | Prompt to update docs/ |
| Post-commit | After git commit | Prompt to update Active Work Items |
| Post-push | After git push | Prompt to create PR |
| Stop | Before agent stops | Verify completion criteria |

**Customize hooks** by editing `.claude/settings.json`.

---

## Part 9: Documentation Issues & Fixes

### Known Inconsistencies in Current Documentation

#### 1. CLAUDE.md Location Confusion

**Issue:** CLAUDE.md exists in two locations:
- Root directory: `.claude/CLAUDE.md` (ACTIVE - this is what agents use)
- Template directory: `docs-eng-process/.claude-templates/CLAUDE.md` (TEMPLATE)

**Fix:** The root `.claude/CLAUDE.md` is authoritative. The template is for new projects. When updating from template, compare both and merge changes.

#### 2. Skills Documentation vs Implementation

**Issue:** Some skills documented in `skills-guide.md` may not exist in `.claude/skills/`.

**Fix:** Check `.claude/skills/` for actual skill files. Documented skills may be planned but not yet implemented.

**Workaround:** If a skill doesn't exist, follow the manual workflow described in the skill documentation.

#### 3. Team Templates vs Active Teams

**Issue:** Many team templates exist in `docs-eng-process/.claude-templates/teams/` but only one is typically in `.claude/teams/`.

**Fix:** Team templates are available but not installed by default. To use additional teams:

1. Copy template to `.claude/teams/`:
   ```bash
   cp docs-eng-process/.claude-templates/teams/openup-feature-team.md .claude/teams/
   ```

2. Reference by name when creating teams.

#### 4. Documentation Split

**Issue:** Getting started info is scattered across multiple files:
- `getting-started.md`
- `init-prompts.md`
- `README.md`

**Fix:** This USER-GUIDE.md consolidates all user-facing information.

### Recommended File Locations

| File Type | Location | Purpose |
|-----------|----------|---------|
| Project artifacts | `docs/` | All your project work |
| Process docs | `docs-eng-process/` | DO NOT MODIFY (template) |
| Skills | `.claude/skills/` | Active skills (installed) |
| Team configs | `.claude/teams/` | Active team configs (installed) |
| Role instructions | `.claude/teammates/` | Role-specific instructions |
| Claude settings | `.claude/settings.json` | Claude Code config |
| Templates | `docs-eng-process/templates/` | Reference for creating docs |

### How to Update from Template

If you have an existing project and want to update to the latest template:

**Option 1: Git Submodule (Recommended)**
```bash
git submodule add https://github.com/GermanDZ/open-up-for-ai-agents.git .openup-template
```

**Option 2: Manual Copy**
```bash
# Compare and copy individual files
cp docs-eng-process/.claude-templates/CLAUDE.md .claude/CLAUDE.md.backup
cp -r /path/to/new-template/docs-eng-process/* docs-eng-process/
```

**Caution:** Never overwrite your `docs/` directory when updating.

---

## Part 10: Troubleshooting

### Common Issues and Solutions

#### Agent Teams Not Appearing

**Symptom:** When you create a team, only one agent appears.

**Solutions:**
1. Check agent teams are enabled:
   ```bash
   echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS
   # Should output: 1
   ```
2. If not enabled:
   ```bash
   export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
   ```
3. Press `Shift+Down` to cycle through teammates (in-process mode)

#### Teammates Stop on Errors

**Symptom:** A teammate stops working and shows an error.

**Solutions:**
1. Check their output using `Shift+Up` (in-process) or click pane (split)
2. Give additional instructions to the teammate
3. Spawn a replacement teammate if needed

#### Changes Not Committed

**Symptom:** Agent stopped without committing changes.

**Solutions:**
1. Check for uncommitted changes:
   ```bash
   git status
   ```
2. If changes exist, remind agent to commit:
   ```
   Please commit the uncommitted changes before stopping.
   Follow the End-of-Run SOP.
   ```
3. If agent has stopped, manually commit:
   ```bash
   git add -A
   git commit -m "Manual commit: [description]"
   ```

#### Can't Find Task in Roadmap

**Symptom:** Agent can't find the task you mentioned.

**Solutions:**
1. Verify task exists in `docs/roadmap.md`
2. Check task ID format (T-001, not T001)
3. Ensure task has `status: pending`

#### Branch Already Exists

**Symptom:** Agent tries to create branch that already exists.

**Solutions:**
1. Check current branch:
   ```bash
   git branch
   ```
2. If on existing feature branch, continue there
3. If need new branch, delete or rename existing:
   ```bash
   git branch -D feature/old-name
   ```

#### Skills Not Found

**Symptom:** `/skill-name` returns "skill not found".

**Solutions:**
1. Check skill exists in `.claude/skills/`:
   ```bash
   ls .claude/skills/
   ```
2. If missing, copy from template:
   ```bash
   cp docs-eng-process/.claude-templates/skills/skill-name.md .claude/skills/
   ```
3. Use manual workflow as fallback

#### Project Status Missing

**Symptom:** Agent can't find `docs/project-status.md`.

**Solutions:**
1. Initialize project using Prompt A from `init-prompts.md`
2. Or manually create following template in `agent-workflow.md`

### FAQ

**Q: Should I modify files in `docs-eng-process/`?**
A: No. These are template/process files. Modify only files in `docs/`.

**Q: How do I know which phase I'm in?**
A: Check `docs/project-status.md` for the `phase` field.

**Q: Can I skip the Inception phase?**
A: Not recommended. Inception establishes vision and scope. If you have a clear vision, you can accelerate through it but should still document key artifacts.

**Q: Do I need to use agent teams?**
A: No. Agent teams are optional. Single-agent workflows work fine for small tasks.

**Q: How often should I commit?**
A: At least once per task. More frequent commits are better for complex tasks.

**Q: What if the branch naming convention differs?**
A: Follow your project's convention. The key is descriptive names with task IDs when possible.

**Q: Can I work on multiple tasks in one branch?**
A: Not recommended. One task per branch ensures clean history and easier reviews.

**Q: How do I recover if the agent stops mid-task?**
A: Just continue with your next prompt. The agent will read project-status.md and can resume.

**Q: What if I disagree with the agent's approach?**
A: Provide corrective feedback. Agents follow your guidance. You can redirect at any time.

### Getting Help

- **Documentation:** See `docs-eng-process/README.md` for process docs
- **Agent Workflow:** See `docs-eng-process/agent-workflow.md` for detailed SOP
- **Skills:** See `docs-eng-process/skills-guide.md` for skill reference
- **Teams:** See `docs-eng-process/teams-guide.md` for team reference
- **Issues:** Report issues at https://github.com/GermanDZ/open-up-for-ai-agents/issues

---

## Appendix: File Structure Reference

### Complete Project Structure

```
my-project/
├── docs/                          # YOUR PROJECT ARTIFACTS
│   ├── project-status.md          # Current state (EDIT THIS)
│   ├── roadmap.md                 # Task backlog (EDIT THIS)
│   ├── vision.md                  # Project vision (EDIT THIS)
│   ├── risk-list.md               # Risks (EDIT THIS)
│   ├── architecture-notebook.md   # Architecture (EDIT THIS)
│   ├── phases/                    # Phase-specific docs
│   │   ├── inception/
│   │   │   ├── overview.md        # Phase overview
│   │   │   └── notes.md           # Phase notes
│   │   ├── elaboration/
│   │   ├── construction/
│   │   └── transition/
│   ├── use-cases/                 # Use case specifications
│   ├── agent-logs/                # Execution logs
│   │   ├── YYYY/MM/DD/            # Daily logs
│   │   └── agent-runs.jsonl       # Log index
│   └── input-requests/            # Async stakeholder communication
│       ├── archive/               # Processed requests
│       └── YYYY-MM-DD-topic.md    # Active requests
├── docs-eng-process/              # ENGINEERING PROCESS (DO NOT MODIFY)
│   ├── README.md                  # Process entry point
│   ├── agent-workflow.md          # Agent SOP
│   ├── skills-guide.md            # Skills reference
│   ├── teams-guide.md             # Teams reference
│   ├── getting-started.md         # Setup instructions
│   ├── init-prompts.md            # Initialization prompts
│   ├── USER-GUIDE.md              # This file
│   ├── QUICK-REFERENCE.md         # Quick reference card
│   ├── templates/                 # Document templates
│   │   ├── vision.md
│   │   ├── risk-list.md
│   │   ├── input-request.md
│   │   └── ...
│   ├── .claude-templates/         # Claude Code templates
│   │   ├── CLAUDE.md
│   │   ├── settings.json.example
│   │   ├── teammates/             # Role instructions
│   │   ├── teams/                 # Team configs
│   │   └── skills/                # Skills
│   └── openup-knowledge-base/     # OpenUP reference
├── .claude/                       # CLAUDE CODE CONFIG
│   ├── CLAUDE.md                  # Project instructions
│   ├── settings.json              # Claude settings
│   ├── teammates/                 # Installed role instructions
│   ├── teams/                     # Installed team configs
│   └── skills/                    # Installed skills
├── scripts/                       # UTILITY SCRIPTS
│   ├── setup-agent-teams.sh       # Install agent teams
│   └── update-from-template.sh    # Update from template
├── AGENTS.md                      # Agent entry point
├── README.md                      # Project README
└── .gitignore                     # Git ignore rules
```

---

**End of User Guide**

For detailed process documentation, see:
- [agent-workflow.md](agent-workflow.md) - Complete Agent SOP
- [skills-guide.md](skills-guide.md) - Skills Reference
- [teams-guide.md](teams-guide.md) - Teams Reference

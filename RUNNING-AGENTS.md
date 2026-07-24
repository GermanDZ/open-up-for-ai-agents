# Running AI Agents via CLI

This document explains how to run AI agents (Cursor CLI or Claude Code) to execute a single OpenUP task cycle following this repository's development process.

## One Agent Run = One Roadmap Task

**By default, each agent run completes exactly one task from `docs/roadmap.md`.**

The agent will:
1. Read `docs/project-status.md` to establish context (phase, iteration, goals)
2. Read `docs/roadmap.md` and select the next pending task (highest priority if multiple)
3. Verify the task aligns with the current phase and iteration goals
4. **Create a branch (if on trunk)** - MANDATORY before starting any work
5. Complete the task following role-based execution and commit policies
6. Create traceability logs in `docs/agent-logs/`
7. Stop after completing the single task

This ensures focused, traceable work that aligns with the OpenUP process.

## Preflight Checklist

Before running an agent, verify:

- [ ] **Project initialized**: `docs/project-status.md` and `docs/roadmap.md` exist
- [ ] **Current directory**: You're in the repository root (where `docs-eng-process/` is visible)
- [ ] **State docs permissions**: You're ready to approve updates to `docs/project-status.md` and `docs/roadmap.md` (agents must ask permission by default)
- [ ] **Git status**: Working directory is clean or you understand what changes will be committed
- [ ] **Commit expectation**: You understand that agents MUST commit all changes before stopping (see [End-of-Run SOP](docs-eng-process/agent-workflow.md#end-of-run-sop))

## Canonical Prompt Template

Use this prompt template to ensure agents follow the repository's process. Copy and paste it, then customize the task-specific instructions if needed.

```text
Execute the next task from the roadmap following the OpenUP development process.

You MUST follow [docs-eng-process/agent-workflow.md](docs-eng-process/agent-workflow.md) procedures exactly:

1. **Start-of-Run SOP**:
   - Read `docs/project-status.md` to establish context (phase, iteration, iteration_goal, status)
   - If status is "blocked", report blockers and request guidance before proceeding
   - If status is "completed", propose phase transition (do not auto-advance)
   - Read `docs/roadmap.md` and select the next pending task (highest priority if multiple)
   - Verify the task aligns with current phase and iteration goals
   - **Create branch (if needed)**: Detect trunk branch (origin/HEAD → main → master → current). If on trunk, **MANDATORY** - create a new branch before starting work. If not on trunk, continue on current branch.

2. **Create Branch (MANDATORY before starting work)**:
   - This step is part of Start-of-Run SOP Step 4, but emphasized here for clarity
   - **MANDATORY**: If you are on trunk, you MUST create a new branch before starting any work
   - Use descriptive branch name following project conventions (feature/, fix/, refactor/, etc.)
   - Record branch name and trunk detection for traceability logs
   - **Do NOT proceed to Role-Based Execution until you are on a non-trunk branch**

3. **Role-Based Execution**:
   - Choose the appropriate primary role(s) for the task
   - Plan the task (objective, expected outputs, completion criteria)
   - Execute the task following OpenUP role guidance
   - Complete exactly ONE task per run

4. **Traceability Logging**:
   - Create markdown log: `docs/agent-logs/YYYY/MM/DD/<timestamp>-<agent>-<branch>.md`
   - Append JSONL entry to `docs/agent-logs/agent-runs.jsonl`
   - Include: run metadata, roles, tasks, commits, decisions, prompt (verbatim)
   - **MANDATORY**: Commits must exist before creating logs. The `commits` field must contain actual commit SHAs.

5. **Documentation Updates**:
   - Update phase notes in `docs/phases/{phase}/notes.md`
   - Ask permission before updating `docs/project-status.md` or `docs/roadmap.md` (unless explicitly granted)
   - Create/update decision records if architectural decisions were made

6. **End-of-Run SOP** (MANDATORY):
   - **Commit all changes**: Stage and commit all changes with a descriptive message. Record the commit SHA.
   - **Verify no uncommitted changes**: Run `git status --porcelain` - must be empty. If not empty, return to commit step.
   - **Create traceability logs**: Include commit SHAs in logs (commits must exist before logging)
   - **Update documentation**: Complete all required documentation updates
   - **Final verification**: Confirm all steps complete before stopping

**Task Completion**: A task is NOT complete until the End-of-Run SOP is finished. You MUST commit all changes to git before stopping. Uncommitted changes mean the task execution history is not persisted. After committing and completing all End-of-Run steps, stop. Do not proceed to additional tasks in this run.
```

## Running with Cursor CLI

The Cursor CLI provides `cursor-agent` for running AI agents from the command line.

### Installation

```bash
curl https://cursor.com/install -fsS | bash
```

Verify installation:
```bash
cursor-agent --version
```

Ensure `~/.local/bin` is in your PATH.

### Interactive Mode

Start an interactive session with the canonical prompt:

```bash
cursor-agent "Execute the next task from the roadmap following the OpenUP development process.

You MUST follow [docs-eng-process/agent-workflow.md](docs-eng-process/agent-workflow.md) procedures exactly:

1. **Start-of-Run SOP**:
   - Read \`docs/project-status.md\` to establish context (phase, iteration, iteration_goal, status)
   - If status is \"blocked\", report blockers and request guidance before proceeding
   - If status is \"completed\", propose phase transition (do not auto-advance)
   - Read \`docs/roadmap.md\` and select the next pending task (highest priority if multiple)
   - Verify the task aligns with current phase and iteration goals

2. **Role-Based Execution**:
   - Choose the appropriate primary role(s) for the task
   - Plan the task (objective, expected outputs, completion criteria)
   - Execute the task following OpenUP role guidance
   - Complete exactly ONE task per run

3. **Branching and Commits**:
   - Detect trunk branch (origin/HEAD → main → master → current)
   - If on trunk, create a new branch; if not on trunk, work on current branch
   - All changes must be committed in at least one atomic commit per task
   - **MANDATORY**: When you confirm the task is finished, you MUST commit all changes to git before stopping

4. **Traceability Logging**:
   - Create markdown log: \`docs/agent-logs/YYYY/MM/DD/<timestamp>-<agent>-<branch>.md\`
   - Append JSONL entry to \`docs/agent-logs/agent-runs.jsonl\`
   - Include: run metadata, roles, tasks, commits, decisions, prompt (verbatim)

5. **Documentation Updates**:
   - Update phase notes in \`docs/phases/{phase}/notes.md\`
   - Ask permission before updating \`docs/project-status.md\` or \`docs/roadmap.md\` (unless explicitly granted)
   - Create/update decision records if architectural decisions were made

**Task Completion**: Before confirming a task is finished, ensure all changes are committed to git. Do not leave uncommitted changes. After committing, stop. Do not proceed to additional tasks in this run."
```

### One-Shot Mode (Non-Interactive)

For automated runs or scripts, use the `-p` flag:

```bash
cursor-agent -p "Execute the next task from the roadmap following the OpenUP development process.

You MUST follow [docs-eng-process/agent-workflow.md](docs-eng-process/agent-workflow.md) procedures exactly:

1. **Start-of-Run SOP**:
   - Read \`docs/project-status.md\` to establish context (phase, iteration, iteration_goal, status)
   - If status is \"blocked\", report blockers and request guidance before proceeding
   - If status is \"completed\", propose phase transition (do not auto-advance)
   - Read \`docs/roadmap.md\` and select the next pending task (highest priority if multiple)
   - Verify the task aligns with current phase and iteration goals

2. **Role-Based Execution**:
   - Choose the appropriate primary role(s) for the task
   - Plan the task (objective, expected outputs, completion criteria)
   - Execute the task following OpenUP role guidance
   - Complete exactly ONE task per run

3. **Branching and Commits**:
   - Detect trunk branch (origin/HEAD → main → master → current)
   - If on trunk, create a new branch; if not on trunk, work on current branch
   - All changes must be committed in at least one atomic commit per task
   - **MANDATORY**: When you confirm the task is finished, you MUST commit all changes to git before stopping

4. **Traceability Logging**:
   - Create markdown log: \`docs/agent-logs/YYYY/MM/DD/<timestamp>-<agent>-<branch>.md\`
   - Append JSONL entry to \`docs/agent-logs/agent-runs.jsonl\`
   - Include: run metadata, roles, tasks, commits, decisions, prompt (verbatim)

5. **Documentation Updates**:
   - Update phase notes in \`docs/phases/{phase}/notes.md\`
   - Ask permission before updating \`docs/project-status.md\` or \`docs/roadmap.md\` (unless explicitly granted)
   - Create/update decision records if architectural decisions were made

**Task Completion**: Before confirming a task is finished, ensure all changes are committed to git. Do not leave uncommitted changes. After committing, stop. Do not proceed to additional tasks in this run."
```

### Multiline Prompt (Heredoc)

For better readability, use a heredoc:

```bash
cursor-agent <<'PROMPT'
Execute the next task from the roadmap following the OpenUP development process.

You MUST follow [docs-eng-process/agent-workflow.md](docs-eng-process/agent-workflow.md) procedures exactly:

1. **Start-of-Run SOP**:
   - Read `docs/project-status.md` to establish context (phase, iteration, iteration_goal, status)
   - If status is "blocked", report blockers and request guidance before proceeding
   - If status is "completed", propose phase transition (do not auto-advance)
   - Read `docs/roadmap.md` and select the next pending task (highest priority if multiple)
   - Verify the task aligns with current phase and iteration goals
   - **Create branch (if needed)**: Detect trunk branch (origin/HEAD → main → master → current). If on trunk, **MANDATORY** - create a new branch before starting work. If not on trunk, continue on current branch.

2. **Create Branch (MANDATORY before starting work)**:
   - This step is part of Start-of-Run SOP Step 4, but emphasized here for clarity
   - **MANDATORY**: If you are on trunk, you MUST create a new branch before starting any work
   - Use descriptive branch name following project conventions (feature/, fix/, refactor/, etc.)
   - Record branch name and trunk detection for traceability logs
   - **Do NOT proceed to Role-Based Execution until you are on a non-trunk branch**

3. **Role-Based Execution**:
   - Choose the appropriate primary role(s) for the task
   - Plan the task (objective, expected outputs, completion criteria)
   - Execute the task following OpenUP role guidance
   - Complete exactly ONE task per run

4. **Traceability Logging**:
   - Create markdown log: `docs/agent-logs/YYYY/MM/DD/<timestamp>-<agent>-<branch>.md`
   - Append JSONL entry to `docs/agent-logs/agent-runs.jsonl`
   - Include: run metadata, roles, tasks, commits, decisions, prompt (verbatim)
   - **MANDATORY**: Commits must exist before creating logs. The `commits` field must contain actual commit SHAs.

5. **Documentation Updates**:
   - Update phase notes in `docs/phases/{phase}/notes.md`
   - Ask permission before updating `docs/project-status.md` or `docs/roadmap.md` (unless explicitly granted)
   - Create/update decision records if architectural decisions were made

6. **End-of-Run SOP** (MANDATORY):
   - **Commit all changes**: Stage and commit all changes with a descriptive message. Record the commit SHA.
   - **Verify no uncommitted changes**: Run `git status --porcelain` - must be empty. If not empty, return to commit step.
   - **Create traceability logs**: Include commit SHAs in logs (commits must exist before logging)
   - **Update documentation**: Complete all required documentation updates
   - **Final verification**: Confirm all steps complete before stopping

**Task Completion**: A task is NOT complete until the End-of-Run SOP is finished. You MUST commit all changes to git before stopping. Uncommitted changes mean the task execution history is not persisted. After committing and completing all End-of-Run steps, stop. Do not proceed to additional tasks in this run.
PROMPT
```

## Running with Claude Code

Claude Code provides the `claude` command for running AI agents from the command line.

### Installation

Install Claude Code CLI following the [official documentation](https://docs.anthropic.com/en/docs/claude-code/cli-usage).

### Interactive Mode

Start an interactive session with the canonical prompt:

```bash
claude "Execute the next task from the roadmap following the OpenUP development process.

You MUST follow [docs-eng-process/agent-workflow.md](docs-eng-process/agent-workflow.md) procedures exactly:

1. **Start-of-Run SOP**:
   - Read \`docs/project-status.md\` to establish context (phase, iteration, iteration_goal, status)
   - If status is \"blocked\", report blockers and request guidance before proceeding
   - If status is \"completed\", propose phase transition (do not auto-advance)
   - Read \`docs/roadmap.md\` and select the next pending task (highest priority if multiple)
   - Verify the task aligns with current phase and iteration goals

2. **Role-Based Execution**:
   - Choose the appropriate primary role(s) for the task
   - Plan the task (objective, expected outputs, completion criteria)
   - Execute the task following OpenUP role guidance
   - Complete exactly ONE task per run

3. **Branching and Commits**:
   - Detect trunk branch (origin/HEAD → main → master → current)
   - If on trunk, create a new branch; if not on trunk, work on current branch
   - All changes must be committed in at least one atomic commit per task
   - **MANDATORY**: When you confirm the task is finished, you MUST commit all changes to git before stopping

4. **Traceability Logging**:
   - Create markdown log: \`docs/agent-logs/YYYY/MM/DD/<timestamp>-<agent>-<branch>.md\`
   - Append JSONL entry to \`docs/agent-logs/agent-runs.jsonl\`
   - Include: run metadata, roles, tasks, commits, decisions, prompt (verbatim)

5. **Documentation Updates**:
   - Update phase notes in \`docs/phases/{phase}/notes.md\`
   - Ask permission before updating \`docs/project-status.md\` or \`docs/roadmap.md\` (unless explicitly granted)
   - Create/update decision records if architectural decisions were made

**Task Completion**: Before confirming a task is finished, ensure all changes are committed to git. Do not leave uncommitted changes. After committing, stop. Do not proceed to additional tasks in this run."
```

### One-Shot Mode (Non-Interactive)

For automated runs or scripts, use the `-p` flag:

```bash
claude -p "Execute the next task from the roadmap following the OpenUP development process.

You MUST follow [docs-eng-process/agent-workflow.md](docs-eng-process/agent-workflow.md) procedures exactly:

1. **Start-of-Run SOP**:
   - Read \`docs/project-status.md\` to establish context (phase, iteration, iteration_goal, status)
   - If status is \"blocked\", report blockers and request guidance before proceeding
   - If status is \"completed\", propose phase transition (do not auto-advance)
   - Read \`docs/roadmap.md\` and select the next pending task (highest priority if multiple)
   - Verify the task aligns with current phase and iteration goals

2. **Role-Based Execution**:
   - Choose the appropriate primary role(s) for the task
   - Plan the task (objective, expected outputs, completion criteria)
   - Execute the task following OpenUP role guidance
   - Complete exactly ONE task per run

3. **Branching and Commits**:
   - Detect trunk branch (origin/HEAD → main → master → current)
   - If on trunk, create a new branch; if not on trunk, work on current branch
   - All changes must be committed in at least one atomic commit per task
   - **MANDATORY**: When you confirm the task is finished, you MUST commit all changes to git before stopping

4. **Traceability Logging**:
   - Create markdown log: \`docs/agent-logs/YYYY/MM/DD/<timestamp>-<agent>-<branch>.md\`
   - Append JSONL entry to \`docs/agent-logs/agent-runs.jsonl\`
   - Include: run metadata, roles, tasks, commits, decisions, prompt (verbatim)

5. **Documentation Updates**:
   - Update phase notes in \`docs/phases/{phase}/notes.md\`
   - Ask permission before updating \`docs/project-status.md\` or \`docs/roadmap.md\` (unless explicitly granted)
   - Create/update decision records if architectural decisions were made

**Task Completion**: Before confirming a task is finished, ensure all changes are committed to git. Do not leave uncommitted changes. After committing, stop. Do not proceed to additional tasks in this run."
```

### Multiline Prompt (Heredoc)

For better readability, use a heredoc:

```bash
claude <<'PROMPT'
Execute the next task from the roadmap following the OpenUP development process.

You MUST follow [docs-eng-process/agent-workflow.md](docs-eng-process/agent-workflow.md) procedures exactly:

1. **Start-of-Run SOP**:
   - Read `docs/project-status.md` to establish context (phase, iteration, iteration_goal, status)
   - If status is "blocked", report blockers and request guidance before proceeding
   - If status is "completed", propose phase transition (do not auto-advance)
   - Read `docs/roadmap.md` and select the next pending task (highest priority if multiple)
   - Verify the task aligns with current phase and iteration goals
   - **Create branch (if needed)**: Detect trunk branch (origin/HEAD → main → master → current). If on trunk, **MANDATORY** - create a new branch before starting work. If not on trunk, continue on current branch.

2. **Create Branch (MANDATORY before starting work)**:
   - This step is part of Start-of-Run SOP Step 4, but emphasized here for clarity
   - **MANDATORY**: If you are on trunk, you MUST create a new branch before starting any work
   - Use descriptive branch name following project conventions (feature/, fix/, refactor/, etc.)
   - Record branch name and trunk detection for traceability logs
   - **Do NOT proceed to Role-Based Execution until you are on a non-trunk branch**

3. **Role-Based Execution**:
   - Choose the appropriate primary role(s) for the task
   - Plan the task (objective, expected outputs, completion criteria)
   - Execute the task following OpenUP role guidance
   - Complete exactly ONE task per run

4. **Traceability Logging**:
   - Create markdown log: `docs/agent-logs/YYYY/MM/DD/<timestamp>-<agent>-<branch>.md`
   - Append JSONL entry to `docs/agent-logs/agent-runs.jsonl`
   - Include: run metadata, roles, tasks, commits, decisions, prompt (verbatim)
   - **MANDATORY**: Commits must exist before creating logs. The `commits` field must contain actual commit SHAs.

5. **Documentation Updates**:
   - Update phase notes in `docs/phases/{phase}/notes.md`
   - Ask permission before updating `docs/project-status.md` or `docs/roadmap.md` (unless explicitly granted)
   - Create/update decision records if architectural decisions were made

6. **End-of-Run SOP** (MANDATORY):
   - **Commit all changes**: Stage and commit all changes with a descriptive message. Record the commit SHA.
   - **Verify no uncommitted changes**: Run `git status --porcelain` - must be empty. If not empty, return to commit step.
   - **Create traceability logs**: Include commit SHAs in logs (commits must exist before logging)
   - **Update documentation**: Complete all required documentation updates
   - **Final verification**: Confirm all steps complete before stopping

**Task Completion**: A task is NOT complete until the End-of-Run SOP is finished. You MUST commit all changes to git before stopping. Uncommitted changes mean the task execution history is not persisted. After committing and completing all End-of-Run steps, stop. Do not proceed to additional tasks in this run.
PROMPT
```

## Running with the harness-free reference driver (`openup-agent`)

The two options above drive OpenUP through a **harness** (Cursor CLI or Claude Code).
You can also run a delivery cycle with **no harness at all** — a plain Python loop
against any **OpenAI-compatible** endpoint, including a local model in LM Studio,
Ollama, or vLLM. This is the reference driver; it reads the neutral procedure pack
directly and runs the deterministic OpenUP scripts itself.

Use this when you want to run OpenUP on a non-Anthropic / local model, in CI, or
anywhere Claude Code / Cursor isn't available.

### Requirements

Just `python3` (3.8+) and `git` — the driver is **stdlib-only** (no `pip install`).

### One-shot run

```bash
# Point at any OpenAI-compatible endpoint (local example: LM Studio)
export LLM_API_URL=http://localhost:1234/v1
export LLM_API_KEY=lm-studio                 # any non-empty string for local servers
export OPENUP_MODEL_MAIN=your-loaded-model   # a model the endpoint actually serves

# Drive one procedure to completion (equivalent to /openup-next)
python3 scripts/openup-agent.py run --dir . --procedure next
```

On success the driver prints the procedure's sentinel (e.g.
`OPENUP-NEXT: ADVANCED — T-074`) to stdout and exits 0 — the same sentinel an outer
loop reads from `/openup-next`. Model selection is by **tier** (no hardcoded model);
enforcement (write-fence, doc validation) is run by the driver itself, so it does not
depend on the model remembering to check.

**Full guide** — configuration, per-endpoint recipes (LM Studio / Ollama / vLLM /
OpenAI), the six-tool surface, exit codes, and troubleshooting:
[docs-eng-process/reference-driver.md](docs-eng-process/reference-driver.md).

## Customizing the Prompt

You can customize the prompt for specific tasks. For example, to grant permission to update state documents:

```text
[Include the canonical prompt above, then add:]

You have explicit permission to update `docs/project-status.md` and `docs/roadmap.md` for this run.
```

Or to target a specific task:

```text
[Include the canonical prompt above, then add:]

Focus on the task: "[Task ID or description from roadmap]"
```

## Additional Resources

- [Reference driver (`openup-agent`)](docs-eng-process/reference-driver.md) - Run OpenUP harness-free on any OpenAI-compatible / local model
- [Agent Workflow](docs-eng-process/agent-workflow.md) - Complete operating procedures
- [Project Initialization](docs-eng-process/init-prompts.md) - Prompts for initializing new projects
- [Getting Started](docs-eng-process/getting-started.md) - Manual project setup guide

# Project Initialization Prompts

This document provides **copy/paste prompts** to initialize a new project from this template using an AI agent. These prompts follow a **two-run flow**: first setup (scaffolding via the `/openup-init` skill), then guided Vision document completion.

> **Why these prompts drive `/openup-init` (read before editing files by hand).**
> A fresh project has **no `.openup/state.json`** yet, so the `gate-edits.py`
> PreToolUse hook **blocks the `Write`/`Edit`/`NotebookEdit` tools** on
> `docs/project-status.md`, `docs/roadmap.md`, and other non-exempt paths — you
> cannot start an iteration in a project that does not exist yet. The sanctioned,
> gate-aware initializer is the **`/openup-init`** skill, which scaffolds the
> project with the gate-exempt `Bash` tool (`cp`/heredocs). Do not hand-write the
> initial docs with `Write`/`Edit`; the hook will block them and the run will
> stall. Prompt A below runs `/openup-init` for you.

## When to Use These Prompts

Use these prompts when:
- You've just cloned/copied this template repository for a new project
- The `docs/` directory is empty (or contains only `.gitkeep`)
- You want an agent to handle the technical setup and initial scaffolding
- You prefer a guided, interactive initialization over manual file creation

## What This Produces

After running both prompts, you'll have (scaffolded by `/openup-init` in Prompt A,
then filled in Prompt B):
- `docs/project-status.md` - Project state tracking (phase=inception)
- `docs/roadmap.md` - Prioritized task backlog (setup + requirements elicitation tasks only)
- `docs/project-config.yaml` - Project-owned context + per-artifact rules (placeholders to fill)
- `docs/vision.md` - Vision document (created via `/openup-create-vision` in Prompt B)
- `docs/` working dirs - `input-requests/`, `use-cases/`, `agent-logs/`

**Important**: The agent will **NOT** implement product features or write code during initialization. This is setup-only.

## Process Rules

The agent must follow these constraints:
- **Do NOT modify** anything under `docs-eng-process/` (this is the strict process directory)
- Follow procedures in [agent-workflow.md](agent-workflow.md) exactly
- Read `docs/project-status.md` and `docs/roadmap.md` at the start of every run (after initialization)
- Ask permission before updating state documents (`docs/project-status.md`, `docs/roadmap.md`) unless explicitly granted in the prompt

## Permission Requirement

By default, agents must ask permission before updating `docs/project-status.md` and `docs/roadmap.md` (these are state documents requiring human oversight). **The prompts below explicitly grant this permission** for the initialization run only.

---

## Prompt A: Project Setup (Run First)

**Copy and paste this prompt to your AI agent. Replace the placeholders in angle brackets with your project information.**

```text
You are initializing a brand-new project using this repo as a template.

Project information:
- Project name: <YOUR_PROJECT_NAME>
- One-sentence description: <ONE_TO_TWO_SENTENCE_DESCRIPTION>
- Target users (optional): <TARGET_USERS_OR_LEAVE_BLANK>

Hard constraints:
- Do NOT implement product features or write code after setup. Setup only.
- Do not modify anything under docs-eng-process/.
- Ask the user for ONLY the minimal info needed to customize the initial docs (project name, description, optional target users).
- Scaffold via the /openup-init skill — do NOT hand-write the initial docs with
  the Write/Edit tools. A fresh project has no .openup/state.json, so the
  gate-edits.py hook BLOCKS Write/Edit on docs/project-status.md, docs/roadmap.md,
  and other non-exempt paths. /openup-init creates files with the gate-exempt Bash
  tool (cp/heredocs). If you hit "[gate-edits] Editing source code with no active
  OpenUP iteration plan", you reached for the wrong tool — use /openup-init.

You have my explicit permission to CREATE and UPDATE the state docs that
/openup-init scaffolds during initialization (docs/project-status.md,
docs/roadmap.md, docs/project-config.yaml, and the docs/ working directories).

Goal of this run:
1) **Create branch (if needed)**: Before starting any work, follow [Start-of-Run SOP Step 4](agent-workflow.md#start-of-run-sop) from docs-eng-process/agent-workflow.md:
   - Detect trunk branch (origin/HEAD → main → master → current)
   - If on trunk, **MANDATORY** - create a new branch before starting work (e.g., `feature/init-project-setup`)
   - If not on trunk, continue on current branch
   - Record branch name for traceability
2) **Confirm project info**, then run the initializer skill:

       /openup-init project_name: "<YOUR_PROJECT_NAME>"

   Answer its prompts using the project information above (type=other if none
   fits; phase=inception for a new project). The skill scaffolds, with the Bash
   tool, the docs/ structure + docs/project-status.md, docs/roadmap.md, and
   docs/project-config.yaml. Use reasonable placeholders / TODO markers for any
   optional info not provided.
3) **Seed the roadmap** for inception. Edit docs/roadmap.md (via Bash, since no
   iteration is active yet) so it contains ONLY setup/requirements-elicitation
   tasks (no implementation), including at least:
   - "Fill Vision document (guided Q&A)" - status: pending  ← mark as the next pending task
   - "Draft initial risk list" - status: pending
   - "Define top use cases" - status: pending
   - "Agree on scope + non-goals" - status: pending
4) Stop after setup and present:
   - a short project summary (name + description + current phase)
   - what files were created
   - the next steps for the human
   - the exact Prompt B (from docs-eng-process/init-prompts.md) to run next for Vision Q&A

**MANDATORY**: Before stopping, commit all changes to git. Follow the [End-of-Run SOP](agent-workflow.md#end-of-run-sop) from docs-eng-process/agent-workflow.md:
   - Stage all changes: `git add -A`
   - Create commit: `git commit -m "Initialize project: <project-name>"`
   - Verify no uncommitted changes: `git status --porcelain` must be empty
   - Do NOT stop until all changes are committed

Interaction rules:
- First, confirm the project information provided above (or ask for any missing required info).
- Then run /openup-init and seed the roadmap.
- Then stop and summarize. Do NOT start the "Fill Vision" Q&A in this same run.
- Do NOT create the Vision document yet — that is Prompt B, where it is authored
  via the /openup-create-vision skill (which applies the vision rubric).

Finally, provide the exact Prompt B (from docs-eng-process/init-prompts.md) that the human should use in the next run to start the guided Vision Q&A.
```

---

## Prompt B: Vision Document Q&A (Run After Prompt A)

**Copy and paste this prompt to your AI agent after Prompt A completes successfully.**

```text
Start the "Fill Vision document (guided Q&A)" task from docs/roadmap.md.

Follow docs-eng-process/agent-workflow.md start-of-run SOP:
1) Read docs/project-status.md to establish context (phase, iteration, iteration_goal)
2) Read docs/roadmap.md and select the "Fill Vision document (guided Q&A)" task
3) Verify the task aligns with current phase + iteration goals

Then START AN ITERATION before touching docs/vision.md:
4) Run /openup-start-iteration for the "Fill Vision document" task. This is
   REQUIRED, not optional: it creates the branch, persists .openup/state.json and
   the iteration plan, and only then does the gate-edits.py hook allow the
   Write/Edit tools on docs/vision.md. (Without an active iteration, editing
   docs/vision.md is blocked — that is the gate working as intended, not an error.)

Then author the Vision via its skill (do NOT hand-write docs/vision.md):
- Run /openup-create-vision — it creates docs/vision.md and applies the vision rubric.
- Drive it with guided Q&A: ask the minimum set of questions needed, in small
  batches (no more than 5 at a time). After each batch, update the Vision via the
  skill and show what changed.
- Stop when the vision doc is "good enough for Inception" (core sections filled;
  TODOs are acceptable for less critical sections).

You have permission to update docs/vision.md (through /openup-create-vision) for
this run. Do NOT hand-edit docs/roadmap.md or docs/project-status.md — those
shared views are regenerated by scripts/sync-status.py; let /openup-start-iteration
and /openup-complete-task drive their state.

**MANDATORY**: Close the iteration cleanly — run /openup-complete-task for the
"Fill Vision document" task. It commits the work, writes the traceability log with
the commit SHA, and syncs the roadmap/status views. Do NOT stop with an open
iteration or uncommitted changes (git status --porcelain must be empty).

Do NOT proceed to other roadmap tasks in this run. Focus only on completing the Vision document.
```

---

## Next Steps After Initialization

After both prompts complete:

1. **Review** `docs/vision.md` - ensure it captures your project vision accurately
2. **Review** `docs/roadmap.md` - verify the prioritized task list aligns with your goals
3. **Optional: Set up Agent Teams** - If you want to use Claude Code agent teams:
   - Run `./scripts/setup-agent-teams.sh` (if not already done during bootstrap)
   - Enable agent teams: `export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
   - See [agent-teams-setup.md](agent-teams-setup.md) for usage instructions
4. **Continue with Inception tasks** - use the normal agent workflow:
   - The agent will read `docs/project-status.md` and `docs/roadmap.md` at start
   - Select the next pending task from the roadmap
   - Follow [agent-workflow.md](agent-workflow.md) procedures

For detailed agent procedures, see [agent-workflow.md](agent-workflow.md).

For agent teams setup and usage, see [agent-teams-setup.md](agent-teams-setup.md).

For manual initialization (without an agent), see [getting-started.md](getting-started.md).

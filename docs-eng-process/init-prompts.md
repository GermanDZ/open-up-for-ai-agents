# Project Initialization Prompts

This document provides **copy/paste prompts** to initialize a new project from this template using an AI agent. These prompts follow a **two-run flow**: first setup (technical preparation + minimal customization), then guided Vision document completion.

## When to Use These Prompts

Use these prompts when:
- You've just cloned/copied this template repository for a new project
- The `docs/` directory is empty (or contains only `.gitkeep`)
- You want an agent to handle the technical setup and initial scaffolding
- You prefer a guided, interactive initialization over manual file creation

## What This Produces

After running both prompts, you'll have:
- `docs/project-status.md` - Project state tracking (phase=inception, iteration=1)
- `docs/roadmap.md` - Prioritized task backlog (setup + requirements elicitation tasks only)
- `docs/vision.md` - Vision document template (partially filled, ready for guided Q&A)
- `docs/risk-list.md` - Risk list template (with placeholders)
- `docs/phases/inception/overview.md` - Inception phase overview
- `docs/phases/inception/notes.md` - Inception phase notes

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
- Follow docs-eng-process/getting-started.md and docs-eng-process/agent-workflow.md conventions.
- Do not modify anything under docs-eng-process/.
- Ask the user for ONLY the minimal info needed to customize the initial docs (project name, description, optional target users).

You have my explicit permission to CREATE and UPDATE the following state docs during initialization:
- docs/project-status.md
- docs/roadmap.md
…and to create any docs/* files required by getting-started.md.

Goal of this run:
1) Technical preparation: create the docs structure and copy templates into place.
   - Copy `docs-eng-process/templates/vision.md` to `docs/vision.md`
   - Copy `docs-eng-process/templates/risk-list.md` to `docs/risk-list.md`
   - Create the required directory structure (docs/phases/inception/)
2) Minimal customization: use the project information provided above to fill in:
   - project_name in docs/project-status.md
   - Basic project description in docs/vision.md (with TODO markers for unknown sections)
   - Target users in docs/vision.md if provided
   Use reasonable placeholders if optional info is not provided.
3) Stop after setup and present:
   - a short project summary (name + description + current phase/iteration_goal)
   - what files were created
   - the next steps for the human
   - the exact Prompt B (from docs-eng-process/init-prompts.md) to run next for Vision Q&A

Required outputs to create (no more, unless strictly required by the process):
- docs/vision.md - Copy from `docs-eng-process/templates/vision.md` and fill with the minimal info above + TODO markers for unknown sections
- docs/risk-list.md - Copy from `docs-eng-process/templates/risk-list.md` and populate with initial placeholders and TODOs
- docs/project-status.md (phase=inception, iteration=1, iteration_goal="Define project vision and identify key risks", status=in-progress, dates set reasonably, updated_by set)
- docs/phases/inception/overview.md
- docs/phases/inception/notes.md
- docs/roadmap.md with ONLY setup/requirements elicitation tasks (no implementation). Include at least:
  - "Fill Vision document (guided Q&A)" - status: pending
  - "Draft initial risk list" - status: pending
  - "Define top use cases" - status: pending
  - "Agree on scope + non-goals" - status: pending
  Mark "Fill Vision document (guided Q&A)" as the next pending task.

**Template locations** (copy these files to docs/):
- Vision template: `docs-eng-process/templates/vision.md` → `docs/vision.md`
- Risk list template: `docs-eng-process/templates/risk-list.md` → `docs/risk-list.md`

Interaction rules:
- First, confirm the project information provided above (or ask for any missing required info).
- Then perform file creation/customization.
- Then stop and summarize. Do NOT start the "Fill Vision" Q&A in this same run.

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

Then:
- Ask the minimum set of questions needed to complete docs/vision.md
- Ask questions in small batches (no more than 5 questions at a time)
- After each batch, update docs/vision.md accordingly and show what changed
- Stop when the vision doc is "good enough for Inception" (core sections filled; TODOs are acceptable for less critical sections)

You have permission to update docs/vision.md and docs/roadmap.md (mark the task as in-progress, then completed when done).

Do NOT proceed to other roadmap tasks in this run. Focus only on completing the Vision document.
```

---

## Next Steps After Initialization

After both prompts complete:

1. **Review** `docs/vision.md` - ensure it captures your project vision accurately
2. **Review** `docs/roadmap.md` - verify the prioritized task list aligns with your goals
3. **Continue with Inception tasks** - use the normal agent workflow:
   - The agent will read `docs/project-status.md` and `docs/roadmap.md` at start
   - Select the next pending task from the roadmap
   - Follow [agent-workflow.md](agent-workflow.md) procedures

For detailed agent procedures, see [agent-workflow.md](agent-workflow.md).

For manual initialization (without an agent), see [getting-started.md](getting-started.md).

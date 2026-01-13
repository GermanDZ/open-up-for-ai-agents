# Getting Started

This guide explains how to initialize a new project from this template.

## Prefer to Have an Agent Do This?

If you want an AI agent to handle the technical setup and initial scaffolding, see [init-prompts.md](init-prompts.md) for copy/paste prompts that guide the agent through a two-run initialization process (setup + Vision Q&A). This is the recommended approach for new projects.

## Manual Initialization

If you prefer to initialize manually, follow the steps below.

## Initial Setup

### 1. Copy Essential Templates

Start by copying these templates from [templates/](templates/) into your project `docs/`:

- **Vision** - `templates/vision.md` → `docs/vision.md`
- **Risk List** - `templates/risk-list.md` → `docs/risk-list.md`

These are the first artifacts you'll need in the Inception phase.

### 2. Initialize Project Status

Create `docs/project-status.md` using the template structure defined in [agent-workflow.md](agent-workflow.md#project-status-definition). This file is the single source of truth for the project's current state.

Example initial state:

```yaml
---
project_name: "[Your Project Name]"
phase: inception
iteration: 1
iteration_goal: "Define project vision and identify key risks"
status: not-started
# ... other required fields
---
```

### 3. Create Initial Phase Documentation

For the Inception phase, create:

```
docs/phases/inception/
├── overview.md
└── notes.md
```

- `overview.md` - Phase-specific notes and context
- `notes.md` - Flattened notes for all disciplines in this phase

**Do not** pre-create discipline-specific notes unless needed. Create them only when the work requires it:

```
docs/phases/inception/disciplines/
├── requirements.md  # Only if needed
└── architecture.md  # Only if needed
```

### 4. Create Roadmap

Create `docs/roadmap.md` with prioritized work items. This is used by agents to select tasks.

## When to Create Discipline-Specific Notes

Create discipline-specific notes (`docs/phases/{phase}/disciplines/{discipline}.md`) only when:

- The work requires detailed discipline-specific documentation
- Multiple team members need to coordinate on a specific discipline
- The phase notes file becomes too large and needs organization

Otherwise, use the flattened `notes.md` file.

## Lifecycle-Spanning Documents

Some documents are maintained across the entire lifecycle (not phase-scoped):

- **Use Cases** - `docs/use-cases/` (flattened, no per-phase split)
- **Architecture** - `docs/architecture.md` (if it exists)
- **Stack** - `docs/stack.md` (if it exists)

## Next Steps

1. Fill in the Vision document
2. Identify initial risks
3. Update `docs/project-status.md` with your project details
4. Begin iteration planning

For detailed agent procedures, see [agent-workflow.md](agent-workflow.md).

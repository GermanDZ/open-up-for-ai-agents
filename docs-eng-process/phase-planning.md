# Phase Planning and Management

This document explains how to plan and track work using the OpenUP phase structure.

## Overview

This project follows the **OpenUP** (Open Unified Process) methodology with four main phases:

1. **Inception** - Define project scope, vision, and feasibility
2. **Elaboration** - Establish architecture, detailed requirements, and risk mitigation
3. **Construction** - Build production-ready features iteratively
4. **Transition** - Deploy, train users, and transition to production

Each phase consists of multiple **iterations** (typically 1-4 weeks each), and each iteration delivers working software.

## Phase Documentation Structure

Phase-specific planning and tracking documents live under `docs/phases/{phase}/`:

- `overview.md` - Phase-specific notes and context
- `notes.md` - Flattened notes for all disciplines in this phase
- `roadmap.md` - Iteration planning and task tracking (if exists)
- `outputs.md` - Expected artifacts and deliverables (if exists)

Optional discipline-specific notes (created only when needed):
- `disciplines/{discipline}.md` - Detailed notes for a specific discipline

## Phase Milestones

Each phase ends with a milestone that provides evaluation criteria:

- **Inception → Lifecycle Objectives Milestone**: Do we agree on project scope and objectives?
- **Elaboration → Lifecycle Architecture Milestone**: Do we agree on the executable architecture?
- **Construction → Initial Operational Capability Milestone**: Is the product ready for transition?
- **Transition → Product Release Milestone**: Is the application ready to release?

See [phase milestones reference](openup-knowledge-base/practice-management/risk_value_lifecycle/guidances/concepts/phase-milestones.md) for details.

## Agent Workflow: Phase-First Approach

**Every AI agent MUST follow this checklist before implementing anything:**

1. Check if phase plans exist (look for `docs/phases/{phase}/roadmap.md`)
2. Identify current phase (from `docs/project-status.md`)
3. Identify current iteration (from phase roadmap)
4. Verify task exists in roadmap
5. Read referenced use cases
6. Check required artifacts
7. Proceed with implementation

If phase plans don't exist, agents must stop and request human initialization.

## Starting a New Phase

1. Create `docs/phases/{phase}/overview.md`
2. Create `docs/phases/{phase}/notes.md`
3. If needed, create `docs/phases/{phase}/roadmap.md` and `outputs.md`
4. Update `docs/project-status.md` with new phase information

## Completing a Phase

1. Review phase completion criteria in `docs/project-status.md`
2. Verify all required artifacts are complete
3. Get sign-offs from stakeholders
4. Document phase summary
5. Transition to next phase (requires human approval)

For complete phase planning guidance, see the [OpenUP knowledge base](openup-knowledge-base/process/base/deliveryprocesses/).

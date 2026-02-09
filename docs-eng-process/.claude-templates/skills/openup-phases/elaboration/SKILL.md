---
name: elaboration
description: Initialize and manage Elaboration phase activities - establish architecture baseline
arguments:
  - name: activity
    description: Specific activity to perform (initiate, check-status, next-steps)
    required: false
---

# Elaboration Phase

This skill guides you through the Elaboration phase of OpenUP - establishing the architecture baseline.

## Elaboration Overview

**Goal**: Design and implement the architecture, resolve high-risk elements
**Duration**: Typically 4-8 weeks
**Key Milestone**: Lifecycle Architecture

## Phase Objectives

1. Design and validate the architecture
2. Detail the critical use cases
3. Implement and test the architectural baseline
4. Refine the project plan with accurate estimates
5. Mitigate high-priority risks

## Completion Criteria

- [ ] Architecture notebook completed
- [ ] Critical use cases detailed (80%)
- [ ] Technical risks identified and mitigated
- [ ] Prototype(s) validated key architectural decisions
- [ ] Project plan refined with accurate estimates
- [ ] Stakeholder agreement on architecture

## Process

### 1. Read Project Status

Read `docs/project-status.md` to:
- Confirm phase is `elaboration`
- Check iteration goals
- Review active work items

### 2. Based on Activity

**`initiate`**: Start Elaboration phase
- Update `docs/project-status.md` to set `phase: elaboration`
- Create `docs/architecture-notebook.md` from template
- Review and refine `docs/risk-list.md` for technical risks
- Update `docs/roadmap.md` with elaboration tasks

**`check-status`**: Review progress
- Check all completion criteria above
- List what's done and what remains
- Identify blockers

**`next-steps`**: Get recommendations
- Suggest next tasks based on current state
- Prioritize by technical risk and dependencies

## Key Work Products

- **Architecture Notebook** (`docs/architecture-notebook.md`) - Architecture documentation
- **Design** (`docs/design/*.md`) - Detailed design documents
- **Use Cases** (`docs/use-cases/*.md`) - Detailed use cases
- **Developer Tests** - Test implementations
- **Updated Project Plan** (`docs/project-plan.md`)

## Recommended Team

For Elaboration phase work, create a team with:
- **architect** - Lead architecture design
- **developer** - Implement architectural baseline
- **tester** - Validate architecture through testing
- Add **analyst** for detailed requirements

## References

- Elaboration Phase: `docs-eng-process/openup-knowledge-base/practice-management/risk_value_lifecycle/guidances/concepts/phase-elaboration.md`
- Architect Role: `docs-eng-process/openup-knowledge-base/core/role/roles/architect-6.md`
- Architecture Notebook Template: `docs-eng-process/templates/architecture-notebook.md`

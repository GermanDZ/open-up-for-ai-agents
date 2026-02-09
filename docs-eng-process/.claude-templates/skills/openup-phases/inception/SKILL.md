---
name: inception
description: Initialize and manage Inception phase activities - define scope, vision, and feasibility
arguments:
  - name: activity
    description: Specific activity to perform (initiate, check-status, next-steps)
    required: false
---

# Inception Phase

This skill guides you through the Inception phase of OpenUP - defining scope, vision, and feasibility.

## Inception Overview

**Goal**: Understand what to build and identify key risks
**Duration**: Typically 2-4 weeks
**Key Milestone**: Lifecycle Objectives

## Phase Objectives

1. Define the project's vision
2. Understand the problem to be solved
3. Identify key stakeholders
4. Define initial scope
5. Identify major risks
6. Demonstrate viability with a business case

## Completion Criteria

- [ ] Vision document approved by stakeholders
- [ ] Key use cases identified (20-30% detailed)
- [ ] Major risks documented with mitigation strategies
- [ ] Initial project plan with cost/schedule estimates
- [ ] Business case demonstrates viability
- [ ] Stakeholder agreement to proceed

## Process

### 1. Read Project Status

Read `docs/project-status.md` to:
- Confirm phase is `inception`
- Check iteration goals
- Review active work items

### 2. Based on Activity

**`initiate`**: Start Inception phase
- Update `docs/project-status.md` to set `phase: inception`
- Create initial `docs/vision.md` from template
- Create initial `docs/risk-list.md` from template
- Create `docs/roadmap.md` with initial backlog

**`check-status`**: Review progress
- Check all completion criteria above
- List what's done and what remains
- Identify blockers

**`next-steps`**: Get recommendations
- Suggest next tasks based on current state
- Prioritize by dependencies and value

## Key Work Products

- **Vision** (`docs/vision.md`) - Project vision and scope
- **Use Cases** (`docs/use-cases/*.md`) - Key use cases
- **Risk List** (`docs/risk-list.md`) - Identified risks
- **Project Plan** (`docs/project-plan.md`) - Initial plan
- **Glossary** (`docs/glossary.md`) - Project terminology

## Recommended Team

For Inception phase work, create a team with:
- **analyst** - Lead requirements and vision
- **project-manager** - Plan and coordinate
- Add **architect** for technical feasibility assessment

## References

- Inception Phase: `docs-eng-process/openup-knowledge-base/practice-management/risk_value_lifecycle/guidances/concepts/phase-inception.md`
- Analyst Role: `docs-eng-process/openup-knowledge-base/core/role/roles/analyst-6.md`
- Vision Template: `docs-eng-process/templates/vision.md`

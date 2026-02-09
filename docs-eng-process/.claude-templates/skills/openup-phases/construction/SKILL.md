---
name: construction
description: Initialize and manage Construction phase activities - build the system incrementally
arguments:
  - name: activity
    description: Specific activity to perform (initiate, check-status, next-steps)
    required: false
---

# Construction Phase

This skill guides you through the Construction phase of OpenUP - building the system incrementally.

## Construction Overview

**Goal**: Build the system iteratively until it's ready for deployment
**Duration**: Typically 8-16 weeks (multiple iterations)
**Key Milestone**: Operational Capability

## Phase Objectives

1. Implement all remaining features
2. Iteratively test and refine the system
3. Prepare for beta testing
4. Complete user documentation
5. Achieve acceptable quality levels

## Completion Criteria

- [ ] Product is stable enough for beta testing
- [ ] Alpha test results documented
- [ ] Critical issues resolved
- [ ] User documentation is adequate
- [ ] Stakeholder agreement to deploy to beta users

## Process

### 1. Read Project Status

Read `docs/project-status.md` to:
- Confirm phase is `construction`
- Check iteration goals
- Review active work items

### 2. Based on Activity

**`initiate`**: Start Construction phase
- Update `docs/project-status.md` to set `phase: construction`
- Review `docs/architecture-notebook.md` for implementation guidance
- Update `docs/roadmap.md` with construction tasks
- Create iteration plans for upcoming iterations

**`check-status`**: Review progress
- Check all completion criteria above
- List what's done and what remains
- Identify blockers

**`next-steps`**: Get recommendations
- Suggest next tasks based on current state
- Prioritize by value and dependencies

## Key Work Products

- **Implementation** - Source code
- **Unit Tests** - Developer-written tests
- **Design** (`docs/design/*.md`) - Detailed design documents
- **Test Cases** (`docs/test-cases/*.md`) - Test documentation
- **User Documentation** - User guides and manuals

## Recommended Team

For Construction phase work, create a team with:
- **developer** - Lead implementation
- **tester** - Continuous testing and validation
- Add **architect** for technical guidance
- Add **analyst** for requirements clarification

## Iteration Focus

Each construction iteration should:
1. Select features from the roadmap
2. Implement with tests
3. Review and validate
4. Update documentation
5. Prepare for next iteration

## References

- Construction Phase: `docs-eng-process/openup-knowledge-base/practice-management/risk_value_lifecycle/guidances/concepts/phase-construction.md`
- Developer Role: `docs-eng-process/openup-knowledge-base/core/role/roles/developer-11.md`
- Tester Role: `docs-eng-process/openup-knowledge-base/core/role/roles/tester-5.md`

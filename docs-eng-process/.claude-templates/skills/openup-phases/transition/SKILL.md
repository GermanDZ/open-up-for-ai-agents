---
name: transition
description: Initialize and manage Transition phase activities - deploy to users
arguments:
  - name: activity
    description: Specific activity to perform (initiate, check-status, next-steps)
    required: false
---

# Transition Phase

This skill guides you through the Transition phase of OpenUP - deploying to users.

## Transition Overview

**Goal**: Deploy the system to users and ensure user satisfaction
**Duration**: Typically 2-4 weeks
**Key Milestone**: Product Release

## Phase Objectives

1. Deploy the system to users
2. Train users and support staff
3. Fix defects found during testing
4. Complete user documentation
5. Obtain user acceptance

## Completion Criteria

- [ ] Product is ready for release
- [ ] All acceptance tests pass
- [ ] Deployment documentation complete
- [ ] Support materials ready
- [ ] Stakeholder sign-off obtained

## Process

### 1. Read Project Status

Read `docs/project-status.md` to:
- Confirm phase is `transition`
- Check iteration goals
- Review active work items

### 2. Based on Activity

**`initiate`**: Start Transition phase
- Update `docs/project-status.md` to set `phase: transition`
- Review test results from construction
- Create deployment checklist
- Update `docs/roadmap.md` with transition tasks

**`check-status`**: Review progress
- Check all completion criteria above
- List what's done and what remains
- Identify blockers

**`next-steps`**: Get recommendations
- Suggest next tasks based on current state
- Prioritize by deployment readiness

## Key Work Products

- **Deployment Documentation** - Installation and configuration guides
- **User Documentation** - Final user manuals
- **Support Materials** - Troubleshooting guides, FAQs
- **Test Results** - Final test reports
- **Release Notes** - What's new and changed

## Recommended Team

For Transition phase work, create a team with:
- **tester** - Lead final testing and validation
- **developer** - Fix deployment issues
- **project-manager** - Coordinate deployment
- Add **analyst** for user feedback and acceptance

## Deployment Activities

1. **Final Testing** - Comprehensive testing including:
   - Beta testing with real users
   - Performance testing
   - Security testing
   - User acceptance testing

2. **Deployment Preparation** - Prepare for release:
   - Create deployment scripts
   - Prepare production environment
   - Plan rollback procedures
   - Train support staff

3. **User Preparation** - Prepare users:
   - Create user documentation
   - Develop training materials
   - Conduct training sessions
   - Prepare communication materials

4. **Release** - Deploy to production:
   - Execute deployment plan
   - Monitor for issues
   - Provide support
   - Collect feedback

## References

- Transition Phase: `docs-eng-process/openup-knowledge-base/practice-management/risk_value_lifecycle/guidances/concepts/phase-transition.md`
- Tester Role: `docs-eng-process/openup-knowledge-base/core/role/roles/tester-5.md`
- Project Manager Role: `docs-eng-process/openup-knowledge-base/core/role/roles/project-manager-4.md`

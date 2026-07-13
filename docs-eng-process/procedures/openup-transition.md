---
name: openup-transition
description: Initialize and manage Transition phase activities - deploy to users
tier: coordination
capabilities: {required: [read_write_files, exec], optional: []}
arguments:
  - name: activity
    description: Specific activity to perform (initiate, check-status, next-steps)
    required: false
---

# Transition Phase

This skill guides you through the Transition phase of OpenUP - deploying to users.

> **Thin front over the process map (T-077).** This phase's **activity
> composition is data**, not prose: run
> `python3 scripts/openup-process-map.py activities-for transition` for the
> authoritative ordered activities (each resolved to its role + skills), and let
> **`/openup-start-iteration` Plan Iteration** generate this phase's work-item
> lanes from that map. The guidance below is human-facing reference — the map +
> Plan Iteration are the source of truth for *what* a Transition iteration runs.

## When to Use

Use this skill when:
- Construction is complete and system is ready for deployment
- Preparing for beta or production release
- Conducting final testing and user acceptance
- Training users and support staff
- Checking if Transition phase is complete
- Getting guidance on next steps in Transition

## When NOT to Use

Do NOT use this skill when:
- Still implementing features (use `/openup-construction`)
- System is not stable enough for testing (continue Construction)
- Need to create specific artifacts (use artifact skills)
- Looking for deployment procedures (use DevOps/ops documentation)

## Success Criteria

After using this skill, verify:
- [ ] Phase status is clearly understood (initiated, in-progress, or complete)
- [ ] Deployment readiness is assessed
- [ ] Support materials are prepared
- [ ] User acceptance is documented
- [ ] Release decision is clear

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

### 0. Load the Environment Chain (project config)

If `docs/project-config.yaml` defines an ordered `environments:` list (see
`docs-eng-process/project-config.md`), Transition walks that chain **hop by
hop** instead of a single hop to production:

- Each entry has a `name` and (except the last) a `promotion:` criterion — a
  free-text, checkable statement of what must be true before the release moves
  to the next environment.
- Build **one promotion checklist per hop** into the deployment checklist
  (step 2 `initiate`): the hop's `promotion:` criterion + the relevant
  completion criteria above.
- OpenUP's Transition beta-test objective ("beta test to validate that user
  expectations are met") maps onto the configured **pre-production**
  environment(s) — e.g. a `beta` entry — rather than being an unanchored
  activity. Per-environment flag default states come from each task's
  `## Rollout` section.
- `check-status` reports **which environment the release currently sits in**
  and which promotion criteria block the next hop.

If the key is absent, skip this step — single-hop deployment to production,
unchanged framework default.

### 1. Read Project Status

Read `docs/project-status.md` to:
- Confirm phase is `transition`
- Check iteration goals
- Review active work items

### 2. Based on Activity

**`initiate`**: Start Transition phase
- Update `docs/project-status.md` to set `phase: transition`
- Review test results from construction
- Create deployment checklist — one promotion checklist **per hop** of the
  `environments:` chain when configured (step 0), single-hop otherwise
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

## See Also

- [openup-phase-review](../../openup-workflow/phase-review/SKILL.md) - Check phase completion
- [openup-create-test-plan](../../openup-artifacts/create-test-plan/SKILL.md) - Final test planning
- [openup-construction](../construction/SKILL.md) - Previous phase
- [openup-log-run](../../openup-workflow/log-run/SKILL.md) - Document deployment

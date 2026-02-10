---
name: openup-phase-review
description: Check phase completion criteria and prepare for phase review
arguments:
  - name: phase
    description: The phase to review (inception, elaboration, construction, transition)
    required: false
---

# Phase Review

This skill checks phase completion criteria and prepares documentation for a phase review meeting.

## When to Use

Use this skill when:
- Nearing end of a phase and need to check completion
- Preparing for phase review meeting with stakeholders
- Assessing readiness to move to next phase
- Generating phase summary documentation
- Need to demonstrate phase accomplishments

## When NOT to Use

Do NOT use this skill when:
- Just starting a phase (use phase skill instead)
- Need to complete iteration tasks (use `/openup-complete-task`)
- Looking for iteration planning (use `/openup-create-iteration-plan`)
- Phase is clearly not complete (continue work first)

## Success Criteria

After using this skill, verify:
- [ ] All phase completion criteria are checked
- [ ] Missing items are clearly identified
- [ ] Phase review summary is generated
- [ ] Recommendations for next phase are provided
- [ ] User knows what decisions are needed

## Process

### 1. Read Current Project Status

Read `docs/project-status.md` to determine:
- Current phase (or use `$ARGUMENTS[phase]` if provided)
- Iteration status
- Phase completion criteria checklist

### 2. Check Phase Completion Criteria

For the current phase, verify all completion criteria are met:

**Inception - Lifecycle Objectives Milestone**:
- [ ] Vision document approved by stakeholders
- [ ] Key use cases identified (20-30% detailed)
- [ ] Major risks documented with mitigation strategies
- [ ] Initial project plan with cost/schedule estimates
- [ ] Business case demonstrates viability
- [ ] Stakeholder agreement to proceed

**Elaboration - Lifecycle Architecture Milestone**:
- [ ] Architecture notebook completed
- [ ] Critical use cases detailed (80%)
- [ ] Technical risks identified and mitigated
- [ ] Prototype(s) validated key architectural decisions
- [ ] Project plan refined with accurate estimates
- [ ] Stakeholder agreement on architecture

**Construction - Operational Capability Milestone**:
- [ ] Product is stable enough for beta testing
- [ ] Alpha test results documented
- [ ] Critical issues resolved
- [ ] User documentation is adequate
- [ ] Stakeholder agreement to deploy to beta users

**Transition - Product Release Milestone**:
- [ ] Product is ready for release
- [ ] All acceptance tests pass
- [ ] Deployment documentation complete
- [ ] Support materials ready
- [ ] Stakeholder sign-off obtained

### 3. Generate Phase Review Summary

Create a phase review summary including:
- Phase accomplishments
- Work products completed
- Risks and issues
- Lessons learned
- Recommendations for next phase

### 4. Create Review Presentation

Generate a review presentation outline:
- Executive summary
- Phase objectives vs. results
- Demonstrations (if applicable)
- Open issues and decisions needed

### 5. Notify User

Inform the user that:
- Phase review materials are ready
- Any completion criteria that are not yet met
- Decisions needed from stakeholders

## Output

Returns:
- Phase completion criteria checklist status
- List of completed work products
- Review summary
- Recommendations

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Project status not found | docs/project-status.md doesn't exist | Initialize project with phase skill first |
| Phase not recognized | Invalid phase name provided | Use valid phase: inception, elaboration, construction, transition |
| Criteria not met | Phase incomplete | Continue work or document exceptions |

## References

- Phase Milestones: `docs-eng-process/openup-knowledge-base/practice-management/risk_value_lifecycle/guidances/concepts/phase-milestones.md`
- Agent Workflow: `docs-eng-process/agent-workflow.md`

## See Also

- [openup-inception](../../openup-phases/inception/SKILL.md) - Inception phase details
- [openup-elaboration](../../openup-phases/elaboration/SKILL.md) - Elaboration phase details
- [openup-construction](../../openup-phases/construction/SKILL.md) - Construction phase details
- [openup-transition](../../openup-phases/transition/SKILL.md) - Transition phase details

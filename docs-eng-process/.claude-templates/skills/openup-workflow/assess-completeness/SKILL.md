---
name: openup-assess-completeness
description: Lightweight readiness assessment before task completion or phase transition
arguments:
  - name: scope
    description: Assessment scope (task, iteration, phase)
    required: false
  - name: strict
    description: Fail on any missing items (true/false, default: false)
    required: false
---

# Assess Completeness

This skill performs a lightweight readiness assessment to verify that all required work is complete before marking a task complete, completing an iteration, or transitioning to a new phase.

## When to Use

Use this skill when:
- About to complete a task and want to verify readiness
- Approaching end of iteration and need to assess completion
- Considering phase transition and need to verify criteria
- Want to ensure nothing was missed before moving forward
- Preparing for code review or handoff

## When NOT to Use

Do NOT use this skill when:
- Mid-iteration and just checking progress (use project status instead)
- Need detailed quality assessment (use dedicated testing skills)
- Looking for code review feedback (use peer review process)
- Only need to check git status (use git directly)

## Success Criteria

After using this skill, verify:
- [ ] All required checks are performed
- [ ] Readiness report is generated
- [ ] Missing items are identified (if any)
- [ ] Recommendations are provided
- [ ] Pass/fail status is clear

## Process Summary

1. Determine assessment scope
2. Perform scope-specific checks
3. Generate readiness report
4. Provide recommendations

## Detailed Steps

### 1. Determine Assessment Scope

Based on `$ARGUMENTS[scope]` (defaults to "task"):

| Scope | Focus | Typical Checks |
|-------|-------|----------------|
| task | Single task completion | Code, tests, docs, commit |
| iteration | Iteration completion | All tasks, metrics, goals met |
| phase | Phase transition | Phase criteria, artifacts |

### 2. Perform Scope-Specific Checks

#### Task Scope

**Code Status:**
```bash
git status --porcelain
```
- [ ] No uncommitted changes (or changes are intentional)
- [ ] Changed files match task scope

**Test Status:**
- [ ] Tests exist for new code
- [ ] Tests pass (run project test command)
- [ ] Test coverage is acceptable

**Documentation:**
- [ ] Code is self-documenting or has comments
- [ ] Design docs updated (if applicable)
- [ ] Use cases updated (if applicable)

**Task Tracking:**
- [ ] Task exists in roadmap
- [ ] Task status is accurate
- [ ] Related requirements linked

#### Iteration Scope

**All Task Checks:**
- [ ] All iteration tasks are complete
- [ ] No incomplete high-priority tasks
- [ ] Blocked tasks are documented

**Metrics:**
- [ ] Iteration goals met
- [ ] Planned vs actual comparison
- [ ] Velocity captured

**Documentation:**
- [ ] Project status updated
- [ ] Roadmap reflects completed work
- [ ] Risk list updated

**Quality:**
- [ ] All tests pass
- [ ] No critical bugs
- [ ] Code review complete

#### Phase Scope

**Phase Exit Criteria:**
- [ ] Inception: Vision, stakeholders, initial risk list
- [ ] Elaboration: Architecture baseline, 80% use cases detailed
- [ ] Construction: Feature complete, test coverage adequate
- [ ] Transition: Deployment ready, user documentation complete

**Artifacts:**
- [ ] Required phase artifacts exist
- [ ] Artifacts are reviewed and approved
- [ ] Artifacts are version-controlled

**Transition Readiness:**
- [ ] Stakeholder buy-in obtained
- [ ] Next phase planned
- [ ] Risks identified for next phase

### 3. Generate Readiness Report

Create a structured report:

```markdown
# Completeness Assessment Report

**Scope:** $ARGUMENTS[scope]
**Date:** [current date]
**Strict Mode:** $ARGUMENTS[strict]

## Overall Status: PASS/FAIL

## Checks Performed

### [Category]
- [x] Check 1: PASS
- [x] Check 2: PASS
- [ ] Check 3: FAIL - [reason]

## Missing Items
1. [Item 1]
2. [Item 2]

## Recommendations
1. [Recommendation 1]
2. [Recommendation 2]

## Next Steps
1. [Next step 1]
2. [Next step 2]
```

### 4. Handle Strict Mode

If `$ARGUMENTS[strict] == "true"`:
- Any missing item results in FAIL status
- All checks must pass for readiness

If `$ARGUMENTS[strict] != "true"` (default):
- Provide warnings for missing items
- May pass with recommendations

## Output

Returns a summary of:
- Assessment scope
- Overall pass/fail status
- Checks performed with results
- Missing items (if any)
- Recommendations
- Next steps

## Example Usage

```
/openup-assess-completeness scope: task
```

```
/openup-assess-completeness scope: iteration strict: true
```

```
/openup-assess-completeness scope: phase
```

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Invalid scope | Scope not one of: task, iteration, phase | Use valid scope value |
| No project status | docs/project-status.md doesn't exist | Initialize project first |
| Test command fails | Tests don't pass | Fix failing tests |
| Uncommitted changes | Work not committed | Commit or stash changes |

## References

- Agent Workflow: `docs-eng-process/agent-workflow.md`
- Phase Criteria: `docs-eng-process/openup-knowledge-base/practice-management/risk_value_lifecycle/`
- Quality Checklist: `docs-eng-process/.claude-templates/settings.json.example` (quality hooks)

## See Also

- [openup-complete-task](../complete-task/SKILL.md) - Complete task after passing assessment
- [openup-retrospective](../retrospective/SKILL.md) - Create retrospective after iteration
- [openup-phase-review](../phase-review/SKILL.md) - Formal phase review process

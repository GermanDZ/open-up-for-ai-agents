---
name: openup-assess-completeness
description: Lightweight readiness assessment before task completion or phase transition
arguments:
  - name: scope
    description: Assessment scope (task, iteration, phase)
    required: false
  - name: strict
    description: "Fail on any missing items (true/false, default: false)"
    required: false
---

# Assess Completeness

Lightweight readiness assessment to verify all required work is complete before marking a task done, completing an iteration, or transitioning phases.

## Process

### 1. Determine Assessment Scope

Based on `$ARGUMENTS[scope]` (defaults to "task"):

| Scope | Focus | Typical Checks |
|-------|-------|----------------|
| task | Single task completion | Code, tests, docs, commit |
| iteration | Iteration completion | All tasks, metrics, goals met |
| phase | Phase transition | Phase criteria, artifacts |

### 2. Perform Scope-Specific Checks

**Task Scope:**
- No uncommitted changes (or changes are intentional): `git status --porcelain`
- Changed files match task scope
- Tests exist for new code and pass
- Test coverage is acceptable
- Code is self-documenting; design docs updated if applicable
- Task exists in roadmap with accurate status

**Iteration Scope** (all task checks plus):
- All iteration tasks complete; no incomplete high-priority tasks
- Blocked tasks documented
- Iteration goals met; planned vs actual comparison; velocity captured
- Project status and roadmap updated; risk list updated
- All tests pass; no critical bugs; code review complete

**Phase Scope** (all iteration checks plus):
- Phase exit criteria met:
  - Inception: Vision, stakeholders, initial risk list
  - Elaboration: Architecture baseline, 80% use cases detailed
  - Construction: Feature complete, test coverage adequate
  - Transition: Deployment ready, user documentation complete
- Required phase artifacts exist, reviewed, and version-controlled
- Stakeholder buy-in obtained; next phase planned; risks identified

### 3. Generate Readiness Report

Output a structured report with: scope, date, strict mode, overall PASS/FAIL status, checks performed with results, missing items, recommendations, and next steps.

### 4. Handle Strict Mode

If `$ARGUMENTS[strict] == "true"`: any missing item results in FAIL. Otherwise: provide warnings for missing items; may pass with recommendations.

## Output

Returns: assessment scope, overall pass/fail status, checks performed with results, missing items, recommendations, next steps.

## See Also

- [openup-complete-task](../complete-task/SKILL.md) - Complete task after passing assessment
- [openup-retrospective](../retrospective/SKILL.md) - Create retrospective after iteration
- [openup-phase-review](../phase-review/SKILL.md) - Formal phase review process

---
name: openup-assess-completeness
description: Rubric-based readiness assessment before task completion or phase transition
arguments:
  - name: scope
    description: Assessment scope (task, iteration, phase)
    required: false
  - name: artifact
    description: "Work product type to assess against its rubric (use-case, architecture-notebook, iteration-plan, test-plan, vision). Auto-detected if not provided."
    required: false
  - name: strict
    description: "Fail on any missing items (true/false, default: false)"
    required: false
---

# Assess Completeness

Rubric-based readiness assessment to verify all required work is complete before marking a task done, completing an iteration, or transitioning phases.

For work product artifacts (use cases, architecture notebooks, etc.), this skill grades each quality criterion explicitly — producing a per-criterion breakdown rather than a generic pass/fail.

## Process

### 1. Determine Assessment Scope

Based on `$ARGUMENTS[scope]` (defaults to "task"):

| Scope | Focus | Typical Checks |
|-------|-------|----------------|
| task | Single task completion | Code, tests, docs, commit |
| iteration | Iteration completion | All tasks, metrics, goals met |
| phase | Phase transition | Phase criteria, artifacts |

### 2. Detect Work Product Type and Apply Rubric

If the task involves a work product artifact, load the appropriate rubric and grade each criterion explicitly.

**Detect artifact type** (use `$ARGUMENTS[artifact]` if provided, otherwise auto-detect):
- If `docs/use-cases/*.md` was modified → `use-case` rubric
- If `docs/architecture-notebook.md` was modified → `architecture-notebook` rubric
- If `docs/iteration-plan.md` was modified → `iteration-plan` rubric
- If `docs/test-plan.md` was modified → `test-plan` rubric
- If `docs/vision.md` was modified → `vision` rubric

**Load rubric from** `.claude/rubrics/<artifact-type>-rubric.md`

**Grade each criterion** in the rubric:
- `✅ [criterion name]` — fully satisfied
- `❌ [criterion name] — [specific gap description]` — what exactly is missing

**Rubric result:**
- `satisfied` — all criteria are ✅ → proceed
- `needs_revision` — any criteria are ❌ → **do not mark complete; fix gaps and re-assess**

If `needs_revision`: address each ❌ gap, then re-run this assessment. Continue iterating until all criteria are satisfied.

### 3. Perform Scope-Specific Checks

**Task Scope:**
- No uncommitted changes (or changes are intentional): `git status --porcelain`
- Changed files match task scope
- Tests exist for new code and pass
- Test coverage is acceptable
- Code is self-documenting; design docs updated if applicable
- Task exists in roadmap with accurate status
- If a work product artifact was produced: rubric result is `satisfied`

**Iteration Scope** (all task checks plus):
- All iteration tasks complete; no incomplete high-priority tasks
- Blocked tasks documented
- Iteration goals met; planned vs actual comparison; velocity captured
- Project status and roadmap updated; risk list updated
- All tests pass; no critical bugs; code review complete
- All work product artifacts for this iteration have passing rubric assessments

**Phase Scope** (all iteration checks plus):
- Phase exit criteria met:
  - Inception: Vision (rubric satisfied), stakeholders documented, initial risk list
  - Elaboration: Architecture notebook (rubric satisfied), 80% use cases detailed (each rubric satisfied)
  - Construction: Feature complete, test plan (rubric satisfied), test coverage adequate
  - Transition: Deployment ready, user documentation complete
- Required phase artifacts exist, reviewed, and version-controlled
- Stakeholder buy-in obtained; next phase planned; risks identified

### 4. Generate Readiness Report

Output a structured report:

```
## Completeness Assessment
Scope: [task|iteration|phase]
Date: [today]

### Work Product Quality (Rubric Assessment)
[If artifact assessed:]
Artifact: [type]
[Per-criterion grading output]
Result: satisfied | needs_revision

### Process Checks
[Each check with ✅ or ❌]

### Overall
Status: PASS | FAIL
[If FAIL: list specific items to address before re-running]
```

### 5. Handle Strict Mode

If `$ARGUMENTS[strict] == "true"`: any ❌ results in FAIL and the skill stops. Otherwise: provide specific gaps; the agent should address them before proceeding.

## Output

Returns: assessment scope, rubric grading (if applicable), process checks, overall pass/fail status, specific gaps to address.

## See Also

- [openup-complete-task](../complete-task/SKILL.md) - Complete task after passing assessment
- [openup-retrospective](../retrospective/SKILL.md) - Create retrospective after iteration
- [openup-phase-review](../phase-review/SKILL.md) - Formal phase review process

---
name: openup-create-vision
description: Generate a vision document from template
arguments:
  - name: project_name
    description: Name of the project
    required: true
  - name: problem_statement
    description: Brief description of the problem to be solved
    required: true
---

# Create Vision Document

This skill generates a vision document from the OpenUP template.

## When to Use

Use this skill when:
- Starting a new project and need to define the vision
- In Inception phase and need to document project scope
- Stakeholders need a clear understanding of project goals
- Need to define problem statement and proposed solution
- Creating initial project artifacts

## When NOT to Use

Do NOT use this skill when:
- Vision document already exists (update it directly or use revision process)
- Need detailed requirements (use use case skills instead)
- Looking for technical architecture (use `/openup-create-architecture-notebook`)
- In later phases (Elaboration+) when vision should be stable

## Success Criteria

After using this skill, verify:
- [ ] Vision document exists at `docs/vision.md`
- [ ] Project name and problem statement are filled in
- [ ] Stakeholders are identified
- [ ] Key features are listed
- [ ] Success criteria are defined

## Process

### 1. Read Project Context

Read `docs/project-status.md` to understand:
- Current phase
- Stakeholders
- Project context

### 2. Copy Template

Copy `docs-eng-process/templates/vision.md` to `docs/vision.md`

### 3. Fill in Vision Document

Update the vision document with:
- **Project name**: `$ARGUMENTS[project_name]`
- **Problem statement**: `$ARGUMENTS[problem_statement]`
- **Positioning**: What makes this solution unique
- **Stakeholders**: Key stakeholders and their needs
- **Key features**: High-level feature list
- **Constraints**: Technical, business, or other constraints

### 4. Validate Completeness

Ensure the vision document includes:
- Clear problem statement
- Proposed solution overview
- Stakeholder descriptions
- Key features and benefits
- Success criteria

## Output

Returns:
- Path to created vision document
- List of sections filled in
- Any sections that need manual completion

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Template not found | Template path incorrect | Verify `docs-eng-process/templates/vision.md` exists |
| File already exists | Vision document already created | Update existing file or confirm overwrite |
| Missing arguments | Required arguments not provided | Provide project_name and problem_statement |

## References

- Vision Template: `docs-eng-process/templates/vision.md`
- Vision Work Product: `docs-eng-process/openup-knowledge-base/core/common/workproducts/vision.md`
- Analyst Role: `docs-eng-process/openup-knowledge-base/core/role/roles/analyst-6.md`

## See Also

- [openup-inception](../../openup-phases/inception/SKILL.md) - Inception phase guidance
- [openup-create-use-case](../create-use-case/SKILL.md) - Create detailed use cases
- [openup-create-risk-list](../create-risk-list/SKILL.md) - Document project risks

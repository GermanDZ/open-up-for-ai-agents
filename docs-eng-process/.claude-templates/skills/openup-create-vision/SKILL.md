---
name: openup-create-vision
description: Generate a vision document from template
model: sonnet
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

### Load Project Config (context + rules — do this first)

If `docs/project-config.yaml` exists, apply it before drafting (skip if
absent): inject its `context:` as `<project-context>` and its `rules.vision`
as `<project-rules>`, then confirm every injected rule holds before marking
the artifact complete. Rules are *additive* — they may add but never waive a
framework criterion. Full mechanism + precedence (the single source):
`docs-eng-process/project-config.md`.

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

### 4. Self-Critique

Apply the **Self-Critique SOP** (`docs-eng-process/agent-workflow.md`) before
validating: take a hostile-reviewer stance, surface every load-bearing
assumption into the document, and confirm the problem statement and success
criteria are falsifiable — not aspirational claims that could never fail. Fix or
explicitly flag each genuine weakness, then record the weakest point and its
resolution in one line.

### 5. Validate Completeness

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

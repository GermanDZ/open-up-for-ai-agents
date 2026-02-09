---
name: create-vision
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

## References

- Vision Template: `docs-eng-process/templates/vision.md`
- Vision Work Product: `docs-eng-process/openup-knowledge-base/core/common/workproducts/vision.md`
- Analyst Role: `docs-eng-process/openup-knowledge-base/core/role/roles/analyst-6.md`

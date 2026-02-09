---
name: create-architecture-notebook
description: Generate or update architecture documentation from template
arguments:
  - name: system_name
    description: Name of the system
    required: true
  - name: architectural_concerns
    description: Key architectural concerns to address
    required: false
---

# Create Architecture Notebook

This skill generates or updates an architecture notebook from the OpenUP template.

## Process

### 1. Check for Existing Architecture

Check if `docs/architecture-notebook.md` exists:
- If yes, update it
- If no, create from template

### 2. Read Project Context

Read `docs/project-status.md`, `docs/vision.md` to understand:
- System requirements
- Constraints
- Stakeholder concerns

### 3. Copy Template (if new)

If creating new, copy `docs-eng-process/templates/architecture-notebook.md` to `docs/architecture-notebook.md`

### 4. Fill in Architecture Notebook

Update with:
- **System name**: `$ARGUMENTS[system_name]`
- **Architectural concerns**: From `$ARGUMENTS[architectural_concerns]` or derived from requirements
- **Architecture overview**: High-level system architecture
- **Key architectural decisions**: Rationale for major decisions
- **Constraints**: Technical and business constraints
- **Quality attributes**: Performance, security, scalability requirements
- **Subsystem decomposition**: Major system components

### 5. Validate Completeness

Ensure the architecture notebook includes:
- System overview and context
- Key architectural decisions with rationale
- Architectural constraints
- Quality attribute requirements
- Subsystem/component decomposition

## Output

Returns:
- Path to architecture notebook
- List of sections filled in
- Architectural decisions documented

## References

- Architecture Notebook Template: `docs-eng-process/templates/architecture-notebook.md`
- Architecture Notebook Work Product: `docs-eng-process/openup-knowledge-base/practice-technical/evolutionary_arch/base/workproducts/architecture-notebook-6.md`
- Architect Role: `docs-eng-process/openup-knowledge-base/core/role/roles/architect-6.md`

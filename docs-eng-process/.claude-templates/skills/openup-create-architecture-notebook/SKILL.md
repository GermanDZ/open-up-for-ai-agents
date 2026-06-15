---
name: openup-create-architecture-notebook
description: Generate or update architecture documentation from template
model: sonnet
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

## When to Use

Use this skill when:
- Starting Elaboration phase and need to document architecture
- Making significant architectural decisions
- Need to document system design and constraints
- Establishing architecture baseline
- Reviewing or updating existing architecture

## When NOT to Use

Do NOT use this skill when:
- In Inception phase before architecture is defined (use `/openup-create-vision`)
- Need detailed component design (use design documents)
- Looking for implementation details (use code documentation)
- Architecture notebook exists and only minor updates needed (edit directly)

## Success Criteria

After using this skill, verify:
- [ ] Architecture notebook exists at `docs/architecture-notebook.md`
- [ ] System name and context are defined
- [ ] Key architectural decisions are documented
- [ ] Architectural constraints are listed
- [ ] Quality attributes are specified

## Process

### Load Project Config (context + rules — do this first)

If `docs/project-config.yaml` exists, apply it before drafting (skip if
absent): inject its `context:` as `<project-context>` and its `rules.architecture-notebook`
as `<project-rules>`, then confirm every injected rule holds before marking
the artifact complete. Rules are *additive* — they may add but never waive a
framework criterion. Full mechanism + precedence (the single source):
`docs-eng-process/project-config.md`.

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

### 4a. Write Instance Frontmatter (T-038 — doc traceability)

The architecture notebook holds a *series* of architectural decisions; for
v1 we tag the notebook file as a single `decision` work-product instance
that traces back to the project vision (per the v1 spine: `decision →
traces-from → vision`). Per-decision ADR files are still welcome as
additional `decision` instances under `docs/decisions/` — each gets the
same instance frontmatter, with a distinct `id`. Grade against the
cross-cutting
[Doc Traceability Rubric](../../rubrics/doc-traceability-rubric.md).

Example block (replaces the template's provenance frontmatter):

```yaml
---
type: decision              # required — v1 spine
id: D-01                    # stable, project-unique (notebook = first decision)
title: Architecture Notebook — <System Name>
status: approved
traces-from: [VIS-001]      # the vision this architecture serves
owner-role: architect
---
```

Field reference: [`docs-eng-process/doc-frontmatter.md`](../../../docs-eng-process/doc-frontmatter.md).
Validator: `python3 scripts/check-docs.py`.

### 5. Self-Critique

Apply the **Self-Critique SOP** (`docs-eng-process/sops/self-critique.md`) before
validating: take a hostile-reviewer stance, surface every load-bearing
assumption into the notebook, and confirm each architectural decision records
the rejected alternatives and the constraint that forced it — not just the
choice made. Fix or explicitly flag each genuine weakness, then record the
weakest point and its resolution in one line.

### 6. Validate Completeness

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

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Template not found | Template path incorrect | Verify `docs-eng-process/templates/architecture-notebook.md` exists |
| Insufficient context | Vision/requirements not defined | Create vision document first |
| Overwriting existing | Architecture notebook already exists | Update existing file instead of creating new |

## References

- Architecture Notebook Template: `docs-eng-process/templates/architecture-notebook.md`
- Architecture Notebook Work Product: `docs-eng-process/openup-knowledge-base/practice-technical/evolutionary_arch/base/workproducts/architecture-notebook-6.md`
- Architect Role: `docs-eng-process/openup-knowledge-base/core/role/roles/architect-6.md`

## See Also

- [openup-elaboration](../../openup-phases/elaboration/SKILL.md) - Elaboration phase guidance
- [openup-create-vision](../create-vision/SKILL.md) - Define vision before architecture
- [openup-create-risk-list](../create-risk-list/SKILL.md) - Document technical risks

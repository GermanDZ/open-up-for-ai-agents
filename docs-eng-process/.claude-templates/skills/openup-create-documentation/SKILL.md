---
name: openup-create-documentation
description: Generate human-readable documentation from code and artifacts
arguments:
  - name: doc_type
    description: Type of documentation (user-guide, api-reference, troubleshooting, tutorial)
    required: true
  - name: feature
    description: Feature or component to document
    required: true
  - name: output_path
    description: Output path for documentation (optional, defaults to docs/user-guides/)
    required: false
---

# Create Documentation

Generate human-readable documentation from use cases, code, and artifacts.

## Process

### 1. Determine Documentation Type

Based on `$ARGUMENTS[doc_type]`:

| doc_type | Template | Purpose |
|----------|----------|---------|
| user-guide | user-guide-template.md | End-user documentation |
| api-reference | api-reference-template.md | API documentation |
| troubleshooting | (generated) | Common issues and solutions |
| tutorial | (generated) | Step-by-step learning |

### 2. Gather Source Material

Read relevant sources for the feature: use cases (`docs/use-cases/`), test cases (`docs/test-cases/`), design docs (`docs/design/`), and source code (`src/`). Adapt sources based on doc_type.

### 3. Generate Documentation

See type-specific files for detailed generation process:
- [user-guide.md](./user-guide.md)
- [api-reference.md](./api-reference.md)
- [troubleshooting.md](./troubleshooting.md)
- [tutorial.md](./tutorial.md)

### 4. Validate and Review

- Verify all examples are accurate
- Test code examples if applicable
- Check cross-references
- Ensure clarity for target audience

### 5. Create Documentation File

- Default path: `docs/user-guides/<feature>-<doc_type>.md`
- Custom path: Use `$ARGUMENTS[output_path]` if provided
- Link related documentation

## Example Usage

```
/openup-create-documentation doc_type: user-guide feature: user-authentication
/openup-create-documentation doc_type: api-reference feature: payment-api output_path: docs/api/
```

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| No use case found | Feature lacks use cases | Create use cases first |
| Code not found | Feature not implemented | Verify feature name and status |
| Template missing | Template not available | Use generic structure |

## References

- User Guide Template: `docs-eng-process/templates/user-guide-template.md`
- API Reference Template: `docs-eng-process/templates/api-reference-template.md`

## See Also

- [openup-create-use-case](../create-use-case/SKILL.md) - Create use cases first
- [openup-detail-use-case](../detail-use-case/SKILL.md) - Detail use cases for better documentation

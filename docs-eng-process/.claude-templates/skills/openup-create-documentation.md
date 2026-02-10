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

This skill generates human-readable documentation from use cases, code, and other artifacts. It supports multiple documentation types including user guides, API references, troubleshooting guides, and tutorials.

## When to Use

Use this skill when:
- Feature implementation is complete and needs user documentation
- Creating API reference for external or internal developers
- Documenting common issues and solutions
- Creating tutorial content for onboarding
- Preparing for release or deployment

## When NOT to Use

Do NOT use this skill when:
- Feature is still under active development
- Design is likely to change significantly
- Only need technical design docs (use design documents instead)
- Documentation already exists and just needs updates

## Success Criteria

After using this skill, verify:
- [ ] Documentation file is created at the specified location
- [ ] Content is accurate based on use cases and code
- [ ] Examples are clear and tested
- [ ] Structure follows the appropriate template
- [ ] Related documentation is cross-referenced

## Process Summary

1. Determine documentation type and read relevant template
2. Gather source material (use cases, code, tests)
3. Generate documentation structure
4. Fill in content with examples
5. Review and validate accuracy

## Detailed Steps

### 1. Determine Documentation Type

Based on `$ARGUMENTS[doc_type]`, select the appropriate approach:

| doc_type | Template | Purpose |
|----------|----------|---------|
| user-guide | user-guide-template.md | End-user documentation |
| api-reference | api-reference-template.md | API documentation |
| troubleshooting | (generated) | Common issues and solutions |
| tutorial | (generated) | Step-by-step learning |

### 2. Gather Source Material

**For User Guides:**
- Read use case: `docs/use-cases/<feature>.md`
- Read test cases: `docs/test-cases/<feature>*.md`
- Review code: `src/` directories for the feature
- Check for existing documentation

**For API References:**
- Read design documents: `docs/design/<feature>*.md`
- Review API endpoints in code
- Check for OpenAPI/Swagger specs
- Review authentication implementation

**For Troubleshooting:**
- Read test cases for edge cases
- Review error handling in code
- Check issue tracker for common problems
- Review logs and error messages

**For Tutorials:**
- Start with use cases
- Review basic workflow in code
- Identify prerequisite knowledge
- Create progressive learning steps

### 3. Generate Documentation

See type-specific documentation files:
- [user-guide.md](./user-guide.md) - User guide generation process
- [api-reference.md](./api-reference.md) - API reference generation process
- [troubleshooting.md](./troubleshooting.md) - Troubleshooting guide generation
- [tutorial.md](./tutorial.md) - Tutorial creation process

### 4. Validate and Review

- Verify all examples are accurate
- Test code examples if applicable
- Check cross-references
- Ensure clarity for target audience

### 5. Create Documentation File

Create the output file:
- Default path: `docs/user-guides/<feature>-<doc_type>.md`
- Custom path: Use `$ARGUMENTS[output_path]` if provided
- Link related documentation

## Output

Returns a summary of:
- Documentation file created
- Documentation type
- Source artifacts used
- Word count/sections count
- Related documentation references

## Example Usage

```
/openup-create-documentation doc_type: user-guide feature: user-authentication
```

```
/openup-create-documentation doc_type: api-reference feature: payment-api output_path: docs/api/
```

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| No use case found | Feature doesn't have documented use cases | Create use cases first |
| Code not found | Feature implementation doesn't exist | Verify feature name and implementation status |
| Template missing | Documentation template not available | Use generic structure |
| Out of date | Documentation doesn't match current implementation | Review and update |

## References

- User Guide Template: `docs-eng-process/templates/user-guide-template.md`
- API Reference Template: `docs-eng-process/templates/api-reference-template.md`
- Documentation Guide: `docs-eng-process/openup-knowledge-base/` (if available)

## See Also

- [openup-create-use-case](../create-use-case/SKILL.md) - Create use cases first
- [openup-detail-use-case](../detail-use-case/SKILL.md) - Detail use cases for better documentation
- [openup-transition](../../openup-phases/transition/SKILL.md) - Transition phase documentation activities

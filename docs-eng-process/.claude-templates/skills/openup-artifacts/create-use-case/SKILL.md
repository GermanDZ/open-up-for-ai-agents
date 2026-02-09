---
name: openup-create-use-case
description: Create a use case specification from template
arguments:
  - name: use_case_name
    description: Name of the use case
    required: true
  - name: primary_actor
    description: The primary actor for this use case
    required: true
  - name: description
    description: Brief description of what the use case accomplishes
    required: true
---

# Create Use Case

This skill creates a use case specification from the OpenUP template.

## When to Use

Use this skill when:
- Need to document user interactions with the system
- In Inception or Elaboration phase defining requirements
- Capturing functional requirements from user perspective
- Need to specify preconditions, flows, and postconditions
- Creating test scenarios from requirements

## When NOT to Use

Do NOT use this skill when:
- Need non-functional requirements (use architecture notebook)
- Looking for technical specifications (use design documents)
- Documenting internal system behavior (use technical design)
- Use case already exists (update existing file)

## Success Criteria

After using this skill, verify:
- [ ] Use case file exists in `docs/use-cases/`
- [ ] Use case name and primary actor are defined
- [ ] Basic flow is documented
- [ ] Alternative flows are identified
- [ ] Pre/postconditions are specified

## Process

### 1. Create Use Cases Directory

Ensure `docs/use-cases/` directory exists.

### 2. Generate Filename

Create filename from use case name: `docs/use-cases/<use-case-name>.md`

### 3. Copy Template

Copy `docs-eng-process/templates/use-case-specification.md` to the new file.

### 4. Fill in Use Case

Update the use case specification with:
- **Use case name**: `$ARGUMENTS[use_case_name]`
- **Primary actor**: `$ARGUMENTS[primary_actor]`
- **Description**: `$ARGUMENTS[description]`
- **Preconditions**: What must be true before starting
- **Basic flow**: Step-by-step main interaction
- **Alternative flows**: Alternative paths and edge cases
- **Postconditions**: What is true after completion

### 5. Validate Completeness

Ensure the use case includes:
- Clear name and description
- Identified actors
- Basic flow of events
- Key alternative flows
- Pre/postconditions

## Output

Returns:
- Path to created use case file
- Use case ID (for tracking)
- Sections filled in

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Template not found | Template path incorrect | Verify `docs-eng-process/templates/use-case-specification.md` exists |
| Invalid filename | Use case name has invalid characters | Sanitize filename, replace spaces with dashes |
| Missing actors | Actors not identified | Identify primary and secondary actors from vision/requirements |

## References

- Use Case Template: `docs-eng-process/templates/use-case-specification.md`
- Use Case Work Product: `docs-eng-process/openup-knowledge-base/core/common/workproducts/use_case.md`

## See Also

- [openup-create-vision](../create-vision/SKILL.md) - Define project vision first
- [openup-create-test-plan](../create-test-plan/SKILL.md) - Generate tests from use cases
- [openup-elaboration](../../openup-phases/elaboration/SKILL.md) - Elaboration phase use case detail

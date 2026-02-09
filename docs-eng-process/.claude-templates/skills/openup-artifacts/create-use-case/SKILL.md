---
name: create-use-case
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

## References

- Use Case Template: `docs-eng-process/templates/use-case-specification.md`
- Use Case Work Product: `docs-eng-process/openup-knowledge-base/core/common/workproducts/use_case.md`

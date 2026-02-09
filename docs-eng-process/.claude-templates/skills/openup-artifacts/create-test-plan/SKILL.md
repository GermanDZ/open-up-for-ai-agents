---
name: create-test-plan
description: Generate test cases and test plan from use cases and requirements
arguments:
  - name: scope
    description: What to test (e.g., specific feature, use case)
    required: true
---

# Create Test Plan

This skill generates test cases and test documentation from the OpenUP templates.

## Process

### 1. Read Requirements

Read relevant documentation:
- `docs/use-cases/*.md` for use cases
- `docs/requirements/*.md` for requirements
- Any design documents for the `$ARGUMENTS[scope]`

### 2. Create Test Directory

Ensure `docs/test-cases/` and `docs/test-scripts/` directories exist.

### 3. Copy Templates

Copy templates as needed:
- `docs-eng-process/templates/test-case.md` → `docs/test-cases/<name>-test-case.md`
- `docs-eng-process/templates/test-script.md` → `docs/test-scripts/<name>-test-script.md`

### 4. Fill in Test Cases

For each test case, document:
- **Test case ID** and name
- **Description**: What is being tested
- **Preconditions**: State before test
- **Test steps**: Step-by-step actions
- **Expected results**: What should happen
- **Postconditions**: State after test
- **Priority**: Test priority level

### 5. Fill in Test Scripts

For each test script, document:
- **Test script ID** and name
- **Purpose**: What the script validates
- **Setup**: How to prepare for the test
- **Test procedures**: Detailed test execution steps
- **Cleanup**: How to clean up after test

### 6. Validate Coverage

Ensure test coverage includes:
- Happy path scenarios
- Edge cases
- Error conditions
- Integration points

## Output

Returns:
- Paths to created test cases and scripts
- Test coverage summary
- Any gaps identified

## References

- Test Case Template: `docs-eng-process/templates/test-case.md`
- Test Script Template: `docs-eng-process/templates/test-script.md`
- Tester Role: `docs-eng-process/openup-knowledge-base/core/role/roles/tester-5.md`

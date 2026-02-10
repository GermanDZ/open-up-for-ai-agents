---
name: openup-detail-use-case
description: Transform a high-level use case into detailed scenarios with test cases
arguments:
  - name: use_case_name
    description: Name of the use case to detail (file name without .md)
    required: true
  - name: generate_tests
    description: Generate test cases from scenarios (true/false, default: true)
    required: false
---

# Detail Use Case

This skill transforms a high-level use case specification into detailed scenarios with Gherkin acceptance criteria and test cases.

## When to Use

Use this skill when:
- A high-level use case exists but lacks detailed scenarios
- Need to document happy paths, alternative flows, and error cases
- Ready to create Gherkin acceptance criteria for automation
- Preparing to generate test cases from use cases
- In Elaboration phase when detailing requirements

## When NOT to Use

Do NOT use this skill when:
- The use case doesn't exist (use `/openup-create-use-case` first)
- The use case is already fully detailed with scenarios
- Just need to create a new use case from scratch
- Working on non-functional requirements (use architecture notebook)

## Success Criteria

After using this skill, verify:
- [ ] Use case is updated with detailed scenarios
- [ ] Happy path, alternative paths, and error paths are documented
- [ ] Gherkin acceptance criteria are written for each scenario
- [ ] Test cases are generated (if generate_tests=true)
- [ ] All actors are identified (primary and secondary)
- [ ] Preconditions and postconditions are clear

## Process Summary

1. Read existing use case
2. Identify scenarios (happy path, alternatives, errors)
3. Document each scenario with step-by-step flows
4. Generate Gherkin acceptance criteria
5. Create test cases (if requested)
6. Update the use case file

## Detailed Steps

### 1. Read Existing Use Case

Read the use case file from `docs/use-cases/$ARGUMENTS[use_case_name].md`:
- Extract use case name, ID, and description
- Identify the primary actor
- Review existing basic flow
- Note any alternative flows already documented

### 2. Identify Scenarios

Break down the use case into distinct scenarios:

**Happy Path (Primary Scenario):**
- The main success scenario where everything goes as expected
- User follows the most common workflow

**Alternative Paths:**
- Different ways to accomplish the same goal
- Optional steps or branching logic
- User choices and variations

**Error Paths:**
- Invalid inputs or actions
- System failures
- Edge cases and boundary conditions

### 3. Document Scenarios

For each scenario, document:

| Element | Description |
|---------|-------------|
| Scenario Name | Clear, descriptive name |
| Description | What makes this scenario unique |
| Steps | Step-by-step interaction (Actor → System) |
| Preconditions | What must be true before this scenario |
| Postconditions | What is true after this scenario |

### 4. Generate Gherkin Acceptance Criteria

For each scenario, write Gherkin format criteria:

```gherkin
Given <precondition>
And <additional preconditions>
When <actor takes action>
And <additional actions>
Then <expected outcome>
And <additional outcomes>
```

**Example:**

```gherkin
Given the user is logged in
And the user has items in their cart
When the user clicks "Checkout"
Then the user is redirected to the payment page
And the order total is displayed
```

### 5. Create Test Cases (Optional)

If `$ARGUMENTS[generate_tests] == "true"`:

Create test case files for each scenario in `docs/test-cases/`:
- Filename format: `<use-case-name>-<scenario>-test.md`
- Use the test case template as a guide
- Include scenario steps, test data, and expected results

### 6. Update the Use Case File

Update the existing use case file with:
- Add detailed scenarios section
- Include Gherkin acceptance criteria
- Link to test case files
- Ensure all actors are documented
- Verify pre/postconditions are complete

## Output

Returns a summary of:
- Use case file updated
- Number of scenarios documented
- Test cases created (if applicable)
- Sections added to use case

## Example Usage

```
/openup-detail-use-case use_case_name: user-login generate_tests: true
```

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Use case not found | File doesn't exist in docs/use-cases/ | Verify use case name or create use case first |
| No basic flow | Use case is incomplete | Complete basic flow before detailing |
| Duplicate scenarios | Same scenario documented multiple times | Consolidate similar scenarios |
| Missing actors | Actors not identified | Identify primary and secondary actors from context |

## References

- Use Case Template: `docs-eng-process/templates/use-case-specification.md`
- Use Case Scenarios Template: `docs-eng-process/templates/use-case-scenarios.md`
- Test Case Template: `docs-eng-process/templates/test-case.md`
- Gherkin Syntax: https://cucumber.io/docs/gherkin/reference/

## See Also

- [openup-create-use-case](../create-use-case/SKILL.md) - Create a new use case
- [openup-create-test-plan](../create-test-plan/SKILL.md) - Generate test plan from use cases
- [openup-elaboration](../../openup-phases/elaboration/SKILL.md) - Elaboration phase activities

---
name: openup-create-test-plan
description: Generate test cases and test plan from use cases and requirements
model: inherit
arguments:
  - name: scope
    description: What to test (e.g., specific feature, use case)
    required: true
---

# Create Test Plan

This skill generates test cases and test documentation from the OpenUP templates.

## When to Use

Use this skill when:
- Need to create test cases for features or use cases
- In Elaboration or Construction phase planning tests
- Starting testing for a new feature
- Need to document test procedures
- Creating test scripts for automation

## When NOT to Use

Do NOT use this skill when:
- Looking to execute tests (use test runner)
- Need to debug test failures (use debugging tools)
- Test plan exists and only minor updates needed (edit directly)
- Looking for test reports (use test reporting)

## Success Criteria

After using this skill, verify:
- [ ] Test cases exist in `docs/test-cases/`
- [ ] Test scripts exist in `docs/test-scripts/`
- [ ] Test coverage includes happy path and edge cases
- [ ] Expected results are defined
- [ ] Test procedures are documented

## Process

### Load Project Config (context + rules — do this first)

Before drafting, layer in project-owned context and rules so the artifact reflects
facts and standards the framework can't infer. Full mechanism + precedence:
`docs-eng-process/project-config.md`.

1. If `docs/project-config.yaml` exists, read it. If it is **absent, skip this
   step** — framework defaults apply unchanged.
2. Inject `context:` into your working prompt wrapped in
   `<project-context>…</project-context>`, and `rules.<TYPE>` (if present) wrapped
   in `<project-rules>…</project-rules>`. For this skill `<TYPE>` is **`test-plan`**.
3. Project rules are **additive** to the framework rubric — precedence is
   **framework rubric → project rules → task-spec safeguards**. A project rule may
   add a criterion but may **not** waive a framework rubric criterion or a safeguard.
4. Before marking this artifact complete, confirm every injected `<project-rules>`
   item is satisfied alongside the framework rubric.

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

### 6. Self-Critique

Apply the **Self-Critique SOP** (`docs-eng-process/agent-workflow.md`) before
validating coverage: take a hostile-reviewer stance, surface every load-bearing
assumption into the plan, and confirm the suite genuinely exercises error and
edge paths — not happy-path restatements — and that every case is written so it
can actually fail. Fix or explicitly flag each genuine weakness, then record the
weakest point and its resolution in one line.

### 7. Validate Coverage

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

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Template not found | Template path incorrect | Verify `docs-eng-process/templates/test-case.md` and `test-script.md` exist |
| Insufficient coverage | Only happy path tests | Add edge cases and error conditions |
| Missing expected results | Test steps without validation | Define expected results for each test step |

## References

- Test Case Template: `docs-eng-process/templates/test-case.md`
- Test Script Template: `docs-eng-process/templates/test-script.md`
- Tester Role: `docs-eng-process/openup-knowledge-base/core/role/roles/tester-5.md`

## See Also

- [openup-create-use-case](../create-use-case/SKILL.md) - Generate tests from use cases
- [openup-construction](../../openup-phases/construction/SKILL.md) - Construction phase testing
- [openup-phase-review](../../openup-workflow/phase-review/SKILL.md) - Review test coverage

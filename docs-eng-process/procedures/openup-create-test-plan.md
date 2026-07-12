---
name: openup-create-test-plan
description: Generate test cases and test plan from use cases and requirements
tier: authoring
capabilities: {required: [read_write_files, exec], optional: []}
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
- [ ] Test coverage includes happy path, edge cases, error conditions, and integration points
- [ ] Expected results are defined
- [ ] Test procedures are documented

## Process

### Load Project Config (context + rules — do this first)

If `docs/project-config.yaml` exists, apply it before drafting (skip if
absent): inject its `context:` as `<project-context>` and its `rules.test-plan`
as `<project-rules>`, then confirm every injected rule holds before marking
the artifact complete. Rules are *additive* — they may add but never waive a
framework criterion. Full mechanism + precedence (the single source):
`docs-eng-process/project-config.md`.

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

### 4a. Write Instance Frontmatter (T-038 — doc traceability)

Replace each test-case file's template provenance frontmatter (`type:
Template`, `source_url`) with an **instance** block declaring the file as a
typed `test-case` work-product instance. Every test-case must trace from
the requirement or use case it verifies (per the v1 spine: `test-case →
traces-from → requirement | use-case`). The **upstream** instance ALSO
gains a `verified-by:` entry pointing at this test-case id — that bidir
link is what `check-docs.py --coverage` reads when it grades whether a
requirement has a verifying test. Grade against the cross-cutting
[Doc Traceability Rubric](../../rubrics/doc-traceability-rubric.md).

Example block:

```yaml
---
type: test-case             # required — v1 spine
id: TC-031                  # stable, project-unique
title: <Test Case Name>
status: implemented
traces-from: [REQ-014]      # or a use-case id; both are valid upstream types
owner-role: tester
---
```

Then add `verified-by: [TC-031, …]` to the upstream requirement / use-case
instance(s). Doing both halves at the test-plan step keeps the trace
symmetric in one author-time pass instead of leaving it to a later cleanup.

Field reference: [`docs-eng-process/doc-frontmatter.md`](../../../docs-eng-process/doc-frontmatter.md).
Validator: `python3 scripts/check-docs.py --coverage`.

### 5. Fill in Test Scripts

For each test script, document:
- **Test script ID** and name
- **Purpose**: What the script validates
- **Setup**: How to prepare for the test
- **Test procedures**: Detailed test execution steps
- **Cleanup**: How to clean up after test

### 6. Self-Critique

Apply the **Self-Critique SOP** (`docs-eng-process/sops/self-critique.md`) before
validating coverage: take a hostile-reviewer stance, surface every load-bearing
assumption into the plan, and confirm the suite genuinely exercises error and
edge paths — not happy-path restatements — and that every case is written so it
can actually fail. List every weakness you find — including ones you are uncertain about — then fix or explicitly flag each one. Rank them and record the top one or two with their resolutions.

### 7. Validate Coverage

Re-check every item in **Success Criteria** (top of this skill) against the
document you produced; fix any gap before returning.

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

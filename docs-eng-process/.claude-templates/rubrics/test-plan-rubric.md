# Test Plan Rubric

Use this rubric to assess whether a test plan is complete and correct.
Grade each criterion: ✅ satisfied / ❌ gap — [specific description of what's missing]

---

## 1. Test Scope
**Satisfied when:** The plan clearly states what is in scope for testing (features, components, integrations) and what is explicitly out of scope, with justification for exclusions.

## 2. Test Types and Levels
**Satisfied when:** The plan identifies which test types will be used (unit, integration, end-to-end, performance, security, etc.) and at what level (component, API, UI). The rationale for the chosen mix is stated.

## 3. Test Scenarios
**Satisfied when:** At least 5 specific test scenarios are documented. Each scenario has: a name, the precondition, the action(s) taken, and the expected result. Scenarios cover both happy paths and key failure cases.

## 4. Coverage Matrix
**Satisfied when:** The plan includes or references a mapping from features/requirements/use cases to test scenarios, demonstrating that all planned features have test coverage. Gaps are explicitly identified.

## 5. Test Environment
**Satisfied when:** The test environment requirements are described: required services, test data setup, environment configuration differences from production, and how the environment is set up or reset between test runs.

## 6. Exit Criteria
**Satisfied when:** Clear, measurable exit criteria are defined for completing testing. Examples: "All P0 and P1 test cases pass", "Zero open critical defects", "Code coverage ≥ 80%". Vague criteria like "testing is complete" are not acceptable.

## 7. Defect Handling
**Satisfied when:** The plan describes how defects found during testing will be tracked, prioritized, and resolved. Severity levels are defined.

## 8. Test Automation Strategy
**Satisfied when:** The plan states which tests will be automated vs. manual and why. For automated tests, the tooling and where tests live in the repo are identified.

---

## Grading Instructions

For each criterion above, write one of:
- `✅ [criterion name]` — fully satisfied
- `❌ [criterion name] — [specific gap]` — e.g., "❌ Exit Criteria — criteria are vague; need measurable thresholds"

After grading all criteria, output:
- **Result**: `satisfied` (all ✅) or `needs_revision` (any ❌)
- **Summary**: one sentence on the most critical gap if `needs_revision`

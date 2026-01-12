---
title: Run Tests
source_url: practice.tech.concurrent_testing.base/tasks/run_tests_49698054.html
type: Task
uma_name: run_tests
page_guid: _0jVEkMlgEdmt3adZL5Dmdw
keywords:
- results
- test
- tests
related:
  roles:
  - tester-5
---


 Run the appropriate tests scripts, analyze results, articulate issues, and communicate test results to the team.
---
Disciplines: [Test](../../../core/cat/disciplines/test-1.md)

Purpose

To provide feedback to the team about how well a build satisfies the requirements.
---

Relationships

Roles| Primary Performer:
  * [Tester](../../../core/role/roles/tester-5.md)

| Additional Performers:
---|---|---
Inputs| Mandatory:
  * [\[Technical Implementation\]](./../../core.tech.slot.base/workproducts/technical_implementation_slot_E92F6A39.html)
  * [Test Script](../../../core/common/workproducts/test-script.md)

| Optional:
  * None


Outputs|
  * [Test Log](../../../core/common/workproducts/test-log.md)



Steps

Review work items completed in the build | Review work items that were integrated into the build since the last test cycle. Focus on identifying any previously unimplemented or failing requirements are now expected to meet the conditions of satisfaction.
---

Select Test Scripts

Select test scripts related to work items completed in the build.  Ideally, each test cycle should execute all test scripts, but some types of tests are too time-consuming to include in each test cycle. For manual or time-intensive tests, include test scripts that will provide the most useful feedback about the maturing solution based on the objectives of the iteration.  Plan with test suites to simplify the process of selecting tests for each build \(see [Guideline: Test Suite](../../../core/common/guidances/guidelines/test-suite.md)\).
---

Execute Test Scripts against the build

Run the tests using the step-by-step procedure in the [Test Script](../../../core/common/workproducts/test-script.md).  For automated test scripts, initiate the test execution. Automated test scripts should run in suites in the correct sequence, and collect results in the Test Log.  To execute a manual test script, establish its preconditions, perform the steps while logging results in the [Test Log](../../../core/common/workproducts/test-log.md), and perform any teardown steps.
---

Analyze and communicate test results

Post the test results in a conspicuous place that is accessible to the entire team, such as a white board or Wiki.  For each failing test script, analyze the Test Log to identify the cause of the test failure. Begin with failing tests that you expected to begin passing against this build, which may indicate newly delivered work items that do not meet the conditions of satisfaction. Then review previously passing test scripts that are now failing, which may indicate regressive issues in the build.
  * If a test failed because the solution does not meet the conditions of satisfaction for the test case, log the issue in the Work Items List. In the work item, clearly identify the observed behavior, the expected behavior, and steps to repeat the issue. Note which failing test initially discovered the issue.
  * If a test failed because of a change in the system \(such as a user-interface change\), but the implementation still meets the conditions of satisfaction in the test case, update the test script to pass with the new implementation.
  * If a test failed because the test script is incorrect \(a false negative result\) or passed when it was expected to fail \(a false positive result\), update the test script to correctly implement the conditions of satisfaction in the test case. If the test case for a requirement is invalid, create a request change to modify the conditions of satisfaction for the requirement.

It's best to update test scripts as quickly and continuously as possible. If the change to the test script is trivial, update the test while analyzing the test results. If the change is a non-trivial task, submit it to the Work Items List so it can be prioritized against other tasks.
---

Provide feedback to the team

Summarize and provide feedback to the team about how well the build satisfies the requirements planned to the iteration. Focus on measuring progress in terms of passing tests.  Explain the results for the test cycle in the context of overall trends:
  * How many tests were selected for the build, and what are their statuses \(pass, fail, blocked, not run, etc.\)?
  * How many issues were added to the Work Items List, and what are their statuses and severities?
  * For test scripts that were blocked or skipped, what are the main reasons \(such as known issues\)?
---

Key Considerations
  * Run all tests as frequently as possible. Ideally, run all test scripts against each build deployed to the test environment. If this is impractical, run regression tests for existing functionality, and focus the test cycle on work items completed in the new build.
  * Even test scripts that are expected to fail provide valuable feedback. However, once a test script is passing, it should not fail against subsequent builds of the solution.
---

More Information

Guidelines|
  * [Maintaining Automated Test Suites](../../../core/common/guidances/guidelines/maintaining-automated-test-suites.md)
  * [Programming Automated Tests](../../../core/common/guidances/guidelines/programming-automated-tests.md)
  * [Test Suite](../../../core/common/guidances/guidelines/test-suite.md)
---|---

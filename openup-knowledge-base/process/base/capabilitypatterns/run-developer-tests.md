---
title: Run Developer Tests
source_url: process.openup.base/capabilitypatterns/run_developer_tests_91CCE06A.html
type: TaskDescriptor
uma_name: run_developer_tests
page_guid: _iRZNQNOKEdyqlogshP8l4g
keywords:
- developer
- tests
related:
  other:
  - developer-7
---


 Run tests against the individual implementation elements to verify that their internal structures work as specified.
---

Purpose

To verify that the implementation works as specified.
---

Relationships

Roles| Primary:
  * [Developer](developer-7.md)

| Additional: | Assisting:
---|---|---|---
Inputs| Mandatory:
  * [\[Technical Implementation\]](./../../process.openup.base/capabilitypatterns/technical_implementation_slot_E32AE6DF.html)
  * [Developer Test](developer-test-10.md)

| Optional:
  * None

| External:
  * None


Outputs|
  * [Test Log](test-log-4.md)



Steps

Run developer tests |  Run the developer tests. The procedure will vary, depending on whether the test is manual or automated and whether additional test components are necessary, such as drivers or stubs.  To run the tests, you need to make sure that you have initialized the test environment with all necessary elements, such as software, hardware, tools, data, and so on.  Automated tests will often update a test results which you can evaluate to determine where your tests went wrong.
---

Evaluate test execution

Evaluate the test execution by analyzing the test run.  Testing will complete either normally or abnormally. For correctly implemented tests, a normal completion represents a passed test, though it could warrant additional examination of the test results log to ensure the test ran as expected. Abnormal termination could be premature termination or just a test that does not complete as intended.  Review the test log to understand any reported failures, warnings, or unexpected results. The cause of the problem\(s\) might be that the implementation element being tested is faulty, a problem with the developer tests, or a problem with the environment.
---

Respond to test results

Determine the appropriate corrective action to recover from a "failed" developer test run. If the implementation element under test is faulty, fix the problem if possible and rerun the tests. If the problem is serious and cannot be immediately addressed, report the defect. If the developer test is faulty fix the test and rerun the tests. If there was a problem with the environment, resolve it and then rerun the tests.
---

Promote changes for integration test

When the developer tests pass and no further work is need to complete the change set, promote the changes for integration test. If the passing of these tests represent completion of a requirement update the status of the work item.
---

Properties

Multiple Occurrences| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Event Driven| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Ongoing| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Planned| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Repeatable| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

Key Considerations

It is common to require that code pass all developer tests before it can be delivered in an integrated source code repository.  Pair with testing experts to gain insight on testing and quality considerations.  The \[Project Work\] is implicitly used in implementation tasks to manage which requirements or change requests are being realized in the code.
---

More Information

Concepts|
  * [Developer Testing](../../../core/common/guidances/concepts/developer-testing.md)
---|---

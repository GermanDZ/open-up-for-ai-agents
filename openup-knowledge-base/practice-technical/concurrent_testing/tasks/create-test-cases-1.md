---
title: Create Test Cases
source_url: practice.tech.concurrent_testing.base/tasks/create_test_cases_D39E98A1.html
type: Task
uma_name: create_test_cases
page_guid: _0iwc0clgEdmt3adZL5Dmdw
keywords:
- cases
- create
- test
related:
  roles:
  - tester-5
  - analyst-6
  - developer-11
  - stakeholder-6
---


 Develop the test cases and test data for the requirements to be tested.
---
Disciplines: [Test](../../../core/cat/disciplines/test-1.md)

Purpose

To achieve a shared understanding of the specific conditions that the solution must meet.
---

Relationships

Roles| Primary Performer:
  * [Tester](../../../core/role/roles/tester-5.md)

| Additional Performers:
  * [Analyst](../../../core/role/roles/analyst-6.md)
  * [Developer](../../../core/role/roles/developer-11.md)
  * [Stakeholder](../../../core/role/roles/stakeholder-6.md)
---|---|---
Inputs| Mandatory:
  * [\[Technical Specification\]](./../../core.tech.slot.base/workproducts/technical_specification_slot_2812F7EF.html)

| Optional:
  * [Test Case](../../../core/common/workproducts/test-case.md)


Outputs|
  * [Test Case](../../../core/common/workproducts/test-case.md)



Steps

Review the requirements to be tested |  Work with analysts and developers to identify which scenarios and requirements need new or additional test cases. Review the Plans to ensure you understand the scope of development for the current iteration.
---

Identify relevant Test Cases

Identify paths through the scenario as unique test conditions. Consider alternative or exception paths from both a positive and negative perspective. Review the test ideas list for patterns of test cases that apply to the scenario.  Discuss the requirement with stakeholders to identify other conditions of satisfaction for the requirement.  List the test cases with a unique name that identifies the condition they evaluate or their expected result.
---

Outline the Test Cases

For each test case, write a brief description with an expected result. Ensure that a casual reader can clearly understand the difference between test cases. Note the logical pre-conditions and post-conditions that apply to each test case. Optionally, outline steps for the test case.  Verify that test cases meet the [Checklist: Test Case](../../../core/common/guidances/checklists/test-case-1.md) guidelines.
---

Identify test data needs

Review each test case and note where data input or output might be required. Identify the type, quantity, and uniqueness of the required data, and add these observations to the test case. Focus on articulating the data needed and not on creating specific data.  For more information on test data selection, see [Checklist: Test Data](../../../core/common/guidances/checklists/test-data.md).
---

Share and evaluate the Test Cases

Walk through the test cases with the analysts and developers responsible for the related scenario. Ideally, the stakeholders will also participate.  Ask the participants to agree that if _these test cases pass_ , they will consider these requirements implemented. Elicit additional test ideas from Analysts and stakeholders to ensure you understand the expected behavior of the scenario.  During the walkthrough, ensure that:
  * The requirements planned for the current iteration have test cases.
  * All the participants agree with the expected results of the test cases.
  * There are no  _other_ conditions of satisfaction for the requirement being tested, which indicates either a missing test case or a missing requirement.

Optionally, capture new patterns of test cases in the test ideas list \(see [Concept: Test Ideas](../../../core/common/guidances/concepts/test-ideas.md)\).
---

Key Considerations

Develop test cases in parallel with requirements so that Analysts and stakeholders can agree with the specific conditions of satisfaction for each requirement. The test cases act as acceptance criteria by expanding on the intent of the system through actual scenarios of use. This allows team members to measure progress in terms of passing test cases.
---

More Information

Guidelines|
  * [Test Ideas](../../../core/common/guidances/guidelines/test-ideas-1.md)
---|---

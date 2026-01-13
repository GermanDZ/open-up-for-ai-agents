---
title: Test Case
source_url: core.tech.common.extend_supp/workproducts/test_case_335C5DEA.html
type: Artifact
uma_name: test_case
page_guid: _0ZS-0MlgEdmt3adZL5Dmdw
keywords:
- case
- test
related:
  roles:
  - tester-5
---


 This artifact is the specification of a set of test inputs, execution conditions, and expected results that you identify to evaluate a particular aspect of a scenario.
---
Domains: [Test](../../cat/domains/test.md)

Purpose

Use this artifact for the following purposes:
  * To provide a way to capture test inputs, conditions, and expected results for a system
  * To systematically identify aspects of the software to test
  * To specify whether an expected result has been reached, based on the verification of a system requirement, set of requirements, or scenario
---

Relationships

Roles| Responsible:
  * [Tester](../../role/roles/tester-5.md)

| Modified By:
  * [Tester](../../role/roles/tester-5.md)
---|---|---
Tasks| Input To:
  * [Implement Tests](../../../practice-technical/concurrent_testing/tasks/implement-tests-1.md)
  * [Create Test Cases](../../../practice-technical/concurrent_testing/tasks/create-test-cases-1.md)

| Output From:
  * [Create Test Cases](../../../practice-technical/concurrent_testing/tasks/create-test-cases-1.md)



Description

Main Description|  A test case specifies the conditions that must be validated to enable an assessment of aspects of the system under test. A test case is more formal than a test idea; typically, a test case takes the form of a specification. In less formal environments, you can create test cases by identifying a unique ID, name, associated test data, and expected results.  Test cases can be derived from many sources, and typically include a subset of the requirements \(such as use cases, performance characteristics, and reliability concerns\) and other types of quality attributes. For more information on types of tests and their relationships to quality test attributes, see [Concept: Testing Qualitative Requirements](../guidances/concepts/testing-qualitative-requirements.md).
---|---

Illustrations

Templates|
  * [Test Case](../guidances/templates/test-case-2.md)
---|---

Tailoring

Impact of not having|  Without this artifact, it is difficult to validate system functionality. Because this artifact specifies the conditions of acceptance between the stakeholders and the developers, without the artifact, it is difficult to establish exit criteria and to demonstrate that the exit criteria have been met. If the original test cases have not been documented, it is impossible to do regression testing.
---|---
Reasons for not needing|  It might not be necessary to create this artifact to maintain or make small enhancements to existing systems, which likely have existing test assets that you can use. You also might not need this artifact if you use a package application that has its own set of test cases.

More Information

Checklists|
  * [Test Case](../guidances/checklists/test-case-1.md)
---|---
Concepts|
  * [Testing Qualitative Requirements](../guidances/concepts/testing-qualitative-requirements.md)

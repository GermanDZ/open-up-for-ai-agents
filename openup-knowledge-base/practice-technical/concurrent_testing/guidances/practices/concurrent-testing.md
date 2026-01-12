---
title: Concurrent Testing
source_url: practice.tech.concurrent_testing.base/guidances/practices/concurrent_testing_AF686531.html
type: Practice
uma_name: concurrent_testing
page_guid: _9z1PgJ6NEdyQN-zRFaRrCQ
keywords:
- concurrent
- testing
related:
  other:
  - how-to-adopt-the-concurrent-testing-practice
  concepts:
  - test-ideas
  - testing-qualitative-requirements
  workproducts:
  - test-case
  - test-log
  - test-script
  tasks:
  - create-test-cases-1
  - implement-tests-1
  - run-tests-1
  guidelines:
  - maintaining-automated-test-suites
  - programming-automated-tests
  - test-ideas-1
  - test-suite
---


 This practice describes how to fold testing into agile development.
---

Relationships

Content References|
  * [How to Adopt the Concurrent Testing practice](../roadmaps/how-to-adopt-the-concurrent-testing-practice.md)
  * [Test Ideas](../../../../core/common/guidances/concepts/test-ideas.md)
  * [Testing Qualitative Requirements](../../../../core/common/guidances/concepts/testing-qualitative-requirements.md)
  * Work Products
    * [Test Case](../../../../core/common/workproducts/test-case.md)
    * [Test Log](../../../../core/common/workproducts/test-log.md)
    * [Test Script](../../../../core/common/workproducts/test-script.md)
  * Tasks
    * [Create Test Cases](../../tasks/create-test-cases-1.md)
    * [Implement Tests](../../tasks/implement-tests-1.md)
    * [Run Tests](../../tasks/run-tests-1.md)
  * Guidance
    * Guidelines
      * [Maintaining Automated Test Suites](../../../../core/common/guidances/guidelines/maintaining-automated-test-suites.md)
      * [Programming Automated Tests](../../../../core/common/guidances/guidelines/programming-automated-tests.md)
      * [Test Ideas](../../../../core/common/guidances/guidelines/test-ideas-1.md)
      * [Test Suite](../../../../core/common/guidances/guidelines/test-suite.md)
---|---
Inputs|
  * [\[Technical Implementation\]](./../../../core.tech.slot.base/workproducts/technical_implementation_slot_E92F6A39.html)
  * [\[Technical Specification\]](./../../../core.tech.slot.base/workproducts/technical_specification_slot_2812F7EF.html)



Purpose

This practice adopts testing throughout an iteration, concurrent with development. This prevents teams from compressing testing into a separate activity at the end of an iteration or release. Concurrent testing reinforces the concept of feature teams working in parallel.
---

Main Description

This practice requires a high degree of integration and high-bandwidth communication between developers and testers. Given these requirements, the following are the main conditions for applying this practice:
  * **Coverage:** Component, feature, and subsystem \(or system\) testing
  * **Team considerations:** Small team with embedded tester or testers
---

How to read this practice

Use a multi-prong approach when you review this practice. You can start by focusing on the work products that will be produced or used during testing and then shift to the tasks involved in processing those artifacts. You might play different roles within your team. If you are a tester, then you will need to get a very good understanding of the artifacts, the tasks, and the guidelines supporting them. For a developer, the main points of interest are the artifacts used within this practice.  Start with the Test artifacts, read their description, and understand when they are used \(produced or used\), by whom, and which roles are mainly responsible:
  * [Test Case](../../../../core/common/workproducts/test-case.md)
  * [Test Script](../../../../core/common/workproducts/test-script.md)
  * [Test Log](../../../../core/common/workproducts/test-log.md)

Switch the focus to tasks and, depending on your main role within the team, review the associated guidelines, concepts and, if applicable, the tool-related guidance:
  * [Create Test Cases](../../tasks/create-test-cases-1.md)
  * [Implement Tests](../../tasks/implement-tests-1.md)
  * [Run Tests](../../tasks/run-tests-1.md)
---

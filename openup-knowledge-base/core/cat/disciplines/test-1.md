---
title: Test
source_url: core.default.cat_def.base/disciplines/test_discipline_F7EB1A7A.html
type: Discipline
uma_name: test_discipline
page_guid: _iGSHtlZ-EdyIUdvDLLUdeg
keywords:
- test
related:
  tasks:
  - create-test-cases-1
  - implement-tests-1
  - run-tests-1
---


 This discipline explains how to provide feedback about the maturing system by designing, implementing, running, and evaluating tests.
---

Relationships

Tasks|
  * [Create Test Cases](../../../practice-technical/concurrent_testing/tasks/create-test-cases-1.md)
  * [Implement Tests](../../../practice-technical/concurrent_testing/tasks/implement-tests-1.md)
  * [Run Tests](../../../practice-technical/concurrent_testing/tasks/run-tests-1.md)
---|---

Main Description

The purpose of this discipline is to:
  * Provide early and frequent _feedback_ about whether the system satisfies the requirements
  * Objectively measure progress in small increments
  * Identify issues with the solution, increasing the probability that the system will behave correctly
  * Provide assurance that changes to the system do not introduce new defects
  * Improve velocity by facilitating the discovery of issues with requirements, designs, and implementations as early as possible

The Test discipline is iterative and incremental. It applies the strategy of "test early and test often" to retire risks as early as possible in the system's lifecycle.  Testing occurs in each iteration of the lifecycle, beginning with the earliest builds of the system. In fact, it is common for one iteration to have many test cycles, depending on the frequency of new builds.  Testing asks the question: "What does the solution have to _do_ for us to consider a requirement implemented?" Tests elaborate on the requirements with specific conditions of satisfaction that the solution must meet.  This discipline challenges the assumptions, risks, and uncertainty inherent in the development of highly technical artifacts and addresses those concerns by using concrete demonstration and impartial evaluation.  The Test discipline relates to the other disciplines in the following ways:
  * The [Requirements](requirements-2.md) discipline identifies the _intent_ of the system. Testing elaborates on the requirements with detailed tests that measure how the system supports the requirements.
  * The [Development](development-1.md) discipline creates incremental builds of the system that the Test discipline evaluates. In each iteration, testing provides objective feedback. Effective testing enables developers to focus on implementing new functionality and improving the design of the system.
  * The [Project Management](project-management-1.md) discipline plans the overall project and the scope of work for each iteration. The Test discipline provides an objective measure of progress, which enables adaptive planning.
---

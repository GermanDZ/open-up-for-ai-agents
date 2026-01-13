---
title: Test Solution
source_url: process.openup.base/capabilitypatterns/test_solution_B552446C.html_desc.html
type: Activity
uma_name: test_solution
page_guid: _f4VuYdOOEdyqlogshP8l4g
keywords:
- solution
- test
related:
  other:
  - elaboration-phase-iteration-4
---


 From a system perspective, test and evaluate the developed requirements.
---
Extends: [Test Solution](test-solution-2.md)

Purpose

Develop and run test scripts to validate that the system satisfies the requirements.
---

Relationships

Parent Activities|
  * [Elaboration Phase Iteration](elaboration-phase-iteration-4.md)
---|---

Description

This activity is repeated throughout the project lifecycle. The main goal of this activity is to validate that the current build of the system satisfies the requirements allocated to it.  Throughout the iterations, your intent is to validate that the implemented requirements reflect a robust architecture, and that the remaining requirements are consistently implemented on top of that architecture. As developers implement the solution for the requirements in a given iteration, unit test the integrated source code. Then, a tester conducts system-level testing in parallel with development to make sure that the solution, which is continuously being integrated, satisfies the intent specified in the test cases. The tester defines what techniques to use, what the data input is, and what test suites to create. As tests run, defects are identified and added to the work items list, so that they can be prioritized as part of the work that you will do during iterations.  stakeholders and end-users also may also be involved in performing tests to accept the release.
---

Properties

Event Driven| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Multiple Occurrences| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Ongoing| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Planned|
Repeatable| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

Staffing

The staff performing this activity must be integrated into the team.
---

---
title: Test Solution
source_url: process.openup.base/capabilitypatterns/test_solution_D16D88FC.html_desc.html
type: CapabilityPattern
uma_name: test_solution
page_guid: _buG4sdOFEdyqlogshP8l4g
keywords:
- solution
- test
---

 From a system perspective, test and evaluate the developed requirements.
---

Purpose

Develop and run test scripts to validate that the system satisfies the requirements.
---

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

Usage

Usage Notes|  Testing must occur throughout the process and throughout each iteration. Testing is not a final inspection to be performed at the end of the project. As requirements are implemented and integrated into a build, you should test them as soon as possible.
---|---

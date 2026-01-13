---
title: Develop Solution Increment
source_url: process.openup.base/capabilitypatterns/develop_solution_8E22EA8F.html_desc.html
type: Activity
uma_name: develop_solution
page_guid: _-iix4dOOEdyqlogshP8l4g
keywords:
- develop
- increment
- solution
related:
  other:
  - transition-phase-iteration-4
---


 Design, implement, test, and integrate the solution for a requirement within a given context.
---
Extends: [Develop Solution Increment](develop-solution-increment-2.md)

Purpose
  * For developers: To create a solution for the work item for which they are responsible
  * For project managers: To have a goal-based way of tracking project status
---

Relationships

Parent Activities|
  * [Transition Phase Iteration](transition-phase-iteration-4.md)
---|---

Description

###  Introduction

Run this activity as a way to perform goal-based planning and execution. Work is taken on by developers, and work progress is tracked based on the goals achieved using the designed, developer-tested, and integrated source code.

####  Context of what is being developed

A context can be specified when a requirement is assigned to be developed, thus specifying how broadly a requirement is to be developed in an iteration. Development may focus on a layer \(such as the user interface, business logic, or database access\), on a component, and so on.  Whether a context is specified or not, the developer's responsibility is to create a design and implementation for that requirement. The developer also writes and runs developer tests against the implementation to make sure that it works as designed, both as a unit and integrated into the code base.

####  Overview of workflow

Typical changes require some effort in designing the solution before moving into implementation, even if it is only a mental exercise that results in no long-term work product. The design for trivial changes to the existing implementation \(to, for example, support some requirement\) might be self-evident in the context of the existing architecture and design.  Once the organization of the technical solution is clear, define developer tests that will verify the implementation. This test-driven approach ensures that design considerations have in fact taken place before the solution is coded. The tests are run up front and, if they fail, clearly define the criteria to determine if the implementation works as intended.  Failed tests lead to an implementation of the solution, upon completion of which you run the tests again. This innermost loop of implementation and developer testing is repeated until the tests pass.  Passing the tests does not necessarily mean that the solution is a high-quality, appropriate solution. It is proper to revisit the design at this point. That path loops back through the process, since any changes to the design could affect the developer tests and implementation.  Once the tests pass and the design of the solution is appropriate, there is one more possible loopback. It is best to keep the test-driven, evolutionary design inner loops as tight as possible. Come up with some small-scale design solution for a part of the work item, define a test or two for the implementation of that one part of the solution, pass that test, verify the quality, and then continue on in a test-first manner until that part of the design is working. Then, in the outermost loop of the activity, go back to the work item and design another chunk to get closer to completion.
---

Properties

Event Driven| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Multiple Occurrences| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Ongoing| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Planned|
Repeatable| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

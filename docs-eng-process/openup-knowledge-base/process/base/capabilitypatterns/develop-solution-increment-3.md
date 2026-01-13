---
title: Develop Solution Increment
source_url: process.openup.base/capabilitypatterns/develop_solution_4FBB0E6E.html_desc.html
type: CapabilityPattern
uma_name: develop_solution
page_guid: _RXGoodOFEdyqlogshP8l4g
keywords:
- develop
- increment
- solution
---

 Design, implement, test, and integrate the solution for a requirement within a given context.
---

Purpose
  * For developers: To create a solution for the work item for which they are responsible
  * For project managers: To have a goal-based way of tracking project status
---

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

Usage

Usage Notes|  This activity occurs multiple times during each iteration. Usually, there is one instance for each work item planned for that iteration. When instantiated in a project plan, the pattern becomes a development task to be taken on by one or more developers, and you should rename it to include the actual requirement name. Optionally, the words **Solution Increment** may be suppressed, then you can instantiate the pattern this way:

> Develop requirement\_name \(within context\_name context\)

If a context is specified, there will be one instance of this pattern for each requirement for each context.

> **Example**
>
>   1. Develop scenario 1 \(within user interface context\)
>   2. Develop scenario 1 \(within business logic and database access context\)
>   3. Develop scenario 2
>   4. Develop supplemental requirement 1
>

Note that there are four instances of this pattern in the preceding example:
  * The first two are related to the same requirement \(scenario 1\) but within two different contexts
  * The last two are related to different requirements, with no context specified.
---|---

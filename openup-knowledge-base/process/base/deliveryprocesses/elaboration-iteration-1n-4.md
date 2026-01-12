---
title: Elaboration Iteration [1..n]
source_url: process.openup.base/deliveryprocesses/elaboration_phase_iteration_579A68CE.html_desc.html
type: Iteration
uma_name: elaboration_phase_iteration
page_guid: _51ewYdOPEdyqlogshP8l4g
keywords:
- elaboration
- iteration
- phase
related:
  other:
  - elaboration-phase
---


 This iteration template defines the activities \(and associated roles and work products\) performed in a typical iteration in the Elaboration phase.
---
Extends: [Elaboration Phase Iteration](../capabilitypatterns/elaboration-phase-iteration-4.md)

Relationships

Parent Activities|
  * [Elaboration Phase](elaboration-phase.md)
---|---

Description

Most activities during a typical iteration in Elaboration phase happen in parallel. Essentially, the main objectives for Elaboration are related to better understanding the requirements, creating and establishing a baseline of the architecture for the system, and mitigating top-priority risks.  The following table summarizes the Elaboration phase objectives and what activities address each objective:  **Elaboration phase objectives and activities** |  **Phase objectives** |  **Activities that address objectives**
---|---
Get a more detailed understanding of the requirements  |  [Identify and Refine Requirements](../capabilitypatterns/identify-and-refine-requirements-1.md)
Design, implement, validate, and baseline an architecture  |  [Develop the Architecture](../capabilitypatterns/develop-the-architecture-2.md) [Develop Solution Increment](../capabilitypatterns/develop-solution-increment-2.md) [Test Solution](../capabilitypatterns/test-solution-2.md)
Mitigate essential risks, and produce accurate schedule and cost estimates  |  [Plan and Manage Iteration](../capabilitypatterns/plan-and-manage-iteration-12.md)


Properties

Event Driven| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Multiple Occurrences| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Ongoing| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Planned|
Repeatable| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

Alternatives

There will be iterations when projects risks are being addressed by creating software, but they may not be architecturally significant. In this case, [Develop Solution Increment](../capabilitypatterns/develop-solution-increment-2.md) will be performed outside the context of the architecture. For the most part, Develop Solution will be performed in the context of [Develop the Architecture](../capabilitypatterns/develop-the-architecture-2.md) during the Elaboration phase.
---

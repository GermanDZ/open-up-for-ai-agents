---
title: Evolutionary Design
source_url: practice.tech.evolutionary_design.base/guidances/practices/evolutionary_design_DE27D8D9.html
type: Practice
uma_name: evolutionary_design
page_guid: _aSVhIB4qEd2bS8fFOQ7WWA
keywords:
- decisions
- design
- evolutionary
related:
  other:
  - how-to-adopt-the-evolutionary-design-practice
  - using-evolutionary-design-in-context
  concepts:
  - design-2
  - design-mechanism
  - implementation-mechanism
  - requirements-realization
  workproducts:
  - design
  tasks:
  - design-the-solution
  guidelines:
  - analyze-the-design
  - evolve-the-design
  - refactoring-1
---


 This practice describes an approach to design that assumes that the design will evolve over time, minimizing documentation while still providing guidance for making design decisions and communicating those decisions.
---

Relationships

Content References|
  * [How to Adopt the Evolutionary Design Practice](../roadmaps/how-to-adopt-the-evolutionary-design-practice.md)
  * Key Concepts
    * [Design](../concepts/design-2.md)
    * [Design Mechanism](../../../../core/common/guidances/concepts/design-mechanism.md)
    * [Implementation Mechanism](../../../../core/common/guidances/concepts/implementation-mechanism.md)
    * [Requirements Realization](../concepts/requirements-realization.md)
  * [Design](../../workproducts/design.md)
  * [Design the Solution](../../tasks/design-the-solution.md)
  * Guidance
    * ![](../../../../images/supportingmaterial.png) [📄](../../../../images/descriptions/supportingmaterial.md "Image description")[Using Evolutionary Design in Context](../supportingmaterials/using-evolutionary-design-in-context.md)
    * Guidelines
      * [Analyze the Design](../guidelines/analyze-the-design.md)
      * [Evolve the Design](../guidelines/evolve-the-design.md)
      * [Refactoring](../../../../core/common/guidances/guidelines/refactoring-1.md)
---|---
Inputs|
  * [\[Technical Architecture\]](./../../../core.tech.slot.base/workproducts/technical_architecture_slot_FF074CDD.html)
  * [\[Technical Specification\]](./../../../core.tech.slot.base/workproducts/technical_specification_slot_2812F7EF.html)



Purpose

The Evolutionary Design practice reduces time-to-market for agile teams by incrementally formulating the design while implementing the software. It improves productivity, innovation, and time-to-market by leveraging refactoring and patterns to improve quality and maximizing reuse opportunities.
---

Background

The application of evolutionary, iterative, and incremental development methods for software dates back to the 1950s. Evolutionary development is an alternative to a waterfall process. In the waterfall process, each past step or phase in the process was considered complete before moving on to the next. The waterfall implies it is not possible to re-enter previous phases to perform rework on any part of the project. The evolutionary design process realizes a solution by enhancing and changing its structure and capabilities incrementally. This practice fits well within the framework of an incremental, iterative or spiral development process, but can be used in any methodology.
---

Main Description

####  The Essence of Evolutionary Design

During each pass of the design, you will add, refine, and refactor your solution. The following steps summarize the evolutionary design practice:
  * Understand new requirement details
  * Identify design elements
  * Determine how elements collaborate to realize the scenario
  * Refine design decisions
  * Design internals
  * Communicate the design
  * Understand the architecture
  * Evaluate the design
---

How to read this practice

####  Become familiar with its overall structure. Be sure that you understand what it is in it and how it is organized.

Review all of the key concepts to understand the terminology used in this practice, including:
  * [Design](../concepts/design-2.md)
  * [Design Mechanism](../../../../core/common/guidances/concepts/design-mechanism.md)
  * [Implementation Mechanism](../../../../core/common/guidances/concepts/implementation-mechanism.md)
  * [Requirements Realization](../concepts/requirements-realization.md)

Read the [Task: Design the Solution](../../tasks/design-the-solution.md) to understand what needs to be done. Finally, review the associated guidelines for more information on the overall workflow.  See [Using Evolutionary Design in Context](../supportingmaterials/using-evolutionary-design-in-context.md) for more information.
---

Additional Information

Meyer, B., _Object-Oriented Software Construction_ , Prentice Hall, 1997

> A primer on OO basics.

Gamma, E., Helm, R., Johnson, R., Vlissides, J., _Design Patterns: Elements of Reusable Object-Oriented Software_ , Addison-Wesley Professional; 1995

> The "bible" on learning what patterns are and how to describe them.

Shalloway, J., Trott, J. _Design Patterns Explained_ A New Perspective on Object-Oriented Design, Second Edition, Addison Wesley, 2005

> This book describes how to evolve a design via design patterns.

Richard E. Fairley, Mary Jane Willshire, "[Iterative Rework: The Good, the Bad, and the Ugly](http://doi.ieeecomputersociety.org/10.1109/MC.2005.303)," Computer, vol. 38, no. 9, pp. 34-41, Sept., 2005.

Martin Fowler, ["Is Design Dead?"](http://martinfowler.com/articles/designDead.html) Retrieved 8 August 2008

Craig Larman, Victor R. Basili, "[Iterative and Incremental Development: A Brief History](http://doi.ieeecomputersociety.org/10.1109/MC.2003.1204375)" Computer, vol. 36, no. 6, pp. 47-56, Jun., 2003\.
---

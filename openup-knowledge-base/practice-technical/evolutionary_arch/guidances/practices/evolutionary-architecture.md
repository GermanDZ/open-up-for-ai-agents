---
title: Evolutionary Architecture
source_url: practice.tech.evolutionary_arch.base/guidances/practices/evolutionary_arch_CF7385B0.html
type: Practice
uma_name: evolutionary_arch
page_guid: _uVnpQB4qEd2bS8fFOQ7WWA
keywords:
- architecture
- decisions
- evolutionary
related:
  other:
  - how-to-adopt-the-evolutionary-architecture-practice
  concepts:
  - architectural-mechanism
  - architectural-views-and-viewpoints
  - software-architecture
  workproducts:
  - architecture-notebook-6
  tasks:
  - envision-the-architecture-1
  - refine-the-architecture-1
  guidelines:
  - abstract-away-complexity
  - modeling-the-architecture
  - software-reuse
---


 Analyze the major technical concerns that affect the solution, and capture those architectural decisions to ensure that those decisions are assessed and communicated.
---

Relationships

Content References|
  * [How to adopt the Evolutionary Architecture practice](../roadmaps/how-to-adopt-the-evolutionary-architecture-practice.md)
  * Key Concepts
    * [Architectural Mechanism](../../../../core/common/guidances/concepts/architectural-mechanism.md)
    * [Architectural Views and Viewpoints](../../../../core/common/guidances/concepts/architectural-views-and-viewpoints.md)
    * [Software Architecture](../../../../core/common/guidances/concepts/software-architecture.md)
  * [Architecture Notebook](../../workproducts/architecture-notebook-6.md)
  * [Envision the Architecture](../../tasks/envision-the-architecture-1.md)
  * [Refine the Architecture](../../tasks/refine-the-architecture-1.md)
  * Guidance
    * Guidelines
      * [Abstract Away Complexity](../../../../core/common/guidances/guidelines/abstract-away-complexity.md)
      * [Modeling the Architecture](../guidelines/modeling-the-architecture.md)
      * [Software Reuse](../../../../core/common/guidances/guidelines/software-reuse.md)
---|---
Inputs|
  * [\[Technical Design\]](./../../../core.tech.slot.base/workproducts/technical_design_slot_84295A08.html)
  * [\[Technical Implementation\]](./../../../core.tech.slot.base/workproducts/technical_implementation_slot_E92F6A39.html)
  * [\[Technical Specification\]](./../../../core.tech.slot.base/workproducts/technical_specification_slot_2812F7EF.html)



Purpose

The Evolutionary Architecture practice describes how to incrementally build and improve the software architecture while uncovering and addressing architectural issues during software development. This reduces technical risk without requiring significant up-front architectural effort. This practice:
  * Improves quality and productivity by reducing the need to make time-consuming, error-prone fixes to late-detected problems that result from architectural flaws. This is possible because the architecture is validated early, and key architectural problems are corrected before the majority of development is done.
  * Reduces time to market by focusing on reuse. It improves the consistency and maintainability of the system by incorporating lessons learned from development back into the architecture and applying those lessons to the rest of development.
  * Improves predictability by identifying and implementing the highest-risk technical areas first. It improves the team's responsiveness to change by shortening the architectural cycle and minimizing time wasted in architectural scrap and rework when changes arise.
---

Main Description

###  The essence of evolutionary architecture

In the Evolutionary Architecture practice, you analyze the major technical concerns that affect the solution and document architectural decisions to ensure that you have assessed and communicated those decisions.

###  The key principles of the Evolutionary Architecture practice are:
  * **Perform architecture work "just in time" for all other work.** When planning your project, identify and discuss architectural issues with your team, and then prioritize architectural work with any other work. Base your priorities on mitigating technical risk rather than creating value. Deferring architectural issues to handle them "just in time" enables the architecture to _evolve over time_.
  * **Document key architectural decisions and outstanding issues**. The [Architecture Notebook](../../workproducts/architecture-notebook-6.md) a list of the architectural issues to make it easy to understand which architectural decisions you've made and which you've not yet addressed.
  * **Implement and test key capabilities as a way to address architectural issues**. Resolving architectural issues typically requires not only architectural brainstorming, but also associated prototyping. In other words: implement enough code to validate the assumptions behind the architecture. The code becomes production code, except for anything thrown away because it proves the architecture invalid.
---

How to read this practice

The best way to read this practice is to first familiarize yourself with its overall structure: what is in it and how it is organized.  Next, review the key concepts for the practice. An especially important concept is [Concept: Software Architecture](../../../../core/common/guidances/concepts/software-architecture.md). After you understand what architecture is, turn your attention to the Architecture Notebook. Then review the tasks, accessing guidelines and tool mentors associated with each task as needed. You can also access the guidance provided by the practice directly through the Guidance folder.  Be sure to take a look at the list of enablement materials for additional sources of information. See the Additional Resources section of this page.  For step-by-step instructions on how to adopt this practice, see [Roadmap: How to adopt the Evolutionary Architecture practice](../roadmaps/how-to-adopt-the-evolutionary-architecture-practice.md).
---

Additional Information

###  Additional resources

See these sources for more information on the evolutionary architecture approach:
  * [Agile Architecture: Strategies for Scaling Agile Development](http://www.agilemodeling.com/essays/agileArchitecture.htm)
  * [Architectural Envisioning](http://www.agilemodeling.com/essays/initialArchitectureModeling.htm)
  * [Agile Enterprise Architecture](http://www.agiledata.org/essays/enterpriseArchitecture.html)
---

---
title: Refine the Architecture
source_url: process.openup.base/capabilitypatterns/refine_the_arch_42A35209.html
type: TaskDescriptor
uma_name: refine_the_arch
page_guid: _6RuKMN_1EdyOsumnGvWsEg
keywords:
- architecture
- refine
related:
  other:
  - architect-2
  - developer-8
  - project-manager-2
---


 Refine the architecture to an appropriate level of detail to support development.
---

Purpose

To make and document the architectural decisions necessary to support development.
---

Relationships

Roles| Primary:
  * [Architect](architect-2.md)

| Additional:
  * [Developer](developer-8.md)
  * [Project Manager](project-manager-2.md)

| Assisting:
---|---|---|---
Inputs| Mandatory:
  * [\[Technical Specification\]](./../../process.openup.base/capabilitypatterns/technical_specification_slot_799A6A77.html)
  * [Architecture Notebook](architecture-notebook-3.md)

| Optional:
  * [\[Technical Design\]](./../../process.openup.base/capabilitypatterns/technical_design_slot_68337E8D.html)
  * [\[Technical Implementation\]](./../../process.openup.base/capabilitypatterns/technical_implementation_slot_72D15E9D.html)

| External:
  * None


Outputs|
  * [Architecture Notebook](architecture-notebook-3.md)



Main Description

This task builds upon the outlined architecture and makes concrete and unambiguous architectural decisions to support development. It takes into account any design and implementation work products that have been developed so far. In other words, the architecture evolves as the solution is designed and implemented, and the architecture documentation is updated to reflect any changes made during development. This is a key, since the actual implementation is the only real "proof" that the software architecture is viable and provides the definitive basis for validating the suitability of the architecture. For more information, see [Concept: Executable Architecture](../../../core/common/guidances/concepts/executable-architecture.md).  The results are captured for future reference and are communicated across the team.
---

Steps

Refine the architectural goals and architecturally-significant requirements |  Work with the team, especially the stakeholders and the requirements team, to review the status of the [Architectural Goals](../../../core/common/guidances/concepts/architectural-goals.md) and [Architecturally Significant Requirements](../../../core/common/guidances/concepts/architecturally-significant-requirements.md) and refine them as needed. It may be that some new architecturally-significant requirements have been introduced or your architectural goals and priorities may have changed.  The development work performed so far will also inform the decisions and goals you've identified. Use information from designing and implementing the system so far to adjust and refined those decisions and goals.
---

Identify architecturally significant design elements

Identify concrete design elements \(such as [Component](../../../core/common/guidances/concepts/component.md)s, classes and subsystems\) and provide at least a name and brief description for each.  The following are some good sources for design elements:
  * [Architecturally Significant Requirements](../../../core/common/guidances/concepts/architecturally-significant-requirements.md). Highlight the areas of the architecture that participate in realizing, or implementing, the requirements.
  * [Key Abstractions](../../../core/common/guidances/concepts/key-abstractions.md)
  * Components that encapsulate the system's interface with external systems. For more information, see [Guideline: Representing Interfaces to External Systems](../../../core/common/guidances/guidelines/representing-interfaces-to-external-systems.md)
  * Components that implement the [Architectural Mechanism](../../../core/common/guidances/concepts/architectural-mechanism.md)s
  * Architectural and key design [Pattern](../../../core/common/guidances/concepts/pattern.md)s. Apply the chosen patterns to define a new set of elements that conform to the patterns.

Identifying components will help hide the complexity of the system and help you work at a higher level. Components need to be internally cohesive and to provide external services through a limited interface. At this point, interfaces do not need to be as detailed as a signature, but they do need to document what the elements need, what they can use, and what they can depend on.  Component identification can be based on architectural layers, deployment choices, or key abstractions. Ask yourself these questions:
  * What is logically or functionally related \(same use case or service, for example\)?
  * What entities provide services to multiple others?
  * What entities depend on each other? Strongly or weakly?
  * What entities should you be able to exchange independently from others?
  * What will run on the same processor or network node?
  * What parts are constrained by similar performance requirements?

When you identify a component be sure to briefly describe the functionality that should be allocated to the components.
---

Refine architectural mechanisms

Refine the applicable [Architectural Mechanism](../../../core/common/guidances/concepts/architectural-mechanism.md)s, as needed to support the design. For example, refining an analysis mechanism into a design mechanism and/or refining a design mechanism into an implementation mechanism.
---

Define development architecture and test architecture

Ensure that the development and test architectures are defined. Note any architecturally significant differences between these environments and work with the team to devise strategies to mitigate any risks these may introduce.
---

Identify additional reuse opportunities

Continue to look for more opportunities to reuse existing assets. Where applicable, identify existing components that could be built to be reused.  For more information, see [Guideline: Software Reuse](../../../core/common/guidances/guidelines/software-reuse.md).
---

Validate the architecture

Make sure that the architecture supports the requirements and the needs of the team.

Development work should be performed to produce just enough working software to show that the architecture is viable. This should provide the definitive basis for validating the suitability of the architecture. As the software should be developed iteratively, more than one increment of the build may be required to prove the architecture. During the early stages of the project it may be acceptable for the software to have a incomplete or prototypical feel, as it will be primarily concerned with baselining the architecture to provide a stable foundation for the remaining development work.
---

Map the software to the hardware

Map the architecturally significant design elements to the target deployment environment. Work with hardware and network specialists to ensure that the hardware is sufficient to meet the needs of the system; and that any new hardware is available in time.
---

Communicate decisions

Ensure that those who need to act upon the architectural work understand it and are able to work with it. Make sure that the description of the architecture clearly conveys not only the solution but also the motivation and objectives related to the decisions that have been made in shaping the architecture. This will make it easier for others to understand the architecture and to adapt it over time.
---

Properties

Multiple Occurrences| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Event Driven| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Ongoing| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Planned|
Repeatable| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

Key Considerations

It is important to continue to reduce the complexity of the solution by raising the levels of abstraction. For more information, see [Guideline: Abstract Away Complexity](../../../core/common/guidances/guidelines/abstract-away-complexity.md).  Continue the collaboration with the whole team on the refining of the architecture in order to promote consensus and a common understanding of the overall solution. The architect should be working to coordinate and guide the technical activities of the team rather than doing all the work alone. Place special emphasis on involving the developer\(s\) throughout this task since it's the developed solution that will prove out the architecture and may result in refinements to the architecture documentation.  Ensure that those who need to act upon the architectural work understand it and are able to work with it. Make sure that the description of the architecture clearly conveys not only the solution but also the motivation and objectives related to the decisions that have been made in shaping the architecture. This will make it easier for others to understand the architecture and to adapt it over time.  You can communicate your decisions as many ways as you wish. For example:
  * Publication of reference source code
  * Publication of reference models
  * Publication of software architecture documentation
  * Formal presentations of the material
  * Informal walkthroughs of the architecture

As you evolve the architecture, you may wish to evolve your architectural models. For more information, see [Guideline: Modeling the Architecture](../../../practice-technical/evolutionary_arch/guidances/guidelines/modeling-the-architecture.md).
---

More Information

Concepts|
  * [Architectural Constraints](../../../core/common/guidances/concepts/architectural-constraints.md)
  * [Architectural Goals](../../../core/common/guidances/concepts/architectural-goals.md)
  * [Architecturally Significant Requirements](../../../core/common/guidances/concepts/architecturally-significant-requirements.md)
  * [Architectural Mechanism](../../../core/common/guidances/concepts/architectural-mechanism.md)
  * [Component](../../../core/common/guidances/concepts/component.md)
  * [Executable Architecture](../../../core/common/guidances/concepts/executable-architecture.md)
  * [Key Abstractions](../../../core/common/guidances/concepts/key-abstractions.md)
---|---
Guidelines|
  * [Abstract Away Complexity](../../../core/common/guidances/guidelines/abstract-away-complexity.md)
  * [Modeling the Architecture](../../../practice-technical/evolutionary_arch/guidances/guidelines/modeling-the-architecture.md)
  * [Representing Interfaces to External Systems](../../../core/common/guidances/guidelines/representing-interfaces-to-external-systems.md)
  * [Software Reuse](../../../core/common/guidances/guidelines/software-reuse.md)

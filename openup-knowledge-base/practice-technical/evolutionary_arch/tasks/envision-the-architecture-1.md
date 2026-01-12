---
title: Envision the Architecture
source_url: practice.tech.evolutionary_arch.base/tasks/envision_the_arch_FF123A81.html
type: Task
uma_name: envision_the_arch
page_guid: _0f-1oMlgEdmt3adZL5Dmdw
keywords:
- architecture
- envision
related:
  roles:
  - architect-6
  - analyst-6
  - developer-11
  - project-manager-4
  - stakeholder-6
---


 This task is where the "vision" for the architecture is developed through analysis of the architecturally significant requirements and identification of architectural constraints, decisions and objectives.
---
Disciplines: [Architecture](../../../core/cat/disciplines/architecture-1.md)

Purpose

To envision a technical approach to the system that supports the project requirements, within the constraints placed on the system and the development team.  To provide sufficient guidance and direction for the team to begin development.
---

Relationships

Roles| Primary Performer:
  * [Architect](../../../core/role/roles/architect-6.md)

| Additional Performers:
  * [Analyst](../../../core/role/roles/analyst-6.md)
  * [Developer](../../../core/role/roles/developer-11.md)
  * [Project Manager](../../../core/role/roles/project-manager-4.md)
  * [Stakeholder](../../../core/role/roles/stakeholder-6.md)
---|---|---
Inputs| Mandatory:
  * [\[Technical Specification\]](./../../core.tech.slot.base/workproducts/technical_specification_slot_2812F7EF.html)

| Optional:
  * [Architecture Notebook](../workproducts/architecture-notebook-6.md)


Outputs|
  * [Architecture Notebook](../workproducts/architecture-notebook-6.md)



Main Description

This task focuses on envisioning the initial architecture and outlining the architectural decisions that will guide development and testing. It relies on gathering experience gained in similar systems or problem domains to constrain and focus the architecture so that effort is not wasted in re-inventing architecture.  The results are captured for future reference and are communicated across the team. It is important that the team has enough information to understand the technical approach being taken.  The architecture evolves organically over time by outlining and refining portions of it. A few people get together in a room and sketch out what they think the architecture will be. This envisioning effort sets the foundation for prototyping. If the solution is similar to a previously produced solution \(or is a well-known solution domain\), then it will probably be good enough to reference that example as evidence of the feasibility of the approach. In some cases, it may be necessary to develop one or more prototypes to validate some of the decisions or clarify some of the requirements.  The work done here does not seek to produce a detailed and comprehensive technical specification for the system. Rather, the approach should be to decide the overall technical approach at a high level. The conclusion of this work should produce just enough information to communicate the architecture to the team, and to demonstrate its viability to the customer. This allows the project to move forward, enabling you to refine and baseline the architecture.
---

Steps

Identify architectural goals |  Work with the team to describe the remaining goals for the architecture and identify which ones are appropriate to address for this iteration. Look at the requirements and speak to the people asking for them to make sure that the critical goals for this iteration are well understood. These goals will prioritize and guide the approach to important technical decisions.
It's important to regularly review the status of these goals throughout the project to make sure that they are still valid and that the system is on track to deliver them.  For more information, see [Concept: Architectural Goals](../../../core/common/guidances/concepts/architectural-goals.md).
---

Identify architecturally significant requirements

Identify which of the current requirements are architecturally significant. Explore and refine those that must be implemented in order to realize the architectural goals for the current iteration. See [Concept: Architecturally Significant Requirements](../../../core/common/guidances/concepts/architecturally-significant-requirements.md) for more information.
---

Identify constraints on the architecture

List any constraints on the architecture and any trade-offs between competing requirements and resources. Decide how the architecture will meet these issues. Justify each of the decisions made and capture this information. Regularly review the list of constraints to make sure that they are still valid and that no new ones have appeared.
For more information, see [Concept: Architectural Constraints](../../../core/common/guidances/concepts/architectural-constraints.md).
---

Identify key abstractions

Identify the key concepts and abstractions that the system needs to handle. The requirements are good sources for key abstractions. Don't spend too much time describing abstractions in detail at this initial stage, because there is a risk that spending too much time will result in identifying classes and relationships that the solution does not actually need.  When identifying key abstractions, it can be useful to also define any obvious relationships that exist between them. These can be captured in a table or in diagrams \(in a tool or whiteboard. In general, it is not worth agonizing over defining a highly detailed set of relationships at this early stage in design. The relationships will become more concrete and detailed later and will probably modify these early assumptions.  For more information, see [Concept: Key Abstractions](../../../core/common/guidances/concepts/key-abstractions.md).
---

Identify reuse opportunities

Survey, assess, and select available assets. Identify assets from other areas that may be reused in the current architecture. For more information, see [Guideline: Software Reuse](../../../core/common/guidances/guidelines/software-reuse.md).
---

Define approach for partitioning the system

Decide how to partition the software, both in logical and physical terms. Partitioning your system helps you manage its complexity by using the well-known "divide and conquer" strategy. By breaking the process into smaller and more manageable pieces, you make development easier.  As a minimum, decide on:
  * How to partition the software when managing development \(the use of layering as a partitioning strategy, for example\). For more information, see [Guideline: Layering](../../../core/common/guidances/guidelines/layering.md).
  * How the software will be composed at run time.

For each software partition, briefly describe
  * Its name and purpose.
  * Its relationships to other partitions.

At this point, you do not need to identify the elements that should be placed in each of these partitions. Instead, you define how many partitions you will need and how they should be related. Later, during design activities, you decide which elements will populate these partitions.
---

Define approach for deploying the system

Outline how the software will deploy over the nodes on the network. Work with stakeholders such as network support and deployment teams to ensure that the proposed approach is a good fit for the wider technical environment.
---

Identify architectural mechanisms

Make a list of the technical services that the system needs to provide and capture some basic information about each item on the list. It's generally a good idea to make an initial list of all the mechanisms required for the project and then prioritize the development of those that need to be delivered to achieve the architectural goals.  At this point, usually only the analysis mechanisms are defined. However, specific [Architectural Constraints](../../../core/common/guidances/concepts/architectural-constraints.md) may mean that some of those mechanisms can be described as design mechanisms \(even at this early stage\).  For more information on architectural mechanisms, see [Concept: Architectural Mechanism](../../../core/common/guidances/concepts/architectural-mechanism.md).
---

Identify interfaces to external systems

At this point, identify the external systems with which this system must interact. An external system may be anything from software to hardware units that the current system will use, such as printers, terminals, alarm devices, and sensors.  Describe those interfaces at a high level, concentrating on the information that must pass between the systems.
---

Verify architectural consistency

Work with the team to verify that the architecture is consistent with the requirements and that the descriptions of the architecture are complete, meaningful, and clear.
---

Capture and communicate architectural decisions

Capture important decisions about the architecture in the [Architecture Notebook](../workproducts/architecture-notebook-6.md) for future reference. Make sure that the team understands the architecture and can deliver it.
---

Key Considerations

It is important to reduce the complexity of the solution by raising the levels of abstraction. For more information, see [Guideline: Abstract Away Complexity](../../../core/common/guidances/guidelines/abstract-away-complexity.md).  It is critical that this task be performed collaboratively with active involvement of other team members and project stakeholders so that consensus and common understanding is reached. It is particularly vital to involve the developer\(s\) throughout this task. The architecture effort is about providing leadership and coordination of the technical work rather than putting in a solo performance.  At this stage, you may find it useful to develop a draft version of your architectural models. For more information, see [Guideline: Modeling the Architecture](../guidances/guidelines/modeling-the-architecture.md).
---

Alternatives

This task is most needed when developing new and unprecedented systems. In systems where there is already a well-defined architecture, this task may be omitted and replaced with a review of the existing architecture.
---

More Information

Concepts|
  * [Architectural Constraints](../../../core/common/guidances/concepts/architectural-constraints.md)
  * [Architectural Goals](../../../core/common/guidances/concepts/architectural-goals.md)
  * [Architecturally Significant Requirements](../../../core/common/guidances/concepts/architecturally-significant-requirements.md)
  * [Architectural Mechanism](../../../core/common/guidances/concepts/architectural-mechanism.md)
  * [Key Abstractions](../../../core/common/guidances/concepts/key-abstractions.md)
---|---
Guidelines|
  * [Abstract Away Complexity](../../../core/common/guidances/guidelines/abstract-away-complexity.md)
  * [Layering](../../../core/common/guidances/guidelines/layering.md)
  * [Modeling the Architecture](../guidances/guidelines/modeling-the-architecture.md)
  * [Software Reuse](../../../core/common/guidances/guidelines/software-reuse.md)

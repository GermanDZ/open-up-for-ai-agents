---
title: Design the Solution
source_url: practice.tech.evolutionary_design.base/tasks/design_solution_A97CE9EA.html
type: Task
uma_name: design_solution
page_guid: _0fshwMlgEdmt3adZL5Dmdw
keywords:
- design
- solution
related:
  roles:
  - developer-11
  - analyst-6
  - architect-6
  - stakeholder-6
  - tester-5
---


 Identify the elements and devise the interactions, behavior, relations, and data necessary to realize some functionality.Render the design visually to aid in solving the problem and communicating the solution.
---
Disciplines: [Development](../../../core/cat/disciplines/development-1.md)

Purpose

The purpose of this task is to describe the elements of the system so that they support the required behavior, are of high quality, and fit within the architecture.
---

Relationships

Roles| Primary Performer:
  * [Developer](../../../core/role/roles/developer-11.md)

| Additional Performers:
  * [Analyst](../../../core/role/roles/analyst-6.md)
  * [Architect](../../../core/role/roles/architect-6.md)
  * [Stakeholder](../../../core/role/roles/stakeholder-6.md)
  * [Tester](../../../core/role/roles/tester-5.md)
---|---|---
Inputs| Mandatory:
  * [\[Technical Architecture\]](./../../core.tech.slot.base/workproducts/technical_architecture_slot_FF074CDD.html)
  * [\[Technical Specification\]](./../../core.tech.slot.base/workproducts/technical_specification_slot_2812F7EF.html)

| Optional:
  * [Design](../workproducts/design.md)


Outputs|
  * [Design](../workproducts/design.md)



Main Description

This task is about designing part of the system, not the whole system. It should be applied based upon some small subset of requirements. The requirements driving the design could be scenario-based functional requirements, non-functional requirements, or a combination.  This task can be applied in some specific context such as the database access elements required for some scenario. In this case the task might be applied again later to deal with a different context on the same requirements. Keep in mind that to actually build some functionality of value to the users, all contexts will typically need to be designed and implemented. For example, to actually utilize some system capability it will have to have been designed and implemented all its context such as user interface, business rules, database access, etc.  For cohesion and completeness, this task is described as an end-to-end pass of designing a scenario of system usage. In practice, this task will be revisited many times as the design is first considered, portions are implemented, more design is performed based on what was learned, etc. The healthiest application of this task is in very close proximity to the implementation.  If this task is being performed on an architecturally significant element the results of this design should be referenced by the [\[Technical Architecture\]](./../../core.tech.slot.base/workproducts/technical_architecture_slot_FF074CDD.html).
---

Steps

Understand requirement details |  Examine the relevant [\[Technical Specification\]](./../../core.tech.slot.base/workproducts/technical_specification_slot_2812F7EF.html) to understand the scope of the design task and the expectations on the [Design](../workproducts/design.md). Work with the stakeholder and Analyst to clarify ambiguous or missing information.  If the requirements are not represented in some sort of scenario form \(for example a non-functional requirement might not have a scenario associated with it\), a scenario will have to be identified that appropriately exercises the requirements under consideration.  If the requirements are determined to be incomplete or incorrect, work with the analyst to get the requirements improved and possibly submit a change request against the requirements.
---

Identify design elements

Identify the elements that collaborate together to provide the required behavior. This can start with the key abstractions identified in the Architecture Notebook, design, domain analysis, and classical analysis of the requirements \(noun filtering\) to derive the elements that would be required to fulfill them. The [Entity-Control-Boundary Pattern](../../../core/common/guidances/guidelines/entity-control-boundary-pattern.md) provides a good start for identifying elements. Also see [Guideline: Analyze the Design](../guidances/guidelines/analyze-the-design.md).  Existing elements of the design should be examined to see if they should participate in the collaboration. It is a mistake to create all new elements in each execution of this task.
---

Determine how elements collaborate to realize the scenario

Walk through the scenario distributing responsibilities to the participating elements and ensuring that the elements have the relationships required to collaborate.  These responsibilities can be simple statements of behavior assigned to elements; they need not be detailed operation specifications with parameters, etc. Similarly, the relationships can just be defined at this step. This step is about ensuring that a quality model is being created that is robust enough to support the requirements. See [Guideline: Analyze the Design](../guidances/guidelines/analyze-the-design.md).  Look to the architecture and previous design work to create a consistent collaboration. Work with the architect to understand the details and motivations of the architecture. Look to reuse existing behavior and relations or to apply similar structure to simplify the design of the overall system. For more information, see [Guideline: Software Reuse](../../../core/common/guidances/guidelines/software-reuse.md).
---

Refine design decisions

Refine the design to an appropriate level of detail to drive implementation and to ensure that it fits into the architecture. In this step the design can take into consideration the actual implementation language and other technical decisions. Revisit the identification of the elements and the collaborations that realize the scenarios if necessary as this refinement takes into consideration details at a lower level of abstraction. Discuss testability issues, such as design elements that are difficult to test or critical performance areas, with the tester and architect.  Evolve the design by examining recent changes in the larger context of the design and determine if refactoring and redesigning techniques will improve the robustness, flexibility, and understandability of the design. See [Guideline: Evolve the Design](../guidances/guidelines/evolve-the-design.md) for guidance specific design decisions and on making design improvements just when they're needed.  Incorporate [Architectural Mechanism](../../../core/common/guidances/concepts/architectural-mechanism.md)s from the architecture. Apply consistent structure of the elements and organization of the behavior as in other areas of the design and use patterns identified in the architecture.
---

Design internals \(for large or complex elements\)

Design large or complex elements or some complex internal behavior in more detail.  This might just involve devising an algorithm that could be performed to produce the desired behavior. Add additional operations, attributes, and relationships to support the expectations of an element.  Design the state of the element over the course of its lifetime to ensure its proper behavior in various circumstances. It may be useful to describe a state machine for elements with complex states.
---

Communicate the design

Communicate the system's design to those who need to understand it. Though this is described here toward the end of the task, communication should be going on throughout the steps. Working collaboratively is always better than reviewing the work after it is complete.  Here are some ways to communicate the design:
  * Formal models specified in UML.
  * Informal diagrams that render static structure and capture dynamic behavior.
  * Annotated code that communicates information about the static structure. This can be supplemented with textual descriptions of collaborative behavior across code modules.
  * Data models to describe the database schema.

Here are some examples of individuals who will need to understand the design of the system:
  * Developers who will implement a solution based on the design.
  * Architects who can review the design to ensure that it conforms to the architecture or who might examine the design for opportunities to improve the architecture.
  * Other designers who can examine the design for applicability to other parts of the system.
  * Developers or other designers who will be working on other parts of the system that will depend on the elements designed in this task.
  * Other reviewers who will review the design for quality and adherence to standards.
---

Understand the architecture

Review the Architecture Notebook to identify changes and additions to the architecture. See [Guideline: Evolve the Design](../guidances/guidelines/evolve-the-design.md) for more information. Work with the architect if there is any uncertainty on the understanding of relevant parts of the architecture or of the conformance of the design strategy.  This step can be skipped if there were no changes to the architecture in the previous iteration
---

Evaluate the design

Evaluate the object design for coupling, cohesion, and other quality design measurements.  Consider the design from various angles to ensure that it is a high-quality, communicable design. Work with other technical team members; an independent party can provide a fresh perspective. Use the tester and architect to provide perspectives on design quality and adherence to the architecture. However, when identifying potential reviewers keep in mind that if someone can add value by reviewing the design, then perhaps they could have added even more value by actively participating in the design effort itself. If design flaws are identified, improve the design.  See [Concept: Design](../guidances/concepts/design-2.md), [Guideline: Analyze the Design](../guidances/guidelines/analyze-the-design.md), and [Guideline: Evolve the Design](../guidances/guidelines/evolve-the-design.md) for more information.
---

Key Considerations

Each step in this task can cause all previous steps to be revisited in light of new information and decisions. For example, while determining how elements collaborate you might find a gap in the requirements that causes you to go back to the beginning after collaborating with the analyst, or when evaluating the design a reviewer could note that a reusable element being used doesn't work as expected and that could cause you to identify new elements to take its place.  Consider the architecture while performing this task. All design work must be done while regarding the architecture within which the design exists. Furthermore, certain design elements will be deemed architecturally significant; those elements will require updates to the architecture.  This task will be applied numerous times. Design is best performed in small chunks.  Even when starting the design for a particular project it is expected that there will be existing frameworks and reusable elements. Every step of this task must give attention to the existing design and existing implementation, utilizing existing elements when possible and emulating or improving existing elements as appropriate while designing this portion of the solution.  Apply patterns throughout this task. Patterns represent proven designs and their usage promotes quality and consistency across the design.
---

More Information

Concepts|
  * [Architectural Mechanism](../../../core/common/guidances/concepts/architectural-mechanism.md)
  * [Design](../guidances/concepts/design-2.md)
  * [Design Mechanism](../../../core/common/guidances/concepts/design-mechanism.md)
  * [Implementation Mechanism](../../../core/common/guidances/concepts/implementation-mechanism.md)
  * [Pattern](../../../core/common/guidances/concepts/pattern.md)
  * [Requirements Realization](../guidances/concepts/requirements-realization.md)
---|---
Guidelines|
  * [\[Design Guidance\]](./../../core.tech.slot.base/guidances/guidelines/design_guidance_slot_AB88B43E.html)
  * [Analyze the Design](../guidances/guidelines/analyze-the-design.md)
  * [Designing Visually](../guidances/guidelines/designing-visually.md)
  * [Entity-Control-Boundary Pattern](../../../core/common/guidances/guidelines/entity-control-boundary-pattern.md)
  * [Evolve the Design](../guidances/guidelines/evolve-the-design.md)
  * [Software Reuse](../../../core/common/guidances/guidelines/software-reuse.md)

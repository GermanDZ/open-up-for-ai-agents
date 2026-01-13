---
title: Architecture Notebook
source_url: practice.tech.evolutionary_arch.base/guidances/checklists/architecture_notebook_BC815A4B.html
type: Checklist
uma_name: architecture_notebook
page_guid: _17PYUNd6EdmIm-bsRSNCgw
keywords:
- architecture
- notebook
related:
  workproducts:
  - architecture-notebook-6
---



---

Relationships

Related Elements|
  * [Architecture Notebook](../../workproducts/architecture-notebook-6.md)
---|---

Check Items

Is the architecture understandable? |
  * Is the description of the architecture complete, meaningful, and clear?
  * Is the architecture at an appropriate level of detail, given the objectives?
  * Are concepts handled in the simplest way possible?
  * Does the architecture clearly convey not only the solution but also the motivation and objectives related to the decisions that have been made in shaping the architecture?
  * Are the key assumptions and decisions that the architecture is based on documented and visible to reviewers and those who will use the architecture?
  * Is the architecture description current?
  * Have the design guidelines been followed?
---

Have the architectural goals, constraints and requirements been adequately described and handled?
  * Have the [Architectural Goals](../../../../core/common/guidances/concepts/architectural-goals.md) been clearly described?
  * Have any [Architectural Constraints](../../../../core/common/guidances/concepts/architectural-constraints.md) been identified and documented?
  * Have the [Architecturally Significant Requirements](../../../../core/common/guidances/concepts/architecturally-significant-requirements.md) been identified and are they clearly described.
  * Is the architecture is consistent with the architectural goals, constraints and requirements?
---

Have necessary architectural mechanisms been identified and described?
  * Is it clear when each [Architectural Mechanism](../../../../core/common/guidances/concepts/architectural-mechanism.md) should be applied?
  * Is there a clearly defined design pattern in place to support each mechanism?
  * Does each mechanism adequately address the requirements it is intended to meet?
---

Have the system partitions been adequately defined?
  * Is partitioning approach clearly described and applied consistently?
  * Does the partitioning approach reduce complexity and improve understanding?
  * Have the partitions been defined to be highly cohesive within the partition, while the partitions themselves are loosely coupled?
---

Have the key elements been adequately defined?
  * Have the [Key Abstractions](../../../../core/common/guidances/concepts/key-abstractions.md) adequately defined?
  * Have the the key design elements \(i.e., [Component](../../../../core/common/guidances/concepts/component.md)s\) adequately defined?
  *     * Do the components have well-defined interfaces?
    * Have the system's responsibilities been allocated to the components?
    * Are the number and types of components reasonable?
---

Have interfaces to external systems been adequately represented?

See [Guideline: Representing Interfaces to External Systems](../../../../core/common/guidances/guidelines/representing-interfaces-to-external-systems.md)
---

Has all reuse been identified?

Have all reusable assets been identified -- either those reused by the system, or those elements within the system that have been built to be reused. For more information, see [Guideline: Software Reuse](../../../../core/common/guidances/guidelines/software-reuse.md).
---

Has the architecture been built to evolve?
  * Can the architecture easily evolve, so that expected changes can be easily accommodated?
  * Are all technical risks either mitigated or addressed in a contingency plan?
  * Has the architecture been overly structured to handle unlikely change at the expense of simplicity and comprehensibility? \(Hint: "Yes" to this question is not good.\)
---

Can the architecture be delivered by the team?
  * Does the architecture provide a suitable basis for organizing the development teams?
  * Does each team have the skills required to implement their allocated components?
  * Are responsibilities divided well between teams?
  * Do all team members share the same understanding of the architecture as the one presented by the architect?
  * Can team members understand enough from the architecture to successfully design and code their allocated components?
---

Has the software been adequately mapped to the hardware?
  * Have the deployable software components been mapped to physical nodes?
---

More Information

Concepts|
  * [Architectural Constraints](../../../../core/common/guidances/concepts/architectural-constraints.md)
  * [Architectural Goals](../../../../core/common/guidances/concepts/architectural-goals.md)
  * [Architecturally Significant Requirements](../../../../core/common/guidances/concepts/architecturally-significant-requirements.md)
  * [Architectural Mechanism](../../../../core/common/guidances/concepts/architectural-mechanism.md)
  * [Component](../../../../core/common/guidances/concepts/component.md)
  * [Key Abstractions](../../../../core/common/guidances/concepts/key-abstractions.md)
---|---
Guidelines|
  * [Representing Interfaces to External Systems](../../../../core/common/guidances/guidelines/representing-interfaces-to-external-systems.md)
  * [Software Reuse](../../../../core/common/guidances/guidelines/software-reuse.md)

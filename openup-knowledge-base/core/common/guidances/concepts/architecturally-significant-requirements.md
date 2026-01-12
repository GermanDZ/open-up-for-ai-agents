---
title: Architecturally Significant Requirements
source_url: core.tech.common.extend_supp/guidances/concepts/arch_significant_requirements_1EE5D757.html
type: Concept
uma_name: arch_significant_requirements
page_guid: _HrZGIA4MEduibvKwrGxWxA
keywords:
- architecturally
- requirements
- significant
related:
  other:
  - architectural-mechanism
  - executable-architecture
  - software-architecture
  checklists:
  - architecture-notebook-7
  guidelines:
  - effective-requirement-reviews
  tasks:
  - envision-the-architecture-1
  - refine-the-architecture-1
---


 This concept describes what architecturally significant requirements are and why they are important.
---

Relationships

Related Elements|
  * [Architectural Mechanism](architectural-mechanism.md)
  * [Architecture Notebook](../../../../practice-technical/evolutionary_arch/guidances/checklists/architecture-notebook-7.md)
  * [Effective Requirement Reviews](../guidelines/effective-requirement-reviews.md)
  * [Envision the Architecture](../../../../practice-technical/evolutionary_arch/tasks/envision-the-architecture-1.md)
  * [Executable Architecture](executable-architecture.md)
  * [Refine the Architecture](../../../../practice-technical/evolutionary_arch/tasks/refine-the-architecture-1.md)
  * [Software Architecture](software-architecture.md)
---|---

Main Description

Architecturally significant requirements are those requirements that play an important role in determining the architecture of the system. Such requirements require special attention. Not all requirements have equal significance with regards to the architecture.  Architecturally significant requirements are a subset of the requirements that need to be satisfied before the architecture can be considered "stable". Typically, these are requirements that are technically challenging, technically constraining, or central to the system's purpose. Furthermore, the system will generally be more sensitive to changes against architecturally significant requirements, so identifying and communicating this subset will help others understand the potential implications of change.  Requirements can be explicitly or implicitly architecturally significant. Explicitly significant requirements are often overtly technical in nature, such as performance targets; the need to interface to other systems; the number of users that must be supported; or security requirements. Implicitly significant requirements may define the essence of the functional behaviour of the system \(for example, making a purchase from an on-line store\).  Deciding whether a specific requirement is architecturally significant is often a matter of judgment. The selection of requirements that are considered "architecturally significant" is driven by several key driving factors:
  * The benefit of the requirement to stakeholders: critical, **important** , or **useful**.
  * The architectural impact of the requirement: **none** , **extends** , or **modifies**. There may be critical requirements that have little or no impact on the architecture and low-benefit requirements that have a big impact. Low-benefit requirements with big architectural impacts should be reviewed by the project manager for possible removal from the scope of the project.
  * The risks to be mitigated: performance, availability of a product, and suitability of a component.
  * The completion of the coverage of the architecture.
  * Other tactical objectives or constraints, such as demonstration to the user, and so on.

There may be two requirements that hit the same components and address similar risks. If you implement A first, then B is not architecturally significant. If you implement B first, then A is not architecturally significant. Thus these attributes can depend on the order the requirements are realized, and should be re-evaluated when the order changes, as well as when the requirements themselves change.  The following are good examples of Architecturally Significant Requirements:
  * The system must record every modification to customer records for audit purposes.
  * The system must respond within 5 seconds.
  * The system must deploy on Microsoft Windows XP and Linux.
  * The system must encrypt all network traffic.
  * The ATM system must dispense cash on demand to validated account holders with sufficient cleared funds.

Architecturally significant requirements also describe key behaviors that the system needs to perform. Such scenarios represent the important interactions between key abstractions.and should be identified as architecturally significant requirements. For example, for an on-line book store describing the way the software handles the scenarios for ordering a book and checking out the shopping cart are often enough to communicate the essence of the architecture.
---

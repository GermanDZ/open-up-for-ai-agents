---
title: Architecture Notebook
source_url: practice.tech.evolutionary_arch.base/workproducts/architecture_notebook_9BB92433.html
type: Artifact
uma_name: architecture_notebook
page_guid: _0XAf0MlgEdmt3adZL5Dmdw
keywords:
- architecture
- notebook
---

 This artifact describes the rationale, assumptions, explanation, and implications of the decisions that were made in forming the architecture.
---
Domains: [Architecture](../../../core/cat/domains/architecture.md)

Purpose

To capture and make architectural decisions and to explain those decisions to developers.
---

Relationships

Fulfilled Slots|
  * [\[Technical Architecture\]](./../../core.tech.slot.base/workproducts/technical_architecture_slot_FF074CDD.html)
---|---
Roles| Responsible:
  * [Architect](../../../core/role/roles/architect-6.md)

| Modified By:
  * [Architect](../../../core/role/roles/architect-6.md)


Tasks| Input To:
  * [Refine the Architecture](../tasks/refine-the-architecture-1.md)
  * [Envision the Architecture](../tasks/envision-the-architecture-1.md)
  * [Design the Solution](../../evolutionary_design/tasks/design-the-solution.md)
  * [Plan Iteration](../../../practice-management/iterative_dev/tasks/plan-iteration-1.md)

| Output From:
  * [Envision the Architecture](../tasks/envision-the-architecture-1.md)
  * [Refine the Architecture](../tasks/refine-the-architecture-1.md)



Description

Main Description|  This artifact describes the [Software Architecture](../../../core/common/guidances/concepts/software-architecture.md).  It provides a place for maintaining the list of architectural issues, along with the associated architectural decisions, designs, patterns, code documented \(or pointed to\), and so forth -- all at appropriate levels to make it easy to understand what architectural decisions have been made and remain to be made.  It is helpful for architects to use this artifact to collaborate with other team members in developing the architecture and to help team members understand the motivation behind architectural decisions so that those decisions can be robustly implemented. For example, the architect may put constraints on how data is packaged and communicated between different parts of the system. This may appear to be a burden, but the justification in the Architecture Notebook can explain that there is a significant performance bottleneck when communicating with a legacy system. The rest of the system must adapt to this bottleneck by following a specific data packaging scheme.  This artifact should also inform the team members how the system is partitioned or organized so that the team can adapt to the needs of the system. It also gives a first glimpse of the system and its technical motivations to whoever must maintain and change the architecture later.
---|---
Brief Outline|  At a minimum, this artifact should do these three things:
  * List guidelines, decisions, and constraints to be followed
  * Justify those guidelines, decisions, and constraints
  * Describe the Architectural Mechanisms and where they should be applied

Team members who were not involved in those architectural decisions need to understand the reasoning behind the context of the architecture so that they can address the needs of the system. Consider adding more information when appropriate. A small project shouldn't spend a lot of time documenting the architecture, but all critical elements of the system must be communicated to current and future team members. This is all useful content:
  * Goals and philosophy of the architecture
  * Architectural assumptions and dependencies
  * References to architecturally significant requirements
  * References to architecturally significant design elements
  * Critical system interfaces
  * Packaging instructions for subsystems and components
  * Layers and critical subsystems
  * Key abstractions
  * Key scenarios that describe critical behavior of the system



Illustrations

Templates|
  * [Architecture Notebook](../guidances/templates/architecture-notebook-8.md)
---|---

Tailoring

Impact of not having| Without this artifact, there will be no coordination of the individual design efforts, and it will be difficult to establish and communicate an overall architectural vision of the project.
---|---
Reasons for not needing|  This artifact is not required if an existing reference architecture is being used or another approach or set of artifacts are being used to document the architecture. This artifact may not be needed if the design is relatively straight-forward and does not have any architecturally significant risks.
Representation Options| A set of architectural models can be developed as part of the architectural documentation. For more information, see [Guideline: Modeling the Architecture](../guidances/guidelines/modeling-the-architecture.md).

More Information

Checklists|
  * [Architecture Notebook](../guidances/checklists/architecture-notebook-7.md)
---|---
Concepts|
  * [Software Architecture](../../../core/common/guidances/concepts/software-architecture.md)


Guidelines|
  * [Modeling the Architecture](../guidances/guidelines/modeling-the-architecture.md)

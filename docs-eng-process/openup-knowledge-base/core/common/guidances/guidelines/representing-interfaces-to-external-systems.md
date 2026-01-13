---
title: Representing Interfaces to External Systems
source_url: core.tech.common.extend_supp/guidances/guidelines/repres_interfaces_to_ext_systems_51A34F6E.html
type: Guideline
uma_name: repres_interfaces_to_ext_systems
page_guid: _0gjdYMlgEdmt3adZL5Dmdw
keywords:
- external
- interfaces
- representing
- systems
related:
  checklists:
  - architecture-notebook-7
  tasks:
  - refine-the-architecture-1
  concepts:
  - software-architecture
---


 This guideline introduces system level interfaces.
---

Relationships

Related Elements|
  * [Architecture Notebook](../../../../practice-technical/evolutionary_arch/guidances/checklists/architecture-notebook-7.md)
  * [Refine the Architecture](../../../../practice-technical/evolutionary_arch/tasks/refine-the-architecture-1.md)
  * [Software Architecture](../concepts/software-architecture.md)
---|---

Main Description

Interfaces with external systems should be consistently handled throughout the system. The architecture need not include a specific, detailed design for each system interface. It is often enough to simply identify the existence of the interface as a significant part of the architecture and create a [Component](../concepts/component.md) to encapsulate the detail, so that it can be developed later.  The [Entity-Control-Boundary Pattern](entity-control-boundary-pattern.md) provides the basis for a useful technique to support this. Specifically, if the system communicates with another system, define one or more components to describe the communication protocol. The use of a component allows the interface to the external system to be defined and stabilized, while leaving the design details of the system interface hidden as the system evolves.
---

More Information

Concepts|
  * [Component](../concepts/component.md)
---|---
Guidelines|
  * [Entity-Control-Boundary Pattern](entity-control-boundary-pattern.md)

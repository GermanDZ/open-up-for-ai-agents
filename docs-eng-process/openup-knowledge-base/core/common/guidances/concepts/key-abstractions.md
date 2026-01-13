---
title: Key Abstractions
source_url: core.tech.common.extend_supp/guidances/concepts/key_abstractions_1474DBF2.html
type: Concept
uma_name: key_abstractions
page_guid: _pLEGUNqGEdy88NBoQgfGyg
keywords:
- abstractions
related:
  checklists:
  - architecture-notebook-7
  tasks:
  - envision-the-architecture-1
  - refine-the-architecture-1
  other:
  - software-architecture
---


 This concept describes key abstractions and the role they play in the architecture
---

Relationships

Related Elements|
  * [Architecture Notebook](../../../../practice-technical/evolutionary_arch/guidances/checklists/architecture-notebook-7.md)
  * [Envision the Architecture](../../../../practice-technical/evolutionary_arch/tasks/envision-the-architecture-1.md)
  * [Refine the Architecture](../../../../practice-technical/evolutionary_arch/tasks/refine-the-architecture-1.md)
  * [Software Architecture](software-architecture.md)
---|---

Main Description

Key abstractions are the key concepts and abstractions that the system needs to handle. They are those things that, without which, you could not describe the system.  The requirements are good sources for key abstractions. These abstractions are often easily identified because they represent things that are significant to the business. For example, Customer and Account are typical key abstractions in the banking business.  Each key abstraction should have a short description. The are usually not described in detail as they will change and evolve during the course of the project \(as they are refined into actual design elements\).  The value of defining the key abstractions \(and any obvious relationships between them\) is that they establish a common understanding of the key concepts amongst the team, thereby enabling them to develop a coherent solution that handles them consistently.
---

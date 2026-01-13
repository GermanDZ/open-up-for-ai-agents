---
title: Executable Architecture
source_url: core.tech.common.extend_supp/guidances/concepts/executable_arch_D4E68CBD.html
type: Concept
uma_name: executable_arch
page_guid: _O1kAANvfEduv2KOT-Teh6w
keywords:
- architecture
- executable
related:
  tasks:
  - refine-the-architecture-1
  other:
  - software-architecture
---


 An executable architecture is an implementation that realizes a set of validated architecturally significant requirements.
---

Relationships

Related Elements|
  * [Refine the Architecture](../../../../practice-technical/evolutionary_arch/tasks/refine-the-architecture-1.md)
  * [Software Architecture](software-architecture.md)
---|---

Main Description

An executable architecture is an implementation that realizes the [Software Architecture](software-architecture.md). It is used to validate that the [Architecturally Significant Requirements](architecturally-significant-requirements.md) are correctly implemented. It validates the architecture as an integrated whole through integration tests. The team gains feedback about the architecture from the customer or stakeholder by providing the executable architecture for verification. This way the executable architecture helps to assure that the core functionality is stable enough to build the remainder of the system.  An executable architecture is not a work product. It's an identification or attribute of the implementation, indicating that the implementation contains stable architecturally significant functionality.  Each version of an executable architecture should be more complete and robust than previous versions. The final executable architecture contains all the elements that make up the architecture and should validate all architecturally significant requirements. There may be rare exceptions where a portion of the architecture can't practically be implemented until later due to uncontrollable circumstances such as constraints with third part software or unique resources that are unavailable. Delaying any part of the architecture should be avoided as it raises significant technical risk later in the project. But if circumstances dictate that some architectural risk can't be mitigated until later in development, a conscious decision can be made to carry this risk forward until the architecture can be fully implemented.  It's also possible to include non-architectural elements into an executable architecture. This will most likely happen when addressing high risk issues early in the development cycle, which is an excellent practice. Two examples of non-technical risks are resource risks and competitive risks. It may be desirable to obtain a difficult-to-get resource early so they can work on a unique piece of the software now, rather than hoping the resource will be available later. Or it may be useful to implement and deploy some early features to maintain market share against a competitor. Think of the executable architecture as a way to mitigate architectural risk, which is the most significant technical risk in a project. From this perspective, it's appropriate to mitigate other risks in the executable architecture.  The difference between the executable architecture and the implementation later in the development cycle is that the executable architecture is the result of a period of development \(for example an iteration\) that's dedicated to elaborating the architecture. Later iterations build onto the executable architecture but are not flagged as an executable architecture because they extend the system's functionality beyond the architectural framework.
---

More Information

Concepts|
  * [Architecturally Significant Requirements](architecturally-significant-requirements.md)
  * [Software Architecture](software-architecture.md)
---|---

---
title: Design
source_url: practice.tech.evolutionary_design.base/workproducts/design_D677D182.html
type: Artifact
uma_name: design
page_guid: _0WuL8slgEdmt3adZL5Dmdw
keywords:
- design
---

 This artifact describes the realization of required system functionality and serves as an abstraction of the source code.
---
Domains: [Development](../../../core/cat/domains/development.md)

Purpose

Describe the elements of the system so they can be examined and understood in ways not possible by reading the source code.
---

Relationships

Fulfilled Slots|
  * [\[Technical Design\]](./../../core.tech.slot.base/workproducts/technical_design_slot_84295A08.html)
---|---
Roles| Responsible:
  * [Developer](../../../core/role/roles/developer-11.md)

| Modified By:
  * [Developer](../../../core/role/roles/developer-11.md)


Tasks| Input To:
  * [Design the Solution](../tasks/design-the-solution.md)
  * [Implement Solution](../../test_driven_development/tasks/implement-solution-1.md)
  * [Implement Developer Tests](../../test_driven_development/tasks/implement-developer-tests-1.md)
  * [Refine the Architecture](../../evolutionary_arch/tasks/refine-the-architecture-1.md)

| Output From:
  * [Design the Solution](../tasks/design-the-solution.md)



Description

Main Description|  This work product describes the elements that will make up the implemented system. It communicates abstractions of particular portions of the implementation.  While architecture focuses on interfaces, patterns, and key decisions, the design fleshes out the technical details in readiness for implementation, or as part of implementation.  This product can describe multiple static and dynamic views of the system for examination. Although various views may focus on divergent, seemingly independent issues of how the system will be put together and work, they should fit together without contradiction.
---|---

Illustrations

Templates|
  * [Design](../guidances/templates/design-3.md)
---|---

Tailoring

Impact of not having|  Implementation will proceed with fine-grained, inconsistent tactical decisions that lead to poor-quality software.
---|---
Reasons for not needing| The design typically needs to be represented in some form, although it may be captured in code or tests and not distinct as a separate artifact. In circumstances where a project involves applying well-understood, existing strategies for architecture and design, it is possible that you will not need a _new_ design. In those cases, you can simply refer to some existing design.
Representation Options|  It is important that the author of this work product be able to analyze key decisions about the structure and behavior of the system and communicate them to other collaborators. It is also important that these decisions can be communicated at various levels of abstraction and granularity. Some aspects of the design can be represented by source code, possibly with some extra annotations. But more abstract representations of the design will be at a higher-level than source code.  The more abstract representation could use various representation options. UML could be used either strictly or informally; it is a preferred notation based on its rich semantics and broad usage in the industry. Other techniques could be used to communicate the design. Or the design could use a mix of techniques as applicable.  Whether you record these representations on a white board or use a formal tool is not governed by this process. But any representation, whether characterized as formal or informal, should unambiguously communicate the technical decisions embodied by the design.

More Information

Checklists|
  * [Design](../guidances/checklists/design-1.md)
---|---
Concepts|
  * [Design](../guidances/concepts/design-2.md)


Guidelines|
  * [Designing Visually](../guidances/guidelines/designing-visually.md)

---
title: Architectural Views and Viewpoints
source_url: core.tech.common.extend_supp/guidances/concepts/arch_views_viewpoints_7A6CD31.html
type: Concept
uma_name: arch_views_viewpoints
page_guid: _kgtcoNc8Edyd7OybSySFxg
keywords:
- architectural
- viewpoints
- views
related:
  other:
  - software-architecture
---


 This concept describes the important concepts of views and viewpoints in the context of architecture.
---

Relationships

Related Elements|
  * [Software Architecture](software-architecture.md)
---|---

Main Description

Architecture can be represented from a variety of viewpoints, all of which can be combined to create a holistic view of the system. Each architectural view addresses some specific set of concerns, specific to stakeholders in the development process: users, designers, managers, system engineers, maintainers, and so on.  The views capture the major structural design decisions by showing how the software architecture is decomposed into components, and how components are connected by connectors to produce useful forms [\[PW92\]](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html#PW92). These design choices must be tied to the requirements -- functional and supplementary -- and other constraints. But these choices in turn put further constraints on the requirements, and on future design decisions at a lower level.  In essence, architectural views are abstractions, or simplifications, of the entire design, in which important characteristics are made more visible by leaving details aside. These characteristics are important when reasoning about:
  * System evolution-going to the next development cycle.
  * Reuse of the architecture, or parts of it, in the context of a product line.
  * Assessment of supplementary qualities, such as performance, availability, portability, and safety.
  * Assignment of development work to teams or subcontractors.
  * Decisions about including off-the-shelf components.
  * Insertion in a wider system.

To choose the appropriate set of views, identify the stakeholders who depend on software architecture documentation and the information that they need. For an example of a set of views that have been used to represent architecture, see [Example: 4+1 Views of Software Architecture](../examples/41-views-of-software-architecture.md). A more comprehensive set of views can be found in the [IBM Views and Viewpoints Framework for IT systems](http://www.ibm.com/developerworks/rational/library/08/0108_cooks-cripps-spaas/).
---

More Information

Examples|
  * [4+1 Views of Software Architecture](../examples/41-views-of-software-architecture.md)
---|---

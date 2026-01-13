---
title: Requirements Realization
source_url: practice.tech.evolutionary_design.base/guidances/concepts/requirements_realization_55C64ACB.html
type: Concept
uma_name: requirements_realization
page_guid: _T9FbYFRFEd2o7OqLaYh8nA
keywords:
- addressed
- realization
- requirements
related:
  guidelines:
  - analyze-the-design
  - evolve-the-design
  tasks:
  - design-the-solution
---


 Realizations illustrate how requirements are addressed in the design to help assure that all requirements are being addressed.
---

Relationships

Related Elements|
  * [Analyze the Design](../guidelines/analyze-the-design.md)
  * [Design the Solution](../../tasks/design-the-solution.md)
  * [Evolve the Design](../guidelines/evolve-the-design.md)
---|---

Main Description

Requirements realizations represent how one or more requirements are fulfilled in the design. This can take various forms. It may include, for example, a textual description \(a document\), class diagrams of participating classes and subsystems, and interaction diagrams \(communication and sequence diagrams\) that illustrate the flow of interactions between class and subsystem instances.  In a model, requirements realization is typically represented as a UML collaboration that groups the diagrams and other information \(such as textual descriptions\) that form part of the realization. If using use cases, the collaboration may be further stereotyped as a use-case realization.  Note that there can be more than one realization of the same set of requirements. This is particularly important for larger projects, or families of systems where the same requirements may be designed differently in different products within the product family. Consider the case of a family of telephone switches which have many requirements in common, but which design and implement them differently according to product positioning, performance and price.
---

---
title: Use-Cases Realizations
source_url: practice.tech.use_case_driven_dev.base/guidances/guidelines/uc_realizations_448DDA77.html
type: Guideline
uma_name: uc_realizations
page_guid: _2uan8NbyEdqu5o2S60g5LA
keywords:
- case
- cases
- realizations
---

 A use-case realization represents how a use case will be implemented in terms of collaborating objects. This guideline describes its purpose and UML notation.
---

Relationships

Related Elements|
  * [\[Design Guidance\]](./../../../core.tech.slot.base/guidances/guidelines/design_guidance_slot_AB88B43E.html)
---|---

Main Description

A use-case realization represents how a use case will be implemented in terms of collaborating objects. This artifact can take various forms. It can include, for example, a textual description \(a document\), class diagrams of participating classes and subsystems, and interaction diagrams \(communication and sequence diagrams\) that illustrate the flow of interactions between class and subsystem instances.  The reason for separating the use-case realization from its use case is that doing so allows the use cases to be managed separately from their realizations. This is particularly important for larger projects, or families of systems where the same use cases can be designed differently in different products within the product family. Consider the case of a family of telephone switches which have many use cases in common, but which design and implement them differently according to product positioning, performance and price.  For larger projects, separating the use case and its realization allows changes to the design of the use case without affecting the baselined use case itself.  In a model, a use-case realization is represented as a UML collaboration that groups the diagrams and other information \(such as textual descriptions\) that form part of the use-case realization.  UML diagrams that support use-case realizations can be produced in an analysis context, a design context, or both, depending on the needs of the project. For each use case in the use-case model, there can be a use-case realization in the analysis/design model with a realization relationship to the use case. In UML this is shown as a dashed arrow, with an arrowhead like a generalization relationship, indicating that a realization is a kind of inheritance, as well as a dependency.
![Use Case Realizations](../../../../images/ucrea1.png) [📄](../../../../images/descriptions/ucrea1.md "Image description") A use-case realization in the design can be traced to a use case in the use-case model.

####  Class Diagrams Owned by a Use-Case Realization

For each use-case realization there can be one or more class diagrams depicting its participating classes. A class and its objects often participate in several use-case realizations. It is important while designing to coordinate all the requirements on a class and its objects that different use-case realizations can have. The figure below shows an analysis class diagram for the realization of the Receive Deposit Item use case. Note the use of boundary-control-entity stereotypes to represent analysis classes \(see [Guideline: Entity-Control-Boundary Pattern](../../../../core/common/guidances/guidelines/entity-control-boundary-pattern.md)\).  ![Class diagram for the realization of Receive Deposit Item](../../../../images/md_ucre3.png) [📄](../../../../images/descriptions/md_ucre3.md "Image description") **The use case Receive Deposit Item and its analysis-level class diagram**.

####  Communication and Sequence Diagrams Owned by a Use-Case Realization

For each use-case realization there can be one or more interaction diagrams depicting its participating objects and their interactions. There are two types of interaction diagrams: sequence diagrams and communication diagrams. They express similar information, but show it in different ways. Sequence diagrams show the explicit sequence of messages and are better when it is important to visualize the time ordering of messages, whereas communication diagrams show the communication links between objects and are better for understanding all of the effects on a given object and for algorithm design.  Realizing use cases through interaction diagrams helps to keep the design simple and cohesive. Assigning responsibilities to classes on the basis of what the use-case scenario explicitly requires encourages the design to contain the following:
  * Only the functionality actually used in support of a use case scenario,
  * Functionality that can be tested through an associated test case,
  * Functionality that is more easily traceable to requirements and changes,
  * Explicitly declared class dependencies that are easier to manage.

These factors help improve the overall quality of the system.
---

More Information

Guidelines|
  * [Entity-Control-Boundary Pattern](../../../../core/common/guidances/guidelines/entity-control-boundary-pattern.md)
---|---

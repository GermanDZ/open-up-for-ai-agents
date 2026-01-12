---
title: Entity-Control-Boundary Pattern
source_url: core.tech.common.extend_supp/guidances/guidelines/entity_control_boundary_pattern_C4047897.html
type: Guideline
uma_name: entity_control_boundary_pattern
page_guid: _uF-QYEAhEdq_UJTvM1DM2Q
keywords:
- boundary
- control
- entity
- pattern
related:
  guidelines:
  - analyze-the-design
  - use-cases-realizations
  tasks:
  - design-the-solution
  other:
  - representing-interfaces-to-external-systems
---


 This guideline describes a rapid way to build a design that is robust enough to realize the functional requirements.
---

Relationships

Related Elements|
  * [Analyze the Design](../../../../practice-technical/evolutionary_design/guidances/guidelines/analyze-the-design.md)
  * [Design the Solution](../../../../practice-technical/evolutionary_design/tasks/design-the-solution.md)
  * [Representing Interfaces to External Systems](representing-interfaces-to-external-systems.md)
  * [Use-Cases Realizations](../../../../practice-technical/use_case_driven_dev/guidances/guidelines/use-cases-realizations.md)
---|---

Main Description

When identifying the elements for a scenario of system behavior, you can align each participating element with one of three key perspectives: **Entity** , **Control** , or **Boundary**. Although specifics of languages, frameworks, and heuristics of quality design will drive the final design, a first cut that covers required system behavior can always be assembled with elements of these three perspectives.  This pattern is similar to the Model View Controller pattern \(described here \[[BUS96](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html#BUS96)\] and here \[[WIKP-MVC](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html#WIKP-MVC)\], among other places\), but the Entity Control Boundary \(ECB\) pattern is not solely appropriate for dealing with user interfaces, and it gives the controller a slightly different role to play.

####  ECB pattern example

![](../../../../images/ebc_diagram.jpg) [📄](../../../../images/descriptions/ebc_diagram.md "Image description")

###  Entity elements

An entity is a long-lived, passive element that is responsible for some meaningful chunk of information. This is not to say that entities are "data," while other design elements are "function." Entities perform behavior organized around some cohesive amount of data.  An example of an entity for a customer service application is a Customer entity that manages all information about a customer. A design element for this entity would include data about the customer, behavior to manage the data, behavior to validate customer information and to perform other business calculations, such as "Is this customer allowed to purchase product X?"  The identification of the entities as part of this pattern can be done many times at different levels of abstraction from the code, at different levels of granularity in size, and from the perspectives of different contexts. For example, you could do an analysis pass on a scenario of creating a marketing campaign and identify the customer element with various customer data elements, such as name and address, plus various required behaviors, such as the management of the name and address data and the ability to rate the customer based on some algorithm \(such an application of this pattern would be abstract from code, coarse-grained, and have no specific context\). Later, you could do a pass on the same scenario applying an architectural mechanism for database access that breaks the address out as its own element, moves the responsibility for storing and retrieving customers to a new control element, and identifies specific database decisions, such as the use of primary keys in the entities. \(Such an application of this pattern would be closer to the code, finer-grained, and aligned with a database context.\)

###  Control elements

A control element manages the flow of interaction of the scenario. A control element could manage the end-to-end behavior of a scenario or it could manage the interactions between a subset of the elements. Behavior and business rules relating to the information relevant to the scenario should be assigned to the entities; the control elements are responsible only for the flow of the scenario.  CreateMarketingCampaign is an example of a control element for a customer service application. This design element would be responsive to certain front-end boundary elements and would collaborate with other entities, control elements, and back-end boundary elements to support the creation of a marketing campaign.  As with the entity example here, there might be many passes over the identification of control elements. A first pass might be an analysis pass that identifies one control element for a scenario, with behavior to make sure that the design can support the flow of events. A subsequent pass might find controllers to manage reusable collaborations of low-level elements that will map to a specific code unit to be written.

###  Boundary elements

A boundary element lies on the periphery of a system or subsystem, but within it. For any scenario being considered either across the whole system or within some subsystem, some boundary elements will be "front end" elements that accept input from outside of the area under design, and other elements will be "back end," managing communication to supporting elements outside of the system or subsystem.  Two examples of boundary elements for a customer service application might be a front end MarketingCampaignForm and a back end BudgetSystem element. The MarketingCampaignForm would manage the exchange of information between a user and the system, and the BudgetSystem would manage the exchange of information between the system and an external system that manages budgets.  If the system communicates with another system \(where that system could be anything from software to hardware units that the current system will use, such as printers, terminals, alarm devices, and sensors\). An analysis pass could identify one boundary element for each external relevant to a scenario.  Example:

> An automated teller machine \(ATM\) must communicate with the ATM network to ascertain whether a customer's bank number and PIN are correct, and whether the customer has sufficient funds to withdrawal the requested amount. The ATM network is an external system \(from the perspective of the ATM\); therefore, you would use a **boundary** class to represent it in a use-case analysis.

Subsequently, these could be broken down into multiple boundary elements or small communities made up of collaborating elements of all three stereotypes. If the interfaces with the system are simple and well-defined, a single class may be sufficient to represent the external system. Often, however, these interfaces are too complex to be represented by using a single class; they often require complex collaborations of many classes. Moreover, interfaces between systems are often highly reusable across applications. As a result, in many cases, a component models the system interfaces more appropriately. The use of a component allows the interface to the external system to be defined and stabilized, while leaving the design details of the system interface hidden as the system evolves.

###  Walking through the scenario

You can walk through a scenario initiated by something outside of the boundaries of the system or subsystem being designed and distribute the responsibility to perform behavior supporting the scenario to the elements identified of each type. The appropriate design element responsible for each action in the scenario will be as described in the definition of each of the element types described here previously.  In addition to identifying the behavior necessary to perform the scenario, the initiation of this behavior from design element to design element identifies the necessary relationships. There are certain appropriate relations between the participating elements. An element can communicate with other elements of the same kind. Control elements can communicate with each of the other two kinds, but entities and boundary elements should not communicate directly.  This table shows appropriate links between design elements.  |  |  Entity  |  Boundary  |  Control
---|---|---|---
Entity  |  X  |  |  X
Boundary  |  |  |  X
Control  |  X  |  X  |  X

By applying this pattern, you can put a robust design together that identifies the elements, behavior, and relationships necessary to support a scenario.

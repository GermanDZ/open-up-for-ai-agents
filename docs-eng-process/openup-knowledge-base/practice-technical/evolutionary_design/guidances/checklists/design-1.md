---
title: Design
source_url: practice.tech.evolutionary_design.base/guidances/checklists/design_68980812.html
type: Checklist
uma_name: design
page_guid: _0XSzsMlgEdmt3adZL5Dmdw
keywords:
- design
related:
  guidelines:
  - analyze-the-design
  - evolve-the-design
  - refactoring-1
  workproducts:
  - design
  concepts:
  - design-2
---



---

Relationships

Related Elements|
  * [Analyze the Design](../guidelines/analyze-the-design.md)
  * [Design](../../workproducts/design.md)
  * [Design](../concepts/design-2.md)
  * [Evolve the Design](../guidelines/evolve-the-design.md)
  * [Refactoring](../../../../core/common/guidances/guidelines/refactoring-1.md)
---|---

Check Items

The design is understandable |
  * Is the design organized in a way that team members can easily find the information that they're looking for?
  * Is the design as simple as it can be, while still fulfilling the objectives of the design and giving sufficient direction to implementers?
  * Is the design neither too simple nor too advanced? The design sophistication should be appropriate to the experience level of other team members and technical stakeholders. This applies to both the concept and the representation of the design.
  * Does the design express what the designer intends to express?
---

The design is consistent
  * Does the design follow any design standards?
  * Does the design apply other idioms consistently?
  * Are the names of the design elements consistent and easy to interpret?
  * Does any part of the design contradict another part of it in such a way that puts the project at risk?
  * If the design is rendered visually, is the notation used to describe the design used consistently so that it can be understood and is not ambiguous?
---

The design is maintainable
  * Is the design structured well enough to be maintained?
  * Is the design set up to appropriately accommodate expected changes? The design should not be overdone to handle _any_ possible change, just reasonably expected changes.
  * Have redundant areas of the design been removed so that the implementation does not contain redundant code?
---

The design is traceable
  * Is it clear how the design elements relate to the requirements? This does not need to involve a heavyweight traceability strategy, but is there some way to figure out what part of the design supports a particular requirement?
  * It what portions of the implementation support each design element clear?
---

The design reflects the architectural objectives of the system
  * Does the design conform to the architecture as specified?
  * Does it apply the architectural patterns appropriately?
  * Are Architectural Mechanisms used appropriately? Are they applied in all applicable circumstances?
---

The design elements are modular
  * Do the design elements have high internal cohesion? Does the degree of interaction within the unit demonstrate that all of the internal parts belong together?
  * Do the design elements have low coupling? Is there minimal interdependence between design elements? When design elements depend upon one another, is this done as simply as possible and in such a way that the client element will not be affected by changes to the internal parts of the supplier element?
  * Are the design elements defined with abstract interfaces in ways that changes can be made to the internal implementation without affecting client design elements?
  * Does each design element represent a clearly defined abstraction?
---

The system can be implemented from the information in the design
  * Has sufficient detail been included to direct the implementation?
  * Does the design constrain the implementation only as much as necessary? Does the design allow freedom for the implementer to implement it appropriately?
  * Is the design feasible? Is it a design that can be reasonably implemented by the team by using the technologies selected within the timeframe of the project?
---

The design provide enough information for developer testing
  * Does the design provide enough information for developer test design? Are the expected behavior and constraints on the methods clear?
  * Are the collaborations between design elements clear enough to create integration tests?
---

The design describe the system at the appropriate level of abstraction

Does the design describe the system at the appropriate level of abstraction given the objectives? This usually means that the system is described at several different levels of abstraction and from different perspectives.
---

The design supports a coarse-grained perspective of the system
  * Can the design be understood as a set of higher-order subsystems?
  * Are the subsystem dependencies documented?
  * Are interfaces clearly defined for each subsystem? Is each subsystem designed so that its services can be accessed through the interface without a need to access internal parts?
  * Is each subsystem designed so that someone can work within one part without having to understand the internal parts of the other elements?
---

Packages and Organization

Is the package partitioning logical and consistent? Does it make sense to team members and stakeholders?  Do package names accurately describe the contents of the package and the role they play in the architecture? Do they follow naming conventions?  Do public packages and interfaces provide a logically cohesive set of services?  Are all the contents of a package listed? Are the classes within a package cohesive?  Do package dependencies correspond to the dependencies of the contained classes?  Are there packages or classes within a package that can be separated into and independent or sub-package?
---

Views

Does each diagram help the designer reason about the design, or communicate key design decisions to the team?  Are the relationships between diagrams clear when several diagrams are used to describe behavior?  Is it easy to navigate between related diagrams?  Does each diagram focus on a relevant perspective? For instance, does a set of diagrams show a single class and its direct relationships, rather than using one or two diagrams to show all classes?  Is each diagram complete and minimal? Does it show everything relevant to that view and nothing more?  Are the diagrams tidy and easy to interpret, with a minimum of clutter?
---

UML

Does the visual model conform to UML standards so all stakeholders can understand the model over time? See the [OMG UML Resource Page](http://www.uml.org/) for more information.  Does the visual model conform to project or organization specific modeling standards? Is the visual model internally consistent? For instance, if an object diagram shows a relationship between objects, does a corresponding relationship exist between the appropriate classes?
Does the name of each class clearly reflect the role it plays?  Does each class offer the required behavior?  Is there at least one realization association defined for each interface? The realization may represent a 3rd party implementation of the subsystem.  Are there dependency associations from each subsystem to the interfaces it uses?  Is each operation in a subsystem interface described in a sequence diagram? Or at least mapped directly to an operation in a class?  Does each class represent a single well defined abstraction?  Are generalization relationships used only to inherit definitions, not behavior \(implementation\)? In other words, is behavior shared through the use of association, aggregation and containment relationships instead of generalization?  Are parent classes in generalization relationships abstract? Are the "leaf" classes in a generalization hierarchy the only concrete classes?  Are stereotypes used consistently and meaningfully?  Do statecharts exist for classes with complex or restrictive state changes?  Do relationships have descriptive role or association names \(one or the other but not both\), and correct multiplicities?  Are relationships between classes unidirectional whenever possible?
---

Non-UML Visual Modeling

Are the semantics of the visual modeling language clearly defined, documented, and accessible to team members? The semantics should be meaningful to the users of the model.  Can the semantics of the modeling language be understood over time? Is the language documented well enough so that team members can understand the model long after design decisions have taken place?  Are team members and stakeholders trained in the modeling language being used?  Does the visual model conform to the semantics of the visual modeling language? In other words, are the meanings of the symbols in the diagrams consistent across the model and diagrams?
---

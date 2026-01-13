---
title: Evolve the Design
source_url: practice.tech.evolutionary_design.base/guidances/guidelines/evolve_the_design_3C9D6965.html
type: Guideline
uma_name: evolve_the_design
page_guid: _C4U9QPTeEduDKIuqTXQ8SA
keywords:
- design
- evolve
- techniques
related:
  other:
  - analyze-the-design
  tasks:
  - design-the-solution
---


 This guideline describes techniques to refine and evolve the design of the software. Good object-oriented techniques are applied within the context of the architecture
to create a system design that's understandable, extensible, and maintainable.
---

Relationships

Related Elements|
  * [Analyze the Design](analyze-the-design.md)
  * [Design the Solution](../../tasks/design-the-solution.md)
---|---

Main Description

###  Review the design

Design is best accomplished collaboratively, because it is a problem-solving activity with a range of parts and perspectives. There should be a constant level of review to ensure that the decisions make sense within the area being designed and in the design of the system overall. There also might be occasions where some area of design is reviewed by a set of interested or knowledgeable parties, such as the architect who will verify that the design conforms to an architectural decision or a developer who will be expected to implement the design.  The design should be examined to ensure that it follows heuristics of quality design, such as loose coupling and high cohesion. Responsibilities should be appropriately distributed to elements in ways that there are no elements with too much responsibility and no elements that are left without any responsibilities. The design should be able to clearly communicate the design decisions, yet not delve into concerns best dealt with during implementation of code.  Ensure that the design follows any project-specific guidelines and conforms to the architecture. Modifications to the design to improve it \(based on issues identified in reviewing it\) should apply [Refactoring](../../../../core/common/guidances/guidelines/refactoring-1.md) to ensure that the design and any existing implementation of the design continues to fulfill its responsibilities. Revisit the relationships between elements to improve the coupling in the design. Remove redundant relationships, try to make relationships unidirectional, and so forth. See [Guideline: Analyze the Design](analyze-the-design.md) for more information.

###  Refine the design

After creating an implementation that includes a set of collaborating elements, with the behavior and relationships robust enough to pass developer tests, the design can be improved and transformed into a more robust and maintainable system.  The visibility of each operation should be selected to be as restrictive as possible. Based on walking through the scenario, it should be clear which operations must be available to other elements in the design and which can be considered behavior inside of the element that has the operation. Minimizing the number of public operations creates a more maintainable and understandable design.  With respect to parameters, the return value, and a description of how it perform the behavior, operations can be detailed at a lower level that drives the actual implementation, or that detail might be left to be handled when writing the code.  Data attributes can be identified based on information needed to support behavior or based on additional requirements, such as information to be presented to the user or transmitted to another system. Avoid indiscriminate domain analysis, because there might be a great deal of data in the domain that is not needed to support the requirements. Data attributes can simply be identified or they can be designed in detail, with attribute types, initial values, and constraints. Decide on the visibility of the data attribute; operations to access and update the data can be added or deferred until implementation.  Generalization and interfaces can be applied to simplify or otherwise improve the design. Ensure that the use of these techniques actually improves the design, rather than bogging it down with complexity. For example, common behavior can be factored into a parent class through generalization or out to a helper class through delegation. The latter solution can be more understandable and maintainable, because generalization is an inflexible relationship \(see the section that follows on inheritance\).  The refinement of any portion of the design could include another pass through the design process. You might find that what was initially identified as a single behavior of an element warrants a detailed walkthrough of the collaborating elements to realize that behavior.  When updating an existing design -- especially one that has had portions already implemented -- apply refactoring to ensure that the improved design continues to perform as expected.

####  Organize elements

In a design of any notable size, the elements must be organized into packages. Assign the elements to existing or new packages, and ensure that the visibility relationships between the packages support the navigation required between the elements. Decide whether each element should be visible to elements outside of the package.  When structuring the design into packages, consider [Layering](../../../../core/common/guidances/guidelines/layering.md) and other patterns. Although all design work must conform to existing architectural decisions, the allocation of elements to packages and possible updates to package visibility are of significant architectural concern. The developer should collaborate with the architect to ensure that package-level decisions are in accordance with the rest of the architecture.  This guideline first talks about the identification and design of the elements and then about organizing the elements into packages. However, this is not a strict order of events. There is nothing wrong with identifying a package structure for the system and then populating that structure with identified elements, as long as the actual elements identified are allowed to influence the resulting package structure. See the sections on identification and behavior of elements in [Guideline: Analyze the Design](analyze-the-design.md).

####  Identify patterns

Identifying [Pattern](../../../../core/common/guidances/concepts/pattern.md)s and seeking opportunities to leverage patterns are useful techniques. The value of patterns here is that they provide a shortcut to a robust design. For instance, when there's an interface realized by multiple classes, it's possible that an Abstract Factory pattern will be useful, because the pattern encapsulates the logic of what class should be instantiated. The more experienced a developer is, the better the developer is at identifying opportunities to take advantage of, or leverage, patterns.  The longer you use patterns, the easier it will be to identify opportunities to leverage them. At first, look for places where you can clearly specify the need for some behavior. Perhaps there's a place where some function or algorithm must be shared between many different classes. How can this behavior be shared over and over among heterogeneous classes? Or perhaps a third-party library is replacing a block of custom code. Is there a way to make this transition easier by creating an interface that can use either implementation? These are opportunities for finding or possibly creating a pattern.  See also [\[GAM95\]](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html#GAM95) and [\[SHA05\]](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html#SHA05)

###  Inheriting behavior versus inheriting interfaces

Inheritance \(or generalization\) is often used as a shortcut during implementation to quickly re-use behavior \(code\).  **Caution:**
Work hard to remove behavior inheritance in design. It will almost always cost more effort than it saves.  Inheritance is a very rigid structure with strict rules. A class that inherits from another class is establishing an **is-a** relationship. The inheriting class is a type of the parent class-- the child has the same relationships and behaviors as the parent. In most hierarchies, it will be impossible to maintain this type of relationship. Exceptions quickly creep in, and it's common to find child classes that remove or override behavior in the parent classes. This increases maintenance costs and makes it difficult to understand what each class does.  It's also too tempting to instantiate parent classes, which makes the parent class both abstract and concrete. If a class has children, it must be abstract enough to support the generalized behavior of the children. But if it's instantiated, it must be concrete enough to provide specific behavior. It's rarely possible to fulfill both of these competing imperatives at the same time, and the design suffers.  Use association and aggregation relationships instead of inheriting behavior. Patterns are a good tool to leverage in breaking up inheritance hierarchies.  Inheriting interfaces is safe, because only the description and not the implementation of what needs to be done is reused.  Avoiding inheriting behavior is an application of the Open-Closed Principle. See [Concept: Design](../concepts/design-2.md) for more information.

###  **Revisit the analysis**

The [Guideline: Analyze the Design](analyze-the-design.md) describes techniques that are also useful when evolving a more robust design.

####  **Consider the architecture**

The architecture must be considered in all design changes. The "best" design for a particular part of the solution may not be appropriate because of architectural constraints that must support the entire system. The architecture may also help to make design decisions, because it can be part of the selection criteria between two potential solutions. Developers should always be up-to-date with the architecture and review it often, particularly in early iterations.  This guideline remarks on conforming to the architecture in various ways; it is written as though it is about designing within a pre-existing architecture. Although projects will often have pre-existing architectures available, a particular architecture is the result of design activities. Therefore, in addition to discussing conformance to some existing architecture, you must also consider the creation of the architecture, as well as updates and improvements based on the work of design.  Also, see [\[SHA05\]](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html#SHA05) for a useful introduction to object-oriented techniques that should be applied when evolving a good design.
---

More Information

Checklists|
  * [Design](../checklists/design-1.md)
---|---
Concepts|
  * [Design](../concepts/design-2.md)
  * [Refactoring](../../../../core/common/guidances/concepts/refactoring.md)
  * [Requirements Realization](../concepts/requirements-realization.md)


Guidelines|
  * [Analyze the Design](analyze-the-design.md)
  * [Designing Visually](designing-visually.md)
  * [Refactoring](../../../../core/common/guidances/guidelines/refactoring-1.md)
  * [Software Reuse](../../../../core/common/guidances/guidelines/software-reuse.md)

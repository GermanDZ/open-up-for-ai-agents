---
title: Design
source_url: practice.tech.evolutionary_design.base/guidances/concepts/design_E36137FA.html
type: Concept
uma_name: design
page_guid: _bFjlAPTYEduDKIuqTXQ8SA
keywords:
- design
related:
  guidelines:
  - analyze-the-design
  - evolve-the-design
  workproducts:
  - design
  tasks:
  - design-the-solution
---


 This concept outlines important principles that should be taken into account when considering the design of a system.
---

Relationships

Related Elements|
  * [Analyze the Design](../guidelines/analyze-the-design.md)
  * [Design](../../workproducts/design.md)
  * [Design the Solution](../../tasks/design-the-solution.md)
  * [Evolve the Design](../guidelines/evolve-the-design.md)
---|---

Main Description

Designing a system is about creating the internal structure and behavior of a system that's robust, extensible, and high-quality. Good design improves quality and makes a system easier to maintain and extend, while a poor design can significantly raise the cost of producing and maintaining the software.  Design is an abstraction of the code that presents the system from a perspective that makes it easier to address the structure and behavior of the software. This can be done through viewing the code, but it's more difficult and less effective to address structural and behavioral issues this way. Design can be visual models, simple sketches, text descriptions, etc. The critical element of design is that it describes how different elements of the system interact to fulfill the requirements.  The amount of design that's formally documented and maintained will vary depending on the criticality of the design and how much of the design needs to be communicated to future team members. At a minimum, all architecturally significant design elements should be documented and kept up-to-date with the implementation. These are critical aspects of the system that are necessary for the understanding and maintenance of the software. Other important or complex structure and behavior may be maintained as well. And some contracts may require that the entire design is thoroughly documented.  On many projects there will probably be aspects of the design that are only documented for the purpose of creating a solution or walking through how certain behavior will be realized. It may not be worth the overhead of maintaining this information as the design is transformed through refactoring and other influences. However, it may be useful to archive the initial decisions, whiteboard images, or files so they can be referenced in the future if necessary. These can be viewed as "old meeting minutes" that are stored for potential future reference. They may not reflect the current design, but they may still provide useful insight.

###  Multiple Passes

The design will be revisited many times throughout an iterative lifecycle and even within an iteration. Each time some design activity is being performed, it will be performed in the context of a specific goal. The goal might be to identify a notional set of participants in a collaboration that can be exercised to realize the behavior required \(an analysis pass\). The goal might be in the identification of some coarse-grained elements that are required to act out some scenario \(an architectural pass\). Then a pass might be done within one of those components to identify the elements within that will collaborate together to perform the behavior required \(a more detailed design pass\).

Design might be performed in a particular context such as database context, user-interface context, or perhaps the context of how some existing library will be applied. In these cases the design steps will be performed just to make and communicate decisions regarding that context  Avoid analysis paralysis. Avoid refining, extending, and improving the design beyond a minimal version that suffices to cover the needs of the requirements within the architecture. Design should be done in small chunks, proven via implementation, improved via refactoring, and integrated into the baseline to provide value to the stakeholders.

###  Design versus Architecture

Design is a real thing, the construction of the system's structure and behavior. Architecture defines principles, contexts, and constraints on the system's construction. Architecture is described in architecture artifacts, but it's realized as design \(visual or otherwise\) and implementation.

One way to look at architecture is that it helps to make the entire design more cohesive with itself by balancing the needs of the entire system. Design tends to focus on one area at a time. Architecture helps assure the design is consistent and appropriate to the goals of the system. For instance, there may be constraints placed on most of the design to support the performance of one part of the system, such as improving access to a legacy system. Failure to conform to those constraints in the design may cause the system to fail to meet the performance requirements of the legacy system access. Conforming to the architecture assures that all the goals of the system are met by balancing competing technical issues.

###  Quality of Design

####  You Aren't Going to Need It

The YAGNI principle is a good general approach to design. While designs should be robust enough to modify, re-use, and maintain, it should also be as simple as possible. One of the ways to keep it simple is to make few assumptions about what the design's going to need in the future. Don't assume you'll need something until you know you need it, then do a good job of adding it. Add what's needed for the current requirement or iteration. Refactor the design as necessary when more functionality needs to be added or the design must be made more complex to deal with new circumstances.

####  Coupling and Cohesion

Two of the most fundamental principles of design are coupling and cohesion. A good design contains elements that have high cohesion and low coupling. High cohesion means that a single element, such as a class or subsystem, is composed of parts that are closely related or work closely together to fulfill some purpose. Low coupling means that the elements of a system have a minimum of dependencies on each other. A single element such as a subsystem should be easily replaceable by another subsystem that provides similar behavior.

For example, in a payroll system an Employee class would have high cohesion if it contained elements and functions such as Name, Tax ID Number, and Monthly Salary. At first, it may seem as if the Calculate Paycheck functional would also be cohesive. But when you consider that hourly employees must be paid overtime, sales people must have commission calculated for them, etc, the function is less related to Employee and should probably be its own class or subsystem.

An example of low coupling would be if the Calculate Paycheck subsystem can be easily replaced by third party that may be more robust and offer more features.

Coupling and cohesion are so important to be aware of because they arise in so many design principles and design strategies such as patterns.

####  Open-Closed Principle

Elements in the design should be "open" for extension but "closed" for modification. The goal of this principle is to create software than can be extended without changing code [\[MEY97\]](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html#MEY97). This is because every change to software runs the risk of introducing bugs into code that's already correct. It also allows functionality to be re-used without having to know the details of the implementation, reducing the time it takes to create something new. Keeping this principle in mind helps make a design more maintainable.
---

More Information

Checklists|
  * [Design](../checklists/design-1.md)
---|---
Concepts|
  * [Refactoring](../../../../core/common/guidances/concepts/refactoring.md)
  * [Software Architecture](../../../../core/common/guidances/concepts/software-architecture.md)

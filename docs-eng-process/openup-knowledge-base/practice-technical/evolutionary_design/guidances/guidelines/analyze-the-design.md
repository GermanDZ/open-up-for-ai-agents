---
title: Analyze the Design
source_url: practice.tech.evolutionary_design.base/guidances/guidelines/analyze_the_design_4C4750C0.html
type: Guideline
uma_name: analyze_the_design
page_guid: __MnggPTdEduDKIuqTXQ8SA
keywords:
- analyze
- design
- solution
related:
  tasks:
  - design-the-solution
  other:
  - evolve-the-design
---


 This guideline describes how to approach creating a solution from requirements or change requests. A better solution will usually emerge when even a brief amount of time is spent analyzing the problem and considering approaches.
---

Relationships

Related Elements|
  * [Design the Solution](../../tasks/design-the-solution.md)
  * [Evolve the Design](evolve-the-design.md)
---|---

Main Description

###  Identification of elements

Identify the elements, based on the needs of the requirements. The identification of elements can stem from a static perspective of walking through the requirements and identifying elements clearly called out, which is a form of domain modeling. This can pull in other elements identified as being in the application domain or deemed necessary from examining the requirements for the portion of the system being designed. This identification can also pull from key abstractions identified while defining the architecture.  The identification of elements should also apply a dynamic perspective by walking through scenarios of use of the system \(or subsystem\) and identifying elements needed to support the behavior. That behavior might be a scenario of use from an external user perspective or, while designing a subsystem, a responsibility assigned to the subsystem that has complex algorithmic behavior. Consider applying the [Entity-Control-Boundary Pattern](../../../../core/common/guidances/guidelines/entity-control-boundary-pattern.md) to identify the elements necessary to support the scenario, or apply other patterns identified in the architecture that specify the elements that will be used to support specific aspects of the scenario.  If you are designing a real-time system, include elements to represent events and signals that allow you to describe the asynchronous triggers of behavior to which the system must respond. **Events** are specifications of interesting occurrences in time and space that usually \(if they are noteworthy\) require some response from the system. **Signals** represent asynchronous mechanisms used to communicate certain types of events within the system.  If there are existing elements from previous passes over the design or from selected frameworks or other reusable elements, reuse them whenever possible. See [Guideline: Software Reuse](../../../../core/common/guidances/guidelines/software-reuse.md).  After identifying the elements, give each one meaningful name. Each element should also have a description, so that the team members who work together to refine the design and implement from the design will understand the role that each element plays.  Based on this information, the identification of elements could be applied several times in designing just one part of the system. Although there is no one correct strategy for multiple passes, they could be done at a coarse-grained level and then a fine-grained level, or at an analysis \(abstract\) level and then a design level.

###  Behavior of elements

To identify the behavior of the elements, go through scenarios and assign behavior to the appropriate collaborating participants. If a particular use of the system or subsystem can have multiple possible outcomes or variant sequences, cover enough scenarios to ensure that the design is robust enough to support the possibilities.  When assigning behavior to elements, consider applying the [Entity-Control-Boundary Pattern](../../../../core/common/guidances/guidelines/entity-control-boundary-pattern.md) or other patterns identified in the architecture.  Behavior can be represented as a simple statement of responsibility, or it can be a detailed operation specification. Use the appropriate level of detail to communicate important design decisions while giving the freedom to make appropriate implementation decisions as those tasks ensue.  Avoid too much identification of behavior solely from the perspective of domain modeling. Include only behavior that is really needed -- behavior identified by going through required scenarios of system use.  Behavior must be understood as a responsibility of an element, as well as an interaction between two elements in the context of some broader behavior of the system or subsystem. The latter part of this will lead the developer to identify relationships that are necessary between the elements.

###  Design element relationships

The relationships between the elements necessary for the behavior must be designed. This can simply be the identification of the ability to traverse from one element to another or else a need to manage an association between the elements. Relationships can be designed in more detail, as appropriate. This can include: optionality, multiplicity, whether the relationship is a simple dependency or managed association, and so on. These decisions that drive implementation details are best made at the design level, where it is easier to see how all of the pieces fit together.  Avoid defining too many relationships based on relationships in the application domain. Include only relationships that are needed based on the requirements. On the other hand, a combination of requirements knowledge and domain knowledge can lead to some detailed decisions on the relationships, such as optionality and multiplicity.

###  Analysis classes and YAGNI

Analysis classes are used to identify initial buckets where system functionality should go. They're the first pass at understanding where system behavior will be realized in the design and implementation. For example, an entity class might initially represent all of the behavior for an employee, such as storing personal information and calculating the value of a paycheck. Few assumptions are made about how the final design will look at this point. Analysis classes are about making sure required behavior is represented somewhere in the system, rather than about creating a perfect design.  Analysis classes allow you to begin designing from abstractions, so that the details of the system depend on those abstractions and not the other way around. In the Employee class, the notion of an employee should start with the idea of someone who works for the company, who has responsibilities and receives benefits. It's easier to create a design from this simple idea. The complexity of the design should emerge from the abstract ideas of what the design needs to do. This will also help keep coupling low and cohesion high.  YAGNI \(You Aren't Going to Need It\) is an approach to design where the developer creates only enough implementation and design to address the required functionality. No assumptions are made about re-use or possible future uses of the software. Software is improved when the system requirements demand more functionality or robustness.  The first classes created from a YAGNI perspective are much like analysis classes. You don't know how complex it may be to calculate a paycheck for your employee, so you assume that functionality is highly cohesive with the rest of what the Employee class must do. As you understanding of the requirement develops, the analysis class evolves into a set of collaborating classes and patterns that better support the behavior of the system. For example, payroll calculations could be moved into a pattern that handles all of the different types of paycheck calculations \(overtime, commissions, and so forth\), thereby increasing the internal cohesion of the class.  Use analysis classes to define an initial place to put system behavior, and add only enough behavior to satisfy the YAGNI perspective. Analysis classes will evolve into concrete design classes as more behavior is added and as the design is refactored. See [Guideline: Evolve the Design](evolve-the-design.md).
---

More Information

Checklists|
  * [Design](../checklists/design-1.md)
---|---
Concepts|
  * [Design](../concepts/design-2.md)
  * [Requirements Realization](../concepts/requirements-realization.md)


Guidelines|
  * [Designing Visually](designing-visually.md)
  * [Entity-Control-Boundary Pattern](../../../../core/common/guidances/guidelines/entity-control-boundary-pattern.md)
  * [Evolve the Design](evolve-the-design.md)
  * [Software Reuse](../../../../core/common/guidances/guidelines/software-reuse.md)

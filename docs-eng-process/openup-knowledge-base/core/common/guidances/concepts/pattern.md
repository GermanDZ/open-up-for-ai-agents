---
title: Pattern
source_url: core.tech.common.extend_supp/guidances/concepts/pattern_10BE6D96.html
type: Concept
uma_name: pattern
page_guid: _0YJvUMlgEdmt3adZL5Dmdw
keywords:
- pattern
related:
  guidelines:
  - abstract-away-complexity
  - software-reuse
  other:
  - architectural-mechanism
  - how-to-adopt-the-evolutionary-design-practice
  - software-architecture
  tasks:
  - design-the-solution
---


 A generalized solution that can be implemented and applied in a problem situation \(a context\) and thereby eliminate one or more of the inherent problems.
---

Relationships

Related Elements|
  * [Abstract Away Complexity](../guidelines/abstract-away-complexity.md)
  * [Architectural Mechanism](architectural-mechanism.md)
  * [Design the Solution](../../../../practice-technical/evolutionary_design/tasks/design-the-solution.md)
  * [How to Adopt the Evolutionary Design Practice](../../../../practice-technical/evolutionary_design/guidances/roadmaps/how-to-adopt-the-evolutionary-design-practice.md)
  * [Software Architecture](software-architecture.md)
  * [Software Reuse](../guidelines/software-reuse.md)
---|---

Main Description

####  Origins

The idea of patterns as it is now applied to software design comes from the work of Christopher Alexander. He has written widely on the subject of applying patterns to the design and construction of towns and buildings. Two of his books, _A Pattern Language_ \[[ALE77](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html)\] and _The Timeless Way of Building_ \[[ALE79](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html)\] have had the greatest impact on the software community and the adoption of software patterns for the design of software. His concepts of patterns and pattern language provide a model for the capture of software design expertise in a form that can then be reapplied in recurring situations.

####  A definition of patterns

Today, the most commonly used definition of software patterns is from \[[GAM95](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html)\]:

> "A design pattern describes the problem, a solution to the problem consisting of a general arrangement of objects and classes, when to apply the solution, and the consequences of applying the solution."

This definition often serves only as a starting point, however. A richer definition, based on Alexander's work, is offered by Gabriel in his book, _A Timeless Way of Hacking_ \[[ALU03](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html)\], in which each pattern is a three-part rule that expresses relationships among a certain context, a certain system of forces that occur repeatedly in that context, and a certain software configuration that allows these forces to resolve themselves.

####  Describing patterns

It is commonplace to describe patterns using the format made popular by Erich Gamma and his three colleagues \[[GAM95](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html)\]. They have come to be known as the Gang of Four \(GoF\); therefore, their description is known as the **GoF format**. The GoF format uses the following keywords to describe object-oriented design patterns:
  * **Pattern name and classification:** Naming the pattern allows design to work at a higher level of abstraction, using a vocabulary of patterns. Gamma says that finding a good name is one of the hardest problems of developing a catalogue of patterns \(see **Pattern catalogues** later in this section\).
  * **Intent:** An answer to questions such as: What does the pattern do? What problem does it address?
  * **Also known as:** Other names for the pattern.
  * **Motivation:** A concrete scenario that illustrates a design problem and how the pattern solves the problem.
  * **Applicability:** Instructions for how you can recognize situations in which patterns are applicable.
  * **Structure:** A graphical representation of the classes in the pattern.
  * **Participants:** The responsibilities of the classes and objects that participate in the pattern.
  * **Collaborations:** How participants collaborate to fulfill their responsibilities.
  * **Consequences:** The results, side effects and trade offs caused by using the pattern.
  * **Implementation:** Guidance on the implementation of the pattern.
  * **Sample code:** Code fragments that illustrate the pattern's implementation.
  * **Known uses:** Where to find real-world examples of the pattern.
  * **Related patterns:** Synergies, differences, and other pattern relationships.

Although the GoF format is specifically intended for object-oriented development, you can use it, with slight modification, to address other software patterns. A more general keyword format for software patterns based on Alexander's principles uses keywords such as _problem_ , _context_ , _forces_ and _solution_.

####  Pattern catalogs

To assist with the identification and selection of patterns, various classification schemes have been proposed. One of the early schemes, proposed by Buschmann and his associates, \[[BUS96](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html)\] uses three classifiers: granularity, functionality, and structured principles. Of those three classifiers, it is their granularity classifier that has remained popular. Granularity classifies patterns into three levels of abstraction:
  * **Architectural patterns:** Architectural patterns express the fundamental structure of a software scheme. Examples of architectural pattern include: layers, pipes and filters, and the model view controller pattern.
  * **Design patterns:** Software architecture usually consists of smaller architectural units that are described by design patterns. The GoF pattern is an example of a design pattern.
  * **Idioms.** An idiom is the lowest-level pattern, and it is specific to a programming language.

Buschmann and his colleagues introduced four groups for categorizing architectural patterns:
  * Structure
  * Distributed systems
  * Interactive systems
  * Adaptable systems

The following table shows the categorization of their architectural patterns.  **Categories for Architectural Patterns
** |  **Category** |  **Pattern**
---|---
Structure  |  Layers
Pipes and filters
Blackboard
Distributed systems  |  Broker
Interactive systems  |  Model view controller
Presentation abstraction control
Adaptable systems  |  Reflection
Micro kernel

For design patterns, Gamma's group categorized their design patterns by purpose, using three categories:
  * Creational
  * Structural
  * Behavioral

####  Pattern languages

In addition to the concept of patterns, Alexander also gave the software community the concept of a pattern language. The purpose of developing a pattern language was to provide a vocabulary of design principles \(patterns\) that would allow those who work, study, or live in buildings to communicate effectively with the planners and designers of those buildings. Alexander explains that when using a pattern language:

> We always use it as a sequence, going through the patterns, moving always from the larger patterns to the smaller, always from the ones that create structure to the ones which then embellish those structures, and then to those that embellish the embellishments.

In applying patterns in this way, Alexander advocated the use of generative pattern languages, ones that, given an initial context, would always lead to good design. Alexander states:

> Thus, as in the case of natural languages, the pattern language is generative. It not only tells us the rules of arrangement, but shows us how to construct arrangements - as many as we want - which satisfies the rules.

In the application of software patterns, pattern names provide a vocabulary for the communication of software ideas. The sequential application of patterns finds application in software design processes, both waterfall and iterative, that successively apply architectural patterns, and then design patterns, and, finally, idioms to design and implement a software system. Software processes, however, rely on the skills of the Architect and Developer roles to guide the application of patterns, rather than a generative pattern language.

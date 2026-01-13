---
title: Software Reuse
source_url: core.tech.common.extend_supp/guidances/guidelines/software_reuse_B6B04C26.html
type: Guideline
uma_name: software_reuse
page_guid: _vO2uoO0OEduUpsu85bVhiQ
keywords:
- reuse
- software
related:
  other:
  - abstract-away-complexity
  guidelines:
  - analyze-the-design
  - evolve-the-design
  checklists:
  - architecture-notebook-7
  tasks:
  - design-the-solution
  - envision-the-architecture-1
  - refine-the-architecture-1
  concepts:
  - software-architecture
---


 This guideline describes how to re-use software and design elements.
---

Relationships

Related Elements|
  * [Abstract Away Complexity](abstract-away-complexity.md)
  * [Analyze the Design](../../../../practice-technical/evolutionary_design/guidances/guidelines/analyze-the-design.md)
  * [Architecture Notebook](../../../../practice-technical/evolutionary_arch/guidances/checklists/architecture-notebook-7.md)
  * [Design the Solution](../../../../practice-technical/evolutionary_design/tasks/design-the-solution.md)
  * [Envision the Architecture](../../../../practice-technical/evolutionary_arch/tasks/envision-the-architecture-1.md)
  * [Evolve the Design](../../../../practice-technical/evolutionary_design/guidances/guidelines/evolve-the-design.md)
  * [Refine the Architecture](../../../../practice-technical/evolutionary_arch/tasks/refine-the-architecture-1.md)
  * [Software Architecture](../concepts/software-architecture.md)
---|---

Main Description

Maximizing reuse has always been an important goal of software development. It's better to re-use than to expend the cost of creating something new, testing it, and releasing it for the first time with the risk of hidden problems that all new software has. Languages, particularly object-oriented ones, have been developed to make reuse easier. But a language alone isn't enough to provide cost effective reuse. The bulk of reusable software comes from skilled developers and architects who are able to identify and leverage reuse opportunities.

###  What is a Reusable Asset?

The following are some examples of reusable software assets:
  * Architectural frameworks
  * Architectural mechanisms
  * Architectural decisions
  * Constraints
  * Applications
  * Components
  * COTS software

###  Identifying Reuse Opportunities

There are three perspectives to look at when reusing software: code \(implementation\), design, and framework or architecture. Architects should look to reuse significant application frameworks such as layers that can be applied to many different types of applications \(for more information, see [Guideline: Layering](layering.md). Developers should look to designs and [Pattern](../concepts/pattern.md)s that can be reused to produce desired behavior or robust structures. They should also look at how to reduce the amount of code that needs to be written by leveraging stable components and code that has been proven in production environments.  The best way to enable a team to find opportunities for reuse is to exercise excellent design and coding practices. It's difficult to find code and design that can be reused when dealing with large classes, classes that don't have a clearly defined focus, or classes with relationships that are difficult to understand. Classes should be small, easy to understand, and highly cohesive to make it easier to identify reuse opportunities. Any functionality that can be reasonably separated into another class should be. Another way of saying this is that any concept that could be applied to more than one type of class should be its own class.  For example, if some calculations are added to an existing class, it may make sense to then refactor those calculations into a new helper class. Those calculations can then be re-used in any number of other classes without the burden of having to know about the functionality of the original class.  The simplest but least efficient way to identify reuse opportunities is to "smell" similar code. A developer may recall doing something similar to what they're designing or implementing now. Once the previous implementation has been discovered or recalled it can be reused. Developers will always find reuse opportunities this way. But the unstructured nature of it won't maximize the potential areas for reuse.  Collaboration is a good technique for identifying reuse opportunities. It provides a structure where identifying reuse \- instead of writing code - is the goal of the exercise. And the more brains that are looking for reuse opportunities, the more likely it is that they'll be found. A brainstorming or review meeting that focuses on identifying reuse opportunities would be useful to support this.  Patterns are good ways to find reuse opportunities in designs and frameworks. See [Concept: Pattern](../concepts/pattern.md) for more information.  Analyzing behavior is another good way to identify potential areas for reuse. Analyze how classes need to collaborate in order to deliver some specific functionality such as a requirement or feature. This collaboration can be documented in sequence \(behavior\) and class \(structure\) diagrams and can be reused in similar circumstances.  After looking for similar behavior and returned values, then look for similarity of parameters. If their interfaces are not an exact match for the component interfaces being proposed, you can modify the proposed signatures to increase the degree of reuse. Some design mechanisms, such as performance or security requirements, may disqualify a component from reuse even when there is a perfect match between operation signatures.  A common set of components may exist that provides many of the [Architectural Mechanism](../concepts/architectural-mechanism.md) that you need for the new system. These components may be available either because they were developed or purchased previously for similar systems. Given their suitability and compatibility within the software architecture, there may be a need to reverse-engineer these components to represent them in a design model and reuse them in a project.  Similar thinking applies to existing databases. Part of the information to be used by the application under development may already reside in a database. You may be able to get the classes that represent the database structures that hold this information by reverse-engineering the database.  [Refactoring](../concepts/refactoring.md) should always be considered when reusing code. Code \(or design\) is often not originally written for re-use, or reusable code may not be a perfect fit for a new situation.

###  Assessing and Selecting Assets to Reuse

To assess and select assets to reuse on your project, you need to understand the requirements of the system's environment. You also need to understand the scope and general functionality of the system that the stakeholders require. There are several types of assets to consider, including \(but not limited to\): reference architectures; frameworks; patterns; analysis mechanisms; classes; and experience. You can search asset repositories \(internal or external to your organization\) and industry literature to identify assets or similar projects.  You need to assess whether available assets contribute to solving the key challenges of the current project and whether they are compatible with the project's architectural constraints. You also need to analyze the extent of the fit between assets and requirements, considering whether any of the requirements are negotiable \(to enable use of the asset\). Also, assess whether the asset could be modified or extended to satisfy requirements, as well as what the tradeoffs in adopting it are, in terms of cost, risk, and functionality.  Leverage reuse of existing components by evaluating their interfaces and the behavior that they provide. Reuse components when their interfaces are similar or match the interfaces of components you would need to develop from scratch. If not similar, modify the newly identified interfaces so you improve the fit with existing components interfaces. Work with developers to gain consensus on the suitability of using existing components.  Finally, decide, in principle, whether to use one or more assets, and record the rationale for this decision.

###  Reuse Techniques

Reuse can be performed differently depending on the capabilities of the implementation environment. The simplest technique is to copy the code from one place to another. This isn't advisable because it's not really reuse. Multiple copies of source code are difficult to maintain and can eventually diverge from each other. Reuse is about using the same code to perform similar tasks as a way to increase quality and reduce overhead.  Some languages, such as C++, support templates. Templates, sometimes referred to as parameterized code, are a precursor to patterns. Templates are code with parameters that are applied just when the code's needed, at compile time. The C++ Standard Template Library \(STL\) is one example. It provides many types of reusable containers \(lists, sets, safe arrays, etc\) that don't have some of the drawbacks of inheritance. Templates such as these are also useful as mix-in classes in languages like C++ that support multiple inheritance. Because mix-ins are implemented as templates, they allow for a type of multiple inheritance without the baggage.

###  Inheritance and Aggregation

Inheritance \(also known as generalization\) is an easy way to implement polymorphism and has been used as the primary mechanism for reuse in modern object-oriented languages. This is unfortunate, as inheritance imposes a rigid structure on the software's design that is difficult to change. Any inheritance hierarchy that shares code from parents to children will have problems when it grows to be three or more levels deep. Too many exceptions occur to maintain a pure "is-a" relationship between parents and children, where children are always considered to have all the properties and behaviors of the parents. Inheritance should be used to share definitions \(interfaces\), not implementations. Years of difficulties with inheriting implementations have made this practice a primary object-oriented design principle.  Whenever inheritance is used, it is best to have only the last child class \(leaf node\) of the inheritance hierarchy be instantiated. All parent classes should be abstract. This is because a class that tries to be both reusable and concrete - to provide reusable and specific behavior at the same time - almost always fails to fulfill either goal. This is a dimension of cohesiveness. One thing that makes a class cohesive is that it's dedicated to reuse or dedicated to a specific implementation, but not both.  Aggregation is a technique that collects or aggregates functionality into larger elements of functionality. It provides a structure that's far more flexible and reusable than inheritance. It's better to reuse implementation and design by aggregating small pieces of functionality together rather than trying to inherit the functionality from a parent.  You may also find reuse opportunities by reviewing interfaces. If interfaces describe similar behavior it may be possible to eliminate one of the interfaces, have just one implementation realize both interfaces, or refactor the interfaces to put redundant content in a new, simpler interface.

###  Finding Reusable Code

There are many sources of reusable code beyond what the developers are writing for a specific project. Other places from which to harvest code include the following:
  * Internal \(corporate\) code libraries
  * Third party libraries
  * Built-in language libraries
  * Code samples from tutorials, examples, books, etc.
  * Local code guru or knowledgeable colleague
  * Existing system code
  * Open source products \(be sure to follow any licensing agreements\)

Also, many tools that generate code will generate comprehensive code based on minimal specification. For example, a design tool might generate the member variable plus a get and a set operation when the designer specifies an attribute. Other more sophisticated tools with knowledge of a specific framework can generate voluminous code to ensure that a class conforms to the framework. An example of this would be a tool that generates significant additional code when a class is marked as a Java entity bean. This sort of consistent transformation from a specification \(the design\) to an implementation \(the code\) could be considered a form of code reuse as well.

###  Don't Reuse Everything

Reuse makes code and design cheap to use but expensive to build. It requires experience and thoughtful consideration to create an implementation or design that's abstract enough for others to re-use, but concrete enough to be truly useful. Reusable code must also be maintained. Many organizations have difficulty assigning responsibility for maintaining reusable code if they don't have a group dedicated to reuse.  It's usually not a good idea to create code or designs for reuse unless you know it's going to be reused. It's better to refactor software to be more reusable after it's discovered that they can be reused. One rule of thumb is to write for reuse only when you know you'll use it at least 3 times. Otherwise the cost of building and maintaining that part of the software will not be recovered by reduced overhead in other areas of development.
---

More Information

Concepts|
  * [Pattern](../concepts/pattern.md)
  * [Refactoring](../concepts/refactoring.md)
---|---
Guidelines|
  * [Layering](layering.md)

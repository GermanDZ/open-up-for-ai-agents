---
title: Mapping from Design to Code
source_url: core.tech.common.extend_supp/guidances/guidelines/mapping_design_to_code_FA4B08DA.html
type: Guideline
uma_name: mapping_design_to_code
page_guid: _mlKb8JyJEdy9brKHb521mQ
keywords:
- code
- design
- mapping
related:
  tasks:
  - implement-solution-1
---


 This guideline describes some different options for moving from a design to the implementation, and discusses the benefits and drawbacks of these approaches.
---

Relationships

Related Elements|
  * [Implement Solution](../../../../practice-technical/test_driven_development/tasks/implement-solution-1.md)
---|---

Main Description

####  Introduction

Design must define enough of the system so that it can be implemented unambiguously. What constitutes enough varies from project to project and company to company.  In some cases the design resembles a sketch, elaborated only far enough to ensure that the implementer can proceed \(a "sketch and code" approach\). The degree of specification varies with the expertise of the implementer, the complexity of the design, and the risk that the design might be misconstrued.  In other cases, the design is elaborated to the point that the design can be transformed automatically into code. This typically involves extensions to standard UML to represent language and/or environment specific semantics.  The design may also be hierarchical, such as the following:
  * a high level design model which sketches an overview of the overall system
  * a subsystem specification model which precisely specifies the required interfaces and behavior of major subsystems within the system
  * a detailed design model for the internals of subsystems

The sections below describe some different options for relating a design and implementation, and discuss benefits and drawbacks of these approaches.

####  Sketch and Code

One common approach to design is to sketch out the design at a fairly abstract level, and then move directly to code. Maintenance of the design model is manual.  In this approach, we let a design class be an abstraction of several code-level classes. We recommend that you map each design class to one "head" class that, in turn, can use several "helper" classes to perform its behavior. You can use "helper" classes to implement a complex attribute or to build a data structure that you need for the implementation of an operation. In design, you don't model the "helper" classes and you only model the key attributes, relationships, and operations defined by the head class. The purpose of such a model is to abstract away details that can be completed by the implementer.  This approach is extended to apply to the other design model elements. You may have design interfaces which are more abstract than the code-level interfaces, and so on.

####  Round-Trip Engineering

In round-trip engineering environments, the design model evolves to a level of detail where it becomes a visual representation of the code. The code and its visual representation are synchronized \(with tool support\).  The following are some options for representing a Design Model in a round-trip engineering context.  **High Level Design Model and Detailed Design Model** In this approach, there are two levels of design model maintained. Each high level design element is an abstraction of one or more detailed elements in the round-tripped model. For example, a design class may map to one "head" class and several "helper" classes, just as in the "sketch and code" approach described previously. Traceability from the high level design model elements to round-trip model elements can help maintain consistency between the two models.  Although this can help abstract away less important details, this benefit must be balanced against the effort required to maintain consistency between the models.  **Single Evolving Design Model** In this approach, there is a single Design Model. Initial sketches of design elements evolve to the point where they can be synchronized with code. Diagrams, such as those used to describe design use-case realizations, initially reference sketched design classes, but eventually reference language-specific classes. High level descriptions of the design are maintained as needed, such as:
  * diagrams of the logical structure of the system,
  * subsystem/component specifications,
  * design patterns / mechanisms.

Such a model is easier to maintain consistent with the implementation.

####  Specification and Realization Models

A related approach is to define the design in terms of specifications for major subsystems, detailed to the point where client implementations can compile against them.  The detailed design of the subsystem realization can be modeled and maintained separately from this specification model.  Models can be detailed and used to generate an implementation. Both structure \(class and package diagrams\) and behavior diagrams \(such as collaboration, state, and activity diagrams\) can be used to generate executable code. These initial versions can be further refined as needed.  The design may be platform-independent to varying degrees. Platform-specific design models or even code can be generated by transformations that apply various rules to map high-level abstractions of platform-specific elements. This is the focus of the Object Management Group \(OMG\) Model-Driven Architecture \(MDA\) [\(http://www.omg.org](http://www.omg.org/)\) initiative.  Platform-specific visual models can be used to generate an initial code framework. This framework can be further elaborated with additional code not specified in the design.

####  Patterns

Standard patterns can be applied to generate design and code elements from related design and implementation. For example, a standard transformation pattern can be applied to a data table to create Java™ classes to access the data table. Another example is using an [Eclipse Modeling Framework](http://www.eclipse.org/emf/) to generate code for storing data that matches the model and to generate a user interface implementation for populating data. A pattern or transformation engine can be used to create the implementation, or the implementation can be done by hand. Pattern engines are easier and more reliable, but handwritten code implementing a defined pattern will have fewer errors than handwritten code implementing a novel or unique design.
---

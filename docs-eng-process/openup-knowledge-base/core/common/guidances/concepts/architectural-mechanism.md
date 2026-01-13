---
title: Architectural Mechanism
source_url: core.tech.common.extend_supp/guidances/concepts/arch_mechanism_2932DFB6.html
type: Concept
uma_name: arch_mechanism
page_guid: _mzxI0A4LEduibvKwrGxWxA
keywords:
- architectural
- common
- mechanism
related:
  other:
  - analysis-mechanism
  - design-mechanism
  - software-architecture
  checklists:
  - architecture-notebook-7
  tasks:
  - design-the-solution
  - envision-the-architecture-1
  - refine-the-architecture-1
---


 Architectural Mechanisms are common solutions to common problems that can be used during development to minimize complexity.
---

Relationships

Related Elements|
  * [Analysis Mechanism](analysis-mechanism.md)
  * [Architecture Notebook](../../../../practice-technical/evolutionary_arch/guidances/checklists/architecture-notebook-7.md)
  * [Design Mechanism](design-mechanism.md)
  * [Design the Solution](../../../../practice-technical/evolutionary_design/tasks/design-the-solution.md)
  * [Envision the Architecture](../../../../practice-technical/evolutionary_arch/tasks/envision-the-architecture-1.md)
  * [Refine the Architecture](../../../../practice-technical/evolutionary_arch/tasks/refine-the-architecture-1.md)
  * [Software Architecture](software-architecture.md)
---|---

Main Description

###  What are Architectural Mechanisms?

Architectural Mechanisms are common solutions to common problems that can be used during development to minimize complexity. They represent key technical concepts that will be standardized across the solution. Architecture mechanisms facilitate the evolution of architecturally significant aspects of the system. They allow the team to maintain a cohesive architecture while enabling implementation details to be deferred until they really need to be made.  Architectural Mechanisms are used to satisfy architecturally significant requirements. Usually those are non-functional requirements such as performance and security issues. When fully described, Architectural Mechanisms show patterns of structure and behavior in the software. They form the basis of common software that will be consistently applied across the product being developed. They also form the basis for standardizing the way that the software works; therefore, they are an important element of the overall software architecture. The definition of architecture mechanisms also enable decisions on whether existing software components can be leveraged to provide the required behavior; or whether new software should be bought or built.  The value in defining architecture mechanisms is that they:

  1. Explicitly call out aspects of the solution mechanics that are common across the system. This helps you plan.
  2. Put down markers for the developers to build those aspects of the system once and then re-use them. This reduces the workload.
  3. Promote the development of a consistent set of services. This makes the system easier to maintain.

An Architectural Mechanism can have three states: Analysis, Design and Implementation. These categories reflect the maturity of the mechanism's description. The state changes as successive levels of detail are uncovered during when you refine [Architecturally Significant Requirements](architecturally-significant-requirements.md) into working software. The categories are summarized in the table that follows. **States of an Architectural Mechanism** |  State  |  Description
---|---
Analysis  |  A conceptual solution to a common technical problem. For example, persistence is an abstract solution to the common requirement to store data. The purpose of this category is simply to identify the need for an Architectural Mechanism to be designed and implemented; and capture basic attributes for that mechanism.
Design  |  A refinement of an Analysis Mechanism into a concrete technology \(for example, RDBMS\). The purpose of this category is to guide precise product or technology selection.
Implementation  |  A further refinement from a design mechanism into a specification for the software. This can be presented as a design pattern or example code.


For more information on these different types of mechanisms, see the attached concepts.

Be aware that these states are frequently referred to themselves as Analysis, Design and Implementation mechanisms. These are synonyms and merely represent the architecture mechanisms in different states of development. The transition from one state to another can often be obvious or intuitive. Therefore, it can be achieved in a matter of seconds. It can also require more considered analysis and design, thus take longer. The important point here is that these categories of mechanisms apply to the same concept in different states. The only difference between them is one of refinement or detail.

The following diagram illustrates the transition of Architectural Mechanisms from one state to another.
**State Machine for Architectural Mechanisms**

![Architectural Mechanism States](../../../../images/arch_mech_states.jpg) [📄](../../../../images/descriptions/arch_mech_states.md "Image description")

###  What Information Should be Captured for Architectural Mechanisms?

The information captured for each architectural mechanism category/state is different \(though the information can be seen as refinements of each other\):
  * **Analysis Mechanisms** , which give the mechanism a name, brief description and some basic attributes derived from the project requirements
  * **Design Mechanisms** , which are more concrete and assume some details of the implementation environment
  * **Implementation Mechanisms** , which specify the exact implementation of each mechanism

When a mechanism is initially identified, it can be considered a marker that says to the team, "We are going to handle this aspect of the system in a standard way. We'll figure out the details later." As the project proceeds, the architectural mechanisms are gradually refined until they become part of the software.

####  Analysis Mechanisms

Analysis mechanisms are the initial state for an architectural mechanism. They are identified early in the project and represent bookmarks for future software development. They allow the team to focus on understanding the requirements without getting distracted by the specifics of a complex implementation. Analysis mechanisms are discovered by surveying the requirements and looking for recurrent technical concepts. Security, persistence and legacy interface are some examples of these. In effect, the analysis mechanism is where the requirements that describe architecturally significant topics are collated and brought together in a single list. This makes them easier to manage.

Analysis mechanisms are described in simple terms:
  * **Name:** Identifies the mechanism.
  * **Basic attributes:** Define the requirements of the mechanism. These attributes can vary depending upon the mechanism being analyzed. Refer to [Example: Architectural Mechanism Attributes](../examples/architectural-mechanism-attributes.md) for more guidance.

Once the list of analysis mechanisms has been defined it can be prioritized and the mechanisms refined in line with iteration objectives. It is not necessary to develop the entire set of architecture mechanisms into working software in a single pass. It is often more sensible to develop only those mechanisms required to support the functionality to be delivered in the current iteration.

####  Design Mechanisms

Design mechanisms represent decisions about the concrete technologies that are going to be used to develop architectural mechanisms. For example, the decision to use an RDBMS for persistence. It's often no more complicated than that \(though of course, the effort involved in making the decision can sometimes be quite complex\).

The decision on when to refine an architectural mechanism from an analysis state to a design state is largely arbitrary. Often there will be constraints on the project that force the decision on some of these issues. For example, there may be a corporate standard for databases which mean that the decision for the persistence mechanism can be made on day 1 of the project.

On other occasions the decision may point to products that the project team has not yet acquired. If so, the decision needs to be made in time to enable the required products to be made available to the team.

It can often be useful to develop some prototype code to prove that these decisions are sound. The architect should be confident that the technologies being selected are able to fulfill the requirements. The attributes captured against the corresponding analysis mechanisms should be used as criteria to prove the validity of the decisions.

####  Implementation Mechanism

An implementation mechanism specifies the actual implementation for the architectural mechanism \(hence the name\). It can be modeled as a design pattern or presented as example code.

The best time to produce the implementation mechanism is usually when the first piece of functionality that needs it is scheduled for development. Architects and developers work together to develop this.

For examples of the kinds of information that you might capture for a mechanism, see [Example: Architectural Mechanism Attributes](../examples/architectural-mechanism-attributes.md).

More Information

Concepts|
  * [Analysis Mechanism](analysis-mechanism.md)
  * [Architecturally Significant Requirements](architecturally-significant-requirements.md)
  * [Design Mechanism](design-mechanism.md)
  * [Implementation Mechanism](implementation-mechanism.md)
  * [Pattern](pattern.md)
---|---
Examples|
  * [Architectural Mechanism Attributes](../examples/architectural-mechanism-attributes.md)


Guidelines|
  * [Example: Design Mechanisms](../guidelines/example-design-mechanisms.md)
  * [Identify Common Architectural Mechanisms](../guidelines/identify-common-architectural-mechanisms.md)

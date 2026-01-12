---
title: Software Architecture
source_url: core.tech.common.extend_supp/guidances/concepts/software_architecture_59A08DE0.html
type: Concept
uma_name: software_architecture
page_guid: __O7tAMVvEduLYZUGfgZrkQ
keywords:
- architecture
- components
- software
related:
  workproducts:
  - architecture-notebook-6
  concepts:
  - design-2
  other:
  - executable-architecture
  - how-to-adopt-the-evolutionary-architecture-practice
---


 The software architecture represents the structure or structures of the system, which consists of software components, the externally visible properties of those components, and the relationships among them.
---

Relationships

Related Elements|
  * [Architecture Notebook](../../../../practice-technical/evolutionary_arch/workproducts/architecture-notebook-6.md)
  * [Design](../../../../practice-technical/evolutionary_design/guidances/concepts/design-2.md)
  * [Executable Architecture](executable-architecture.md)
  * [How to adopt the Evolutionary Architecture practice](../../../../practice-technical/evolutionary_arch/guidances/roadmaps/how-to-adopt-the-evolutionary-architecture-practice.md)
---|---

Main Description

###  Introduction

Software architecture is a concept that is easy to understand, and that most engineers intuitively feel, especially with a little experience, but it is hard to define precisely. In particular, it is difficult to draw a sharp line between design and architecture-architecture is one aspect of design that concentrates on some specific features.  In An Introduction to Software Architecture, David Garlan and Mary Shaw suggest that software architecture is a level of design concerned with issues: "Beyond the algorithms and data structures of the computation; designing and specifying the overall system structure emerges as a new kind of problem. Structural issues include gross organization and global control structure; protocols for communication, synchronization, and data access; assignment of functionality to design elements; physical distribution; composition of design elements; scaling and performance; and selection among design alternatives." [\[GAR93\]](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html) But there is more to architecture than just structure; the IEEE Working Group on Architecture defines it as "the highest-level concept of a system in its environment" [\[IEP1471\]](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html). It also encompasses the "fit" with system integrity, with economical constraints, with aesthetic concerns, and with style. It is not limited to an inward focus, but takes into consideration the system as a whole in its user environment and its development environment - an outward focus.  The architecture focuses on specific aspects of the overall system design, concentrating on structure, essential elements, key scenarios and those aspects that have a lasting impact on system qualities such as performance, reliability, adaptability and cost. It also defines the set of [Architectural Mechanism](architectural-mechanism.md)s, [Pattern](pattern.md)s and styles that will guide the rest of the design, assuring its integrity.

###  Purpose of Architecture

The architecture can be used for many things:
  * **To describe the essential structure of the system and the decisions guiding the structure of the system** so the integrity and understandability of the system is assured.
  * **To identify and attack risks to the system** \(using the architecture as an artifact of governance\)
  * **To provide context and guidance for developers** to construct the system by describing the motivations behind the architectural decisions so those decisions can be robustly implemented. The architecture services as the blueprint for development. For example, the architect may place constraints on how data is packaged and communicated between different parts of the system. This may appear to be a burden, but the justification in the Architecture Notebook can explain that there is a significant performance bottleneck when communicating with a legacy system. The rest of the system must adapt to this bottleneck by following a specific data packaging scheme.
  * **To provide an overview of the system to whoever must maintain the architecture** , as well as an understanding of the motivation behind the important technical decisions. Team members who were not involved in those architectural decisions need to understand the reasoning behind the context of the architecture so they can best address the needs of the system.
  * **To define the project structure and team organization.** Architectural elements make excellent units of implementation, unit testing, integration, configuration management and documentation. They can also be used to define so that managers can plan the project.

###  Architecture Description

To speak and reason about software architecture, you must first define an architectural representation, a way of describing important aspects of an architecture.  The following is some information that is worth capturing as part of the software architecture:
  * Architectural goals \(see [Concept: Architectural Goals](architectural-goals.md)\)
  * References to architecturally significant requirements and how the architecture addresses those requirements, including key scenarios that describe critical behavior of the system \(see [Concept: Architecturally Significant Requirements](architecturally-significant-requirements.md)\)
  * Constraints on the architecture and how the architecture addresses those constraints \(see [Concept: Architectural Constraints](architectural-constraints.md)\)
  * Key abstractions \(see [Concept: Key Abstractions](key-abstractions.md)\)
  * [Architectural Mechanism](architectural-mechanism.md) and where they should be applied \(see [Concept: Architectural Mechanism](architectural-mechanism.md)\).
  * Description of the partitioning approach, as well as a description of the key partitions. For example, Layering \(see [Guideline: Layering](../guidelines/layering.md)\)
  * Description of the deployment approach, as well as how key components are allocated to deployment nodes.
  * References to architecturally significant design elements \(see [Concept: Component](component.md)\)
  * Critical system interfaces \(see [Guideline: Representing Interfaces to External Systems](../guidelines/representing-interfaces-to-external-systems.md)\)
  * Assets that have been reused and/or assets that have been developed to be reused \(for more information, see [Guideline: Software Reuse](../guidelines/software-reuse.md)\)
  * Guidance, decisions, and constraints the developers must follow in building the system, along with justification

The architecture can contain any information and references that are appropriate in communicating how developers should build the system.

####  Architectural Representation

The architecture can be represented in many forms and from many viewpoints, depending on the needs of the project and the preferences of the project team. It need not be a formal document. The essence of the architecture can often be communicated through a series of simple diagrams on a whiteboard; or as a list of decisions. The illustration just needs to show the nature of the proposed solution, convey the governing ideas, and represent the major building blocks to make it easier to communicate the architecture to the project team and stakeholders.  If a more complex system is required, then the architecture can be represented as a more comprehensive set of views that describe the architecture from a number of viewpoints. For more information, see [Concept: Architectural Views and Viewpoints](architectural-views-and-viewpoints.md).  The architecture can be expressed as a simple metaphor or as a comparison to a predefined architectural style or set of styles. It may be a precise set of models or documents that describe the various aspects of the system's key elements. Expressing it as skeletal implementation is another option - although this may need to be baselined and preserved to ensure that the essence of the system can be understood as the system grows. Choose the medium that best meets the needs of the project.

###  Architectural Patterns

Architectural [Pattern](pattern.md)s are ready-made forms that solve recurring architectural problems. An architectural framework or an architectural infrastructure \(middleware\) is a set of components on which you can build a certain kind of architecture. Many of the major architectural difficulties should be resolved in the framework or in the infrastructure, usually targeted to a specific domain: command and control, MIS, control system, and so on.  [\[BUS96\]](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html) groups architectural patterns according to the characteristics of the systems in which they are most applicable, with one category dealing with more general structuring issues. The table shows the categories presented in [\[BUS96\]](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html) and the patterns they contain.  |  Category  |  Pattern
---|---
Structure  |  Layers
Pipes and Filters
Blackboard
Distributed Systems  |  Broker
Interactive Systems  |  Model-View-Controller
Presentation-Abstraction-Control
Adaptable Systems  |  Reflection
Microkernel


Refer to [\[BUS96\]](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html) for a complete description of these patterns.

###  Architectural Style

A software architecture \(or an architectural view\) may have an attribute called **architectural style** , which reduces the set of possible forms to choose from, and imposes a certain degree of uniformity to the architecture. The style may be defined by a set of patterns, or by the choice of specific components or connectors as the basic building blocks.

###  Architectural Timing

Teams should expect to spend more time on architectural issues early in the project. This allows the team to reduce risk associated to technology early in the project, hence allowing the team to more rapidly reduce the variance in their estimate on what they can deliver at what time. Examples of architectural issues that needs to be resolved early on include the following:
  * Component and their major interfaces.
  * Major technology choices \(platform, languages, architecture frameworks / reference architectures, etc.\).
  * Interfaces to external systems.
  * Common services \(persistence mechanisms, logging mechanisms, garbage collection, etc.\).
  * Key patterns.

###  Validating the Architecture

The best way to validate the architecture is to actually implement it. For more information, see [Executable Architecture](executable-architecture.md).

More Information

Concepts|
  * [Architectural Constraints](architectural-constraints.md)
  * [Architectural Goals](architectural-goals.md)
  * [Architecturally Significant Requirements](architecturally-significant-requirements.md)
  * [Architectural Mechanism](architectural-mechanism.md)
  * [Architectural Views and Viewpoints](architectural-views-and-viewpoints.md)
  * [Component](component.md)
  * [Executable Architecture](executable-architecture.md)
  * [Key Abstractions](key-abstractions.md)
  * [Pattern](pattern.md)
---|---
Guidelines|
  * [Layering](../guidelines/layering.md)
  * [Representing Interfaces to External Systems](../guidelines/representing-interfaces-to-external-systems.md)
  * [Software Reuse](../guidelines/software-reuse.md)

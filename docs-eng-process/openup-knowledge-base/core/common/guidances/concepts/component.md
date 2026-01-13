---
title: Component
source_url: core.tech.common.extend_supp/guidances/concepts/component_CB167D48.html
type: Concept
uma_name: component
page_guid: _0YP18MlgEdmt3adZL5Dmdw
keywords:
- component
related:
  guidelines:
  - abstract-away-complexity
  - representing-interfaces-to-external-systems
  checklists:
  - architecture-notebook-7
  tasks:
  - refine-the-architecture-1
  other:
  - software-architecture
---


 This concept describes components as they are applied within this process.
---

Relationships

Related Elements|
  * [Abstract Away Complexity](../guidelines/abstract-away-complexity.md)
  * [Architecture Notebook](../../../../practice-technical/evolutionary_arch/guidances/checklists/architecture-notebook-7.md)
  * [Refine the Architecture](../../../../practice-technical/evolutionary_arch/tasks/refine-the-architecture-1.md)
  * [Representing Interfaces to External Systems](../guidelines/representing-interfaces-to-external-systems.md)
  * [Software Architecture](software-architecture.md)
---|---

Main Description

The software industry and literature use the term **componen** t to refer to many different things. It is often used in the broad sense to mean a constituent part. It is also frequently used in a narrow sense to denote specific characteristics that enable replacement and assembly in larger systems.  The Unified Modeling Language \[[UML05](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html)\] defines _component_ as follows:

> > A modular part of a system that encapsulates its contents and whose manifestation is replaceable within its environment. A component defines its behavior in terms of provided and required interfaces. As such, a component serves as a type, whose conformance is defined by these provided and required interfaces \(encompassing both their static as well as dynamic semantics\).  A _component_ is defined as a subtype of structured class. Therefore, a component has attributes and operations, is able to participate in associations and generalizations, and has internal structure and ports.

Here, we use the term _component_ in a broader way than the UML definition. Rather than defining components as having characteristics, such as modularity, deployability, and replaceability, we instead recommend these as desirable characteristics of components. We use _component_ to mean **an encapsulated part of a system** that is nontrivial, nearly independent, and replaceable part of a system that fulfills a clear function in the context of well-defined architecture. This includes two types of components:
  * **Design component.** A significant encapsulated part of the design that includes design subsystems and, sometimes, significant design classes and design packages.
  * **Implementation component.** A significant encapsulated part of the implementation, generally code that implements a design component.

Ideally, the design reflects the implementation; therefore, you can simply refer to _components_ , with each component having a design and an implementation.  Components interact through interfaces and may be composed of successively smaller components and interfaces.

###  Component replaceability

In UML terminology, components should be replaceable. However, this may mean only that the component exposes a set of interfaces that hide an underlying implementation.  There are other, stronger, kinds of replaceability: .
  * **Source file replaceability:** If two classes are implemented in a single source code file, then those classes cannot usually be separately versioned and controlled. However, if a set of files fully implements a single component \(and no other component\), then the component source files are replaceable. This characteristic makes it easier to use version control, to use the file as a baseline, and to reuse the source file.
  * **Deployment replaceability:** If two classes are deployed in a single executable file, then each class is not independently replaceable in a deployed system. It is desirable for larger-granularity components to be replaceable during deployment, which allows new versions of the component to be deployed without having to rebuild the other components. This usually means that there is one file or one set of files that deploy the component, and no other component.
  * **Run-time replaceability:** If a component can be redeployed into a running system, then it is referred to as _run-time replaceable_. This enables you to upgrade software without loss of availability.
  * **Location transparency:** Components with network-addressable interfaces are referred to as having _location transparency_. This allows components to be relocated to other servers or to be replicated on multiple servers to support fault tolerance, load balancing, and so on. These kinds of components are often referred to as _distributed_ or _distributable_ components.

###  Component instantiation

A component may or may not be directly instantiated at run time.  An indirectly instantiated component is implemented, or realized, by a set of classes, subcomponents, or parts. The component itself does not appear in the implementation; it merely serves as a design that an implementation must follow. The set of realizing classes, subcomponents, or parts must cover the entire set of operations specified in the provided interface of the component. The manner of implementing the component is the responsibility of the implementer.  A directly instantiated component specifies its own encapsulated implementation. It is instantiated as an addressable object, which means that a design component has a corresponding construct in the implementation language; therefore, it can be referenced explicitly.

###  Modeling Components

The UML component is a modeling construct that provides the following capabilities:
  * Group classes to define a larger granularity part of a system
  * Separate the visible interfaces from internal implementation
  * Execute instances run-time

A component includes **provided** and **required** interfaces that form the basis for wiring components together. A **provided interface** is one that is either implemented directly by the component or one of its realizing classes or subcomponents, or it is the type of a provided port of the component. A **required interface** is designated by a usage dependency of the component or one of its realizing classes or subcomponents, or it is the type of a required port.  A component has an external view \(or _black box_ view\) through its publicly visible properties and operations .Optionally, a behavior such as a protocol state machine may be attached to an interface, a port, and the component itself to define the external view more precisely by making dynamic constraints in the sequence of operation calls explicit. The wiring between components in a system or other context can be structurally defined by using dependencies between component interfaces \(typically on component diagrams\).  Optionally, you can make a more detailed specification of the structural collaboration by using parts and connectors in composite structures to specify the role or instance-level collaboration between components. That is the component's internal view \(or _white-box_ view\) through its private properties and realizing classes or subcomponents. This view shows how the external behavior is realized internally. The mapping between external and internal views is by dependencies on components diagrams or delegation connectors to internal parts on composite structure diagrams.  A number of UML standard stereotypes exist that apply to components, including <<subsystem>> to model large-scale components, and <<specification>> and <<realization>> to model components with distinct specification and realization definitions, where one specification may have multiple realizations.  The recommendation is to use components as the representation for design subsystems.

###  UML Definitions -- A History

The definition of _component_ with the UML has changed over time with the release of different versions. The version of UML you use may be constrained by the capabilities of the modeling tools you use. That is why the definitions from 1.3 to 2.0 are provided here.  UML 2.0 defined _component_ as the following:

> > ...a modular part of a system that encapsulates its contents and whose manifestation is replaceable within its environment.  A component defines its behavior in terms of provided and required interfaces. As such, a component serves as a type whose conformance is defined by these provided and required interfaces \(encompassing both their static as well as dynamic semantics\).

UML 1.5 defined _component_ as the following:

> > A modular, deployable, and replaceable part of a system that encapsulates implementation and exposes a set of interfaces. A component is typically specified by one or more classes or subcomponents that reside on it and may be implemented by one or more artifacts \(e.g., binary, executable, or script files\).  In UML 1.3 and earlier versions of the UML, the component notation was used to represent files in the implementation. Files are no longer considered components by the latest UML definitions. However, many tools and UML profiles still use the component notation to represent files.
>
>
---

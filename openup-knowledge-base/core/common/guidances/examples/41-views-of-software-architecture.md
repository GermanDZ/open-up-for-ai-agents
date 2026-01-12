---
title: 4+1 Views of Software Architecture
source_url: core.tech.common.extend_supp/guidances/examples/four_plus_one_view_of_arch_9A93ACE5.html
type: Example
uma_name: four_plus_one_view_of_arch
page_guid: _4bC4cNs_EdyEW4klSH3vRA
keywords:
- architecture
- software
- views
related:
  concepts:
  - architectural-views-and-viewpoints
---


 This example describes a possible set of views for describing a software architecture.
---

Relationships

Related Elements|
  * [Architectural Views and Viewpoints](../concepts/architectural-views-and-viewpoints.md)
---|---

Main Description

You may want to consider the following views \(not all views are relevant to all systems or all the stakeholders\). This set of views is known as the 4+1 Views of Software Architecture \[[KRU95](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html)\].  ![4+1 Views of Software Architecture](../../../../images/4plus1_2.jpg) [📄](../../../../images/descriptions/4plus1_2.md "Image description")
  * **Use-case view** : Describes functionality of the system, its external interfaces, and its principal users. This view is mandatory when using the 4+1 Views, because all elements of the architecture should be derived from requirements.
  * **Logical view** : Describes how the system is structured in terms of units of implementation. The elements are packages, classes, and interfaces. The relationship between elements shows dependencies, interface realizations, part-whole relationships, and so forth. Note: This view is mandatory when using the 4+1 Views of Software Architecture.
  * **Implementation view** : Describes how development artifacts are organized in the file system. The elements are files and directories \(any configuration items\). This includes development artifacts and deployment artifacts. This view is optional when using the 4+1 Views.
  * **Process view** : Describes how the run-time system is structured as a set of elements that have run-time behavior and interactions. Run-time structure often bears little resemblance to the code structure. It consists of rapidly changing networks of communication objects. The elements are components that have run-time presence \(processes, threads, Enterprise JavaBeans™ \(EJB™\), servlets, DLLs, and so on\), data stores, and complex connectors, such as queues. Interaction between elements varies, based on technology. This view is useful for thinking about run-time system quality attributes, such as performance and reliability. This view is optional when using the 4+1 Views.
  * **Deployment view** : Describe how the system is mapped to the hardware. This view is optional when using the 4+1 Views.

In addition, you may wish to represent the following,
  * **Data view** : A specialization of the logical view. Use this view if persistence is a significant aspect of the system, and the translation from the design model to the data model is not done automatically by the persistence mechanism.
---

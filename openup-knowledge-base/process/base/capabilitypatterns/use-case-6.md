---
title: Use Case
source_url: process.openup.base/capabilitypatterns/use_case_666AFD9E.html
type: WorkProductDescriptor
uma_name: use_case
page_guid: _EOwqp9OLEdyqlogshP8l4g
keywords:
- case
- system
related:
  other:
  - use-case-model-7
---


 This artifact captures the system behavior to yield an observable result of value to those who interact with the system.
---

Purpose

Use cases are used for the following purposes:
  * To reach a common understanding of system behavior
  * To design elements that support the required behavior
  * To identify test cases
  * To plan and assess work
  * To write user documentation.
---

Relationships

Container Artifact|
  * [Use-Case Model](use-case-model-7.md)
---|---
Fulfilled Slots|
  * [\[Technical Specification\]](./../../process.openup.base/capabilitypatterns/technical_specification_slot_2BF7A564.html)


Roles| Responsible:
  * [Analyst](analyst-4.md)

| Modified By:
  * [Analyst](analyst-4.md)


Input To| Mandatory:
  * [Detail Use-Case Scenarios](detail-use-case-scenarios.md)
  * [Create Test Cases](create-test-cases.md)

| Optional:
  * [Detail System-Wide Requirements](detail-system-wide-requirements.md)
  * [Identify and Outline Requirements](identify-and-outline-requirements.md)

| External:
  * None


Output From|
  * [Detail Use-Case Scenarios](detail-use-case-scenarios.md)
  * [Identify and Outline Requirements](identify-and-outline-requirements.md)



Description

Brief Outline|  A use case typically includes the following information:
  * **Name:** The name of the use case
  * **Brief Description:** A brief description of the role and purpose of the use case
  * **Flow of Events:** A textual description of what the system does in regard to a use case scenario \(not how specific problems are solved by the system\). Write the description so that the customer can understand it. The flows can include a basic flow, alternative flows, and subflows.
  * **Key scenarios:** A textual description of the most important or frequently discussed scenarios
  * **Special Requirements:** A textual description that collects all of the requirements of the use case that are not considered in the use-case model, but that must be taken care of during design or implementation \(for example, non-functional requirements\)
  * **Preconditions:** A textual description that defines a constraint on the system when the use case starts
  * **Post-conditions:** A textual description that defines a constraint on the system when the use case ends
  * **Extension points:** A list of locations within the flow of events of the use case at which additional behavior can be inserted by using the extend-relationship
---|---

Properties

Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Planned| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

Illustrations

Templates|
  * [Use-Case Specification](../../../core/common/guidances/templates/use-case-specification-1.md)
---|---
Examples|
  * [Use-Case Specification](../../../core/common/guidances/examples/use-case-specification.md)



Tailoring

Impact of not having| Without this artifact, it might be unclear which functionality the solution needs to support.
---|---
Reasons for not needing| You might not need to use a use case if your project uses alternative requirements practices \(for example, "The system shall..." statements\).

Representation Options|  You can document the use case as a use-case specification document or you can incorporate the use case in a use-case model. You can also use a requirements management tool to capture use cases and parts of use cases.

More Information

Checklists|
  * [Use Case](../../../core/common/guidances/checklists/use-case-1.md)
---|---
Concepts|
  * [Use Case](../../../core/common/guidances/concepts/use-case-2.md)

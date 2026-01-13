---
title: Identify and Outline Requirements
source_url: process.openup.base/capabilitypatterns/identify_and_outline_requirements_FF8708A2.html
type: TaskDescriptor
uma_name: identify_and_outline_requirements
page_guid: _EOm5oNOLEdyqlogshP8l4g
keywords:
- identify
- outline
- requirements
related:
  other:
  - analyst-4
  - architect-4
  - developer-9
  - stakeholder
  - tester
---


 This task describes how to identify and outline the requirements for the system so that the scope of work can be determined.
---

Purpose

The purpose of this task is to identify and capture functional and non-functional requirements for the system. These requirements form the basis of communication and agreement between the stakeholders and the development team on what the system must do to satisfy stakeholder needs. The goal is to understand the requirements at a high-level so that the initial scope of work can be determined. Further analysis will be performed to detail these requirements prior to implementation.
---

Relationships

Roles| Primary:
  * [Analyst](analyst-4.md)

| Additional:
  * [Architect](architect-4.md)
  * [Developer](developer-9.md)
  * [Stakeholder](stakeholder.md)
  * [Tester](tester.md)

| Assisting:
---|---|---|---
Inputs| Mandatory:
  * None

| Optional:
  * [\[Technical Specification\]](./../../process.openup.base/capabilitypatterns/technical_specification_slot_2BF7A564.html)

| External:
  * None


Outputs|
  * [Glossary](glossary-6.md)
  * [System-Wide Requirements](system-wide-requirements-2.md)
  * [Use Case](use-case-6.md)
  * [Use-Case Model](use-case-model-7.md)
  * [Work Items List](work-items-list-2.md)



Steps

Gather information |  Use various techniques to make gathering requirements easier. Face-to-face meetings with stakeholders is the most effective way to understand stakeholder needs and to gather and validate requirements, but you must prepare in order for these meetings to run efficiently.  Be prepared by gathering and reviewing information related to the problem domain, problem statement, business environment and key stakeholders. Most of this information must be available in the vision. Also review the existing requirements repository for stakeholder requests.
---

Identify and capture domain terms

If there are ambiguous or domain-specific terms that need to be clearly defined, make sure you work closely with stakeholders to capture these terms in the glossary and that you use these terms consistently.
---

Identify the types of requirements relevant to your system

Requirements can be broadly classified as either functional or non-functional requirements. The former specify what the system must do. The latter specify constraints on the solution such as usability, reliability, performance, supportability, interfaces with legacy systems, etc. Depending upon the domain there might be regulatory requirements that apply.  Collaborate with stakeholders to identify the types of requirements relevant to your system. This will help you assess the completeness of your requirement set.
---

Identify and capture use cases and scenarios

Collaborate with stakeholders to identify and capture the use cases and scenarios relevant to your system. Capture references to these requirements with other project to-do items in the [Work Items List](../../../core/common/workproducts/work-items-list-6.md) so that you can prioritize the work.  See [Identify and Outline Actors and Use Cases](../../../practice-technical/use_case_driven_dev/guidances/guidelines/identify-and-outline-actors-and-use-cases.md) for more information.
---

Identify and capture system-wide requirements

Collaborate with stakeholders to identify and capture the system-wide requirements relevant to your system. Capture references to these requirements with other project to-do items in the [Work Items List](../../../core/common/workproducts/work-items-list-6.md) so that you can prioritize the work.  See [Developing System-Wide Requirements Specification](../../../practice-technical/use_case_driven_dev/guidances/guidelines/developing-system-wide-requirements-specification.md) for more information.
---

Achieve concurrence

Conduct a review of the requirements with relevant stakeholders and the development team to ensure consistency with the agreed vision, assess quality, and identify any required changes.
---

Identify and capture Use Cases and Actors in a Use-Case Model

Find and define the line that divides the solution and the real world that surrounds the solution. Collaborate with the project manager and architect, because decisions concerning system boundaries will have a major impact on cost, schedule and system architecture.  Collaborate with stakeholders to identify interfaces, as well as input and output information exchanged with users, machines, or systems. Identify and capture the [Actor](../../../core/common/guidances/concepts/actor.md)s and [Use Case](../../../core/common/workproducts/use-case.md)s in the [Use-Case Model](../../../core/common/workproducts/use-case-model.md). See [Guideline: Identify and Outline Actors and Use Cases](../../../practice-technical/use_case_driven_dev/guidances/guidelines/identify-and-outline-actors-and-use-cases.md) for more information.
---

Properties

Multiple Occurrences| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Event Driven| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Ongoing| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Planned| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Repeatable| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

More Information

Concepts|
  * [Requirements](../../../core/common/guidances/concepts/requirements.md)
  * [System-Wide Requirements](../../../core/common/guidances/concepts/system-wide-requirements-1.md)
---|---
Guidelines|
  * [Developing System-Wide Requirements Specification](../../../practice-technical/use_case_driven_dev/guidances/guidelines/developing-system-wide-requirements-specification.md)
  * [Effective Requirement Reviews](../../../core/common/guidances/guidelines/effective-requirement-reviews.md)
  * [Identify and Outline Actors and Use Cases](../../../practice-technical/use_case_driven_dev/guidances/guidelines/identify-and-outline-actors-and-use-cases.md)
  * [Requirements Gathering Techniques](../../../core/common/guidances/guidelines/requirements-gathering-techniques.md)

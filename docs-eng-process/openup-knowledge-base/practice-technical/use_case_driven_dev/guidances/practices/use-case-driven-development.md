---
title: Use Case Driven Development
source_url: practice.tech.use_case_driven_dev.base/guidances/practices/use_case_driven_dev_practice_64D20777.html
type: Practice
uma_name: use_case_driven_dev_practice
page_guid: _w1JD4B4jEd2bS8fFOQ7WWA
keywords:
- case
- cases
- development
- driven
- requirements
related:
  other:
  - how-to-adopt-the-use-case-driven-development-practice
  concepts:
  - requirements
  - use-case-2
  - actor
  - use-case-model-2
  workproducts:
  - use-case
  - use-case-model
  - system-wide-requirements
  tasks:
  - identify-and-outline-requirements-1
  - detail-use-case-scenarios-1
  - detail-system-wide-requirements-1
  guidelines:
  - detail-use-cases-and-scenarios
  - identify-and-outline-actors-and-use-cases
  - developing-system-wide-requirements-specification
  - use-cases-realizations
---


 This practice describes how to capture requirements with a combination of use cases and system-wide requirements, and then drive development and testing from those use cases.
---

Relationships

Content References|
  * [How to Adopt the Use-Case Driven Development Practice](../roadmaps/how-to-adopt-the-use-case-driven-development-practice.md)
  * Key Concepts
    * [Requirements](../../../../core/common/guidances/concepts/requirements.md)
    * [Use Case](../../../../core/common/guidances/concepts/use-case-2.md)
    * [Actor](../../../../core/common/guidances/concepts/actor.md)
    * [Use-Case Model](../../../../core/common/guidances/concepts/use-case-model-2.md)
  * Work Products
    * [Use Case](../../../../core/common/workproducts/use-case.md)
    * [Use-Case Model](../../../../core/common/workproducts/use-case-model.md)
    * [System-Wide Requirements](../../../../core/common/workproducts/system-wide-requirements.md)
  * Tasks
    * [Identify and Outline Requirements](../../tasks/identify-and-outline-requirements-1.md)
    * [Detail Use-Case Scenarios](../../tasks/detail-use-case-scenarios-1.md)
    * [Detail System-Wide Requirements](../../tasks/detail-system-wide-requirements-1.md)
  * Guidance
    * Guidelines
      * [Detail Use Cases and Scenarios](../guidelines/detail-use-cases-and-scenarios.md)
      * [Identify and Outline Actors and Use Cases](../guidelines/identify-and-outline-actors-and-use-cases.md)
      * [Developing System-Wide Requirements Specification](../guidelines/developing-system-wide-requirements-specification.md)
      * [Use-Cases Realizations](../guidelines/use-cases-realizations.md)
---|---
Inputs|
  * [\[Technical Specification\]](./../../../core.tech.slot.base/workproducts/technical_specification_slot_2812F7EF.html)



Purpose

Many organizations document requirements as a list of declarative statements \(or "shall" statements\) that lead the team to focus on developing atomic functions and fine-grained assertions of need. Moreover, applications developed from such requirements are often difficult to use and require more time for integration and testing than applications developed using user-focused requirements.  A second, more serious organizational anti-pattern is no focus on requirements at all. Many organizations simply fail to document requirements, leaving it to developers to discern from a perhaps vague vision document, or even nothing more than a meeting or conversation, what the application or system to be developed must do.  This practice shows how to avoid these pitfalls by using use cases and scenarios to capture functional requirements. That approach provides development scenarios that clearly express behavior \(or the interaction between users and the system under development\). Use cases categorize valuable and useful end-to-end, testable and collaborative behavior in which the system is involved. Non-functional requirements \(such as performance, stability, usability, and so on\) can still be captured using traditional techniques. This practice also explains how use cases and scenarios are best developed in conjunction with \(and used to drive\) other development activities, including design and testing.
---

How to read this practice

The best way to review a practice is to familiarize yourself with the enablement materials, and then review key concepts, work products, tasks, and the more detailed guidance, either by reviewing the guidance category directly, or by navigating from tasks and work products to their related guidance.  You might first want to become familiar with general requirements concepts:
  * [Requirements](../../../../core/common/guidances/concepts/requirements.md)

Then become familiar with use cases:
  * [Use Case](../../../../core/common/guidances/concepts/use-case-2.md)
  * [Actor](../../../../core/common/guidances/concepts/actor.md)
  * [Use-Case Model](../../../../core/common/guidances/concepts/use-case-model-2.md)

This practice focuses on the following work products:
  * [Use Case](../../../../core/common/workproducts/use-case.md)
  * [System-Wide Requirements](../../../../core/common/workproducts/system-wide-requirements.md)

Both work products go through similar states: they are identified and outlined, which allows them to be prioritized, and then detailed. However, in general, a use case is detailed a scenario at a time. This is particularly important when following an iterative approach, where a scenario is detailed "just in time" to be implemented, as opposed to the approach of detailing all or most requirements up front.  Be also familiar with the tasks that drive the states above. In addition, guidelines and tool mentors associated with each task provide details of how to perform the task. Templates and checklists associated with the work products guide you in their completion and evaluation.  Measurements can guide you on assessing how well you are following this practice.
---

Additional Information

###  Books and Articles


|  Kurt Bittner and Ian Spence 2003. _Use Case Modeling._ Addison Wesley Longman.
---
|  Comprehensive coverage of use case techniques and practices, including useful examples showing how use-case specifications evolve over time.
Alistair Cockburn 2001. _Writing Effective Use Cases._ Addison Wesley Longman.
|  Excellent guidance for those who need to write use cases. Multiple styles and techniques contrasted with insight in an unbiased way. Many helpful tips to improve your use cases.

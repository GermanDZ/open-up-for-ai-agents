---
title: Use Case
source_url: core.tech.common.extend_supp/workproducts/use_case_22BE66E2.html
type: Artifact
uma_name: use_case
page_guid: _0VGbUMlgEdmt3adZL5Dmdw
keywords:
- case
- system
---

 This artifact captures the system behavior to yield an observable result of value to those who interact with the system.
---
Domains: [Requirements](../../cat/domains/requirements-1.md)

Purpose

Use cases are used for the following purposes:
  * To reach a common understanding of system behavior
  * To design elements that support the required behavior
  * To identify test cases
  * To plan and assess work
  * To write user documentation.
---

Relationships

Fulfilled Slots|
  * [\[Technical Specification\]](./../../core.tech.slot.base/workproducts/technical_specification_slot_2812F7EF.html)
---|---
Container Artifact|
  * [Use-Case Model](use-case-model.md)


Roles| Responsible:
  * [Analyst](../../role/roles/analyst-6.md)

| Modified By:
  * [Analyst](../../role/roles/analyst-6.md)


Tasks| Input To:
  * [Detail Use-Case Scenarios](../../../practice-technical/use_case_driven_dev/tasks/detail-use-case-scenarios-1.md)
  * [Detail System-Wide Requirements](../../../practice-technical/use_case_driven_dev/tasks/detail-system-wide-requirements-1.md)
  * [Create Test Cases](../../../practice-technical/concurrent_testing/tasks/create-test-cases-1.md)
  * [Design the Solution](../../../practice-technical/evolutionary_design/tasks/design-the-solution.md)
  * [Envision the Architecture](../../../practice-technical/evolutionary_arch/tasks/envision-the-architecture-1.md)
  * [Implement Solution](../../../practice-technical/test_driven_development/tasks/implement-solution-1.md)
  * [Plan Project](../../../practice-management/release_planning/tasks/plan-project-1.md)
  * [Refine the Architecture](../../../practice-technical/evolutionary_arch/tasks/refine-the-architecture-1.md)
  * [Assess Results](../../../practice-management/iterative_dev/tasks/assess-results-1.md)
  * [Identify and Outline Requirements](../../../practice-technical/use_case_driven_dev/tasks/identify-and-outline-requirements-1.md)
  * [Plan Iteration](../../../practice-management/iterative_dev/tasks/plan-iteration-1.md)

| Output From:
  * [Detail Use-Case Scenarios](../../../practice-technical/use_case_driven_dev/tasks/detail-use-case-scenarios-1.md)
  * [Identify and Outline Requirements](../../../practice-technical/use_case_driven_dev/tasks/identify-and-outline-requirements-1.md)



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

Illustrations

Templates|
  * [Use-Case Specification](../guidances/templates/use-case-specification-1.md)
---|---
Examples|
  * [Use-Case Specification](../guidances/examples/use-case-specification.md)



Tailoring

Impact of not having| Without this artifact, it might be unclear which functionality the solution needs to support.
---|---
Reasons for not needing| You might not need to use a use case if your project uses alternative requirements practices \(for example, "The system shall..." statements\).

Representation Options|  You can document the use case as a use-case specification document or you can incorporate the use case in a use-case model. You can also use a requirements management tool to capture use cases and parts of use cases.

More Information

Checklists|
  * [Use Case](../guidances/checklists/use-case-1.md)
---|---
Concepts|
  * [Use Case](../guidances/concepts/use-case-2.md)

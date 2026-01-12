---
title: System-Wide Requirements
source_url: core.tech.common.extend_supp/workproducts/system_wide_requirements_7D9DD47C.html
type: Artifact
uma_name: system_wide_requirements
page_guid: _BVh9cL-CEdqb7N6KIeDL8Q
keywords:
- captures
- requirements
- system
- wide
---

 This artifact captures the quality attributes and constraints that have system-wide scope. It also captures system-wide functional requirements.
---
Domains: [Requirements](../../cat/domains/requirements-1.md)

Purpose

This artifact is used for the following purposes:
  * To describe the quality attributes of the system, and the constraints that the design options must satisfy to deliver the business goals, objectives, or capabilities
  * To capture functional requirements that are not expressed as use cases
  * To negotiate between, and select from, competing design options
  * To assess the sizing, cost, and viability of the proposed system
  * To understand the service-level requirements for operational management of the solution
---

Relationships

Fulfilled Slots|
  * [\[Technical Specification\]](./../../core.tech.slot.base/workproducts/technical_specification_slot_2812F7EF.html)
---|---
Roles| Responsible:
  * [Analyst](../../role/roles/analyst-6.md)

| Modified By:
  * [Analyst](../../role/roles/analyst-6.md)


Tasks| Input To:
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
  * [Detail System-Wide Requirements](../../../practice-technical/use_case_driven_dev/tasks/detail-system-wide-requirements-1.md)
  * [Identify and Outline Requirements](../../../practice-technical/use_case_driven_dev/tasks/identify-and-outline-requirements-1.md)



Description

Brief Outline|  Organize system-wide requirements by a number of common themes or subcategories: the areas of performance and capacity, availability, usability, security and privacy, maintainability, manageability, and flexibility. See the supporting guidance for a description of the recommended categorization approach.  For each system-wide requirement, capture attributes such as the source and priority of the requirements, as described by the associated requirements management guidance.
---|---

Illustrations

Templates|
  * [System-Wide Requirements Specification](../guidances/templates/system-wide-requirements-specification.md)
---|---

Key Considerations
  * When you document system-wide requirements, ensure that the needs of all of the stakeholders are represented. In particular, include the needs of those who are responsible for maintaining or supporting the system after it is delivered.
  * Typically, there are some overlaps and gray areas between system-wide requirements and other requirements work products. For example, the authorization behavior of a system can be specified as use cases or as statements within system-wide requirements. The overall driving need is that no important requirements are missed or duplicated, and that there is an agreed upon approach for capturing and processing every type of requirement.
  * System-wide requirements originate from many places. Documenting the source of the requirement is particularly important when you separate externally mandated requirements.
  * Requirements are often thought of as "Qualitative" \(specifying a quality or desirable characteristic\) versus "Quantitative" \(specifying a quantity\). Qualitative requirements can sometimes be elaborated into quantitative requirements.
  * A good quality requirement is one that you can verify, either through testing or some other objective evaluation.
  * You must evaluate system-wide requirements for cost, schedule impact, and level of contribution to business goals. Based on your evaluation, the system-wide requirements should be iteratively challenged, defended, and amended.
---

Tailoring

Impact of not having|  If you do not adequately manage and meet system-wide requirements, you risk delivering a system that might be unacceptable to stakeholders.
---|---
Reasons for not needing|  You do not need to use this artifact if none of the categories of system-wide requirements apply to the project under consideration.
Representation Options| This artifact represents the influences on the design and delivery of a system, which cover a broad range of themes. Document the requirements for each theme under separate headings within a document or under appropriate category identifiers in a requirements gathering tool. Give categories easy-to-recognize identifiers, so individual requirements can be readily associated with the appropriate category. The format of requirements vary from category to category; some are heavily textual, and others are more structured and quantitative.

More Information

Guidelines|
  * [Writing Requirements Statements](../guidances/guidelines/writing-requirements-statements.md)
---|---

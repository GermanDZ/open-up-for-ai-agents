---
title: System-Wide Requirements
source_url: process.openup.base/capabilitypatterns/system_wide_requirements_D158548E.html
type: WorkProductDescriptor
uma_name: system_wide_requirements
page_guid: _Nx344UVEEeK93ZZqiMLBsA
keywords:
- captures
- requirements
- system
- wide
---

 This artifact captures the quality attributes and constraints that have system-wide scope. It also captures system-wide functional requirements.
---

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
  * [\[Technical Specification\]](./../../process.openup.base/capabilitypatterns/technical_specification_slot_194926F3.html)
---|---
Roles| Responsible:
  * [Analyst](analyst-2.md)

| Modified By:
Input To| Mandatory:
  * [Plan Project](plan-project.md)

| Optional:
  * None

| External:
  * None



Description

Brief Outline|  Organize system-wide requirements by a number of common themes or subcategories: the areas of performance and capacity, availability, usability, security and privacy, maintainability, manageability, and flexibility. See the supporting guidance for a description of the recommended categorization approach.  For each system-wide requirement, capture attributes such as the source and priority of the requirements, as described by the associated requirements management guidance.
---|---

Properties

Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Planned| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

Illustrations

Templates|
  * [System-Wide Requirements Specification](../../../core/common/guidances/templates/system-wide-requirements-specification.md)
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
  * [Writing Requirements Statements](../../../core/common/guidances/guidelines/writing-requirements-statements.md)
---|---

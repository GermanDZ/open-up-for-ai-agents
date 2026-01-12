---
title: Effective Requirement Reviews
source_url: core.tech.common.extend_supp/guidances/guidelines/effective_req_reviews_5913D369.html
type: Guideline
uma_name: effective_req_reviews
page_guid: _E-dPIL-GEdqb7N6KIeDL8Q
keywords:
- effective
- requirement
- reviews
related:
  tasks:
  - detail-system-wide-requirements-1
  - detail-use-case-scenarios-1
  - develop-technical-vision-1
  - identify-and-outline-requirements-1
---


 This guideline discusses how to conduct reviews with relevant stakeholders to ensure agreement, assess quality, and identify changes required.
---

Relationships

Related Elements|
  * [Detail System-Wide Requirements](../../../../practice-technical/use_case_driven_dev/tasks/detail-system-wide-requirements-1.md)
  * [Detail Use-Case Scenarios](../../../../practice-technical/use_case_driven_dev/tasks/detail-use-case-scenarios-1.md)
  * [Develop Technical Vision](../../../../practice-technical/shared_vision/tasks/develop-technical-vision-1.md)
  * [Identify and Outline Requirements](../../../../practice-technical/use_case_driven_dev/tasks/identify-and-outline-requirements-1.md)
---|---

Main Description

The cost of correcting errors increases exponentially throughout the development lifecycle [\[BOE88\]](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html). Therefore, it is important to discover problems early enough to solve them quickly and inexpensively.  Requirements reviews are intended to discover problems with the [Requirements](../concepts/requirements.md) before you spend significant time and work in implementing the wrong thing. This is not to say that you must have a complete set of requirements before implementation, but be sure to review, internally and with stakeholders, those that are selected for implementation in the early iterations and those that will have a broad impact on the system \(often called [Architecturally Significant Requirements](../concepts/architecturally-significant-requirements.md)\) to ensure everyone's concurrence before investing significant effort in implementation.

###  Informal reviews

Requirements reviews can be informal, such as simply showing draft requirements to your colleagues or demonstrating a prototype.  These informal reviews are excellent for getting the structure of the requirements correct and removing obvious mistakes. By keeping the review team small, it is easier to make rapid progress. However, informal reviews can miss important perspectives of critical stakeholders.

###  Formal reviews

Requirement reviews can be formal meetings. Start with careful preparation, so that you receive and organize comments before the meeting. The meeting itself should produce decisions on all review items. After the meeting, you must pursue the review actions to completion. If these actions involve a substantial amount of work or require a change to an artifact that is under configuration control, consider submitting change requests to prioritize and track the work.  Formal reviews are more wide-ranging and expensive. They provide for more balanced reviews from multiple perspectives. However, formal reviews involve more people, which makes them more difficult to coordinate \(thus the need for formality\) and expensive in terms of work hours.

###  Two-tier reviews

One technique to get the best of both worlds is to use staged, or "two-tier", reviews [\[ADO03\]](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html). The first tier is informal and performed by a smaller team, possibly many times. The second tier is more formal and performed by the complete group, perhaps only once.  **First-tier review:** The authors of the requirements and the development team review the requirements during the first-tier reviews to ensure that they are unambiguous, complete, correct and consistent. It is important to include testers and developers to ensure that the requirements are verifiable and feasible. These reviews determine whether the requirements are ready for the larger community to review. First-tier reviews may be informal, formal, or a combination of the two.  **Second-tier review:** Involve the larger group during the higher-tier review to get more minds working on the problem and to achieve concurrence that the requirements are suitable for implementation and validation.  At both stages, the checklists for the requirements work products are helpful.  Tiered reviews offer several benefits:

  1. Eliminate the noise caused by minor edits during the first-tier reviews, allowing subsequent reviews to focus on functionality
  2. Provide a professional look to the requirements, presenting both the requirements and their authors in the best possible light
  3. Safeguard the time of stakeholders who are reviewing the requirements, thus preventing "review burnout", or diminished effectiveness from overload and stress
  4. Provide the best opportunity for full, effective reviews.

###  Golden rules of reviewing

Follow these golden rules of reviewing [\[TEL06\]](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html):

  1. **Encourage criticism:** Remember that people are improving the requirements, not criticizing you. Even the harshest criticism often contains a grain of truth. Adopt the attitude that every suggestion is a gift.
  2. **Choose your best reviewers:** A few specific people make the best reviewers, time and again. Cultivate them.
  3. **Allow adequate time:** It's not over until you have agreed upon and made the corrections.
---

More Information

Checklists|
  * [General Requirements](../checklists/general-requirements.md)
---|---
Concepts|
  * [Architecturally Significant Requirements](../concepts/architecturally-significant-requirements.md)
  * [Requirements](../concepts/requirements.md)

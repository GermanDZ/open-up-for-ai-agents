---
title: Work Items List
source_url: process.openup.base/capabilitypatterns/work_items_list_83E5C39.html
type: WorkProductDescriptor
uma_name: work_items_list
page_guid: _N7r8MUVEEeK93ZZqiMLBsA
keywords:
- item
- items
- list
- within
- work
related:
  other:
  - project-manager-2
---


 This artifact contains a list of all of the scheduled work to be done within the project, as well as proposed work that may affect the product in this or future projects. Each work item may contain references to information relevant to carry out the work described within the work item.
---

Purpose

To collect all requests for work that will potentially be taken on within the project, so that work can be prioritized, effort estimated, and progress tracked.
---

Relationships

Roles| Responsible:
  * [Project Manager](project-manager-2.md)

| Modified By:
---|---|---

Description

Main Description|  This artifact provides a focal point for the entire team:
  * It provides one list containing all requests for additional capabilities or enhancement for that application. Note that some of these requests may never be implemented, or be implemented in later projects.
  * It provides one list of all the work to be prioritized, estimated, and assigned within the project. The risk list is prioritized separately.
  * It provides one place to go to for the development team to understand what micro-increments need to be delivered, get references to material required to carry out the work, and report progress made.

These are the typical work items that go on this list:
  * Use cases \(and references to use-case specifications\)
  * System-wide requirements
  * Changes and enhancement requests
  * Defects
  * Development tasks

Work items can be very large in scope, especially when capturing requests for enhancements, such as "Support Financial Planning" for a personal finance application. To allow the application to be developed in micro-increments, work items are analyzed and broken down into smaller work items so that they can be assigned to an iteration, such as a use-case scenario for "Calculate Net Worth". Further breakdown may be required to identify suitable tasks to be assigned to developers, such as "Develop UI for Calculate Net Worth". This means that work items often have parent/child relationships, where the lowest level is a specification and tracking device for micro-increments.
---|---
Brief Outline|  This artifact should consist of the following information for each work item:
  * Name and Description
  * Priority
  * Size Estimate
  * State
  * References

Assigned work items should also contain the following:
  * Target Iteration or Completion Date
  * Assignee
  * Estimated Effort Remaining
  * Hours Worked



Properties

Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Planned| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

Illustrations

Templates|
  * [Work Items List](../../../core/common/guidances/templates/work-items-list-9.md)
---|---
Examples|
  * [Work Items List](../../../core/common/guidances/examples/work-items-list-8.md)



Key Considerations

Work Items should contain estimates. See guidelines on managing work items and agile estimation.
---

Tailoring

Impact of not having| Without this artifact, there is not a single place that provides a list of all of the work to be done and its current status. Individual team members may also be unclear as to what work has been assigned to them.
---|---
Reasons for not needing| This artifact may not be needed if the work assignments are going to be managed using a different technique or artifact.
Representation Options|  The recommended representation for the work items list is to capture it as a separate artifact, represented by a spreadsheet or database table. See [Example: Work Items List](../../../core/common/guidances/examples/work-items-list-8.md).  Alternatively, the work items list may be captured in tools such as project management, requirements management, or change request. In fact, the work items list may be spread over several tools, as you may choose to keep different types of work items in different repositories to take advantage of features in those tools. For example, you could use a requirements composition or management tool to track information about requirements, and use another tool to capture defects. Work items may start in one representation \(such as in a spreadsheet\) and move to more sophisticated tools over time, as the number of work items and the metrics you wish to gather grows more sophisticated.

###  As part of the Iteration Plan

The [Iteration Plan](../../../practice-management/iterative_dev/workproducts/iteration-plan-4.md) typically references work items that are assigned to that iteration. If the team is capturing the iteration plan on a whiteboard, for example, the team may choose to reference high-level work items in the Work Items List that are assigned to the iteration, and maintain low-level child work items used to track day-to-day work only in an iteration plan.

More Information

Checklists|
  * [Work Items List](../../../core/common/guidances/checklists/work-items-list-7.md)
---|---
Concepts|
  * [Micro-Increments](../../../practice-management/iterative_dev/guidances/concepts/micro-increments.md)


Guidelines|
  * [Agile Estimation](../../../core/common/guidances/guidelines/agile-estimation.md)
  * [Managing Work Items](../../../practice-management/iterative_dev/guidances/guidelines/managing-work-items.md)

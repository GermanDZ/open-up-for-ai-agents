---
title: Managing Work Items
source_url: practice.mgmt.iterative_dev.base/guidances/guidelines/managing_work_items_32AC6ABD.html
type: Guideline
uma_name: managing_work_items
page_guid: _7vEXEMA4EdqSgKaj2SZBmg
keywords:
- items
- managing
- work
related:
  workproducts:
  - work-items-list-6
---


 This guideline explains the lifecycle of work items and how the work items list is used.
---

Relationships

Related Elements|
  * [Work Items List](../../../../core/common/workproducts/work-items-list-6.md)
---|---

Main Description

###  Overview

The [Artifact: Work Items List](../../../../core/common/workproducts/work-items-list-6.md) captures all scheduled work to be done within the project, as well as proposed work that may affect the product. Some of the work items may be implemented in this project, some of them may be implemented in a future project, and some of them may never be implemented.  Some of the work items may still be poorly defined; therefore, it could represent a big chunk of work, requiring potentially several staff months of effort. As the priority of these work items increases, they are typically decomposed into smaller work items that represent specific and well-defined tasks that may take hours or days to address, see [Micro-Increments](../concepts/micro-increments.md). In other cases, specific and well-defined work items are created directly, representing, for example, a defect to be addressed, as Figure 1illustrates.  ****Figure 1. Work Items List provides one prioritized list of scheduled and proposed work**** **
![](../../../../images/work_item_prioritization_diagram.jpg) [📄](../../../../images/descriptions/work_item_prioritization_diagram.md "Image description")** A work item may represent work associated with a defect, enhancement request, change request, use case, scenario, user story, supporting requirement, stakeholder request, or anything else that captures a potential requirement or improvement to your system. A work item may reference any type of requirement or other useful information that guides you in what needs to be done.  A big advantage with the [Artifact: Work Items List](../../../../core/common/workproducts/work-items-list-6.md) is that it enables you to prioritize only one list containing all of the things that may need to be addressed, whether the work item represents work related to a requirement, enhancement, or defect. The one exception is that you should prioritize the risk list separately.  Nothing in the project will get done if it is not represented or mapped to a work item. This means that all requirements, defect reports, and change requests have to be mapped to a work item at some stage. Also, a developer will not take on work that is not represented in a work item. Only work items need to be prioritized. This also means that tracking work items is a primary means of understanding the status of the project.  There are two major types of work items:
  * **Unscheduled work items:** These work items have not yet been assigned to an iteration, and there is no detailed effort estimate for the work item yet.
  * **Scheduled work items:** These work items are assigned to an iteration, and they typically have an additional set of attributes filled in, such as detailed effort estimates.

###  Unscheduled work items

Most work items are initially unscheduled, meaning that it has not yet been decided whether to do them and when to do them. Unscheduled work items should always represent something meaningful to deliver to stakeholders, such as a scenario to be detailed, designed, implemented, and tested. You may consider capturing the following data for such work items:
  * Name
  * Description
  * Priority
  * Size estimate, such as a point estimate \(see [Guideline: Agile Estimation](../../../../core/common/guidances/guidelines/agile-estimation.md)\)
  * State, such as New, Assigned, Resolved, Verified, Closed \(see work items states section below\)
  * Links to other reference material, such as requirements or detailed specifications of what needs to be done

###  Scheduled work items

After a work item has been assigned to an iteration, it becomes _scheduled_. You assign work items only to the current or next iteration. There is no point in assigning work items to a specific future iteration, because you cannot predict what a meaningful schedule will be more than an iteration in advance \(see [Guideline: Iteration Planning](iteration-planning.md)\).  The following additional attributes are useful for Scheduled work items:
  * Target iteration
  * Responsible team member
  * Effort estimate left, such as actual hours of work \(see [Guideline: Agile Estimation](../../../../core/common/guidances/guidelines/agile-estimation.md)\)
  * Hours worked

This provides the information required to plan and manage an iteration. You can plan iterations by understanding effort involved, and you can manage iterations by tracking how much work is left to do \(see [Report: Iteration Burndown](../reports/iteration-burndown.md)\).

###  Work item states

The following states are useful for tracking work items:
  * **New:** The work item has been created, but not yet assigned to a team member.
  * **Assigned:** A team member has been identified as responsible for the work item.
  * **Resolved:** The team member responsible for the work items has implemented and tested the work item.
  * **Verified:** The work item has been independently tested.
  * **Closed:** The work item is no longer active.

You may choose another set of states, based on your needs.
---

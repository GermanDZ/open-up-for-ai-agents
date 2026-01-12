---
title: Assign Changes to an Iteration
source_url: core.mgmt.common.extend_supp/guidances/guidelines/assign_changes_to_iteration_67B3DEA2.html
type: Guideline
uma_name: assign_changes_to_iteration
page_guid: __yQQ4L6REdqti4GwqTkbsQ
keywords:
- assign
- changes
- current
- during
- iteration
related:
  tasks:
  - manage-iteration-1
  - plan-iteration-1
---


 This guideline promotes the best practice of isolating team members from disruptive changes during the current iteration. Change requests are reviewed and prioritized during the current iteration, but are not acted upon until assigned to a future iteration.
---

Relationships

Related Elements|
  * [Manage Iteration](../../../../practice-management/iterative_dev/tasks/manage-iteration-1.md)
  * [Plan Iteration](../../../../practice-management/iterative_dev/tasks/plan-iteration-1.md)
---|---

Main Description

Most iterative software development processes recommend that changes not be introduced during an iteration. The main idea is that the iterations should be short and with clearly defined scope so that they can be time-boxed.  To limit scope within an iteration, change requests are reviewed and prioritized as soon as possible, but are not assigned for implementation until a future iteration via the work items list.  Since iterations are relatively short this should not cause undue delay in dealing with urgent and important change requests.  One notable exception is a defect discovered during testing that prevents the team from meeting the objectives of the iteration. In this case it is reasonable to assign the work item to the current iteration as this does not represent a scope change, it represents unfinished work.  Consider the following when choosing the future iteration where the change request will be addressed:
  * Group similar change requests in the same iteration. For example multiple change requests focused on the same functionality or that are dependent on each other.
  * Assign change requests that mitigate high risks to the earliest iteration possible.
---

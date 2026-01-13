---
title: Plan Iteration
source_url: process.openup.base/capabilitypatterns/plan_iteration_B0421040.html
type: TaskDescriptor
uma_name: plan_iteration
page_guid: _y05RQNOJEdyqlogshP8l4g
keywords:
- iteration
- plan
related:
  other:
  - project-manager-1
  - analyst-5
  - architect-5
  - developer-3
  - stakeholder-3
  - tester-4
---


 Plan the scope and responsibilities for a single iteration.
---

Purpose

The purpose of this task is to identify the next increment of system capability, and create a fine-grained plan for achieving that capability within a single iteration.
---

Relationships

Roles| Primary:
  * [Project Manager](project-manager-1.md)

| Additional:
  * [Analyst](analyst-5.md)
  * [Architect](architect-5.md)
  * [Developer](developer-3.md)
  * [Stakeholder](stakeholder-3.md)
  * [Tester](tester-4.md)

| Assisting:
---|---|---|---
Inputs| Mandatory:
  * [Work Items List](work-items-list.md)

| Optional:
  * [\[Technical Architecture\]](./../../process.openup.base/capabilitypatterns/technical_architecture_slot_BF7C7753.html)
  * [\[Technical Specification\]](./../../process.openup.base/capabilitypatterns/technical_specification_slot_DDD377AB.html)
  * [Iteration Plan](iteration-plan-3.md)
  * [Risk List](risk-list.md)

| External:
  * None


Outputs|
  * [Iteration Plan](iteration-plan-3.md)
  * [Risk List](risk-list.md)
  * [Work Items List](work-items-list.md)



Main Description

During project planning, iterations are identified, but the estimates have an acceptable uncertainty due to the lack of detail at the project inception. This task is repeated for each iteration within a release. It allows the team to increase the accuracy of the estimates for one iteration, as more detail is known along the project.  Ensure that the team commits to a reasonable amount of work for the iteration, based on team performance from previous iterations.
---

Steps

Prioritize Work Items List | Prioritize the work items list before you plan the next iteration. Consider what has changed since the last iteration plan \(such as new change requests, shifting priorities of your stakeholders, or new risks that have been encountered\).
---

Define iteration objectives

Work with the team to refine the iteration objectives found in the project definition and scope, and document them in the iteration plan in order to provide high-level direction to what should be targeted for the iteration. The objectives should be driven based on stakeholder priorities, and will be revised as the iteration plan is finalized. Those objectives are usually defined as high-level capabilities or scenarios, which need to be implemented and tested during the iteration in order to deliver increased value to the customer.
---

Identify and review risks

Throughout the project, new assumptions and concerns may arise. Help the team identify and prioritize new risks as part of iteration planning, updating the risk list. Add risk responses to the work items list, influencing the work that is being planned for that iteration.
---

Commit work to the iteration

Work with the team, and especially the project stakeholders, to identify the high-priority work items from the work items list to be addressed. The high-level objectives provide guidance on what work items should be considered. The iteration plan from previous iteration should include an assessment of the results, and can also be used as input to the current iteration planning. The team reviews its velocity and determines the amount of work that can be done within the iteration. The team breaks down into tasks those work items that are assigned to the iteration, and estimates the effort to complete each task. Typical tasks range from half a day to two days in length, and are captured in the work items list. See [Guideline: Agile Estimation](../../../core/common/guidances/guidelines/agile-estimation.md) for more information.  When the team has decided to take on a work item, it will assign the work to one or several team members. Ideally, this is done by team members signing up to do the work, since this makes people motivated and committed to doing the job. However, based on your culture, you may instead assign the work to team members.
---

Define evaluation criteria

Each iteration should include testing as a part of the evaluation, as well as the test objectives and test cases that need to be detailed. Other evaluation criteria may include successful demonstrations to key stakeholders, or favorable usage by a small group of target users. Document evaluation criteria in the iteration plan.
---

Refine project definition and scope

Depending on the results of the previous iteration assessment, update the project definition work products as needed. Necessary changes can encompass the need to acquire new resources, to absorb an unplanned effort increase, or to implement a specific change request. If a change affects defined project milestones, consult with the stakeholders before committing to it.
---

Properties

Multiple Occurrences| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Event Driven| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Ongoing| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Planned|
Repeatable| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

More Information

Guidelines|
  * [\[Project Planning Guidance\]](./../../core.mgmt.slot.base/guidances/guidelines/project_planning_guidance_slot_DDA75689.html)
  * [Agile Estimation](../../../core/common/guidances/guidelines/agile-estimation.md)
  * [Assign Changes to an Iteration](../../../core/common/guidances/guidelines/assign-changes-to-an-iteration.md)
  * [Deploy the Solution](../../../core/common/guidances/guidelines/deploy-the-solution.md)
  * [Iteration Planning](../../../practice-management/iterative_dev/guidances/guidelines/iteration-planning.md)
  * [Managing Risks](../../../core/common/guidances/guidelines/managing-risks.md)
  * [Prioritizing Work Items](../../../practice-management/iterative_dev/guidances/guidelines/prioritizing-work-items.md)
---|---

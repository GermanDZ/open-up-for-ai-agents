---
title: Assess Results
source_url: process.openup.base/capabilitypatterns/assess_results_A8262B77.html
type: TaskDescriptor
uma_name: assess_results
page_guid: _0Qiv4NOJEdyqlogshP8l4g
keywords:
- assess
- results
related:
  other:
  - project-manager-1
  - analyst-5
  - architect-5
  - developer-3
  - stakeholder-3
  - tester-4
---


 Determine success or failure of the iteration. Apply the lessons learned to modify the project or improve the process.
---

Purpose

Demonstrate the value of the solution increment that was built during the iteration and apply the lessons learned to modify the project or improve the process.
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
  * [Iteration Plan](iteration-plan-3.md)
  * [Work Items List](work-items-list.md)

| Optional:
  * [\[Project Definition and Scope\]](./../../process.openup.base/capabilitypatterns/project_definition_and_scope_slot_ABFD6480.html)
  * [\[Technical Specification\]](./../../process.openup.base/capabilitypatterns/technical_specification_slot_DDD377AB.html)
  * [\[Technical Test Results\]](./../../process.openup.base/capabilitypatterns/technical_test_results_slot_CC6C8BC1.html)

| External:
  * None


Outputs|
  * [Iteration Plan](iteration-plan-3.md)
  * [Work Items List](work-items-list.md)



Main Description

Coordinate the assessment and discuss with the team how the iteration results will be best presented to stakeholders, so that they can learn as much about the solution as possible. Listen to what the team has to say about what went wrong \(and what went right\) during the iteration. This knowledge will help everybody make informed decisions about the next iteration planning, and determine the best course of action for the project. This task is performed at the end of every iteration until the end of the project.
---

Steps

Prepare for iteration assessment |  Towards the end of the iteration, the team jointly assesses whether the objectives and evaluation criteria established in the Iteration Plan were met, and whether the team adhered to the plan and completed all of the work items committed to the iteration. The team makes use of objective measures to the greatest extent possible. To assess that a given work item is completed, the team ensures that the corresponding test cases were successfully run against it.  The team prepares a demonstration of the features implemented at that point, so that during the iteration assessment stakeholders can have a real sense of progress made. The team decides whether each developer should demonstrate the features that they implemented, or if the project manager or senior developer demonstrates it all, with other team members present to answer questions.  In addition to the demonstration, prepare reports that show project status, such as work burndown and test case reports.  These activities happen in preparation for the iteration assessment meeting with stakeholders that occurs on the last day of the iteration.
---

Demonstrate value and gather feedback

The team demonstrates the product to customers, end-users, and other stakeholders to collect their feedback or, better yet, have end users use the product themselves. This can be done throughout the iteration, but at least during the iteration assessment that occurs at the end of the iteration \(see [Guideline: Iteration Assessment](../../../practice-management/iterative_dev/guidances/guidelines/iteration-assessment.md)\). Work that is not completed should not be demonstrated.  Record resulting knowledge \(such as new functionality, requested changes, and defects\) in the [Work Items List](../../../core/common/workproducts/work-items-list-6.md), so that project priorities, scope, and duration can be refined in the next iteration planning.
---

Perform a retrospective

Review with the team the approach taken to development and collaboration, the effectiveness of the development environment, the suitability of the working environment, and other factors. Discuss what things went well, what could have gone better, and how things could be changed to deliver better results. Capture in the current Iteration Plan the assessment results, stakeholder feedback, and actions to be taken to improve the development approach for the next iteration. Record lessons learned in this iteration with a collection of lessons learned for the entire project.
---

Close-out project

Perform this step when the iteration review coincides with the end of the project. Involve the team and stakeholders in a final assessment for project acceptance which, if successful, marks the point when the customer accepts ownership of the software product. Complete the close-out of the project by disposing of the remaining assets and reassigning the remaining staff.
---

Perform a retrospective \(end of phase\)

When the assessment period coincides with the end of a phase, the corresponding milestone review takes place. These are informal reviews of the work accomplished where the team and stakeholders agree on moving the project on to the next phase, spanning a set of iterations with a new common goal in accordance with the emphasis of the following phase. For more information, see [Concept: Phase Milestones](../../../practice-management/risk_value_lifecycle/guidances/concepts/phase-milestones.md).
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

Concepts|
  * [Phase Milestones](../../../practice-management/risk_value_lifecycle/guidances/concepts/phase-milestones.md)
  * [Retrospective](../../../practice-management/iterative_dev/guidances/concepts/retrospective.md)
---|---
Guidelines|
  * [Conduct Project Retrospective](../../../practice-management/iterative_dev/guidances/guidelines/conduct-project-retrospective.md)
  * [Deploy the Solution](../../../core/common/guidances/guidelines/deploy-the-solution.md)
  * [Iteration Assessment](../../../practice-management/iterative_dev/guidances/guidelines/iteration-assessment.md)


Tool Mentors|
  * [Use Method Composer to Update the Process](../../../practice-management/iterative_dev/guidances/toolmentors/use-method-composer-to-update-the-process.md)

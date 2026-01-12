---
title: Iteration Planning
source_url: practice.mgmt.iterative_dev.base/guidances/guidelines/iteration_planning_C77F13CE.html
type: Guideline
uma_name: iteration_planning
page_guid: _0auiMMlgEdmt3adZL5Dmdw
keywords:
- iteration
- planning
related:
  tasks:
  - plan-iteration-1
---


 This guideline presents the activities related to iteration planning that help establish high-level iteration objectives, produce a plan outlining who needs to do what, and define how to assess end results.
---

Relationships

Related Elements|
  * [Plan Iteration](../../tasks/plan-iteration-1.md)
---|---

Main Description

###  Introduction

The goal with iteration planning is to establish a few high-level objectives for what to accomplish during the iteration, produce a sufficiently detailed plan outlining who needs to do what to accomplish those objectives, and define how to assess that you accomplished what you set out to accomplish.  Iteration planning is ideally done with the entire team \(including key stakeholders\) in a meeting \(typically lasting one to a few hours\), at the beginning of an iteration. This ensures that the entire team understands what needs to be done, and they become committed to the success of the team. In some cases, it is preferred to have a smaller subset of people \(such as the Project Manager, an Architect, and an Analyst\) to meet in advance to prepare the meeting with a draft iteration plan.

###  Define high-level objectives

A key aspect of an iteration is to focus the team on a short-term deliverable of measurable value. Document between one and five high-level objectives to make sure that you do not lose focus on what to accomplish during the iteration. Typically, the project plan should outline one or several objectives for each iteration, and those objectives are used as a starting point. If you need to further detail or clarify the objectives as you plan your iteration, do so.  The objectives are usually based on the following factors:
  * **Critical risks not yet mitigated:** Iteration goals often include driving down the most critical risks.
  * **The time allocated to the iteration:** Iterations are fixed in duration, so the Project Manager must ensure that the goals for the iteration are realistic relative to the time and the resources allocated to the iteration.
  * **The highest priority features:** Requirements are prioritized to ensure that the critical features of the application will be developed and tested early on.

###  Produce an Iteration Plan

There is an Iteration Plan per iteration that should outline who will implement which work item in how long a time. Since iterations are time-boxed, you need to understand how big your "box" is by assessing how many hours of actual work can be taken on \(see [Guideline: Agile Estimation](../../../../core/common/guidances/guidelines/agile-estimation.md). Let's assume that you have six team members, and you have 15 working days in your iteration, and you on average can do five actual hours of work per person and day. This will give you 6x15x5h = 450 hours of actual work. Note that the average team member only performs between four and six hours of actual project work per day, with the rest being consumed by e-mails, meetings, and other overhead activities not directly related to the project.  The team should then revisit and update priorities for all of the high-priority items in the Work Items List, to make sure that an important work item is not missed that would otherwise fall just below the list of what can be taken on in this iteration.  Pick the top-priority work item and see if it matches the objectives of the iteration. If it does, assess whether the work item is too big to take on within an iteration. If it is too big, break it down into smaller work items. Once the work item has been decomposed, the team determines whether to take on one or several child work items.  **Example:** The team would like to take on the work item called _Develop Use Case A_ , but it would take roughly 300 hours to develop, so they feel that it is only necessary to do a subset of the use case to achieve their iteration objectives, allowing them to take on other high-priority work items. They divide the work item into five smaller work items representing different scenarios of use case A. The team decides to take on one out of the five identified scenarios in this iteration.  When a team has decided to take on a work item, it will assign the work to one or several team members. Ideally, this is done by team members signing up to do the work, because this makes people motivated and committed to doing the job. However, based on your team culture, you may instead have the project manager assign the work.  The next step is for team member\(s\) to assess how many actual hours or days it will take to do the work. Ideally, you want to have each work assignment to be from a few hours up to two days of work. If the work item is too big, consider breaking it down into smaller work items.  The team sums up the actual estimate for each work item they have committed to, and checks if they can commit to any more work.  **Example:** Jack signed up to develop the chosen scenario for use case A. He thinks that it would take 50 hours, so he decided to develop the work into a set of tasks, and he asks other team members to help out with various subtasks:
  * Detail the requirements \(Jack\): five hours
  * Design the scenario \(Jack, Ann, and David\): five hours
  * Implement and test the dB changes \(Ann\): 12 hours
  * Implement and test the server portion \(David\): 16 hours
  * Implement and test the client portion \(Jack\): 12 hours
  * Total: 50 hours

As work items are decomposed into smaller tasks, estimates can typically be improved. You also better come to understand what is involved, and whether other team members may be better suited to take on a subset of the task.  The team now determines whether they are willing to take on another work item by comparing actual hours signed up for to the actual hours available. In this case, the team has only signed up for 50 hours so far, and hence has another 400 hours available.

###  Define Evaluation Criteria

It is critical that it is clear to all team members and other stakeholders how you will measure success at the end of the iteration. Obvious success criteria should include that you can test the functionality implemented, and that no or few defects are detected. Having too many defects makes it impossible to use the functionality, and it will prevent meaningful feedback. Test objectives and test cases need to be clearly outlined.  There may be other success criteria, such as that you demo the capabilities to a certain set of stakeholders with favorable review comments, or that you can successfully demonstrate or make available a tech preview at a conference.
---

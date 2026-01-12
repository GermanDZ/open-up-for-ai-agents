---
title: Agile Estimation
source_url: core.mgmt.common.extend_supp/guidances/guidelines/agile_estimation_A4EF42B3.html
type: Guideline
uma_name: agile_estimation
page_guid: _CGHskBEdEdqY7JB6N6CW2w
keywords:
- agile
- concepts
- estimation
related:
  tasks:
  - plan-iteration-1
  - plan-project-1
  workproducts:
  - work-items-list-6
---


 This guideline explains the three key concepts of agile estimation and how they relate to each other. It describes agile estimation concepts of size, velocity, and effort.
---

Relationships

Related Elements|
  * [Plan Iteration](../../../../practice-management/iterative_dev/tasks/plan-iteration-1.md)
  * [Plan Project](../../../../practice-management/release_planning/tasks/plan-project-1.md)
  * [Work Items List](../../workproducts/work-items-list-6.md)
---|---

Main Description

###  Agile Estimation

There are three main concepts you need to understand to do agile estimation, see \[[COH05](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html#COH05)\] for more information:
  * **Estimation of Size** gives a high-level estimate for the work item, typically measured using a neutral unit such as points
  * **Velocity** tells us how many points this project team can deliver within an iteration;
  * **Estimation of Effort** translates the size \(measured in points\) to a detailed estimate of effort typically using the units of Actual Days or Actual Hours. The estimation of effort indicates how long it will take the team member\(s\) to complete the assigned work item\(s\).

####  Estimation of Size
**Points** is a relative measure that can be used for agile estimation of size. The team decides how big a point is, and based on that size, determines how many points each work item is. To make estimation go fast, use only full points, 1, 2, 3, 5, 8, and so on, rather than fractions of a point, such 0.25, or 1.65 points. To get started, look at 10 or so representative work items, give the smallest the size of one point, and then go through all other work items and give them a relative point estimate based on that point. Note that points are used for high-level estimates, so do not spend too much time on any one item. This is especially true for work items of lower priority, to avoid wasting effort on things that are unlikely to be addressed within the current iteration.  A key benefit of points is that they are neutral and relative. Let's say that Ann is 3 times more productive than Jack. If Ann and Jack agree that work item A is worth 1 point, and they both think work item B is roughly 5 times as big, they can rapidly agree that work item B is worth 5 points. Ann may however think work item B can be done in 12 hours, while Jack thinks it can be done in 36 hours. That is fine, they may disagree about the actual effort required to do it, but we do not care at this point in time, we only want the team to agree on the relative size. We will later use Velocity to determine how much 'size', or how many points, the team can take on within an iteration.  One project team may say that a work item of a certain size is worth 1 point. Another project team would estimate the same sized work item to be worth 5 points. That is fine, as long as you are consistent within the same project. Make sure that the entire team is involved in assessing size, or at least that the same people are involved in all your size estimates, to ensure consistency within your project. We will see how the concept of velocity will fix also this discrepancy in a point meaning different things to different project teams.  You can also use other measures of size, where the most common alternative is Ideal Days. See for example \[[COH05](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html)\] for more information.

####  Velocity

Velocity is a key metric used for iteration planning. It indicates how many points are delivered upon within an iteration for a certain team and project. As an example, a team planned to accomplish 20 points in the first iteration. At the end of the iteration, they noticed that they only delivered upon 14 points, their velocity was hence 14. For the next iteration, they may plan for fewer points, let's say 18 points, since they think they can do a little better than in previous iteration. In this iteration, they delivered 17 points, giving them a velocity of 17.  Expect the velocity to change from iteration to iteration. Some iterations go smoother than others, and points are not always identical in terms of effort. Some team members are more effective than others, and some problems end up being harder than others. Also, changes to the team structure, learning new skills, changes to the tool environment, better teaming, or more overhead with meetings or tasks external to the project will all impact velocity. In general, velocity typically increases during the project as the team builds skills and becomes more cohesive.  Velocity compensates for differences between teams in terms of how big a point is. Let's assume that project team Alpha and project team Beta are equally efficient in developing software, and they run the same project in parallel. Team Alpha, however, assesses all work items as being worth 3 times as many points as team Beta's estimates. Team Alpha assesses work item A, B, C, and D to correspond to 30 points, and team Beta estimates the same work items to correspond to 10 points. Both teams deliver upon those 4 work items in the next iteration, giving team Alpha a velocity of 30, and team Beta a velocity of 10. It may sound as if team Alpha is more effective, but let's look at what happens when they plan the next iteration. They both want to take on work item E-H, which team Alpha has estimated to be 30 points, and team Beta as normal has estimated to be 1/3 as many points, or 10 points. Since a team can typically take on as many points as indicated by their velocity, they can both take on all of E-H. The end result is that it does not matter how big a point is, as long as you are consistent within your team.  Velocity also averages out the efficiency of different team members. Let's look at an example; Let's assume that Ann always works 3 times as fast as Jack and Jane. Ann will perhaps deliver 9 points per iteration, and Jack and Jane 3 points each per iteration. The velocity of that 3-person team will be 15 points. As mentioned above, Ann and Jack may not agree on how much effort is associated with a work item, but they can agree on how many points it is worth. Since the team velocity is 15, the velocity will automatically translate the point estimate to how much work can be taken on. As you switch team members, or as team members become more or less efficient, your velocity will change, and you can hence take on more or less points. This does however not require you to change the estimate of the size. The size is still the same, and the velocity will help you to calculate how much size you can deliver upon with the team at hand for that iteration.

####  Estimation of Effort

Estimation of Effort translates the size \(measured in points\) to a detailed estimate of effort typically using the units of Actual Days or Actual Hours. As you plan an iteration, you will take on a work item, such as detail, design, implement and test a scenario, which may be sized to 5 points. Since this is still a reasonably big work item, break it down into a number of smaller work items, such as 4 separate work items for Detailing, Designing, Implementing and Testing Server portion, and Implementing and Testing Client portion of the scenario. Team members are asked to sign up for the tasks, and then detail the estimate of the actual effort, measured in hours or days, for their tasks. In this case, the following actual estimates were done \(with person responsible within parenthesis\):
  * Detailing scenario \(Ann\): 4 hours
  * Designing scenario \(Ann and Jack\): 6 hours
  * Implementing and Testing Server portion of scenario \(Jack\): 22 hours
  * Implementing and Testing Client portion of scenario \(Ann\): 12 hours
  * **Total Effort Estimate for Scenario:** 44 hours

If other people would be assigned to the tasks, the estimated actual hours could be quite different. There is hence no point doing detailed estimates until you know who will do the work, and what actual problems you will run into. Often, some level of analysis and design of the work item needs to take place before a reasonable estimate can be done. Remember that estimates are still estimates, and a person assigned to a task should feel free \(and be encouraged\) to re-estimate the effort required to complete the task, so we have a realistic view of progress within an iteration.
---

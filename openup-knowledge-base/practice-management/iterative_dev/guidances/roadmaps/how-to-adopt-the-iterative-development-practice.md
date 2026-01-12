---
title: How to Adopt the Iterative Development Practice
source_url: practice.mgmt.iterative_dev.base/guidances/roadmaps/how_to_adopt_85BF1B9B.html
type: Roadmap
uma_name: how_to_adopt
page_guid: _bpWt8OMPEdyM47cGD2jiaQ
keywords:
- adopt
- development
- iterative
- practice
---

 This roadmap describes how to adopt the iterative development practice. It helps an organization get prepared for developing and delivering software incrementally.
---

Main Description

###  Getting started

Iterative development is based on the idea that a software system is built iteratively in a series of increments. Each increment adds a subset of the final system's functionality, and the system grows to become more and more complete over the course of the project's iterations.  Consider making all of your iterations have the same duration. This is important for two reasons: it establishes the "heart beat" of the project, and it helps understand the project team's performance. This supports the creation of successively more accurate estimates of remaining work. Attack the hardest problems on the first iterations, but do not overload the first iteration too much. Make sure that you can show progress at the end of each iteration. Do not extend an iteration in order to finish work, but also do not finish an iteration without any software to be demonstrated. If needed, break the problem into smaller, more manageable pieces so that this balance can be achieved.  Plan an iteration in detail only when it is due to start. Each iteration starts with an iteration planning meeting with the whole project team. In this meeting, the objectives of the iteration are defined in terms of work items, tasks are identified for these work items, and team members sign up for tasks and provide their estimates. At the end of the iteration planning meeting, the iteration plan is comprised of a set of work items, decomposed into tasks that individual team members sign up for. The iteration can be started. Once an iteration is under way, it should be allowed to proceed according to its plan, with as little external interruption as possible.  During the course of the iteration, team members provide frequent status of their tasks in focused meetings. The frequency of these meetings is decided by team: it could be daily, a couple times a week, or weekly. Team members work on the tasks they signed up for, following the appropriate priority. Allow detailed informal peer coordination to happen, and mark completed work items in the iteration plan. The overall iteration status is hence readily available in the iteration plan at all times. Any work items that have not been justifiably completed by the end of the iteration are removed from the iteration and re-assigned to the next one \(or just returned to the work items list\).  Make all iterations follow the same pattern. This helps the team to focus on activities that are specific to the beginning, middle, and end of an iteration. For example, some common activities performed during an iteration are:
  * Iteration planning
  * Iteration architecture work
  * Continuous development of micro-increments
  * Creation of stable weekly builds
  * Bug fixing
  * Iteration review and Retrospective

See [Iteration Lifecycle](../concepts/iteration-lifecycle.md) for more information.

###  Common Pitfalls

There are common pitfalls experienced when adopting an iterative approach, including the ones listed in the following sections. Fore more information on challenges when transitioning from waterfall to an iterative development approach, see [\[KRU00\]](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html#KRU00).

####  What project managers should plan for

One of the most difficult situations for project managers is to transition from a traditional development approach \(such as waterfall\) to an iterative approach. There is more planning with iterative development than with waterfall: one plan per iteration. At every iteration, there is negotiation with stakeholders, changes in scope, and re-planning. Project managers need to avoid detailed planning upfront, and should work with their best estimates for the tasks at hand in a given iteration.  However, this behavior should not result in unplanned and non-prioritized requirements creating scope-creep, nor unnecessary rework happening on elements that are not broken. The iteration plan, with iteration objectives and planned tasks, should be collaboratively created by the project manager, the team, and stakeholders in order to promote a common understanding and buy-in into what is expected at the end of an iteration.

####  Which comes first: specifications or software?

In a waterfall approach, progress is often measured by the completion of specifications. For example, if the design specification is completed and signed-off, the team advances to the implementation based on the design specification.  With iterative development, artifacts evolve throughout the iterations, and every iteration should result in an increment in the capabilities offered by the solution: in other words, implemented, tested software that is able to be demonstrated \(and potentially shipped\) to customers. Software comes first. Planning is more important than the plans. Designing and architecting an evolving solution is more important than capturing and polishing design and architecture models. At the end of each iteration, perform an assessment to gauge the completion of requirements that have passed test cases. Another way to make significant progress is by focusing on the harder problems \(or risks\) as early as possible, thus making sure that you create and use a sound, executable architecture as the basis for the other requirements.

####  Different iterations for the different disciplines

A common problem found in organizations moving from a waterfall to an iterative process is that they use the iteration concept only as an "envelope" for their engineering disciplines. For example, it is common to hear people in those organizations talk about "requirements iteration" or "test iteration". A fundamental tenet of iterative development is that it takes a holistic view of work items: each work item assigned to an iteration is completed in that iteration. For example, a "Login User" work item would see all required tasks \(such as design, code, and test\) to complete that work item. At the end of the iteration, the Login User behavior can be demonstrated as an integral part of the executable system.

####  No visible progress

Some teams will have work items that are not completed during an iteration as expected, and will not report problems. This creates a false impression that work items planned for the iteration are being closed, thus showing an inaccurate iteration burndown.
In order to avoid this, monitor active tasks closely, and address any slippage promptly. Use frequent, short status meetings to gauge progress and detect issues. Create a "no blame" environment where everyone feels empowered by the team and actively seeks advice and help from the team.

####  Adding work to an ongoing iteration

Management or stakeholders may impose more work to be added to an on-going iteration. While this is sometimes legitimate \(for business reasons\), there is a risk that this work just gets informally accepted by the team, without passing through the Work Items List, where it gets prioritized with the remaining work.
In order to minimize the impact of new work being added to an iteration, make sure to involve stakeholders in the planning process, so that they understand the impact a new work item brings to the current iteration. Be prepared to negotiate the removal of lower priority work from the iteration, in order to accommodate the new requested work. Another approach is to convince stakeholders that in a few weeks the iteration will end \(with demonstrable progress\), and that the new work item can be prioritized and assigned to the next iteration.
---

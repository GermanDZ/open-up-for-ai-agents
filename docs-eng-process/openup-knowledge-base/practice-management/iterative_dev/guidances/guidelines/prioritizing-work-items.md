---
title: Prioritizing Work Items
source_url: practice.mgmt.iterative_dev.base/guidances/guidelines/prioritizing_work_items_A12C9BEC.html
type: Guideline
uma_name: prioritizing_work_items
page_guid: _oVMZADSoEdy07ZJqOGUGaQ
keywords:
- items
- prioritizing
- work
related:
  tasks:
  - plan-iteration-1
---


 This guidelines describes work items prioritization throughout the project lifecycle.
---

Relationships

Related Elements|
  * [Plan Iteration](../../tasks/plan-iteration-1.md)
---|---

Main Description

###  What is prioritized?

Prioritization should happen for work items, such as enhancement requests, requirements, defects, project tasks, and so on. The work items list provides one place for prioritizing work. Prioritizing units of work that are too small may lead to analysis-paralysis.

###  Who prioritizes?

Prioritization is done by the extended team. Here are some examples on how different team members contribute to the prioritization:
  * Analysts collaborate with stakeholders to establish the initial priorities for work items to implement, such as features, use cases, and scenarios.
  * Architects collaborate with stakeholders and the development team to identify the architecturally significant use cases and scenarios, and re-prioritize these so that the team understands what needs to be done to drive down technical risk, and to make progress on evolving the product in a technically sensible fashion.
  * Developers and testers help define \(but do not decide\) the priorities of defects relative to achieving iteration objectives.
  * Project managers facilitate \(but do not decide\), driving convergence on what the team should focus on when planning a project, planning an iteration, and managing an iteration. They do this in order to ensure smooth execution, and that the perspectives of all team members are properly heard. When the team cannot gain consensus in a reasonable time, the project manager has final say on the priority of work items that are too small to warrant the attention of the paying stakeholders.
  * stakeholders that pay for the application have the final say on what capabilities to prioritize.

###  When do you prioritize?

When you enter a new work item in the Work Items List, give it an initial priority. Priorities are always changing. The sections below describe what re-prioritization is done when you are planning a project, planning an iteration, or managing an iteration.

####  Prioritizing when planning a project

During project planning, prioritize the key features, use cases, and scenarios. Also, potentially assign them to iterations as a part of laying out the project plan, by defining at a high level what should be done when. These priorities will be revised later on as iterations are planned.  When starting a project where an existing application will be enhanced, a Work Items List may exist from past projects and usage of the application. If this is the case, go through the Work Items List to survey and re-prioritize existing work items, so that the team understands what to focus on.

####  Prioritizing when planning an iteration

When planning what to deliver for an iteration, the team needs to balance what delivers immediate value to the stakeholders with what risks need to be mitigated.The chosen balance should be reflected in the iteration objectives, which then drive further prioritization and assignments of work items to the next iteration. This exercise should be done by the entire team to reflect all of the key perspectives, such as technical \("doing task A before task B saves you time"\), managerial \("we do not have anybody that knows that legacy application until next iteration", or business \("this scenario is more important than that scenario"\).

####  Prioritizing when managing an iteration

The recommendation is not to expand or change the scope of an iteration, because this will almost certainly lead to scope creep, as well as potential confusion among the team on what to work on. As new features and enhancements are requested, capture them in the Work Items List, but do not assign them to the current iteration.  During an iteration, you are developing and testing code. As you develop solution increments, you will find defects. In most cases, you will directly fix trivial defects as you find them during development. Examples of such defects are the many problems you find as you implement your code \(for example, using a test-driven development approach or doing your regular unit tests\). In other cases, the defect should be captured as a work item. This allows it to be prioritized, and potentially developed by somebody else or at a different time. If a defect needs to be addressed to provide an iteration build of reasonable quality and that aligns with the iteration objectives, the defect should be fixed during the current iteration. Note that this is not a creep or change of scope, since it merely indicates that something needs to be fixed to deliver what the team already committed to.

###  How do you prioritize?

Prioritizing is the difficult balancing of frequently competing priorities. For more information on the art of prioritizing, see for example \[[COH05](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html#COH05)\].
---

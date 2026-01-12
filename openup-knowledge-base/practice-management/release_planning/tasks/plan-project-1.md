---
title: Plan Project
source_url: practice.mgmt.release_planning.base/tasks/plan_the_project_A4A80C96.html
type: Task
uma_name: plan_the_project
page_guid: _0lC70MlgEdmt3adZL5Dmdw
keywords:
- plan
- project
related:
  roles:
  - project-manager-4
  - analyst-6
  - architect-6
  - developer-11
  - stakeholder-6
  - tester-5
---


 A collaborative task that outlines an initial agreement on how the project will achieve its goals. The resulting project plan provides a summary-level overview of the project.
---
Disciplines: [Project Management](../../../core/cat/disciplines/project-management-1.md)

Purpose

Get stakeholder buy-in for starting the project and team commitment to move forward with it. This plan can be updated as the project progresses based on feedback and changes in the environment.
---

Relationships

Roles| Primary Performer:
  * [Project Manager](../../../core/role/roles/project-manager-4.md)

| Additional Performers:
  * [Analyst](../../../core/role/roles/analyst-6.md)
  * [Architect](../../../core/role/roles/architect-6.md)
  * [Developer](../../../core/role/roles/developer-11.md)
  * [Stakeholder](../../../core/role/roles/stakeholder-6.md)
  * [Tester](../../../core/role/roles/tester-5.md)
---|---|---
Inputs| Mandatory:
  * [\[Project Work\]](./../../core.mgmt.slot.base/workproducts/project_work_slot_F12BAC46.html)
  * [\[Technical Specification\]](./../../core.tech.slot.base/workproducts/technical_specification_slot_2812F7EF.html)

| Optional:
  * None


Outputs|
  * [Project Plan](../workproducts/project-plan-4.md)



Main Description

Developing the project plan provides an opportunity for the team to agree on project scope, objectives, initial timeframe, and deliverables. It allows the team to begin demonstrating self-organization by defining success criteria and work practices to be used. Collaboration and consensus by all key project participants is the goal, but the role responsible for this task must ensure that everybody is committed to the plan.
---

Steps

Identify a cohesive team | Revisit the resourcing for the project. Identify gaps and initiate hiring or re-allocation of resources as needed. Discuss with the team who plays which roles, and have them agree on their responsibilities.
---

Estimate project size

The team produces rough size estimates for each work item found in the [\[Project Work\]](./../../core.mgmt.slot.base/workproducts/project_work_slot_F12BAC46.html).  Discuss with stakeholders to determine what is realistic to develop within the constraints of the project. Use stakeholder priorities and estimates from the team to guide these discussions.
---

Evaluate risks

The team identifies project risks, performs a qualitative risk analysis to assess their order of magnitude, and updates the [\[Project Risk\]](./../../core.mgmt.slot.base/workproducts/project_risk_slot_FC0351C4.html). The project manager facilitates the team decision about which risks they should respond to, and which risks they should watch for.  Responses may include avoiding or mitigating risks, exploring opportunities, or increasing the probability and positive impacts of the risk. Depending on the case, work items may have to be added or removed from the [\[Project Work\]](./../../core.mgmt.slot.base/workproducts/project_work_slot_F12BAC46.html) to make sure that responses will be prioritized and handled by the team along with other project work. Because it is not feasible to plan responses for all identified risks, the team may decide to accept some of them. Keep the risks to watch in the risks list, and communicate them to stakeholders. Determine actions only if they occur.
---

Forecast project velocity and duration

Define the iteration length and use it to assess target velocity. The number of items to be delivered in each iteration will be set by the velocity of the team and the estimates for each item.  If the project is feature-driven, the team uses the [\[Project Work\]](./../../core.mgmt.slot.base/workproducts/project_work_slot_F12BAC46.html) and target velocity to forecast the number of iterations required to complete the project. If the project instead is date-driven, the team assesses \(using the known velocity of the team\) roughly how much work can be done in the given time-frame. Out-of-scope work can be considered for future releases.  The team should not spend too much time doing this planning. The project plan should document only a brief summary of project milestones and between one and three objectives for each iteration. Do not commit individual work items to the plan, because this will force too much re-planning. The goal is just to create a high-level plan outlining how the team can build the resulting application in the given set of iterations. Extra levels of detail will be achieved in other planning sessions throughout the project \(for example, when planning iterations\). You may need to revisit this plan later to adapt it based on what you will learn by running the iterations.
---

Outline project lifecycle

Organize iterations into a set of phases. Each phase in the project lifecycle will end with a milestone aimed at providing stakeholders with oversight and steering mechanisms to control project funding, scope, risk exposure, value provided, and other aspects of the process \(see [Concept: Project Lifecycle](../../risk_value_lifecycle/guidances/concepts/project-lifecycle.md)\).
---

Establish costs and articulate value

Develop a rough order of magnitude estimate for the costs of resources needed to complete project work items. A simplified project costing model can be applied by multiplying the approximate cost per person for the entire team by the length of an iteration to derive ongoing financial impact \(that is, cost per iteration\). This first round of planning should keep things very rough and flexible. The goal is just to articulate value against the budget constraints of the project, and to help stakeholders decide whether it is worth moving forward with the project or not. If necessary, propose options to decrease costs, such as removing low-value and high-cost work items from the scope .
---

Plan deployment

Plan the strategy for deploying the software \(and its updates\) into the production environment as early as possible, because it may impact the [\[Project Work\]](./../../core.mgmt.slot.base/workproducts/project_work_slot_F12BAC46.html). The team may need to discuss the release timeframe with the operations and support departments to ensure that the project fits into the overall corporate deployment system.  Whenever possible, the team should consider deploying small releases \(release cycles of three to four months at most\). Releasing software into production frequently is a good way to get early feedback from the users, in order to enhance the overall product quality.  Capture the objectives for deployment and release dates in the [Project Plan](../workproducts/project-plan-4.md).
---

Key Considerations

Gain agreement with stakeholders and the rest of the project team regarding the order of objectives and the duration of the project. Make adjustments as necessary.
---

More Information

Concepts|
  * [Phase Milestones](../../risk_value_lifecycle/guidances/concepts/phase-milestones.md)
---|---
Guidelines|
  * [\[Project Planning Guidance\]](./../../core.mgmt.slot.base/guidances/guidelines/project_planning_guidance_slot_DDA75689.html)
  * [Agile Estimation](../../../core/common/guidances/guidelines/agile-estimation.md)
  * [Deploy the Solution](../../../core/common/guidances/guidelines/deploy-the-solution.md)
  * [Managing Risks](../../../core/common/guidances/guidelines/managing-risks.md)
  * [Staffing a Project](../guidances/guidelines/staffing-a-project.md)

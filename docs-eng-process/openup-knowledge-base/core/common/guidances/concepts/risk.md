---
title: Risk
source_url: core.mgmt.common.extend_supp/guidances/concepts/risk_AF5840DA.html
type: Concept
uma_name: risk
page_guid: _0bsLgMlgEdmt3adZL5Dmdw
keywords:
- risk
related:
  concepts:
  - elaboration-phase-10
  - project-lifecycle
  tasks:
  - manage-iteration-1
  workproducts:
  - risk-list-4
---


 A risk is whatever may stand in the way to success, and is currently unknown or uncertain. Usually, a risk is qualified by the probability of occurrence and the impact in the project, if it occurs.
---

Relationships

Related Elements|
  * [Elaboration Phase](../../../../practice-management/risk_value_lifecycle/guidances/concepts/elaboration-phase-10.md)
  * [Manage Iteration](../../../../practice-management/iterative_dev/tasks/manage-iteration-1.md)
  * [Project Lifecycle](../../../../practice-management/risk_value_lifecycle/guidances/concepts/project-lifecycle.md)
  * [Risk List](../../workproducts/risk-list-4.md)
---|---

Main Description

###  What is a Risk?

A risk is an uncertain event or condition that, if it occurs, will have a negative or positive effect on one or more project objectives \[[PMI](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html#PMI)\]. Project risks may be seen as threats or opportunities. The latter means that taking a calculated risk may bring, for example, competitive advantage for a product or organization. If there are benefits associated with an opportunity, then you can take certain degrees of risk for a project to be successful \[[SEI99](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html#SEI99)\].  In everyday life a risk is an exposure to loss or injury: A factor, thing, element, or course involving uncertain danger. Similarly, in software development a risk is something that can compromise the success of a project. Examples of potential sources of risk in software development are listed below \(see \[[SEI99](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html#SEI99)\] for more details\):
  * Requirements
  * Design
  * Development process
  * Work environment
  * Resources
  * Contract
  * Project interdependencies
  * And so on

###  Risk Attributes

You can record as much information as you like or need about your risks. You will find a list of common risk attributes following.
  * **Risk Description:** A description of the risk detailing the impact for the project if this risk becomes a problem \(that is, it becomes a reality\).
  * **Risk Category** : Risk identification is usually more easily done when there is a "mental framework" in place to ensure that potential areas of risk are not overlooked. One way of doing this is to divide risks into categories \(such as technical, project management, organizational, and external\), to ensure that all aspects of the project which are prone to risk are covered.
  * **Risk Type:** Used to classify the risk as:
  *     * Direct or Indirect risk: if the project has or does not have a large degree of control over the risk
    * Resource risk: organization, people, funding, or time
    * Business risk
    * Technical risk: scope, technology, or external dependency
    * Schedule risk
  * **Risk Probability:** How likely the risk event will happen. This is usually represented as a scale of values \(for example: High, Medium, Low\). Probability is one of the most difficult quantities to judge accurately.
  * **Risk Impact** \(level\): If this risk becomes a problem, what will the impact on the project be? This is not the actual **description** of the impact, but the **level** of impact. As the risk probability, it is usually represented as a scale. This attribute is also sometimes called the **severity** of the risk.
  * **Risk Magnitude** : To be able to rank and define which risks need to be mitigate first, the **Risk Probability** and **Risk Impact** attributes are often combined in a single **Risk** **Magnitude** indicator represented as a scale similar to the combined attributes.

###  Risk Response Strategies

The risk response should be in line with the significance of the risk. The strategies for handling risk cover two main types: negative risks and positive risks \(or opportunities\). Common response strategies for negative risks or threats include \[[BOE91](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html)\]:
  * **Avoid** : Reorganize the project so that it cannot be affected by that risk \(for example, removing work\)
  * **Mitigate** : Define actions to reduce the probability or the impact of the risk, removing it from the top of the list
  * **Transfer** : Reorganize the project so that someone or something else bears the risk. It simply gives another party responsibility for its management. It doesn't eliminate the risk.

Common response strategies for positive risks or opportunities include:
  * **Exploit** : Add work or reorganize the project to make sure that the opportunity occurs \(it is the reverse of avoid\)
  * **Enhance** : Define actions to increase the probability or the positive impact of the risk \(this is the reverse of mitigate\)
  * **Share** : Allocate the ownership of the opportunity to a third party who is best able to capture the opportunity for the benefit of the project.

Another response strategy for both threats or opportunities is to **Accept** : Decide to live with the risk, and define a contingency plan.  Some scenarios for software development may help to make these concepts more clear:
  * You need to use a new framework. A risk avoidance strategy could be to drop this new framework and use another one that is already understood by the team.
  * The application you are developing needs to communicate with a legacy system. A risk transfer strategy would be to have the legacy support team be responsible for providing the APIs to access the legacy system.
  * You need to use new middleware. A risk mitigation strategy could be to build a prototype using this new middleware to validate that it will provide the features you need for your application.
  * Your integrator is the only one who knows how to integrate the different components of your application. A contingency plan could be to identify a resource on another project that you could bring on if your integrator is sick, leaves the company, and so on.
---

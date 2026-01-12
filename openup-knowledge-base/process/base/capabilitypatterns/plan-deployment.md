---
title: Plan Deployment
source_url: process.openup.base/capabilitypatterns/plan_deployment_1136026.html
type: TaskDescriptor
uma_name: plan_deployment
page_guid: _DZttwJlXEeGlkdGl1HQlDA
keywords:
- deployment
- plan
- release
related:
  other:
  - deployment-engineer-3
  - developer-4
---


 If a deployment plan for the project already exists, update it to reflect the nature of this release. If this document does not exist, develop a deployment plan to indicate how this release will be rolled out to the production environment.
---

Purpose

The purpose of this task is to ensure that the various aspects of deploying a release to production are considered and understood between the development team and the deployment engineer.
---

Relationships

Roles| Primary:
  * [Deployment Engineer](deployment-engineer-3.md)

| Additional:
  * [Developer](developer-4.md)

| Assisting:
---|---|---|---
Outputs|
  * [Deployment Plan](deployment-plan-2.md)



Main Description

Because a deployment engineer is responsible for accepting the results of one or more development team members and deploying those integrated releases into the production environment, it is important for all parties to agree on the details of a particular release. The deployment plan documents, in one place, all the information that will be consumed by the deployment engineer before and during the deployment to production of a particular release package.
---

Steps

Determine if deployment plan exists | Determine whether the development team has a deployment plan already written for a previous release. If so, part of that plan might be reusable. If this is the development team's first release, another development team with a similar feature set might have a plan that can be used as a starting point.
---

Develop the deployment plan \(if applicable\)

If a deployment plan does not exist, or one cannot be found to be used as a starting point, use the recommended format documented in the [Artifact: Deployment Plan](../../../practice-general/production_release/workproducts/deployment-plan-4.md) and refer to the [Checklist: Deployment Plan](../../../practice-general/production_release/guidances/checklists/deployment-plan-5.md) to start and develop a deployment plan.
---

Update the deployment plan \(if applicable\)

If a deployment plan does exist that can be used as a baseline, review that plan and update, add, or delete information as necessary. When the plan is done, it should reflect entirely the contents of the upcoming deployment only, not a release in the past or one in the future. In other words, the deployment plan should be specific only to this release.
---

Properties

Multiple Occurrences| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Event Driven| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Ongoing| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Planned| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Repeatable| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

More Information

Checklists|
  * [Deployment Plan](../../../practice-general/production_release/guidances/checklists/deployment-plan-5.md)
---|---

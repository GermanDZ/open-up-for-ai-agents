---
title: Develop Backout Plan
source_url: practice.gen.production_release.base/tasks/develop_backout_plan_A909CDFE.html
type: Task
uma_name: develop_backout_plan
page_guid: _IAIu8uB-EeC1y_NExchKwQ
keywords:
- backout
- deployment
- develop
- plan
related:
  roles:
  - developer-11
  - deployment-engineer-4
---


 This task results in a plan to be used by the production support organization to roll back the release if there is a problem during or after deployment.
---
Disciplines: [Deployment](../../../core/cat/disciplines/deployment-1.md)

Purpose

The purpose of this task is to develop the criteria, procedures, and responsibilities associated with rolling back a specific release into the production environment to prevent or minimize interruptions to other products or services.
---

Relationships

Roles| Primary Performer:
  * [Developer](../../../core/role/roles/developer-11.md)

| Additional Performers:
  * [Deployment Engineer](../../../core/role/roles/deployment-engineer-4.md)
---|---|---
Inputs| Mandatory:
  * None

| Optional:
  * [Deployment Plan](../workproducts/deployment-plan-4.md)


Outputs|
  * [Backout Plan](../workproducts/backout-plan-4.md)



Main Description

A rollback might be needed for a variety of reasons, including corruption of the production code base, inoperable components, an unplanned undesirable effect of the release on other production systems, an unhappy customer, etc. The Development team should provide the production support organization with a specific plan and decision criteria made available to them to avoid or minimize service interruptions.
---

Steps

Determine if backout plan exists | Determine whether the development team has a backout plan already written for a previous release. If so, part of that plan might be reusable. If this release is the development team's first, another development team with a similar feature set might have a plan that can be used as a starting point.
---

Develop the backout plan \(if applicable\)

If a backout plan does not exist, or one cannot be found to be used as a starting point, answer the questions documented in the [Artifact: Backout Plan](../workproducts/backout-plan-4.md) to start and develop a backout plan.
---

Update the backout plan \(if applicable\)

If a backout plan does exist that can be used as a baseline, review that plan and update, add, or delete information as necessary. When the plan is completed, it should reflect entirely the contents of the upcoming deployment only, not a release in the past or one in the future. In other words, the backout plan should be specific only to this release.
---

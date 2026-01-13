---
title: Verify Successful Deployment
source_url: practice.gen.production_release.base/tasks/verify_successful_deployment_8B4202DE.html
type: Task
uma_name: verify_successful_deployment
page_guid: _IAFEkuB-EeC1y_NExchKwQ
keywords:
- deployment
- successful
- verify
related:
  roles:
  - deployment-engineer-4
  - developer-11
  - product-owner-2
---


 Determine whether the rollout of a particular release into production has been successful or not.
---
Disciplines: [Deployment](../../../core/cat/disciplines/deployment-1.md)

Purpose

The purpose of this task is to confirm that a release has not caused any unintentional interruptions to service in the production environment.
---

Relationships

Roles| Primary Performer:
  * [Deployment Engineer](../../../core/role/roles/deployment-engineer-4.md)

| Additional Performers:
  * [Developer](../../../core/role/roles/developer-11.md)
  * [Product Owner](../../../core/role/roles/product-owner-2.md)
---|---|---
Inputs| Mandatory:
  * [Release](../workproducts/release-4.md)

| Optional:
  * [Deployment Plan](../workproducts/deployment-plan-4.md)



Main Description

Using the success criteria documented either in the deployment plan or in the backout plan, the deployment engineer, in collaboration with the development team, will determine whether the rollout can be declared a success or not.  If the deployment is successful, the previously prepared release communiques should be delivered. If the deployment is unsuccessful, then the backout plan should be invoked.
---

Steps

Test production release | In this step, automated smoke tests should be run to determine whether key components were deployed successfully. These tests should be brief but revealing enough to quickly determine the validity of the deployment.
---

Run manual tests

If the automated smoke tests are successful, run several complex manual tests to simulate key end user behavior. These tests should be executed by development team members or stakeholders recruited specifically for this purpose.
---

Determine if release should be reversed

In some situations, problems with the release might be encountered but are not serious enough to reverse the deployment. If the problem\(s\) associated with the release can be fixed easily, and if they are not detrimental to the production environment, an emergency bug fix \(EBF\) might be the answer. In that case, the release is not backed out; rather, an EBF is scheduled to be executed as soon as possible.
---

---
title: Verify Successful Deployment
source_url: process.openup.base/capabilitypatterns/verify_successful_deployment_1BB58D68.html
type: TaskDescriptor
uma_name: verify_successful_deployment
page_guid: _y7a0KZiLEeGOvpP1fVrVNA
keywords:
- deployment
- successful
- verify
related:
  other:
  - deployment-engineer-2
  - developer
  - product-owner
---


 Determine whether the rollout of a particular release into production has been successful or not.
---

Purpose

The purpose of this task is to confirm that a release has not caused any unintentional interruptions to service in the production environment.
---

Relationships

Roles| Primary:
  * [Deployment Engineer](deployment-engineer-2.md)

| Additional:
  * [Developer](developer.md)
  * [Product Owner](product-owner.md)

| Assisting:
---|---|---|---
Inputs| Mandatory:
  * [Release](release-2.md)

| Optional:
  * [Deployment Plan](deployment-plan.md)

| External:
  * None



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

Properties

Multiple Occurrences| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Event Driven| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Ongoing| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Planned|
Repeatable| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

---
title: Execute Deployment Plan
source_url: process.openup.base/capabilitypatterns/execute_deployment_plan_87F3E91A.html
type: TaskDescriptor
uma_name: execute_deployment_plan
page_guid: _y7a0IJiLEeGOvpP1fVrVNA
keywords:
- deployment
- execute
- plan
related:
  other:
  - deployment-engineer-2
  - developer
---


 The deployment plan has all the unique instructions necessary to roll out a release.
---

Purpose

The purpose of this task is to ensure that the rollout is based on clear, validated, repeatable instructions and to reduce the risk of a deployment issue.
---

Relationships

Roles| Primary:
  * [Deployment Engineer](deployment-engineer-2.md)

| Additional:
  * [Developer](developer.md)

| Assisting:
---|---|---|---
Inputs| Mandatory:
  * [Deployment Plan](deployment-plan.md)
  * [Infrastructure](infrastructure.md)
  * [Release](release-2.md)

| Optional:
  * [Release Controls](release-controls.md)

| External:
  * None



Main Description

This task is straightforward: follow the procedures in the Deployment Plan for the rollout of a specific product release. If the deployment plan does not exist or it is poorly constructed, this task might be much more difficult.  The main point here is that to achieve a high probability of success, the development team should have previously developed a detailed plan that organizes and articulates all the unique instructions for deploying that particular release. Because an experienced deployment engineer normally executes this task, they might be able to overcome any missing deployment procedures or content. However, that is not an excuse for a development team to not develop the plan's contents.
---

Steps

Review deployment plan | Review the contents of the deployment plan to ensure that the production environment has all the dependent components installed and that the system is in the correct state. Also ensure that the release window is ready to be achieved.
---

Release code

When the preliminary review has been completed and the release window has started, deploy the release package into production. Depending on the release script and the size of the package, this installation might take anywhere from a few minutes to a few hours.  Monitor the release as the release script is run. Be prepared to terminate the script and back out the release if significant errors are encountered.
---

Properties

Multiple Occurrences| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Event Driven| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Ongoing| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Planned|
Repeatable| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

More Information

Checklists|
  * [Deployment Plan](../../../practice-general/production_release/guidances/checklists/deployment-plan-5.md)
---|---

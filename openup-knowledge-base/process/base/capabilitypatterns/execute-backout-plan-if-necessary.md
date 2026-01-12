---
title: Execute Backout Plan (if necessary)
source_url: process.openup.base/capabilitypatterns/execute_backout_plan_CDFFE70B.html
type: TaskDescriptor
uma_name: execute_backout_plan
page_guid: _y7a0HZiLEeGOvpP1fVrVNA
keywords:
- backout
- execute
- necessary
- plan
related:
  other:
  - deployment-engineer-2
  - developer
---


 If a particular release into production goes wrong, the plan for cleanly reversing that deployment is executed.
---

Purpose

The purpose of this task is to remove a specific release quickly and seamlessly from the production environment because the release has caused problems or because it has been determined by the stakeholder community as unfit for service.
---

Relationships

Roles| Primary:
  * [Deployment Engineer](deployment-engineer-2.md)

| Additional:
  * [Developer](developer.md)

| Assisting:
---|---|---|---
Inputs| Mandatory:
  * [Backout Plan](backout-plan-2.md)
  * [Release](release-2.md)

| Optional:
  * None

| External:
  * None



Main Description

Assuming a backout plan is available for this release, the deployment engineer \(or development team\) will follow the instructions for reversing the installation of the product into production, if there is a problem. While the plan might have been written with good intentions, sometimes key procedures are missing or have not been thought out. The team backing out the release should be aware that blindly following the backout plan might not be the best approach. It is best to consider the unique circumstances within which the deployment has failed and rely on common sense and experience when executing the backout plan.
---

Steps

Identify release problem\(s\) |  In the event that the release to production experiences problems, either during or after deployment, the backout plan should be invoked. However, the deployment engineer \(or development team\) must understand where the release went wrong so that the code can be fixed before the next release attempt. This is a critical step, but it should be done quickly so that the problematic release can be reversed before significant damage is done to the production environment.  Log the issues as critical defects as soon as possible and assign those defects to the appropriate team members for resolution.
---

Backout the release

Following the instructions in the backout plan, reverse the deployment. However, be aware that the backout plan instructions are a guide and should not always be taken literally. This interpretation is due to the fact that not every problematic condition can be documented in advance and because each real-world situation might be slightly different.
---

Determine if the backout was successful

Ascertain whether the reversal was successful. If not, key members of the release team, development team, or program level agile system team might need to be engaged to find and fix the problem\(s\).
---

Communicate the backout

Ensure that all interested parties are aware of the failed release. Because releases often take place at odd hours to minimize end user impact, use beeper-based notifications judiciously. In most cases, an email to key stakeholders \(such as the product owner and program manager\) might suffice. Following up with a phone call also might be warranted.
---

Properties

Multiple Occurrences| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Event Driven| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Ongoing| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Planned|
Repeatable| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

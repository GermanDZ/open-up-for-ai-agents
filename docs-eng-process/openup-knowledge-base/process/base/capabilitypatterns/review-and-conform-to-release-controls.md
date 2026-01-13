---
title: Review and Conform to Release Controls
source_url: process.openup.base/capabilitypatterns/review_conform_to_release_controls_D8F48DB4.html
type: TaskDescriptor
uma_name: review_conform_to_release_controls
page_guid: _y7az_piLEeGOvpP1fVrVNA
keywords:
- conform
- controls
- release
- review
related:
  other:
  - developer-5
---


 Release controls normally are specified by the deployment manager. These controls document the requirements to which all releases must conform before being placed into the production environment.
---

Purpose

The purpose of this task is to ensure that there are no \(or minimal\) negative impacts to existing production systems, products, services, and operations.
---

Relationships

Roles| Primary:
  * [Developer](developer-5.md)

| Additional: | Assisting:
---|---|---|---
Inputs| Mandatory:
  * [Release Controls](release-controls-1.md)

| Optional:
  * None

| External:
  * None



Main Description

Release controls describe the minimum number of requirements that a software package must adhere to before being released into production. This is especially important if a development team is new or emerging, because they might not be aware of the great responsibilities a deployment manager has. In fact, a deployment manager is responsible to senior management for ensuring that nothing is placed into production that does not conform to the rigid controls designed to protect the IT organization's ability to successfully deliver IT services to internal and external customers.  Release controls typically consist of the following:
  * Release or deployment plan
  * Backout plan
  * Release component definitions
  * Release package integrity verification
  * References to configuration items \(CIs\)
  * Customer approval
  * Ready for transfer to operations and support staff
---

Steps

Locate release controls | If the program's release controls are not readily available, the development team must engage the deployment manager and/or their deployment engineers to know where to find the release controls and be able to comply with them.
---

Review release controls

The development team should thoroughly review the release controls so that it understands what is expected before a release is accepted into the production environment. If the team has any questions or issues with the controls, team members should communicate directly with the deployment manager or the deployment engineer to understand the issues.
---

Ensure the team release conforms to the controls

Coordinated releases at the program level are very formal processes. They are formal for a very good reason - namely, the company's production environment could be corrupted and serious business ramifications could result, including:
  * Lost revenue
  * customer dissatisfaction
  * Fines resulting from legal noncompliance
  * Lost employee productivity

All development team members that contribute to a release are expected to adhere to all the controls defined at the program level. Non-compliance could result in multiple impacts:
  * The entire release being abandoned, which could lead to customer or end user dissatisfaction
  * The results of multiple feature development Sprint/Iterations not being included in the release
  * Embarrassment on the part of the development team member that did not comply with the controls
  * Loss of funding for that development team
---

Properties

Multiple Occurrences| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Event Driven| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Ongoing| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Planned|
Repeatable| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

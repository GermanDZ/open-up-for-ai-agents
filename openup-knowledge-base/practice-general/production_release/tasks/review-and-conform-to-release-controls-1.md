---
title: Review and Conform to Release Controls
source_url: practice.gen.production_release.base/tasks/review_conform_to_release_controls_6D9BB01D.html
type: Task
uma_name: review_conform_to_release_controls
page_guid: _IAIu9uB-EeC1y_NExchKwQ
keywords:
- conform
- controls
- deployment
- release
- review
related:
  roles:
  - developer-11
---


 Release controls normally are specified by the deployment manager. These controls document the requirements to which all releases must conform before being placed into the production environment.
---
Disciplines: [Deployment](../../../core/cat/disciplines/deployment-1.md)

Purpose

The purpose of this task is to ensure that there are no \(or minimal\) negative impacts to existing production systems, products, services, and operations.
---

Relationships

Roles| Primary Performer:
  * [Developer](../../../core/role/roles/developer-11.md)

| Additional Performers:
---|---|---
Inputs| Mandatory:
  * [Release Controls](../workproducts/release-controls-2.md)

| Optional:
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

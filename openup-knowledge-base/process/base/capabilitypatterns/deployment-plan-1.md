---
title: Deployment Plan
source_url: process.openup.base/capabilitypatterns/deployment_plan_212DAE67.html
type: WorkProductDescriptor
uma_name: deployment_plan
page_guid: _y7a0BpiLEeGOvpP1fVrVNA
keywords:
- deployment
- plan
related:
  other:
  - deployment-engineer-1
---


 A deployment plan is used to document all the information needed by deployment engineers to deploy a release successfully.
---

Purpose

The purpose of this work product is to capture, in one document, the unique information that will be consumed by deployment engineers before and during the deployment to production of a particular release package.
---

Relationships

Roles| Responsible:
  * [Deployment Engineer](deployment-engineer-1.md)

| Modified By:
---|---|---
Input To| Mandatory:
  * [Develop Release Communications](develop-release-communications.md)
  * [Install and Validate Infrastructure](install-and-validate-infrastructure.md)

| Optional:
  * [Develop Backout Plan](develop-backout-plan.md)

| External:
  * None



Main Description

The deployment plan should contain the unique instructions for deploying a particular version of a product. By "unique instructions" we mean those things that are not part of a deployment engineer's normal procedures. Rather, they often are specific procedures and timing constraints that a deployment engineer should be aware of as they are rolling out a particular release.  While a draft version of the deployment plan is typically developed by a development team, the deployment engineer is responsible for its contents and existence. A deployment plan normally consists of the following sections:
  * The scope of the release and a general overview of the capabilities to be deployed
  * The timing and dependencies for deploying components to various nodes
  * The risks or issues associated with the release based on a risk assessment
  * The customer organization, stakeholders, and end user community that will be impacted by the release
  * The person or persons who have the authority to approve the release as "ready for production"
  * The development team members responsible for delivering the release package to the Deployment Manager, along with contact information
  * The approach for transitioning the release package to the Deployment Engineer, including appropriate communications protocols and escalation procedures
  * The success criteria for this deployment; in other words, how will the Deployment Engineer know that the release is successful so it can report success
---

Properties

Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Planned| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

More Information

Checklists|
  * [Deployment Plan](../../../practice-general/production_release/guidances/checklists/deployment-plan-5.md)
---|---

---
title: Deployment Plan
source_url: practice.gen.production_release.base/workproducts/deployment_plan_121938C3.html
type: Artifact
uma_name: deployment_plan
page_guid: _IAJ9FeB-EeC1y_NExchKwQ
keywords:
- deployment
- plan
related:
  roles:
  - deployment-engineer-4
---


 A deployment plan is used to document all the information needed by deployment engineers to deploy a release successfully.
---
Domains: [Deployment](../../../core/cat/domains/deployment.md)

Purpose

The purpose of this work product is to capture, in one document, the unique information that will be consumed by deployment engineers before and during the deployment to production of a particular release package.
---

Relationships

Roles| Responsible:
  * [Deployment Engineer](../../../core/role/roles/deployment-engineer-4.md)

| Modified By:
  * [Deployment Engineer](../../../core/role/roles/deployment-engineer-4.md)
---|---|---
Tasks| Input To:
  * [Develop Release Communications](../tasks/develop-release-communications-1.md)
  * [Execute Deployment Plan](../tasks/execute-deployment-plan-1.md)
  * [Install and Validate Infrastructure](../tasks/install-and-validate-infrastructure-1.md)
  * [Package the Release](../tasks/package-the-release-1.md)
  * [Develop Backout Plan](../tasks/develop-backout-plan-1.md)
  * [Verify Successful Deployment](../tasks/verify-successful-deployment-1.md)

| Output From:
  * [Plan Deployment](../tasks/plan-deployment-1.md)



Description

Main Description|  The deployment plan should contain the unique instructions for deploying a particular version of a product. By "unique instructions" we mean those things that are not part of a deployment engineer's normal procedures. Rather, they often are specific procedures and timing constraints that a deployment engineer should be aware of as they are rolling out a particular release.  While a draft version of the deployment plan is typically developed by a development team, the deployment engineer is responsible for its contents and existence. A deployment plan normally consists of the following sections:
  * The scope of the release and a general overview of the capabilities to be deployed
  * The timing and dependencies for deploying components to various nodes
  * The risks or issues associated with the release based on a risk assessment
  * The customer organization, stakeholders, and end user community that will be impacted by the release
  * The person or persons who have the authority to approve the release as "ready for production"
  * The development team members responsible for delivering the release package to the Deployment Manager, along with contact information
  * The approach for transitioning the release package to the Deployment Engineer, including appropriate communications protocols and escalation procedures
  * The success criteria for this deployment; in other words, how will the Deployment Engineer know that the release is successful so it can report success
---|---

More Information

Checklists|
  * [Deployment Plan](../guidances/checklists/deployment-plan-5.md)
---|---

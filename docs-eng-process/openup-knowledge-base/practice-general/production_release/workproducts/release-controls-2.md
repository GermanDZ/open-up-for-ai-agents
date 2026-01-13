---
title: Release Controls
source_url: practice.gen.production_release.base/workproducts/release_controls_B00EB28E.html
type: Artifact
uma_name: release_controls
page_guid: _IAJWA-B-EeC1y_NExchKwQ
keywords:
- controls
- deployment
- release
related:
  roles:
  - deployment-manager
---


 Release controls normally are established by IT management and enforced by the deployment manager.
---
Domains: [Deployment](../../../core/cat/domains/deployment.md)

Purpose

The purpose of this work product is to identify all the requirements to which a release package must conform to be considered "deployable."
---

Relationships

Roles| Responsible:
  * [Deployment Manager](../../../core/role/roles/deployment-manager.md)

| Modified By:
---|---|---
Tasks| Input To:
  * [Package the Release](../tasks/package-the-release-1.md)
  * [Review and Conform to Release Controls](../tasks/review-and-conform-to-release-controls-1.md)
  * [Develop Release Communications](../tasks/develop-release-communications-1.md)
  * [Execute Deployment Plan](../tasks/execute-deployment-plan-1.md)
  * [Install and Validate Infrastructure](../tasks/install-and-validate-infrastructure-1.md)

| Output From:

Description

Main Description|  Some common release controls are:
  * A release or deployment plan must be documented and reviewed with the Deployment Manager \(or the release organization\). This plan must address how risks, issues, or code deviations are to be handled during the key timeframe leading up to the actual release
  * The components of each release package must be defined, integrated, and compatible with one another
  * The integrity of each release package must be verified and maintained
  * References to the configuration items \(CIs\) that the release package represents, if applicable
  * The customer for which the application is being developed must approve the release, indicating that the user community \(or a specific subset\) is ready to receive and use the requisite capabilities of the release
  * Each release package must be capable of being backed out of production without negatively impacting the remaining production environment
  * The contents of each release package must be transferred to operations and support staff with sufficient documentation and knowledge transfer so that those organizations can effectively support the released capabilities in production
---|---

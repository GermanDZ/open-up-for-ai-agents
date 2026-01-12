---
title: Release Controls
source_url: process.openup.base/capabilitypatterns/release_controls_6E02B832.html
type: WorkProductDescriptor
uma_name: release_controls
page_guid: _y7a0AZiLEeGOvpP1fVrVNA
keywords:
- controls
- release
related:
  other:
  - review-and-conform-to-release-controls
  - develop-release-communications
  - install-and-validate-infrastructure
---


 Release controls normally are established by IT management and enforced by the deployment manager.
---

Purpose

The purpose of this work product is to identify all the requirements to which a release package must conform to be considered "deployable."
---

Relationships

Input To| Mandatory:
  * [Review and Conform to Release Controls](review-and-conform-to-release-controls.md)

| Optional:
  * [Develop Release Communications](develop-release-communications.md)
  * [Install and Validate Infrastructure](install-and-validate-infrastructure.md)

| External:
  * None
---|---|---|---

Main Description

Some common release controls are:
  * A release or deployment plan must be documented and reviewed with the Deployment Manager \(or the release organization\). This plan must address how risks, issues, or code deviations are to be handled during the key timeframe leading up to the actual release
  * The components of each release package must be defined, integrated, and compatible with one another
  * The integrity of each release package must be verified and maintained
  * References to the configuration items \(CIs\) that the release package represents, if applicable
  * The customer for which the application is being developed must approve the release, indicating that the user community \(or a specific subset\) is ready to receive and use the requisite capabilities of the release
  * Each release package must be capable of being backed out of production without negatively impacting the remaining production environment
  * The contents of each release package must be transferred to operations and support staff with sufficient documentation and knowledge transfer so that those organizations can effectively support the released capabilities in production
---

Properties

Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Planned| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

---
title: Install and Validate Infrastructure
source_url: practice.gen.production_release.base/tasks/install_validate_infrastructure_65313685.html
type: Task
uma_name: install_validate_infrastructure
page_guid: _IAIH4eB-EeC1y_NExchKwQ
keywords:
- infrastructure
- install
- validate
related:
  roles:
  - deployment-engineer-4
  - developer-11
---


 Any infrastructure components needed to support a release must be procured, installed, and tested.
---
Disciplines: [Deployment](../../../core/cat/disciplines/deployment-1.md)

Purpose

The purpose of this task is to ensure that all the necessary infrastructure components needed to support a successful release are in place.
---

Relationships

Roles| Primary Performer:
  * [Deployment Engineer](../../../core/role/roles/deployment-engineer-4.md)
  * [Developer](../../../core/role/roles/developer-11.md)

| Additional Performers:
---|---|---
Inputs| Mandatory:
  * [Deployment Plan](../workproducts/deployment-plan-4.md)

| Optional:
  * [Release Controls](../workproducts/release-controls-2.md)


Outputs|
  * [Infrastructure](../workproducts/infrastructure-2.md)



Main Description

A release package cannot be deployed to production if the environmental infrastructure within which the release will be run is not sufficiently built or tested. Whether the release is deployed as a "push" \(where the application is deployed from a central point and proactively delivered to target locations\) or a "pull" \(where the application is made available at central point and pulled by a user at a time of their choosing\), the infrastructure needed to support the application must be considered and implemented.  Some key aspects of installing and/or validating the desired infrastructure:
  * Identify the requirements and components of the environment configuration
  * Determine the lead times required to establish the infrastructure environments
  * Procure and install the infrastructure components that are not yet available
  * Test the newly installed infrastructure components
  * Test the integration of newly installed components with the rest of the environmental configuration
  * Validate other aspects of the infrastructure including:
    * Security components and their integration
    * Database connectivity and security
    * License management, as appropriate
    * Configuration management, in terms of configuration items \(CIs\)
---

Steps

Identify infrastructure needs | Identify and describe all the components of the infrastructure that are needed to support the upcoming release. These requirements should be based completely on the feature set that is about to be deployed, not on intended future needs.
---

Procure components

Determine how long it will reasonably take to procure the needed components and to engage the appropriate division in the organization to place the order. Be sure to work with the procurement agency to track the order and to identify any issues with that order. Ultimately, the development team, not the procurement agency, is responsible for ensuring that the correct infrastructure components are in place.
---

Schedule components for installation

After the procured components arrive, schedule to have them installed by the IT operations group\(s\) that control the production environment. The development team should be developing tests to confirm the correct installation at this time.
---

Install and test components

When the components have been installed, be prepared to run the validation tests developed in the previous step. These tests should not only verify the individual components' readiness, but also should validate their integration with each other and with legacy components.
---

Validate other component aspects

As the validation testing is underway, the development team also should consider how the newly installed components impact overall system security, whether or not database connectivity and security have been compromised, and what impact they have on the configuration management database that contains an inventory of CIs.  Also reconcile any licensing issues for the new components with the division that is responsible for documenting and tracking enterprise licenses.
---

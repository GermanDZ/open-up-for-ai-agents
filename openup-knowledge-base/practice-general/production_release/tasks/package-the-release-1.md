---
title: Package the Release
source_url: practice.gen.production_release.base/tasks/package_the_release_7FC3863C.html
type: Task
uma_name: package_the_release
page_guid: _IAEdgOB-EeC1y_NExchKwQ
keywords:
- package
- release
related:
  roles:
  - developer-11
  - deployment-engineer-4
---


 Each release should be built and packaged in a standard, controlled, and repeatable manner.
---
Disciplines: [Deployment](../../../core/cat/disciplines/deployment-1.md)

Purpose

The purpose of this task is to render a complete, deployable package capable of being released into the production environment by the deployment engineer.
---

Relationships

Roles| Primary Performer:
  * [Developer](../../../core/role/roles/developer-11.md)

| Additional Performers:
  * [Deployment Engineer](../../../core/role/roles/deployment-engineer-4.md)
---|---|---
Inputs| Mandatory:
  * [Deployment Plan](../workproducts/deployment-plan-4.md)
  * [Release Controls](../workproducts/release-controls-2.md)

| Optional:
  * None


Outputs|
  * [Release](../workproducts/release-4.md)



Main Description

The key activities normally used to package a release:
  * Assemble the components and integrate them through a normal \(i.e., continuous integration\) or release build script
  * Install the release package in one or more test environments and verify its integrity
  * Tag the elements of the release package in the code base to create a baseline
  * Package appropriate documentation to accompany the release:
    * Deployment plan
    * Build plan, procedures, and scripts
    * Backout plan
    * Relevant licensing information
    * Relevant infrastructure information
    * Release communiques
---

Steps

Assemble components | Question all the developers on the development team to determine which components are ready for packaging. Only package those components that were completed and accepted during the previous feature development sprint/iterations. Components that were not finished or not accepted should not be bundled, unless the customer has granted an exception or they are infrastructure-related components.
---

Test the release

After the components have been packaged and built, that executable should be installed and run in a test environment that mimics the production environment. A "staging" environment usually is maintained for this purpose. Testing typically includes a "smoke test" in which key features are exercised to highlight any unplanned behavior.
---

Tag source code repository

In the team's configuration management \(CM\) tool, tag all the components that went into the release package so that the package can be reconstructed at a later date, if needed. This tag is known as the release "baseline."
---

Package release documentation

Gather all the product, user, and support documentation developed earlier in the production release sprint/iteration and add it to the release package.
---

Deliver release package

When the entire release package, including documentation, is ready, deliver it to the deployment manager and the release team in a timely manner. Be prepared to answer questions from the deployment engineer, especially questions about conformity to release controls.
---

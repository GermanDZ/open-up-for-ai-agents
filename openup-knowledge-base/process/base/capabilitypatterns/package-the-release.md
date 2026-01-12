---
title: Package the Release
source_url: process.openup.base/capabilitypatterns/package_the_release_FED024DC.html
type: TaskDescriptor
uma_name: package_the_release
page_guid: _y7a0GJiLEeGOvpP1fVrVNA
keywords:
- package
- release
related:
  other:
  - developer
  - deployment-engineer-2
---


 Each release should be built and packaged in a standard, controlled, and repeatable manner.
---

Purpose

The purpose of this task is to render a complete, deployable package capable of being released into the production environment by the deployment engineer.
---

Relationships

Roles| Primary:
  * [Developer](developer.md)

| Additional:
  * [Deployment Engineer](deployment-engineer-2.md)

| Assisting:
---|---|---|---
Inputs| Mandatory:
  * [Deployment Plan](deployment-plan.md)
  * [Release Controls](release-controls.md)

| Optional:
  * None

| External:
  * None


Outputs|
  * [Release](release-2.md)



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

Properties

Multiple Occurrences| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Event Driven| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Ongoing| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Planned|
Repeatable| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

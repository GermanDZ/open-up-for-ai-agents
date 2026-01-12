---
title: Build
source_url: process.openup.base/capabilitypatterns/build_DEC44124.html
type: WorkProductDescriptor
uma_name: build
page_guid: _N8kF8UVEEeK93ZZqiMLBsA
keywords:
- build
- system
---

 An operational version of a system or part of a system that demonstrates a subset of the capabilities to be provided in the final product.
---

Purpose

Deliver incremental value to the user and customer, and provide a testable artifact for verification.
---

Relationships

Fulfilled Slots|
  * [\[Technical Implementation\]](./../../process.openup.base/capabilitypatterns/technical_implementation_slot_4A0321FD.html)
---|---
Roles| Responsible:
  * [Developer](developer-6.md)

| Modified By:
Input To| Mandatory:
  * [Run Tests](run-tests.md)

| Optional:
  * [Implement Tests](implement-tests.md)

| External:
  * None



Main Description

This working version of the system or part of the system is the result of putting the implementation through a build process \(typically an automated build script\) that creates an executable version, or one that runs. This executable version will typically have a number of supporting files that are also considered part of this artifact.
---

Properties

Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Planned| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

Tailoring

Impact of not having|  Without this artifact, there is no operational version of the system.
---|---
Reasons for not needing|  This artifact is not needed if the development of an application is not within the scope of the solution.
Representation Options|  This work product is almost always a product made up of numerous parts required to make the executable system. Therefore, a build is more than just executable files; it also includes such things as configuration files, help files, and data repositories that will be put together, resulting in the product that the users will run. The specifics of those parts will vary by technology in use.

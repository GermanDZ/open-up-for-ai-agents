---
title: Build
source_url: core.tech.common.extend_supp/workproducts/build_95D7D8FD.html
type: Artifact
uma_name: build
page_guid: _0YuXEMlgEdmt3adZL5Dmdw
keywords:
- build
- system
---

 An operational version of a system or part of a system that demonstrates a subset of the capabilities to be provided in the final product.
---
Domains: [Development](../../cat/domains/development.md)

Purpose

Deliver incremental value to the user and customer, and provide a testable artifact for verification.
---

Relationships

Fulfilled Slots|
  * [\[Technical Implementation\]](./../../core.tech.slot.base/workproducts/technical_implementation_slot_E92F6A39.html)
---|---
Roles| Responsible:
  * [Developer](../../role/roles/developer-11.md)

| Modified By:
  * [Developer](../../role/roles/developer-11.md)


Tasks| Input To:
  * [Implement Developer Tests](../../../practice-technical/test_driven_development/tasks/implement-developer-tests-1.md)
  * [Integrate and Create Build](../../../practice-technical/continuous_integration/tasks/integrate-and-create-build-1.md)
  * [Run Developer Tests](../../../practice-technical/test_driven_development/tasks/run-developer-tests-1.md)
  * [Run Tests](../../../practice-technical/concurrent_testing/tasks/run-tests-1.md)
  * [Implement Solution](../../../practice-technical/test_driven_development/tasks/implement-solution-1.md)
  * [Implement Tests](../../../practice-technical/concurrent_testing/tasks/implement-tests-1.md)
  * [Refine the Architecture](../../../practice-technical/evolutionary_arch/tasks/refine-the-architecture-1.md)

| Output From:
  * [Integrate and Create Build](../../../practice-technical/continuous_integration/tasks/integrate-and-create-build-1.md)



Description

Main Description|  This working version of the system or part of the system is the result of putting the implementation through a build process \(typically an automated build script\) that creates an executable version, or one that runs. This executable version will typically have a number of supporting files that are also considered part of this artifact.
---|---

Tailoring

Impact of not having|  Without this artifact, there is no operational version of the system.
---|---
Reasons for not needing|  This artifact is not needed if the development of an application is not within the scope of the solution.
Representation Options|  This work product is almost always a product made up of numerous parts required to make the executable system. Therefore, a build is more than just executable files; it also includes such things as configuration files, help files, and data repositories that will be put together, resulting in the product that the users will run. The specifics of those parts will vary by technology in use.

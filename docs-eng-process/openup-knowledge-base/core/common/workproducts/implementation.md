---
title: Implementation
source_url: core.tech.common.extend_supp/workproducts/implementation_AFFEFC46.html
type: Artifact
uma_name: implementation
page_guid: _JqYbgJ01EdyQ3oTO93enUw
keywords:
- files
- implementation
---

 Software code files, data files, and supporting files \(such as online help files\) that represent the raw parts of a system that can be built.
---
Domains: [Development](../../cat/domains/development.md)

Purpose

To represent the physical parts that compose the system to be built, and to organize the parts in a way that is understandable and manageable.
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
  * [Implement Solution](../../../practice-technical/test_driven_development/tasks/implement-solution-1.md)



Description

Main Description|  This artifact is the collection of one or more of these elements:
  * Source code files
  * Data files
  * Build scripts
  * Other files that are transformed into the executable system
---|---

Tailoring

Impact of not having| Without this artifact, there is no way to produce the application to be delivered as part of the solution.
---|---
Reasons for not needing| You do not need to produce this artifact if the actual development of an application is not in the scope of the solution.
Representation Options|  Implementation files are represented as files in the local file system. File folders \(directories\) are represented as packages, which group the files into logical units.

---
title: Implementation
source_url: process.openup.base/capabilitypatterns/implementation_1DA9E76A.html
type: WorkProductDescriptor
uma_name: implementation
page_guid: _dC4w4JojEd2XAqcHTC2Siw
keywords:
- files
- implementation
---

 Software code files, data files, and supporting files \(such as online help files\) that represent the raw parts of a system that can be built.
---

Purpose

To represent the physical parts that compose the system to be built, and to organize the parts in a way that is understandable and manageable.
---

Relationships

Fulfilled Slots|
  * [\[Technical Implementation\]](./../../process.openup.base/capabilitypatterns/technical_implementation_slot_E32AE6DF.html)
---|---
Roles| Responsible:
  * [Developer](developer-7.md)

| Modified By:
  * [Developer](developer-7.md)


Input To| Mandatory:
  * [Implement Developer Tests](implement-developer-tests.md)
  * [Integrate and Create Build](integrate-and-create-build.md)
  * [Run Developer Tests](run-developer-tests.md)

| Optional:
  * [Implement Solution](implement-solution.md)

| External:
  * None


Output From|
  * [Implement Solution](implement-solution.md)



Main Description

This artifact is the collection of one or more of these elements:
  * Source code files
  * Data files
  * Build scripts
  * Other files that are transformed into the executable system
---

Properties

Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Planned| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

Tailoring

Impact of not having| Without this artifact, there is no way to produce the application to be delivered as part of the solution.
---|---
Reasons for not needing| You do not need to produce this artifact if the actual development of an application is not in the scope of the solution.
Representation Options|  Implementation files are represented as files in the local file system. File folders \(directories\) are represented as packages, which group the files into logical units.

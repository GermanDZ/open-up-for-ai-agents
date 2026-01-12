---
title: Change Set
source_url: core.mgmt.common.extend_supp/guidances/concepts/change_set_430BF233.html
type: Concept
uma_name: change_set
page_guid: _1QU9MAIoEdyLh7vsrHZ4YA
keywords:
- change
related:
  other:
  - how-to-adopt-the-continuous-integration-practice
  tasks:
  - integrate-and-create-build-1
---


 A change set is a meaningful set of related changes made to the implementation and supporting artifacts for a particular purpose.
---

Relationships

Related Elements|
  * [How to adopt the Continuous Integration practice](../../../../practice-technical/continuous_integration/guidances/roadmaps/how-to-adopt-the-continuous-integration-practice.md)
  * [Integrate and Create Build](../../../../practice-technical/continuous_integration/tasks/integrate-and-create-build-1.md)
---|---

Main Description

A change set is a logical grouping of related changes made to the implementation and supporting artifacts. Change sets are defined for a specific purpose and encompass all changes made to achieve that purpose.  Change sets allow for multiple related changes to be referred to as single item, simplifying tracking of that item's progress through the development lifecycle.  The change set forms the basic unit of configuration control, accountability, and collaboration on the development team. Additionally, change sets track the dependencies between artifact changes that facilitate discovery and correction of configuration inconsistencies. The relationship between items in a change set can be used to verify that all related changes have been included in a build.  Change sets have the following characteristics:

  1. Change sets consist of changes that belong together and can be built and tested together.
  2. Change sets are owned by a single developer.
  3. Change sets represent small, testable changes to the system.

Multiple change sets may be related to a single work item.  Change sets are also known as CM tasks, activity change sets, change lists or change packages.
---

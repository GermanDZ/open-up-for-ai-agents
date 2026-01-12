---
title: Integrate and Create Build
source_url: practice.tech.continuous_integration.base/tasks/integrate_and_create_build_6191BF5D.html
type: Task
uma_name: integrate_and_create_build
page_guid: _kkZBgJOKEdyaRbFYa4AN4A
keywords:
- build
- create
- integrate
related:
  roles:
  - developer-11
---


 This task describes how to integrate all changes made by developers into the code base and perform the minimal testing to validate the build.
---
Disciplines: [Development](../../../core/cat/disciplines/development-1.md)

Purpose

The purpose of this task is to integrate all changes made by all developers into the code base and perform the minimal testing on the system increment in order to validate the build. The goal is to identify integration issues as soon as possible, so they can be corrected easily by the right person, at the right time.
---

Relationships

Roles| Primary Performer:
  * [Developer](../../../core/role/roles/developer-11.md)

| Additional Performers:
---|---|---
Inputs| Mandatory:
  * [\[Technical Implementation\]](./../../core.tech.slot.base/workproducts/technical_implementation_slot_E92F6A39.html)
  * [Test Script](../../../core/common/workproducts/test-script.md)

| Optional:
  * None


Outputs|
  * [Build](../../../core/common/workproducts/build.md)



Steps

Integrate implemented elements |  In the relevant [Workspace](../guidances/concepts/workspace.md), combine all completed [Change Set](../../../core/common/guidances/concepts/change-set.md)s that are not in the latest baseline. Resolve any conflicting versions of the artifacts by either removing one of the change sets that created the conflict or by creating a new change set that includes merged versions of the conflicting artifacts.
---

Create build

Create the build. The details of this step depend upon the implementation language and development environment and may involve compiling and linking \(in the case of compiled languages\) and/or other processes that result in an executable increment of the system.  Examples of these steps include:

  1. Compiling and linking the source artifacts to create an executable
  2. Loading binary objects on a test bench or simulator
  3. Running a script to load/update database schemas
  4. Packaging and deploying web applications
---

Test integrated elements

Re-run the developer tests against the integrated elements to verify that they behave the same as they did in isolation. Ensure that the scope of these tests is as broad as possible, which ensures that the latest change sets did not cause failing developer tests in other areas of the system.
---

Run "Smoke Tests"

Several builds will be created in each iteration. For each build, this step is performed only when change sets have been delivered to satisfy the requirements of that build.  Execute a sub-set of the system tests to ensure that the build is suitable prior to committing resources to the full scope of system testing. While the level of testing will vary, focus on gaining confidence that the increment is of sufficient quality to establish a baseline for system testing.
---

Make changes available

When tests are successfully completed and the build is considered "good," the results are made available to the rest of the team by [Promoting Changes](../guidances/guidelines/promoting-changes.md). The details of this step depend on the configuration management tools in use, but in general this involves committing a tested change set to the CM repository so that it serves as the basis of development for the next increment of the system. This is the essence of [Continuous Integration](../guidances/guidelines/continuous-integration.md).
---

Key Considerations

In order to be effective at applying the practice of [Continuous Integration](../guidances/guidelines/continuous-integration.md), the time to integrate, build, and test the increment must be short enough that it can be performed several times per day. Changes should be broken down into relatively small [Change Set](../../../core/common/guidances/concepts/change-set.md)s that can be implemented, integrated and tested quickly.
---

More Information

Concepts|
  * [Change Set](../../../core/common/guidances/concepts/change-set.md)
  * [Workspace](../guidances/concepts/workspace.md)
---|---
Guidelines|
  * [Continuous Integration](../guidances/guidelines/continuous-integration.md)
  * [Promoting Changes](../guidances/guidelines/promoting-changes.md)

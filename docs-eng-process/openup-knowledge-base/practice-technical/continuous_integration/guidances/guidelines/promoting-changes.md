---
title: Promoting Changes
source_url: practice.tech.continuous_integration.base/guidances/guidelines/promoting_changes_9087B764.html
type: Guideline
uma_name: promoting_changes
page_guid: _SM4YIL6dEdqti4GwqTkbsQ
keywords:
- area
- changes
- promoting
related:
  tasks:
  - integrate-and-create-build-1
---


 This guideline describes how to promote a set of related changes up through a set of tiers from a private development area to a release area.
---

Relationships

Related Elements|
  * [Integrate and Create Build](../../tasks/integrate-and-create-build-1.md)
---|---

Main Description

During iterative software development, the team creates numerous [Change Set](../../../../core/common/guidances/concepts/change-set.md)s that are combined into a [Build](../../../../core/common/workproducts/build.md). A build is initiated by combining the work completed by one or more developers and resolving any conflicts between those changes. Ideally a build is then subjected to a battery of tests to determine if it is of sufficient quality to move into production.  As the changes progress from development towards production, its beneficial to know two characteristics:  **Test Context** – identifying the elements and their versions that are tested together
  * What changes are in this build \(completed work items\)
  * What changes are partially in this build \(work items that are partially complete\)
  * What changes are not in this build \(work items that are not reflected at all in this build\)
**Verification Level** – identifying what amount of testing is complete. For example,
  * Unit Tested
  * Integration Tested
  * System Tested

The promotion lifecycle coordinates and synchronizes the efforts of the development team. This lifecycle consists of the following steps:
  * Changes are introduced into the system in the form of completed [Change Set](../../../../core/common/guidances/concepts/change-set.md)s
  * A build is generated clearly identifying the changes included in the build
  * Testing is conducted
  * When testing is successful the changes are marked with the appropriate verification level through labeling, baselining or other related techniques.

Ultimately all required testing is complete and a new system increment is ready.  Separate [Workspace](../concepts/workspace.md)s are often used as the context for each level of testing. As changes are added to the [Workspace](../concepts/workspace.md), it is verified for consistency and tested. This ensures that the effort of testing a build is applied to the correct set of changes, makes the context for the tests stable, and also allows developers to continue working on the next build while the tests are being conducted.  A change promotion lifecycle such as this offers three key benefits

  1. Reduces effort because there is no reason to execute the tests in the next stages until the changes passes the previous stage. For example you would not commit the resources to system testing a build until it passes developer tests.
  2. Helps to ensure that a change which is moved into production has been subjected to the appropriate level of testing first.
  3. Simplifies debugging since developers can base their work on a proven set of changes in relative isolation from destabilizing changes from other developers

For an example of this approach see [Development Sandboxes: An Agile "Best" Practice.](http://www.agiledata.org/essays/sandboxes.html)
---

---
title: Continuous Integration
source_url: practice.tech.continuous_integration.base/guidances/guidelines/continuous_integration_13C1A8CA.html
type: Guideline
uma_name: continuous_integration
page_guid: _i8bUEL6cEdqti4GwqTkbsQ
keywords:
- continuous
- integration
related:
  tasks:
  - integrate-and-create-build-1
---


 This guideline describes how to apply continuous integration to reduce the risk and effort associated with late integration.
---

Relationships

Related Elements|
  * [Integrate and Create Build](../../tasks/integrate-and-create-build-1.md)
---|---

Main Description

Continuous integration is a software development practice that completely rebuilds and tests the application frequently \-- ideally, every time a change is introduced. This approach provides many benefits as outlined in [Continuous Integration](../practices/continuous-integration-1.md) and in [\[WIKP-CI\]](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html#WIKP-CI).

###  Basic steps

The detailed application of continuous integration depends on which tools you use \(configuration management system, automated build tool, automated test tool, and so forth\). However, these are the basic steps:

  1. A developer, let's call her Jane, selects a work item to work on.
  2. Jane updates her [Workspace](../concepts/workspace.md) to include the most recent [\[Technical Implementation\]](./../../../core.tech.slot.base/workproducts/technical_implementation_slot_E92F6A39.html) from the integration workspace.
  3. Jane makes her changes in her workspace to both her developer tests and to the implementation, and then she tests the changes.
  4. Before committing the changes, Jane updates her workspace again \(because other developers may have introduced conflicting changes\) and reruns her developer tests.
  5. If these tests are successful, the changes are promoted \(see [Guideline: Promoting Changes](promoting-changes.md)\) to the integration workspace.
  6. A complete [Build](../../../../core/common/workproducts/build.md) of the application is performed by using the implementation from the integration workspace, and the entire suite of developer tests is run on this build.
  7. If any of these tests fail, the team is notified, and the failed test should be addressed as soon as possible.
  8. This process repeats as the team develops and continuously integrates and tests functionality in small increments.

###  Constraints

Conceptually, continuous integration can be performed manually \(see [\[SHO06\]](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html#SHO06) for example\). However, in practice, there are several constraints that must be respected for it to be effective:

  1. All changes must be introduced into a tested configuration that you know to be good.
  2. The integrate-build-test cycle must be fast enough so that it can be completed quickly and the team notified of the results. Many published guidelines promote a 10-minute cycle.
  3. Keep the [Change Set](../../../../core/common/guidances/concepts/change-set.md)s small enough so that the work can be completed and integration performed several times per day. Many published guidelines promote a 2- to 4-hour cycle between integrations.

These constraints imply the need for a configuration management \(CM\) repository to maintain configuration information \(Item 1 listed previously\), automated build and test tools to meet the turnaround constraints \(Item 2\), and proper planning and discipline by developers to ensure that their work items and change sets are small enough to complete quickly \(Item 3\).  For a more detailed description of continuous integration, see [\[FOW06\]](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html#FOW06) or [\[WIKP-CI\]](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html#WIKP-CI).
---

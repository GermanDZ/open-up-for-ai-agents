---
title: Workspace
source_url: practice.tech.continuous_integration.base/guidances/concepts/workspace_722BBA90.html
type: Concept
uma_name: workspace
page_guid: _0cEmAMlgEdmt3adZL5Dmdw
keywords:
- developers
- workspace
related:
  tasks:
  - integrate-and-create-build-1
---


 Workspace refers to storage areas where developers can implement and test code in accordance with the project's adopted standards in relative isolation from other developers.
---

Relationships

Related Elements|
  * [Integrate and Create Build](../../tasks/integrate-and-create-build-1.md)
---|---

Main Description

On small teams, shared workspaces may work fine, but you must coordinate activities between team members to avoid conflicts.  A better approach is for each developer to have a reasonably private area for the development and testing of their work products. This workspace should be insulated so that destabilizing or conflicting changes made by others do not interfere with progress. However, it should not be isolated to the extent that the developer's work is unavailable to the team.  In addition, insulated workspaces can be created for each test phase, such as integration testing and system testing. This approach to workspaces provides several benefits [\[WIB04\]](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html):
  * Developers can develop, test, and debug software changes without being affected by others team members' changes until they are ready. When ready, developers can update their insulated environments to test the latest changes from other developers.
  * With separate workspaces for integration and system testing, a team could use a methodology that ensures changes have passed integration testing before other developers get them, thereby minimizing the time spent solving integration problems. For example, if two team members check in incompatible changes without realizing it, and both changes are immediately available to everyone on the team, all team members might waste time trying to resolve the broken build. Conversely, if both changes must pass integration testing before being distributed to others, the problem could be found and fixed by one person with minimal disruption to the team.
  * By setting up an integration area to collect and build the latest changes, the team can integrate early and often. That is a well-known best practice for reducing overall cost and time to deliver software projects.
  * The system test area, which is used for preparing releases, is insulated from developers' ongoing changes and contains only configurations that have passed integration testing. This lets you control the content of the release while still enabling developers to continue working.
---

---
title: Verify Tool Configuration and Installation
source_url: practice.mgmt.project_process_tailoring.base/tasks/verify_tool_config_installation_22B5077F.html
type: Task
uma_name: verify_tool_config_installation
page_guid: _jcjbMEmgEd-UYMQAaXd4fQ
keywords:
- configuration
- installation
- tool
- verify
related:
  roles:
  - tool-specialist-1
---


 This task describes how to verify that the Development Configuration is ready to be used by the project.
---
Disciplines: [Environment](../../../core/cat/disciplines/environment-1.md)

Purpose

The purpose of this task is to verify that the tools can be used to develop the system.
---

Relationships

Roles| Primary Performer:
  * [Tool Specialist](../../../core/role/roles/tool-specialist-1.md)

| Additional Performers:
---|---|---
Inputs| Mandatory:
  * [Tools](../workproducts/tools-1.md)

| Optional:
  * None


Outputs|
  * [Tools](../workproducts/tools-1.md)



Main Description

The tools and the development infrastructure has to be verified before the project starts using them. How this is done will clearly vary dependent upon skills, technology, and tools.
---

Steps

Verify the Environment  | Verify the environment contains the correct hardware, software, and data. Verify that the correct hardware is installed. This may be done visually or through a tool \(such as using Windows Properties for My Computer\).
---

Verify the Tools

Verify that the correct software configuration is installed. This may be done by looking at the registry settings, 'ini' files, or by launching the tool and looking at some information options or configuration options.
---

Verify Data

Verify the data contains the appropriate data. Verifying data may require using tools to visually inspect the data, or using an application to display the data. At some point, one or more use cases may be selected and executed \(one or more scenarios\) for each tool to ensure the tool and the results of using the tool are consistent with the need.
---

Run the Tools

Assemble a small team of people who know the [Tools](../workproducts/tools-1.md)and the [Project Defined Process](../../../core/common/workproducts/project-defined-process-1.md) well, and let them run the tools.
  * Test multi site, many colliding users
  * At least one use case scenario for each tool has been executed to verify the appropriate installation and configuration of the tools.
  * Try the normal scenarios of the development process and in the tool guidelines.
  * Test the integration between different tools.

Issue change requests if necessary.
---

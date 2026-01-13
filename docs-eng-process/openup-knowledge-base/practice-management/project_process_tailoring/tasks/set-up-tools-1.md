---
title: Set Up Tools
source_url: practice.mgmt.project_process_tailoring.base/tasks/setup_tools_93457979.html
type: Task
uma_name: setup_tools
page_guid: _okIOcEmfEd-UYMQAaXd4fQ
keywords:
- tools
related:
  roles:
  - tool-specialist-1
---



---
Disciplines: [Environment](../../../core/cat/disciplines/environment-1.md)

Purpose

The purpose of this task is to:
  * Install the tools
  * Customize the tools.
  * Make the tools available to the end users.
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

Many software-development tools support teams of people, with several users working with information stored in a shared repository. Each user uses the tool on their personal computer \(client\) and the shared repository is stored on a central server. In this case the tool must be installed on the server and on the clients. Customizing the tool is done both on the server and on the client.  There are tools that do not use a shared repository, such as compilers, debuggers, editors, graphic tools, etc. These tools can simply be installed on the users' computers. It may still be needed to customize the tools so that all members of the project use the tool in the same way.  The approach should be to automate as much as possible of the installation and customization procedures.
---

Steps

Install the Tool on the Server  |  Identify what other software is required for the specific tool to work, and install this software. For example, a tool may require a database management system \(DBMS\) be installed first.  When you have installed the support software, you can install the tool on the server.
---

Customize the Tool

Decide how to customize the tool so that it supports the [Project Defined Process](../../../core/common/workproducts/project-defined-process-1.md) in the best way.  In addition to customizing the tools, you should set up user groups and access rights on the server. In some cases, a tool may provide its own mechanisms for this. In other cases, user groups and access rights are defined using the operating system. The configuration of user groups and access rights affects how the tools can be used. For example, you can set constraints on what parts of a repository certain users will have access to.  Document the customizations in project-specific guidelines.
---

Integrate with Other Tools

Integrate the tool with other tools to make it easier to use. An integration between tools is in most cases in the form of an extension to one or several tools. An 'integration extension' to a tool typically:
  * Synchronize data between the different tools. It automates the creation and maintenance of related items in development projects
  * Automatically adds traceability between related items in different tools.
  * Allow the user to add traceability between items in different tools.
  * Allow the user to navigate between tools. For example, access an item in a test tool from a requirements management tool.
  * Allow the user to run certain functionality from one tool. For example, the possibility to create items in another tool.
  * Allow the user to version a tool's items in a configuration management tool.

Most tools offer ready-to-use extensions to integrate tools with each other.  Describe how the tools are integrated with each other in the project-specific guidelines.
---

Install and Customize Tools on Clients

Install the tool on each client. The least that is needed to do when installing a tool on the client side, is to set up the connection to the repository on the server.  Customize the tool on the clients, just as you customized the tool on the server:
  * In some cases you do not have to do anything with the client. For example, if the client is a web-interface it is enough that the clients get the address to the application on the server. Some tools allow you to do all customization on the server side. When the users access the repository on the server, they automatically get the correct settings.
  * In other cases you customize the tool on the client by installing software that customizes the tool, or installing files with customization information.

It may be necessary to install 'integration software' on the client. Place the 'integration software' on a server and allow the users to download and install it on their computers.  If it possible you should automate the tool installation, and the tool customization for the users. The benefit of creating installation programs is that it allows you to set up the tools so that the clients get all the right settings, extensions, and connections to the repository. You create installation \(and customization\) programs, and place them on a server. Then the users download these programs and run them to install and customize the tool in their computer.
---

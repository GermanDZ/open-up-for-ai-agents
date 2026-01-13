---
title: Deploying Tools
source_url: practice.mgmt.project_process_tailoring.base/guidances/guidelines/deploying_tools_316AAD08.html
type: Guideline
uma_name: deploying_tools
page_guid: _A1qOACu3Ed-UrP371xHUyw
keywords:
- deploying
- tools
related:
  tasks:
  - deploy-the-process-1
---



---

Relationships

Related Elements|
  * [Deploy the Process](../../tasks/deploy-the-process-1.md)
---|---

Main Description

###  Install the Tool on the Server

Identify what other software is required for the specific tool to work, and install this software. For example, a tool may require a database management system \(DBMS\) be installed first.

When you have installed the support software, you can install the tool on the server.

###  Customize the Tool \(on the Server\)

Decide how to customize the tool so that it supports the Development Process in the best way. The following are some brief examples of how you can customize tools:

####  Modeling tools

You can create a template model that defines the structure of models. The template model will be used when creating a new model. You can create a file in which you define what stereotypes to use, and their icons. Then this file can be installed on all users' computers, so that they use the same set of stereotypes.

####  Requirements and Change Management tools

You can create a project template, in which you define the attribute types to use. You can start with provided templates and customize according to your needs.

####  Configuration Management tools

You can often configure actions in response to 'events' that make the tool behave in a certain way. For example, you can customize the tool so that when a user checks-in an item, a script is automatically executed that does some checking on the item. There may also be customizations that support distributed development, such as "multi-site" support with duplicated repositories.

###  Document the customizations in your process.

Integrate with Other Tools

Integrate the tool with other tools to make it easier to use. An integration between tools is in most cases in the form of an extension to one or several tools. An 'integration extension' to a tool typically:  Synchronize data between the different tools. It automates the creation and maintenance of related items in development projects
Automatically adds traceability between related items in different tools.
Allow the user to add traceability between items in different tools.
Allow the user to navigate between tools. For example, access an item in a test tool from a requirements management tool.
Allow the user to run certain functionality from one tool. For example, the possibility to create items in another tool.
Allow the user to version a tool's items in a configuration management tool. For example, the possibility to version control requirements \(from RequisitePro\) using ClearCase.
Most tools offer ready-to-use extensions to integrate tools with each other.  Describe how the tools are integrated with each other in the process.

###  Install and Customize Tools on Clients

Install the tool on each client. The least that is needed to do when installing a tool on the client side, is to set up the connection to the repository on the server.

Customize the tool on the clients, just as you customized the tool on the server:

In some cases you do not have to do anything with the client. For example, if the client is a web-interface it is enough that the clients get the address to the application on the server. Some tools allow you to do all customization on the server side. When the users access the repository on the server, they automatically get the correct settings.
In other cases you customize the tool on the client by installing software that customizes the tool, or installing files with customization information.
It may be necessary to install 'integration software' on the client. Place the 'integration software' on a server and allow the users to download and install it on their computers.

If it possible you should automate the tool installation, and the tool customization for the users. The benefit of creating installation programs is that it allows you to set up the tools so that the clients get all the right settings, extensions, and connections to the repository. You create installation \(and customization\) programs, and place them on a server. Then the users download these programs and run them to install and customize the tool in their computer.

###  Setting up workspaces

Most project teams require workspaces for a variety of purposes including:  \- development workspaces for individuals to do their work  \- integration workspaces for individuals to share their work  \- build workspaces for builds that have achieved a certain level of quality  Part of setting up the tool environment is to set up the needed workspaces and the policies for how they are used.
---

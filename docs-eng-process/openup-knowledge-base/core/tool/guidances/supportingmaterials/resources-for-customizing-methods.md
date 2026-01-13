---
title: Resources for Customizing Methods
source_url: core.default.tool_def.base/guidances/supportingmaterials/resources_for_customizing_methods_7663A1A6.html
type: SupportingMaterial
uma_name: resources_for_customizing_methods
page_guid: _omneEMX4EduywMSzPTUUwA
keywords:
- customizing
- method
- methods
- provides
- resources
related:
  tasks:
  - tailor-the-process-1
  other:
  - use-method-composer-to-update-the-process
---


 This supporting material provides guidance on how to customize an existing method element by using Method Composer and provides links to additional information on method customization.
---

Relationships

Related Elements|
  * [Tailor the Process](../../../../practice-management/project_process_tailoring/tasks/tailor-the-process-1.md)
  * [Use Method Composer to Update the Process](../../../../practice-management/iterative_dev/guidances/toolmentors/use-method-composer-to-update-the-process.md)
---|---

Main Description

There are several use scenarios for [method configuration](../../../uma/guidances/termdefinitions/method-configuration.md)s produced by using EPF Composer or Rational Method Composer \(both referred to generically here as "Method Composer"\). The simplest is to use the published content as-is \(either using a prepublished Web site or by publishing one using the content that is included with Method Composer\). However, you may be looking for how to add, remove, suppress, or modify [method content](../../../uma/guidances/termdefinitions/method-content.md) or [process](../../../uma/guidances/termdefinitions/process.md) elements, or both, to make an existing method configuration more suitable to your teams' needs, while keeping it consistent and understandable. This guidance page describes typical customization scenarios and then provides references to additional information on how to customize methods.

###  Customization scenarios

The following sections describe possible customization scenarios. For information on specific tool features, consult the Method Composer online Help. For additional information on customizing methods, see the Additional Resources section that follows here.

####  Use existing plug-ins and packages to build your own process

Some consider this the most straight-forward customization scenario. Based on the provided content, you can use Method Composer to pick and choose the packages with the content that you want to publish and make available to your team. Removing a method package removes all references to the content of that package from the published process. For example, you can simplify a process to have it contain a minimal subset of its content by removing packages that contain elements of work that you do not want to perform. You do this by creating a new method configuration \(or copying an existing one\) into your method library. You can select packages as appropriate without affecting the configuration provided.

####  Add method content that your team needs

Some teams may need to perform a different task that is not covered by the standard content. Maybe they need to perform an extra step in an existing task, or they may need to add a new guideline for a given technique that they are following. Eventually, they need a new template for a document \(or they may need to add or remove sections in an existing template\).  In such situations, the recommended approach is to create a separate plug-in in your library. It is not a good practice to make changes in the provided plug-in \(meaning any plug-in for which you do not have control\), because new versions of these plug-ins, when deployed, can override the changes that you have made.  Method Composer provides a series of mechanisms that allow you to indirectly modify the content in an existing plug-in by using _content variability_. In your plug-in, you can define an element that contributes, extends, or replaces an element in the existing plug-in. For example, in your plug-in, you can define a task that contributes a new step to an existing task. You can also define a new artifact that replaces an existing artifact, and this new artifact can have a different name, structure, and associated template, for example. Then all you need to do is make sure that the existing plug-in and your new plug-in are part of the configuration to be published. During publication, Method Composer will resolve the content variability that you defined by adding the new content into the existing content where appropriate, replacing existing content with the content you defined, and so on.

####  Define a different development lifecycle

Both method content and process are created independently from each other. For example, you create tasks in the method content \(and define their inputs, outputs, and responsible roles\), but you do not necessarily define the lifecycle of your process, meaning the sequence in which the various tasks will be performed. On the process side, you then define the lifecycle \(such as phases, iterations, activities, and tasks\), as well as the precedence among these elements.  Some teams may find the method content appropriate without any further customization, but they may want to work by following a different software development lifecycle. For example, some teams may like the four development phases and iterations from the unified process, but some may want to develop iteratively, without being tied to a specific phase structure. Again, you can add, remove and replace elements in the work breakdown structure of an existing process by applying process variability.  As an alternative to tailoring an existing process, you can write a completely new process that reuses activities from one or more existing processes. In cases where you cannot find any reusable material at all, you can also create a completely new process from scratch. In most cases, however, you will start developing your own process by assembling reusable building blocks from method content, as well as predefined process patterns called [capability patterns](../../../uma/guidances/termdefinitions/capability-pattern.md). The resulting assembled process is called a [delivery process](../../../uma/guidances/termdefinitions/delivery-process.md). This newly created delivery process is part of a configuration that you publish and make available to members of your team.

####  Publish the process Web site

Every customization scenario is finalized by publishing content as HTML \(on a Web site\). Method Composer enables you to publish content based on a given configuration, which will publish all of the content available from the method and process packages selected in that configuration. Another option for publishing is to select only the capability patterns or delivery process of interest. This will make available only the content related to the process packages that you select.  For the published Web site look and feel, you can customize the views and nodes in the directory \(tree\) browser by defining [custom categories](../../../uma/guidances/termdefinitions/custom-category.md) that will be part of your configuration.

###  Additional resources

For more information on the fundamental concepts of method content and process, see [Concept: Basic Process Concepts](../../../uma/guidances/concepts/basic-process-concepts.md).  For information on EPF Composer, see [EPF Resources](epf-resources.md).  For information on Rational Method Composer, see [Rational Method Composer Resources](rational-method-composer-resources.md).  For detailed customization scenarios, consult the tutorials included in the Method Composer online Help, as well the general authoring topics.
---

More Information

Concepts|
  * [Basic Process Concepts](../../../uma/guidances/concepts/basic-process-concepts.md)
---|---
Supporting Materials|
  * [EPF Resources](epf-resources.md)
  * [Rational Method Composer Resources](rational-method-composer-resources.md)


Tool Mentors|
  * [Use Method Composer to Update the Process](../../../../practice-management/iterative_dev/guidances/toolmentors/use-method-composer-to-update-the-process.md)

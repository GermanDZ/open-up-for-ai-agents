---
title: Visual Modeling
source_url: core.tech.common.extend_supp/guidances/concepts/visual_modeling_2C089766.html
type: Concept
uma_name: visual_modeling
page_guid: _0XY6UMlgEdmt3adZL5Dmdw
keywords:
- modeling
- visual
related:
  guidelines:
  - using-visual-modeling
---


 This concept introduces what visual modeling is and its benefits.
---

Relationships

Related Elements|
  * [Using Visual Modeling](../guidelines/using-visual-modeling.md)
---|---

Main Description

![visual modeling](./../../../core.tech.common.extend_supp/guidances/concepts/resources/visual.gif) Visual modeling raises the level of abstraction  Visual modeling is the use of semantically rich, graphical and textual design notations to capture software designs. A notation, such as UML, allows the level of abstraction to be raised, while maintaining rigorous syntax and semantics. In this way, it improves communication in the design team, as the design is formed and reviewed, allowing the reader to reason about the design, and it provides an unambiguous basis for implementation.

###  How visual models help

A model is a simplified view of a system. It shows the essentials of the system from a particular perspective and hides the nonessential details. Visual models help you:
  * Increase understanding of complex systems
  * Explore and compare design alternatives at a low cost
  * Form a foundation for implementation
  * Capture requirements precisely
  * Communicate decisions unambiguously

####  Increase understanding of complex systems

The importance of models increases as systems become more complex. For example, you can build a doghouse without blueprints. However, as you progress to building houses and then to skyscrapers, your need for blueprints becomes pronounced.  Similarly, a small application built by one person in a few days may be easily understood in its entirety. However, an e - commerce system with tens of thousands of source lines of code \(SLOCs\) or an air traffic control system with hundreds of thousands of SLOCs can no longer be easily understood by one person. Constructing models allows a developer to focus on the big picture, understand how components interact, and identify fatal flaws.  Among the various types of models are these examples:
  * Use cases to specify behavior unambiguously
  * Class diagrams and data model diagrams to capture design
  * State transition diagrams to model dynamic behavior

Modeling is important because it helps the team visualize, construct, and document the structure and behavior of the system without getting lost in complexity.

####  Explore and compare design alternatives at a low cost

You can create and modify simple models inexpensively to explore design alternatives. Innovative ideas can be captured and reviewed by other developers before investing in costly code development. When coupled with iterative development, visual modeling helps developers assess design changes and communicate these changes to the entire development team.

####  Form a foundation for implementation

Today, many projects employ object-oriented programming languages to build reusable, change-tolerant, and stable systems. To get these benefits, it is even more important to use object technology in design.  The creation of visual models, whether on paper; around a whiteboard; or in a modeling tool, can help a team to gain agreement on key aspects of the system before investing time in proving their ideas with code. Having a shared model of the system promotes collaboration within the team, encouraging everyone to work towards the same goal.  With the support of appropriate tools, you can use a design model to generate an initial code for implementation. This is referred to as **forward engineering** or **code generation**. You can also enhance design models to include enough information to build the system.  **Reverse engineering** may also be applied to generate design models from existing implementations. You can use this method to evaluate existing implementations.  **Round-trip engineering** combines both forward and reverse engineering techniques to ensure consistent design and code. Combined with an iterative process and the right tools, round-trip engineering allows you to synchronize the design and code during each iteration.

####  Capture requirements precisely

Before building a system, it's critical to capture the requirements. Specifying the requirements using a precise and unambiguous model helps to ensure that all stakeholders can understand and agree on the requirements.  A model that separates the external behavior of the system from the implementation of it helps you focus on the intended use of the system, without getting bogged down in implementation details.

####  Communicate decisions unambiguously

The Unified Modeling Language \(UML\) is a consistent notation that can be applied for system engineering, as well as for business engineering. According to these excerpts from the UML specification, a standard notation::
  * Serves as a language for communicating decisions that are not obvious or cannot be inferred from the code itself.
  * Provides semantics that are rich enough to capture all important strategic and tactical decisions.
  * Offers a form concrete enough for humans to reason \[about\] and for tools to manipulate.

UML represents the convergence of the best practice in software modeling throughout the object-technology industry. For more information on the UML, see [\[UML05\]](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html).
---

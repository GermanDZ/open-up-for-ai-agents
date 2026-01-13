---
title: Abstract Away Complexity
source_url: core.tech.common.extend_supp/guidances/guidelines/abstract_away_complexity_DBF13AE6.html
type: Guideline
uma_name: abstract_away_complexity
page_guid: _we3F4ACpEdu8m4dIntu6jA
keywords:
- abstract
- away
- complexity
related:
  tasks:
  - envision-the-architecture-1
  - refine-the-architecture-1
---



---

Relationships

Related Elements|
  * [Envision the Architecture](../../../../practice-technical/evolutionary_arch/tasks/envision-the-architecture-1.md)
  * [Refine the Architecture](../../../../practice-technical/evolutionary_arch/tasks/refine-the-architecture-1.md)
---|---

Main Description

Software development is a pursuit characterized by complexity. This can take many forms, such as accommodating complex requirements, technology, or team dynamics. Elevating the level of abstraction helps you manage this complexity and make measurable progress, despite the inherent difficulty of the task.  Suggestions for several strategies that help abstract away complexity follow.

###  Leverage patterns

Patterns help you take advantage of proven techniques for solving common problems. You can benefit from the experience of seasoned practitioners and avoid "re-inventing the wheel," as the saying goes. The use of patterns is a crucial aspect of an architecture-centric approach to development, because it helps reduce the novelty and diversity of a solution, thus improves quality.  See [Concept: Pattern](../concepts/pattern.md) for more information.

###  Design the architecture with components and services

This strategy helps manage software complexity through partitioning a system into a set of loosely coupled and highly cohesive components. The benefits of this approach include the ability to organize the team around a set of smaller, more manageable objectives, and the ability to substitute parts of the system without disturbing the overall cohesion of the system. Exposing services encourages re-use by making the functionality of the system easier to comprehend. Focusing on services makes it possible to understand what the system does from a technical perspective without necessarily having to understand the details of how the system works.  See [Concept: Component](../concepts/component.md) for more information.

###  Actively promote reuse

Incorporating existing software into an overall architecture helps reduce cost and improve quality by reusing proven working software, rather than developing from scratch. It also helps reduce the burden of maintenance by eliminating duplication in the software. Although often difficult to manage, a project or enterprise can reap significant benefits from a well-executed re-use strategy.  See [Guideline: Software Reuse](software-reuse.md) for more information.

###  Model key perspectives

Modeling helps raise the level of abstraction because you simplify complex ideas and represent them visually, as illustrations. Good models can convey information that helps the team visualize, specify, construct, and document software.  For more information, see [Guideline: Using Visual Modeling](using-visual-modeling.md).
---

More Information

Concepts|
  * [Component](../concepts/component.md)
  * [Pattern](../concepts/pattern.md)
---|---
Guidelines|
  * [Software Reuse](software-reuse.md)
  * [Using Visual Modeling](using-visual-modeling.md)

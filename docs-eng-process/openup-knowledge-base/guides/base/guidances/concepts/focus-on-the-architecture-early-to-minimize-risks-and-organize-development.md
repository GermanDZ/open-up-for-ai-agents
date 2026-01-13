---
title: Focus on the architecture early to minimize risks and organize development
source_url: publish.openup.base/guidances/concepts/core_principle_focus_346C6FAF.html
type: Concept
uma_name: core_principle_focus
page_guid: _9gocwMvoEdqukPpotm3DYg
keywords:
- architecture
- development
- early
- focus
- minimize
- organize
- risks
related:
  concepts:
  - elaboration-phase-10
---


 An evolving architecture helps the team to address complexity, drive risk mitigation, and organize development.
---

Relationships

Related Elements|
  * [Elaboration Phase](../../../../practice-management/risk_value_lifecycle/guidances/concepts/elaboration-phase-10.md)
---|---

Main Description

###  Introduction

The architecture of a software system is the organization or structure of the system's significant components interacting through interfaces, with components composed of successively smaller components and interfaces.  Without an architectural foundation, a system will evolve in an inefficient and haphazard way. Such a system often proves difficult to extend, reuse, or integrate without substantial rework. It is also difficult to organize the team, or to communicate ideas without the **common technical focus** that the architecture provides.  Focus on the architecture early to minimize risks and organize development.

###  Practices

####  Create the architecture for what you know today

As Albert Einstein said, make everything as simple as possible, but no simpler. Software projects are resource-constrained, and the desire of developers to create elegant solutions may lead to a system of greater complexity than the stakeholder requires. Efforts to future-proof a system in a turbulent or uncertain environment will likely lead to code bloat, which increases overall costs and complexity with few real benefits.  Create architectures that address the stakeholder's real needs, and provide appropriate flexibility and speed for the requirements as they are known today. Avoid the desire, no matter how well-intentioned, to speculate on future requirements and thereby over-engineer the architecture. There is a distinction between over-architecting and building an architecture that is flexible and extensible. For example, there may not be an apparent reason for creating three architectural layers in a system, but it is probable that the system will grow in ways one can't predict, so we should architect for that.

####  Leverage the architecture as a collaborative tool

Lack of a common understanding by developers about a system leads to indecision and contrary opinions among developers, and can quickly paralyze the project. Developers may have different mental models of the system and work at cross purposes to each other.  Create and evolve the system architecture with the intention of using it to align the developers' competing mental models of the system. A good architecture facilitates collaboration by providing a common vocabulary for all discussions regarding the system under development.

####  Cope with complexity by raising the level of abstraction

Software is complex, and people have a limited capacity for coping with complexity. As a system gets larger, it is difficult for the team to develop a common understanding of the system, because it's hard to see the bigger picture.  Use models to raise the level of abstraction to focus on important high-level decisions, such as relationships and patterns, rather than getting bogged down in details. Modeling raises the level of abstraction, and allows the system to be more easily understood from different perspectives.

####  Organize the architecture into loosely coupled, highly cohesive components

Tight coupling between components makes a system fragile and difficult to understand. Software is expensive to create, so if existing components can be reused, that may reduce effort required to create a system.  Organize the architecture of the system into components to maximize cohesion and minimize coupling. This improves comprehension, and increases flexibility and opportunities for re-use.

####  Reuse existing assets

It is wasteful to build what you can simply reuse, download, or even buy.  Make every effort to reuse existing assets. Developers are often reluctant to reuse assets, because those assets do not exactly meet their needs, or those assets are of poor quality. Be prepared to balance the savings you can realize using an existing asset, even if the asset requires you to make some accommodation in the architecture or relax a constraint.
---

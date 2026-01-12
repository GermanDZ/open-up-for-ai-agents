---
title: Architectural Constraints
source_url: core.tech.common.extend_supp/guidances/concepts/arch_constraints_AE56B662.html
type: Concept
uma_name: arch_constraints
page_guid: _jdKSsNpiEdyP58ppo1Ieaw
keywords:
- architectural
- constraints
related:
  checklists:
  - architecture-notebook-7
  tasks:
  - envision-the-architecture-1
  - refine-the-architecture-1
  other:
  - software-architecture
---


 This concept describes those things that may constrain the architecture of a system.
---

Relationships

Related Elements|
  * [Architecture Notebook](../../../../practice-technical/evolutionary_arch/guidances/checklists/architecture-notebook-7.md)
  * [Envision the Architecture](../../../../practice-technical/evolutionary_arch/tasks/envision-the-architecture-1.md)
  * [Refine the Architecture](../../../../practice-technical/evolutionary_arch/tasks/refine-the-architecture-1.md)
  * [Software Architecture](software-architecture.md)
---|---

Main Description

A variety of factors may place constraints on the architecture being developed:
  * Network topology
  * Use of a given database vendor or an existing database
  * Web environment \(server configurations, firewall, DMZs, and so forth\)
  * Servers \(hardware model, operating system\)
  * Use of third-party software or a particular technology
  * Compliance with existing standards

For example, if the company uses only one type of database, you will probably try to use it as much as possible to leverage the existing database administration skills, rather than introducing a new one.  These architectural constraints, combined with the requirements, help you define an appropriate candidate for the system architecture. Capturing these constraints will ease integration with the environment; and may reduce risk, cost and duplication of solution elements.
---

---
title: Refactoring
source_url: core.tech.common.extend_supp/guidances/concepts/refactoring_1B63BA3B.html
type: Concept
uma_name: refactoring
page_guid: _Poc7IPDzEdqYgerqi84oCA
keywords:
- refactoring
related:
  concepts:
  - design-2
  guidelines:
  - evolve-the-design
  - refactoring-1
  - software-reuse
  - test-driven-development
  other:
  - how-to-adopt-the-evolutionary-design-practice
  tasks:
  - implement-solution-1
---


 This concept explains ways of improving the design of existing code in a way that does not alter its external behavior.
---

Relationships

Related Elements|
  * [Design](../../../../practice-technical/evolutionary_design/guidances/concepts/design-2.md)
  * [Evolve the Design](../../../../practice-technical/evolutionary_design/guidances/guidelines/evolve-the-design.md)
  * [How to Adopt the Evolutionary Design Practice](../../../../practice-technical/evolutionary_design/guidances/roadmaps/how-to-adopt-the-evolutionary-design-practice.md)
  * [Implement Solution](../../../../practice-technical/test_driven_development/tasks/implement-solution-1.md)
  * [Refactoring](../guidelines/refactoring-1.md)
  * [Software Reuse](../guidelines/software-reuse.md)
  * [Test Driven Development](../../../../practice-technical/test_driven_development/guidances/guidelines/test-driven-development.md)
---|---

Main Description

Refactoring is a disciplined way to restructure code when small changes are made to the code to improve its design. An important aspect of a refactoring is that it improves the design while not changing the behavior of the design; a refactoring neither adds nor removes functionality.  Refactoring enables you to evolve the code slowly over time, to take an iterative and incremental approach to implementation.  These are the types of refactoring:

  1. Code refactoring. Often referred to simply as refactoring, this is the refactoring of programming source code. Examples of code refactorings include Rename Method, Encapsulate Field, Extract Class, Introduce Assertion, and Pushdown Method.
  2. Database refactoring. A database refactoring is a simple change to a database schema that improves its design while retaining both its behavioral and informational semantics. Examples of database refactorings include Rename Column, Split Table, Move Method to Database, Replace LOB with Table, Introduce Column Constraint, and Use Official Data Source.
  3. User interface \(UI\) refactoring. A UI refactoring is a simple change to the UI which retains its semantics. Examples of UI refactorings include Align Entry Fields, Apply Common Button Size, Apply Common Font, Indicate Format, Reword in Active Voice, and Increase Color Contrast.

Martin Fowler \[[FOW99](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html#FOW99)\] identifies four key reasons to refactor:
  * Refactoring improves the design of software.
  * Refactoring makes software easier to understand.
  * Refactoring helps you find bugs.
  * Refactoring helps you program faster.

Refactoring can improve the design of existing code, but it does not take the place of considering the design before writing code. Refactoring instead changes the role of up-front design, allowing the strictly design work to be more abstract. Small-scale, very tactical decisions can be made during the implementation of the solution with confidence that refactoring will ensure a quality implementation at that level. The designing of the solution before implementation will be more lightweight and focused on broad factors that will drive the implementation.  There is an additional benefit of refactoring: it changes the way a developer thinks about the implementation when not refactoring. The basic task of implementing a solution becomes solely about getting the solution to pass its developer tests in the simplest way possible. Then the design of that solution can be examined and refactored separately. Even if these two things -- implementation of the solution and then improvement -- are just a minute apart, it can be freeing for a developer to single-mindedly create code that causes a test to pass, and then separately single-mindedly improve that code.  These are some additional resources:
  * [_http://www.refactoring.com/_](http://www.refactoring.com/)
  * [_http://www.agiledata.org/essays/databaseRefactoring.html_](http://www.agiledata.org/essays/databaseRefactoring.html)
---

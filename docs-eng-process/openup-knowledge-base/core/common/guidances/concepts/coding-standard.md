---
title: Coding Standard
source_url: core.tech.common.extend_supp/guidances/concepts/coding_standard_1FF691E0.html
type: Concept
uma_name: coding_standard
page_guid: _aGqAsJ01EdyQ3oTO93enUw
keywords:
- coding
- standard
related:
  concepts:
  - collective-code-ownership
  guidelines:
  - refactoring-1
---


 A standard describing various coding conventions used for consistent, quality, understandable implementation.
---

Relationships

Related Elements|
  * [Collective Code Ownership](../../../../practice-technical/test_driven_development/guidances/concepts/collective-code-ownership.md)
  * [Refactoring](../guidelines/refactoring-1.md)
---|---

Main Description

Using a coding standard is a widely accepted software development practice. The need for this practice takes on added importance in a highly collaborative environment. The team should have a standard way of naming and formatting things so they can understand the code quickly and know where to look at all times. This enables shared code ownership since any team member should be able to quickly understand the code written by others.  Ideally, the coding standard should be the result of team consensus. Involving the team members will aid adoption of the standards.  Coding Standards cover such areas as:
  * Naming standards. This includes the naming of elements all the way down to the smallest variable. In covering larger-scale elements, this overlaps into what could be considered design standards.
  * File organization. This includes file naming conventions and how the files will be organized on the file system.
  * Comment standards. Too much emphasis on comments implies a lack of confidence that readable code is being written, plus there is always a concern that the comments are not up to date. Yet, a consistent approach to comments improves understandability and can support the ability to generate documentation from the code.
  * Coding conventions. Consistent application of specific code-level conventions and the exclusion of some considered poor form improve the quality of the code.
  * White space. Though it can be argued to be less critical than the other items listed here, a consistent usage of white space as indentation and blank lines also improves readability.

In some cases, decisions will be arbitrary \(like how much to indent\). Each item in the standard should support one or more goals, improved communication being one of the most critical goals. Once the team agrees on a standard, all members of the teams are expected to follow it. With time, the team will use and modify the standard to develop a style that is well adapted to the environment.  Though some standards can transcend any language, coding standards must be language specific for the most part.  For example coding standards, see the [Code Conventions for the JavaTM Programming Language](http://java.sun.com/docs/codeconv/html/CodeConvTOC.doc.html) or these [Internal Coding Guidelines](http://blogs.msdn.com/brada/articles/361363.aspx) for .NET development.
---

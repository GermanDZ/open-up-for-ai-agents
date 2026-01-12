---
title: Refactoring
source_url: core.tech.common.extend_supp/guidances/guidelines/refactoring_F3D63EBD.html
type: Guideline
uma_name: refactoring
page_guid: _YNx2sJ05EdyQ3oTO93enUw
keywords:
- refactoring
related:
  guidelines:
  - evolve-the-design
  - test-driven-development
  other:
  - how-to-adopt-the-evolutionary-design-practice
---


 This guideline describes how to apply the refactoring technique to improve the quality of existing code.
---

Relationships

Related Elements|
  * [Evolve the Design](../../../../practice-technical/evolutionary_design/guidances/guidelines/evolve-the-design.md)
  * [How to Adopt the Evolutionary Design Practice](../../../../practice-technical/evolutionary_design/guidances/roadmaps/how-to-adopt-the-evolutionary-design-practice.md)
  * [Test Driven Development](../../../../practice-technical/test_driven_development/guidances/guidelines/test-driven-development.md)
---|---

Main Description

Refactoring involves improving the quality of existing code without changing the system's behavior. It is explicitly not about adding or changing behavior, but about improving the implementation quality of existing behavior.  A full set of developer tests is required before refactoring can be safely applied. It is critical that the system behavior be in a known, verifiably correct state before modifying the implementation so that you can improve the quality without fear that the modified implementation will break something. Refactoring is a safe transformation to improve code, but it is safe only if there are tests that can verify that the system still works as intended.  Refactoring is initiated when an area that needs improvement is identified in the system by examining either the code or some other representation of the design. The issues identified are sometimes called "smells."  Here are several smells to look for that might lead to implementation or design refactoring:
  * **Duplicated code:** Duplicated code makes the system harder to understand and harder to maintain.
  * **Large design element or method:** Large design elements or methods diminish the ability of people to understand the code, reduce the potential for reuse, and make developer testing more difficult.
  * **Poorly named element:** Whether the element be a variable, function, class, or implementation element, its name should connote what it is so that the code can be maintained.
  * **Tight coupling:** Each design element should work with minimal concern for the internal aspects of other design elements. Otherwise, changes to one element can have undesirable effects in other elements.

As you can see from this list, refactoring can improve the "internals" of an element or the interface of the element. Also, many of the smells are characterized as making the software more difficult to understand; whereas refactoring is about making the system simpler.  After an issue is identified, a refactoring method can be selected that will improve the situation. There are catalogs of refactoring methods available that are change patterns that will fix common problems while retaining the behavior of the system.  These are examples of refactoring methods:
  * **Extract Method:** Pull out the duplicated code into its own single method or extract part of a large method into its own method.
  * **Extract Class:** Pull some cohesive part of a class into its own class to reduce the size of a design element that is too big.
  * **Rename Method** , **Rename Class** , or **Rename Variable:** Give a more meaningful name to an element to make it more understandable.
  * **Extract Interface:** Create a clean interface.

After refactoring has been applied, developer tests are run again to ensure that the system still behaves correctly. It is important that the system is working correctly after each small refactoring. Although many refactorings can be put together to drive broad change across the code base, the tests should run correctly between each refactoring applied. Refactoring must be applied as small behavior-preserving transformations.  As mentioned previously, refactoring requires full developer test coverage of the area under consideration. There are additional techniques that enable refactoring. Coding standards define a common style and make it easier to refactor consistently. An attitude of collective code ownership within the team is important. Each developer should feel that refactoring can be applied across the code base to improve the implementation.  For deeper coverage on this topic, including a listing of "smells" and a catalog of refactorings to respond to them, see \[[FOW99](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html#FOW99)\].
---

More Information

Checklists|
  * [Design](../../../../practice-technical/evolutionary_design/guidances/checklists/design-1.md)
  * [Implementation](../checklists/implementation-1.md)
---|---
Concepts|
  * [Coding Standard](../concepts/coding-standard.md)
  * [Refactoring](../concepts/refactoring.md)


Guidelines|
  * [Test Driven Development](../../../../practice-technical/test_driven_development/guidances/guidelines/test-driven-development.md)

---
title: How to Adopt the Evolutionary Design Practice
source_url: practice.tech.evolutionary_design.base/guidances/roadmaps/how_to_adopt_evolutionary_design_7CA256E4.html
type: Roadmap
uma_name: how_to_adopt_evolutionary_design
page_guid: _irQiEOCsEdynptYdmll41Q
keywords:
- adopt
- design
- evolutionary
- practice
---

 This roadmap describes how to adopt the Evolutionary Development practice.
---

Main Description
**Getting Started** Begin by gaining an understanding of [design patterns](../../../../core/common/guidances/concepts/pattern.md). There are good references in the Additional Information section of the [Evolutionary Design](../practices/evolutionary-design.md) page. Patterns are essential to creating, managing, and evolving designs. As the name implies, evolutionary design involves returning to the existing design over and over again to refine, change, and improve previous thinking. It can be performed at the beginning of a development cycle \(before implementation\), during a development cycle \(while implementing code\), after the cycle \(when the developer tests have successfully executed\), or any combination of these. The team should determine where in the development cycle the design will be performed. See [Task: Design the Solution](../../tasks/design-the-solution.md).  Understand [refactoring](../../../../core/common/guidances/concepts/refactoring.md) and the difference between code refactoring and design refactoring. There is no exact boundary separating the two, but there are some clear areas where the developer will wear the "design hat" when reworking the design into a better structure. These areas will usually involve identifying where design patterns can replace or enhance the existing design, or areas of the design where patterns can be identified and harvested for reuse.  **Common pitfalls** Evolutionary design emerges from refactoring existing design. This improves the design without changing the behavior of the system. Failing to perform developer or unit testing is a high risk activity, as you can not guarantee that:
  * The original design works correctly
  * The refactored design works correctly

Therefore, you must perform rigorous [developer testing](../../../../core/common/guidances/concepts/developer-testing.md) in order to verify the robustness of the design. Otherwise, you may waste a lot of time refactoring something that does not work, or refactoring the correct behavior out of the system.
---

More Information

Concepts|
  * [Developer Testing](../../../../core/common/guidances/concepts/developer-testing.md)
  * [Pattern](../../../../core/common/guidances/concepts/pattern.md)
  * [Refactoring](../../../../core/common/guidances/concepts/refactoring.md)
---|---
Guidelines|
  * [Developer Testing](../../../../core/common/guidances/guidelines/developer-testing-1.md)
  * [Refactoring](../../../../core/common/guidances/guidelines/refactoring-1.md)


Supporting Materials|
  * [Using Evolutionary Design in Context](../supportingmaterials/using-evolutionary-design-in-context.md)

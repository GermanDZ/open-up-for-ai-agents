---
title: Implement Solution
source_url: practice.tech.test_driven_development.base/tasks/implement_solution_BB8B03DA.html
type: Task
uma_name: implement_solution
page_guid: _Ht-z8JfJEdyZkIR-s-Y8wQ
keywords:
- implement
- solution
related:
  roles:
  - developer-11
  - stakeholder-6
  - tester-5
---


 Implement source code to provide new functionality or fix defects.
---
Disciplines: [Development](../../../core/cat/disciplines/development-1.md)

Purpose

The purpose of this task is to produce an implementation for part of the solution \(such as a class or component\), or to fix one or more defects. The result is typically new or modified source code, which is referred to the implementation.
---

Relationships

Roles| Primary Performer:
  * [Developer](../../../core/role/roles/developer-11.md)

| Additional Performers:
  * [Stakeholder](../../../core/role/roles/stakeholder-6.md)
  * [Tester](../../../core/role/roles/tester-5.md)
---|---|---
Inputs| Mandatory:
  * [\[Technical Design\]](./../../core.tech.slot.base/workproducts/technical_design_slot_84295A08.html)
  * [\[Technical Specification\]](./../../core.tech.slot.base/workproducts/technical_specification_slot_2812F7EF.html)

| Optional:
  * [\[Technical Implementation\]](./../../core.tech.slot.base/workproducts/technical_implementation_slot_E92F6A39.html)
  * [Developer Test](../../../core/common/workproducts/developer-test.md)


Outputs|
  * [Implementation](../../../core/common/workproducts/implementation.md)



Main Description

Usually, this task is focused on a specific implementation element, such as a class or component, but it does not need to be.  A portion of the design is implemented by performing this task. This task can be performed any number of times during an iteration. In fact it is best to do this task in as small a scope as possible to tighten the loop between it and related tasks involving developer testing and consideration of the design.
---

Steps

Determine a strategy |  Determine a strategy based on the software design and developer tests for how you are going to implement the solution. The fundamental options are:

  1. Apply existing, reusable assets.
  2. Model the design in detail and generate the source code \(by model transformation\).
  3. Write the source code.
  4. Any combination of the above.
---

Identify opportunities for reuse

Identify existing code or other implementation elements that can be reused in the portion of the implementation that you are creating or changing. A comprehensive understanding of the overall design is helpful, because it is best to leverage reuse opportunities when you have a thorough understanding of the proposed solution.
---

Transform design into implementation

If you are using sophisticated modeling tools, you should be able to generate a portion of the required source code from the model. Note that programming is commonly required to complete the implementation after the design model has been transformed into code.  Even without tools, there is typically some amount of code that can be created by rote by examining the design and developer tests.
---

Write source code

Write the source code to make the implementation conform to the design and expected behavior. You should strive to reuse and/or generate code wherever possible, but you will still need to do some programming. To do so, consider the following:
  * Examine the technical requirements. Because some requirement information does not translate directly into your design you should examine the requirement\(s\) to ensure that they are fully realized in the implementation.
  * Refactor your code to improve its design. Refactoring is a technique where you improve the quality of your code via small, safe changes.
  * Tune the results of the existing implementation by improving performance, the user interface, security, and other nonfunctional areas.
  * Add missing details, such as completing the logic of operations or adding supporting classes and data structures
  * Handle boundary conditions.
  * Deal with unusual circumstances or error states.
  * Restrict behavior \(preventing users or client code from executing illegal flows, scenarios, or combinations of options\).
  * Add critical sections for multi-threaded or re-entrant code.

Though many different considerations are listed here, there is one clear way to know when the source code is done. The solution has been implemented when it passes the developer tests. Any other considerations can be taken care of in a refactoring pass over the code to improve it once it is complete and correct.
---

Evaluate the implementation

Verify that the implementation is fit for its purpose. Examine the code for its suitability to perform its intended function. This is a quality assurance step that you perform in addition to testing which is described in other tasks. Consider these strategies:
  * Pair programming. By pairing to implement the code in the first place, you effectively evaluate the code as its being written.
  * Read through the code for common mistakes. Consider keeping a checklist of common mistakes that you make, as a reminder reference.
  * Use tools to check for implementation errors and inappropriate code. For example, use a static code rule checker or set the compiler to the most detailed warning level.
  * Use tools that can visualize the code. Code visualization, such as the UML visualizations in the Eclipse IDE, help developers identify issues such as excessive coupling or circular dependencies.
  * Perform informal, targeted code inspections. Ask colleagues to review small critical sections of code and code with significant churn. Avoid reviewing large sections of code.
  * Use a tester to ensure the implementation is testable and understandable to testing resources.

Improve the implementation based on the results of these evaluations.
---

Communicate significant decisions

Communicate the impact of unexpected changes to the design and requirements.  The issues and constraints that you uncover when you implement the system must be communicated to the team. The impact of issues discovered during implementation must be incorporated into future decisions. If appropriate, use the change management process to reflect ambiguities that you identified and resolved in the implementation so they can be tested and you can manage stakeholder expectations appropriately. Similarly, leverage the design process to update the design to reflect new constraints and issues uncovered during implementation to be sure that the new information is communicated to other developers.  Usually, there is no need for a change request if the required change is small and the same person is designing and implementing the code element. That individual can make the design change directly. If the required change has a broad impact, it may be necessary to communicate that change to the other team members through a change request.
---

Key Considerations

It is best when developer tests already exist so there is an unambiguous definition of what behavior is considered correct. The implementation should be immediately tested. The \[Project Work\] is implicitly used in implementation tasks to manage which requirements or change requests are being realized in the code.
---

More Information

Concepts|
  * [Refactoring](../../../core/common/guidances/concepts/refactoring.md)
---|---
Guidelines|
  * [Mapping from Design to Code](../../../core/common/guidances/guidelines/mapping-from-design-to-code.md)

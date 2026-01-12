---
title: Implementation
source_url: core.tech.common.extend_supp/guidances/checklists/implementation_A5578577.html
type: Checklist
uma_name: implementation
page_guid: _etwusJ01EdyQ3oTO93enUw
keywords:
- implementation
related:
  guidelines:
  - refactoring-1
---



---

Relationships

Related Elements|
  * [Refactoring](../guidelines/refactoring-1.md)
---|---

Main Description

Appropriate divergence from the quality criteria described here could be worthy of a comment in the implementation so that developers examining the code in the future know why the exception occurred.
---

Check Items

The implementation conforms to the architecture and design |
  * Is the implementation structured as specified in the design?
  * Are all of the functions in the design implemented?
  * Are all of the interfaces in the design implemented according to their specifications?
  * Does the implementation adhere to all design and architectural constraints?
---

The implementation is testable
  * Can you test the expected behavior at the unit level?
  * Is the code written in a way that all paths can be exercised?
---

The implementation is correct
  * Does the implementation pass all of the developer tests?
  * Does the implementation support the acceptance criteria of the test cases?
  * Is all code executable \(no dead code areas\)?
---

The implementation is understandable

Is the logic clearly specified? Have comments been used sparingly to add clarity, and not to make up for unclear code?
---

There is no redundancy

Is there no redundancy in the implementation? \(Identify candidates for refactoring.\)
---

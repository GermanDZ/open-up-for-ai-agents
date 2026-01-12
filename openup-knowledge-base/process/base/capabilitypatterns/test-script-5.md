---
title: Test Script
source_url: process.openup.base/capabilitypatterns/test_script_E846CFB.html
type: WorkProductDescriptor
uma_name: test_script
page_guid: _N2eFAUVEEeK93ZZqiMLBsA
keywords:
- instructions
- script
- step
- test
related:
  other:
  - tester
---


 This artifact contains the step-by-step instructions that compose a test, enabling its run. Text scripts can take the form of either documented textual instructions that are manually followed, or computer-readable instructions that enable
automated testing.
---

Purpose

Test scripts implement a subset of required tests in an efficient and effective manner.
---

Relationships

Roles| Responsible:
  * [Tester](tester.md)

| Modified By:
---|---|---

Properties

Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Planned| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

Illustrations

Templates|
  * [Test Script](../../../core/common/guidances/templates/test-script-2.md)
---|---

Tailoring

Impact of not having| Without this artifact, it is difficult to ensure that tests are run consistently so that results are repeatable and errors can be recreated. If you do not use a test script, it is more difficult to verify that errors were not caused because of the way tests were run.
---|---
Reasons for not needing|  This artifact might not be required if the tests are simple or if testing is done on an informal basis. However, for this approach to be successful, testers must track their processes, as they might need to recreate a problem scenario. Alternatively, you can use automatic capture and playback tools to provide a record of testing.

More Information

Checklists|
  * [Test Data](../../../core/common/guidances/checklists/test-data.md)
  * [Test Script](../../../core/common/guidances/checklists/test-script-1.md)
---|---
Guidelines|
  * [Maintaining Automated Test Suites](../../../core/common/guidances/guidelines/maintaining-automated-test-suites.md)
  * [Programming Automated Tests](../../../core/common/guidances/guidelines/programming-automated-tests.md)
  * [Test Suite](../../../core/common/guidances/guidelines/test-suite.md)

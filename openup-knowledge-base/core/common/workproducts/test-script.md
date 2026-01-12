---
title: Test Script
source_url: core.tech.common.extend_supp/workproducts/test_script_39A30BA2.html
type: Artifact
uma_name: test_script
page_guid: _0ZfMEMlgEdmt3adZL5Dmdw
keywords:
- instructions
- script
- step
- test
related:
  roles:
  - tester-5
---


 This artifact contains the step-by-step instructions that compose a test, enabling its run. Text scripts can take the form of either documented textual instructions that are manually followed, or computer-readable instructions that enable
automated testing.
---
Domains: [Test](../../cat/domains/test.md)

Purpose

Test scripts implement a subset of required tests in an efficient and effective manner.
---

Relationships

Roles| Responsible:
  * [Tester](../../role/roles/tester-5.md)

| Modified By:
  * [Tester](../../role/roles/tester-5.md)
---|---|---
Tasks| Input To:
  * [Integrate and Create Build](../../../practice-technical/continuous_integration/tasks/integrate-and-create-build-1.md)
  * [Run Tests](../../../practice-technical/concurrent_testing/tasks/run-tests-1.md)
  * [Implement Tests](../../../practice-technical/concurrent_testing/tasks/implement-tests-1.md)

| Output From:
  * [Implement Tests](../../../practice-technical/concurrent_testing/tasks/implement-tests-1.md)



Illustrations

Templates|
  * [Test Script](../guidances/templates/test-script-2.md)
---|---

Tailoring

Impact of not having| Without this artifact, it is difficult to ensure that tests are run consistently so that results are repeatable and errors can be recreated. If you do not use a test script, it is more difficult to verify that errors were not caused because of the way tests were run.
---|---
Reasons for not needing|  This artifact might not be required if the tests are simple or if testing is done on an informal basis. However, for this approach to be successful, testers must track their processes, as they might need to recreate a problem scenario. Alternatively, you can use automatic capture and playback tools to provide a record of testing.

More Information

Checklists|
  * [Test Data](../guidances/checklists/test-data.md)
  * [Test Script](../guidances/checklists/test-script-1.md)
---|---
Guidelines|
  * [Maintaining Automated Test Suites](../guidances/guidelines/maintaining-automated-test-suites.md)
  * [Programming Automated Tests](../guidances/guidelines/programming-automated-tests.md)
  * [Test Suite](../guidances/guidelines/test-suite.md)

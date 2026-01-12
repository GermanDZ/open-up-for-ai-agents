---
title: Programming Automated Tests
source_url: core.tech.common.extend_supp/guidances/guidelines/programming_automated_tests_7DA10019.html
type: Guideline
uma_name: programming_automated_tests
page_guid: _0j5sUMlgEdmt3adZL5Dmdw
keywords:
- automated
- programming
- tests
related:
  tasks:
  - implement-tests-1
  - run-tests-1
  workproducts:
  - test-script
---


 This guideline discusses ways of structuring, recording, entering data, executing and handling errors in automated tests.
---

Relationships

Related Elements|
  * [Implement Tests](../../../../practice-technical/concurrent_testing/tasks/implement-tests-1.md)
  * [Run Tests](../../../../practice-technical/concurrent_testing/tasks/run-tests-1.md)
  * [Test Script](../../workproducts/test-script.md)
---|---

Main Description

###  Introduction

Although the programming of automated tests should contribute to the overall test effort, it usually does not make up the entire test effort. In fact, test environments that are based on a complete automation approach end up spending more time on test automation than on testing. Before you begin the development of automated test scripts, consider first whether it is more efficient to perform manual testing. Some aspects of an application are more efficiently tested manually \(for example, GUI testing versus data-drive testing\). If you decide to program automated test scripts, examine what aspects of your test scripting can be automated and begin designing your scripts.

###  Design your automated tests

Without some level of design of your automated tests, introducing automation into your testing effort can lead to more problems than it solves. You should consider developing your automated tests according to a lifecycle with automation test requirements, design, testing of the automation tests, and implementation of the automation tests. This approach can be informal or formal depending on your project needs. By designing the programming of your automated tests, you can avoid spending time programming the wrong tests, re-working programmed tests, deciphering different coding styles in the programming of the tests, etc.

###  Recorded versus programmed scripts

Although there are clear benefits to recorded scripts \(for example, ease of creation or ability for novice testers to learn a scripting language\), recorded scripts also present their own problems. The disadvantages of playback scripts are well known. They are deceptively easy to create but very difficult to update. Problems with script reliability, hard-coded data values, or changes to the application under test and the need to re-record are well-documented. On the other hand, programming scripts can present difficulties of their own: they are difficult for the novice tester to create, they can require substantial time and effort to develop, and they can be difficult to debug. Most test tooling makes these issues less problematic by providing the tester script support functions, such as ways to establish target of test lists, systematic ways to program verification point, point to datapools, build commands into the script \(for example, sleeper commands\), comment the script, and document the script. Another major advantage, which is often overlooked, of using testing tooling to mitigate these risks is the ability to add to an existing script in the form of making corrections to an existing script, testing new features of a test target or application under test, or resuming a recording after an interruption.

###  Functional and performance test scripts

When discussing automating test scripts, it is important to distinguish between functional and performance tests. Most discussions of programming automated test scripts focus on testing the functionality of an application. This is not inappropriate, since a lot of automated testing focuses on functional testing. Performance test scripting, however, has its unique characteristics. Performance test automation provides you with the ability to programmatically set workloads by adding user groups to test loads under group usage, setting think time behavior, running tests randomly or at set rates, or setting the duration of a run. Performance test automation also allows you to create and maintain schedules for your tests.

###  Testing test scripts

When testing your test scripts, keep in mind whether you are testing recorded or programmed test scripts. For recorded scripts, much of the debugging of the script consists of errors that are introduced due to changes in the test target or test environment. When you run a recorded test script, consider the test target of the script. Some test automation tools capture this information as a part of the test script. Debugging a recorded script consists largely of determining whether changes in the target have created error conditions in the script. In general, there are two main categories to examine here: changes in the UI and test session sensitive data \(for example, date stamped data\). In most cases, discrepancies between recording and playback cause errors in your recorded test scripts.  Testing programmed test scripts involves many of the same debugging techniques you would apply to debugging an application. Consider both the flow control logic and the data aspects of your script. Automated testing tools provide you with test script debugging IDEs as well as datapool management features that facilitate this type of testing. During execution of test scripts, a test that uses a datapool can replace values in the programmed test with variable test data that is stored in the datapool.
---

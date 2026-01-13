---
title: Maintaining Automated Test Suites
source_url: core.tech.common.extend_supp/guidances/guidelines/maintaining_automated_test_suite_13EF3D5.html
type: Guideline
uma_name: maintaining_automated_test_suite
page_guid: _0kF5kMlgEdmt3adZL5Dmdw
keywords:
- automated
- maintaining
- suites
- test
related:
  tasks:
  - implement-tests-1
  - run-tests-1
  workproducts:
  - test-script
---


 This guideline explains ways to maintain automated test suites - collection of tests performed together for breadth and depth coverage.
---

Relationships

Related Elements|
  * [Implement Tests](../../../../practice-technical/concurrent_testing/tasks/implement-tests-1.md)
  * [Run Tests](../../../../practice-technical/concurrent_testing/tasks/run-tests-1.md)
  * [Test Script](../../workproducts/test-script.md)
---|---

Main Description

###  Introduction

At some point in your test effort, you may find it necessary to manage your test effort by creating test suites for your test assets. Maintaining test suites can take many different forms. To facilitate your testing, you may want to introduce some level of automation of your test suites. The fact that you've automated your test suites does not necessarily make your testing easier however. It may actually increase the maintenance burden of your suites.  This guideline introduces you to useful heuristics on how to facilitate the maintenance of your automated test suites.

####  Plan your test suites

Automating your testing without planning increases the chances that testing will be ineffective and inefficient. Some level of planning should take place whether implicit or explicit. An essential part of any test plan is the definition of a strategy for test automation. Use your plan to articulate to the development team how you plan to maintain your test assets. In many cases, this is never done. The rest of the development team may be unaware of how you intend to maintain your tests. It is also a good practice to get the rest of the development team to understand that this maintenance can be a substantial part of the overall development effort. Use your test tooling to capture this information and treat this plan just like you would treat any other test asset in your test repository.

####  Centrally locate your test assets

To facilitate the maintenance of your automated test suites, locate your test assets in a repository that can be accessed by the development team. Many test automation environments provide test management tools that make it easier to organize and access your test assets by maintaining the test assets \(test cases, test scripts, and test suites\) in a common repository.  In addition, some form of access control is enforced by the automation test tool. This eases the maintenance burden by ensuring the integrity of your test suites. You may choose to grant stakeholders and managers read-only access, whereas developers and testers at the practitioner level may have read/write access.

####  Treat your test assets like any other software

Software must be maintained. This also applies to the software in your test suites. Test cases and their associated test scripts, whether recorded or programmed, should be maintained. And just as software has different kinds of maintenance \(e.g., corrective, preventative, or adaptive\) so too do the assets in your automated test suites. As you lifecycle your test suites, identify, if only informally, how you plan to disposition the test suite corrective maintenance \(e.g., syntactical errors in your scripts\), preventative maintenance \(e.g., where possible to write generalized test scripts\), and adaptive maintenance \(e.g., how you can use your test tooling to re-assign test assets within one suite to another suite or suites\). This can be captured, as described in the section **Plan Your Test Suites** above, in your test plan.

####  Improve the testability of your test suites through collaboration with developers

It's one thing to say that your test suites will need to be maintained due to changes in the application, changes in the testing target, etc. It's quite another thing to actually determine whether a test suite needs to be revamped and, if it does, what test assets within it need to be addressed.  One way to facilitate this is to use test suites as a way to communicate test decision to the developers. One way to perform continuous perfective maintenance of test suites is to think of your test suites as assets that belong to the development team rather than just the testers. You can perform a kind of perfective maintenance on test in the following ways:
  * use test suites to raise the level of abstraction
  * use test suites to provide focus for the developer
  * use test suites to articulate areas that the developers would like testers to focus on
  * make the construction and maintenance of test suites more efficient by understanding what area\(s\) developers want to focus on
  * use test suites to clarify test targets with developers

####  Don't be afraid to clean up your suites

Your test assets will evolve just as the application under test will. As requirements to the system change, the application will change as well. To maintain your test suites, you should continually check whether test assets are valid. If possible, validity checks should be performed after each new release of the software, preferably more frequently. Keeping your test suites relevant is a full-time job. Assume that changes in the software will lead to some degree of invalid tests within your test suites. Once these test assets have been identified as invalid, get rid of them. This will make the maintenance burden much more tolerable. Some automated test tooling environments make this task easier by providing ways to package outdated or invalid tests. In some cases, you may not be absolutely sure whether you want to completely get rid of tests within your test suite or even of getting rid of test suites altogether. To alleviate this burden, you can create packages for obsolete tests or test suites and dispose of tests or test suites by putting them in packages labeled for this purpose.
---

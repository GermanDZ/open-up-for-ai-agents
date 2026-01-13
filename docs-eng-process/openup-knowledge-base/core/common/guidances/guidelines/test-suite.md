---
title: Test Suite
source_url: core.tech.common.extend_supp/guidances/guidelines/test_suite_D54EEBED.html
type: Guideline
uma_name: test_suite
page_guid: _0aDz0MlgEdmt3adZL5Dmdw
keywords:
- suite
- test
related:
  tasks:
  - run-tests-1
  workproducts:
  - test-script
---


 This guideline discusses how to maintain automated test suites.
---

Relationships

Related Elements|
  * [Run Tests](../../../../practice-technical/concurrent_testing/tasks/run-tests-1.md)
  * [Test Script](../../workproducts/test-script.md)
---|---

Main Description

###  Introduction

The test suite provides a means of managing the complexity of the test implementation. Many system test efforts fail because the team gets lost in the minutia of all of the detailed tests, and subsequently loses control of the test effort. Similar to UML packages, test suites provide a hierarchy of encapsulating containers to help manage the test implementation. They provide a means of managing the strategic aspects of the test effort by collecting tests together in related groups that can be planned, managed, and assessed in a meaningful way.  The test suite represents a container for organizing arbitrary collections of related test scripts. This may be realized \(implemented\) as one or more automated regression test suites, but the test suite can also be a work plan for the implementation of a group of related manual test scripts. Note also that test suites can be nested hierarchically, therefore one test suite may be enclosed within another.  Sometimes these groups of tests will relate directly to a subsystem or other system design element, but other times they'll relate directly to things such as quality dimensions, core "mission critical" functions, requirements compliance, standards adherence, and many others concerns that are organized based on requirements and therefore cut across the internal system elements.  Consider creating test suites that arrange the available test scripts, in addition to other test suites, in many different combinations: the more variations you have, the more you'll increase coverage and the potential for finding errors. Give thought to a variety of test suites that will cover the breadth and depth of the target test items. Remember the corresponding implication that a single test script \(or test suite\) may appear in many different test suites.  Some test automation tools provide the ability to automatically generate or assemble test suites. There are also implementation techniques that enable automated test suites to dynamically select all or part of their component test scripts for each test cycle run.  Test suites can help you maintain your test assets and impose a level of organization that facilitates the entire testing effort. Like physical objects, tests can break. It's not that they wear down, it's that something changed in their environment. Perhaps they've been ported to a new operating system. Or, more likely, the code they exercise has changed in a way that correctly causes the test to fail. Suppose you're working on version 2.0 of an e-banking application. In version 1.0, this method was used to log in:  public boolean login \(String username\);  In version 2.0, the marketing department has realized that password protection might be a good idea. So the method is changed to this:  public boolean login \(String username, String password\);  Any test that uses the first form of the login will fail. It won't even compile. In this example you could find that, not many useful tests can be written that don't use login. You might be faced with hundreds or thousands of failing tests.  These tests can be fixed by using a global search-and-replace tool that finds every instance of login\(something\) and replaces it with login\(something, "dummy password"\). Then arrange for all the testing accounts to use that password, and you're on your way.  Then, when marketing decides that passwords should not be allowed to contain spaces, you get to do it all over again.  This kind of thing is a wasteful burden, especially when, as is often the case, the test changes aren't so easily made. There is a better way.  Suppose that the test scripts originally did not call the product's login method. Rather, they called a library method that does whatever it takes to get the test logged in and ready to proceed. Initially, that method might look like this:  public boolean testLogin \(String username\) \{
return product.login\(username\);
\}  When the version 2.0 change happens, the utility library is changed to match:  public Boolean testLogin \(String username\) \{
return product.login\(username, "dummy password"\);
\}  Instead of a changing a thousand tests, you change one method.  Ideally, all the needed library methods would be available at the beginning of the testing effort. In practice, they can't all be anticipated-you might not realize you need a testLogin utility method until the first time the product login changes. So test utility methods are often "factored out" of existing tests as needed. It is very important that you perform this ongoing test repair, even under schedule pressure. If you do not, you will waste much time dealing with an ugly and un-maintainable test suite. You might well find yourself throwing it away, or being unable to write the needed numbers of new tests because all your available testing time is spent maintaining old ones.  Note: the tests of the product's login method will still call it directly. If its behavior changes, some or all of those tests will need to be updated. \(If none of the login tests fail when its behavior changes, they're probably not very good at detecting defects.\)

###  Abstraction helps manage complexity

The previous example showed how tests can abstract away from the concrete application. Most likely you can do considerably more abstraction. You might find that a number of tests begin with a common sequence of method calls: they log in, set up some state, and navigate to the part of the application you're testing. Only then does each test do something different. All this setup could-and should-be contained in a single method with an evocative name such as readyAccountForWireTransfer. By doing that, you're saving considerable time when new tests of a particular type are written, and you're also making the intent of each test much more understandable.  Understandable tests are important. A common problem with old test suites is that no one knows what the tests are doing or why. When they break, the tendency is to fix them in the simplest possible way. That often results in tests that are weaker at finding defects. They no longer test what they were originally intended to test.

###  Throwing away tests

Even with utility libraries, a test might periodically be broken by behavior changes that have nothing to do with what it checks. Fixing the test doesn't stand much of a chance of finding a defect due to the change; it's something you do to preserve the chance of the test finding some other defect someday. But the cost of such a series of fixes might exceed the value of the tests hypothetically finding a defect. It might be better to simply throw the test away and devote the effort to creating new tests with greater value.  Most people resist the notion of throwing away a test, at least until they're so overwhelmed by the maintenance burden that they throw all the tests away. It is better to make the decision carefully and continuously, test by test, asking:
  * How much work will it be to fix this test well, perhaps adding to the utility library?
  * How else might the time be used?
  * How likely is it that the test will find serious defects in the future? What's been the track record of it and related tests?
  * How long will it be before the test breaks again?

The answers to these questions will be rough estimates or even guesses. But asking them will yield better results than simply having a policy of fixing all tests.  Another reason to throw away tests is that they are now redundant. For example, early in development, there might be a multitude of simple tests of basic parse-tree construction methods \(the LessOp constructor and the like\). Later, during the writing of the parser, there will be a number of parser tests. Since the parser uses the construction methods, the parser tests will also indirectly test them. As code changes break the construction tests, it's reasonable to discard some of them as being redundant. Of course, any new or changed construction behavior will need new tests. They might be implemented directly \(if they're hard to test thoroughly through the parser\) or indirectly \(if tests through the parser are adequate and more maintainable\).
---

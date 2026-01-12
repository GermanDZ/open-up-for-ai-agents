---
title: Developer Testing
source_url: core.tech.common.extend_supp/guidances/concepts/developer_testing_FEBDAED6.html
type: Concept
uma_name: developer_testing
page_guid: _ADwlAJRtEdyrdaw_xGakyw
keywords:
- developer
- testing
related:
  guidelines:
  - developer-testing-1
  - test-driven-development
  other:
  - how-to-adopt-the-evolutionary-design-practice
  - how-to-adopt-the-test-driven-development-practice
  tasks:
  - implement-developer-tests-1
  - run-developer-tests-1
---


 Developers regression test their code on a continuous basis to ensure that it works as expected.
---

Relationships

Related Elements|
  * [Developer Testing](../guidelines/developer-testing-1.md)
  * [How to Adopt the Evolutionary Design Practice](../../../../practice-technical/evolutionary_design/guidances/roadmaps/how-to-adopt-the-evolutionary-design-practice.md)
  * [How to Adopt the Test Driven Development Practice](../../../../practice-technical/test_driven_development/guidances/roadmaps/how-to-adopt-the-test-driven-development-practice.md)
  * [Implement Developer Tests](../../../../practice-technical/test_driven_development/tasks/implement-developer-tests-1.md)
  * [Run Developer Tests](../../../../practice-technical/test_driven_development/tasks/run-developer-tests-1.md)
  * [Test Driven Development](../../../../practice-technical/test_driven_development/guidances/guidelines/test-driven-development.md)
---|---

Main Description

Developer testing is the act of regression testing source code by developers. This is sometimes called "unit regression testing" but many developer tests go beyond unit testing to address integration testing as well.

###  Testing Philosophies

Here are some important philosophies with regard to developer testing:

  1. The goal is to find defects. Successful tests find bugs, but correcting the bugs falls into other areas.
  2. Test early and often. The cost of change rises exponentially the longer it takes to find and then remove a defect. The implication is that you want to test as early as possible.
  3. Testing builds confidence. Many people fear making a change to their code because they are afraid that they will break it, but with a full test suite in place if you do break something you know you will detect it and then fix it.
  4. One test is worth a thousand opinions. You can say that your application works, but until you show the test results you might not be believed.
  5. Test to the risk. The riskier something is, the more it needs to be reviewed and tested. For example, you should invest significantly more effort testing a safety-critical algorithm for measuring radiation doses, and far less effort testing the "change font size" function of the same application.
  6. You can validate all artifacts. You can test all your artifacts, not just your source code, although the focus of this guidance is testing code.

###  Qualities of a Good Developer Test

These are the qualities of a good developer test:
  * It runs fast. It has short setup, run time, and clean-up.
  * It runs in isolation. You should be able to reorder your tests.
  * It is understandable. Good tests have consistent and informative names and use data that makes them easy to read and to understand.
  * It uses real data. For example, use copies of production data when appropriate, but remember that you'll typically have to create some specific "artificial" test data as well.
  * It is minimally cohesive. The test represents one step toward your overall goal. The test should address one and one only issue.
---

More Information

Guidelines|
  * [Developer Testing](../guidelines/developer-testing-1.md)
  * [Test Driven Development](../../../../practice-technical/test_driven_development/guidances/guidelines/test-driven-development.md)
---|---

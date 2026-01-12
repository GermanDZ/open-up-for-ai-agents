---
title: Test Ideas
source_url: core.tech.common.extend_supp/guidances/guidelines/test_ideas_55AF9B0F.html
type: Guideline
uma_name: test_ideas
page_guid: _0jzlsMlgEdmt3adZL5Dmdw
keywords:
- ideas
- test
related:
  tasks:
  - create-test-cases-1
  - implement-tests-1
---


 This guideline identifies common faults and mistakes done when developing software. It shows how to create test ideas from method calls, and from boolean and relational expressions.
---

Relationships

Related Elements|
  * [Create Test Cases](../../../../practice-technical/concurrent_testing/tasks/create-test-cases-1.md)
  * [Implement Tests](../../../../practice-technical/concurrent_testing/tasks/implement-tests-1.md)
---|---

Main Description

###  Introduction

Test ideas are used to generate tests. Test ideas can come from many different sources. In general, they can be derived in different ways depending on the given development domain, the kind of application being developed, and the sophistication of the testers. Although test ideas are derived in many different ways, there are some useful categories for generating them. This guideline will describe some of these categories as well as some general heuristics for creating good test ideas.

####  Test Ideas and Functions

Below are some test ideas to calculate the square root:

  1. A number that's barely less than zero as input
  2. Zero as the input
  3. Number that's a perfect square, like 4 or 16 \(is the result exactly 2 or 4?\)
  4. Print to a LaserJet IIIp
  5. Test with database full

The first 3 test ideas validate input while the last 2 address environmental issues. Even though these statements are very incomplete they ensure that an idea is not forgotten.

####  Test Ideas and Boundaries

Test ideas are often based on fault models. Consider boundaries. It's safe to assume the square root function can be implemented something like this:
double sqrt\(double x\) \{
if \(x < 0\)
// signal error
...
It's also plausible that the < will be incorrectly typed as <=. People often make that kind of mistake, so it's worth checking. The fault cannot be detected with X having the value 2, because both the incorrect expression \(x<=0\) and the correct expression \(x<0\) will take the same branch of the if statement. Similarly, giving X the value -5 cannot find the fault. The only way to find it is to give X the value 0, which justifies the second test idea.

####  Test Idea and Methods

Let's suppose you're designing tests for a method that searches for a string in a sequential collection. It can either obey case or ignore case in its search, and it returns the index of the first match found or -1 if no match is found.
int Collection.find\(String string, Boolean ignoreCase\);  Here are some test ideas for this method, each of which could be implemented as a test.

  1. Match found in the first position
  2. Match found in the last position
  3. No match found
  4. Two or more matches found in the collection
  5. Case is ignored; match found, but it wouldn't match if case was obeyed
  6. Case is obeyed; an exact match is found
  7. Case is obeyed; a string that would have matched if case were ignored is skipped

However, different test ideas can be combined into a single test; for example, the following test satisfies test ideas 2, 6, and 7:  **Setup:** Collection initialized to \["dawn", "Dawn"\]
**Invocation:** Collection.find\("Dawn", false\)
**Expected result:** Return value is 1 \(it would be 0 if "dawn" were not skipped\)

####  Test Idea Simplicity and Complexity

Making test ideas nonspecific makes them easier to combine.
Creating many several small tests that satisfy a few test ideas makes it simpler to:
  * "Copy and Tweak" the tests to meet other test idea
  * Easy of debugging - if you have test that covers 2 test ideas then you know the fault is one or two area, but if the test covers 7 test ideas you will spend more time debugging the issue.

If the test ideas list were complete, with a test idea for every fault in the program, it wouldn't matter how you wrote the tests. But the list is always missing some test ideas that could find bugs. Smaller more complex tests increase the chance the test will satisfy a test idea that you didn't know you needed.

####  Complex Tests

Sometimes when you're creating more complex tests, new test ideas come to mind. However, there are reasons for not creating complex tests.
  * Complex test are more difficult to debug because they usually cover multiple test ideas
  * Complex tests are more difficult to understand and maintain. The intent of the test is less obvious.
  * Complex tests are more difficult to create.

Constructing a test that satisfies five test ideas often takes more time than constructing five tests that each satisfies one. Moreover, it's easier to make mistakes - to think you're satisfying all five when you're only satisfying four.
In practice, find a reasonable balance between complexity and simplicity.
---

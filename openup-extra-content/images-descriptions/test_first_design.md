---
title: "Image: test_first_design.jpg"
image_file: "../test_first_design.jpg"
source: "practice.tech.test_driven_development.base/guidances/guidelines/resources/test_first_design.jpg"
---

# Image Description: test_first_design.jpg

## Description

This image is a flowchart or activity diagram depicting a Test-Driven Development (TDD) workflow. It illustrates the iterative process of adding a test, running tests, making changes, and re-running tests until all tests pass and development can continue or stop.

**Overall Structure:**

The diagram uses standard flowchart symbols: a filled black circle for the start, rounded rectangles for activities, and a concentric black and white circle for the end. Arrows indicate the flow of control, and labels on the arrows represent conditions for transitions.

**Flow Description:**

1. **Start Node:** The process begins at the top with a solid black circle, indicating the start of the workflow. An arrow points downwards from this node.

2. **Activity 1: "Add a test"**
   - The first activity is a rounded rectangle labeled "Add a test." This signifies the initial step in TDD, where a new test case is written for a desired piece of functionality that does not yet exist.
   - An arrow leads from the Start Node to "Add a test."
   - There is a return arrow from the second "Run the tests" activity, labeled "[Pass, Development continues]," looping back to "Add a test." This indicates that a successful cycle of development leads to adding more tests for new features.

3. **Activity 2: "Run the tests" (First Instance)**
   - An arrow descends from "Add a test" to a rounded rectangle labeled "Run the tests." At this stage, the newly added test (and potentially existing tests) are executed.
   - **Conditional Branch 1 (Failure):** If the tests fail, an arrow labeled "[Fail]" points downwards to the next activity, "Make a little change." This is the expected outcome in TDD when a test is added for functionality that hasn't been implemented yet.
   - **Conditional Branch 2 (Unexpected Pass):** If the tests pass, an arrow labeled "[Pass]" loops back upwards to "Add a test." This scenario implies that the test added did not initially fail, which might mean the functionality already exists or the test is not correctly written to fail first (a key TDD principle of "Red").

4. **Activity 3: "Make a little change"**
   - Following a "[Fail]" result from the first "Run the tests," the flow proceeds to a rounded rectangle labeled "Make a little change." This activity represents writing the minimum amount of code required to make the recently failing test pass.
   - There is a return arrow from the second "Run the tests" activity, labeled "[Fail]," looping back to "Make a little change." This shows that if the tests still fail after a change, further small changes are needed.

5. **Activity 4: "Run the tests" (Second Instance)**
   - An arrow descends from "Make a little change" to another rounded rectangle labeled "Run the tests." All tests are run again after the code change.
   - **Conditional Branch 1 (Failure):** If the tests fail, an arrow labeled "[Fail]" loops back upwards to "Make a little change." This indicates that the implemented change was insufficient or incorrect, and further modifications are required.
   - **Conditional Branch 2 (Success - Continue Development):** If the tests pass, an arrow labeled "[Pass, Development continues]" loops back to "Add a test." This signifies that the current feature is successfully implemented and tested, and the developer can now move on to implement the next feature by adding a new test.
   - **Conditional Branch 3 (Success - Stop Development):** If the tests pass, another arrow labeled "[Pass, Development stops]" points downwards to the End Node. This represents the completion of the overall development effort, where all planned features are implemented and all tests pass.

6. **End Node:** The process concludes at the bottom with a concentric black and white circle, indicating the end of the workflow, reached when all tests pass and development is stopped.

**TDD Principles Illustrated:**

The diagram clearly illustrates the "Red-Green-Refactor" cycle inherent in TDD:
- **Red:** "Add a test" (which is expected to fail).
- **Green:** "Run the tests" (first instance, expecting fail) -> "Make a little change" -> "Run the tests" (second instance, aiming for pass).
- **Refactor (Implied):** While not explicitly labeled as "Refactor," the "Make a little change" and subsequent "Run the tests" (with the "[Fail]" loop back) inherently include the refactoring step to improve code quality while maintaining test passes. The loop "[Pass, Development continues]" back to "Add a test" also implies continuous iteration and potential refactoring.

## For LLMs

This sidecar file provides text-based description of the image to enable understanding without visual processing.

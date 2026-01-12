---
title: "Image: tdd_in_context.jpg"
image_file: "../tdd_in_context.jpg"
source: "practice.tech.test_driven_development.base/guidances/supportingmaterials/resources/tdd_in_context.jpg"
---

# Image Description: tdd_in_context.jpg

## Description

This image is an activity diagram or flowchart illustrating a software development workflow, focusing on iterative design, development, and integration. It depicts a cyclical process for handling changes and completing work items.

**High-Level Description:**

The diagram outlines a process that begins with an initial state, moves through decision points based on the nature of changes (regular or trivial), engages in design and test-driven development practices, and then evaluates the completeness of increments and overall work items, with loops back to earlier stages for incomplete tasks or further design. The process culminates in system integration upon the successful completion of a work item.

**Detailed Description of Elements and Flow:**

1. **Start Node:** The process begins at the top with a solid blue circle, representing the initial state or entry point.

2. **Initial Decision Point:** An unlabelled diamond shape immediately follows the start node. This serves as a primary decision or merge point. An arrow labeled "work item incomplete" loops back to this diamond from a later stage, indicating an iterative flow where tasks are revisited if not fully completed.

3. **Second Decision Point (Change Type):** A second diamond shape is positioned directly below the first. This diamond represents a decision point regarding the type of change required:
   - **"regular change" path:** An arrow labeled "regular change" leads left from this diamond to an activity box titled "Evolutionary Design".
   - **"trivial change" path:** An arrow labeled "trivial change" leads directly downwards from this diamond to an activity box titled "Test Driven Development Practice".

4. **Activity Nodes (User Icons):** There are three activity nodes, each represented by a rounded rectangular box containing an icon depicting two stylized figures at a desk, suggesting human involvement, collaboration, or a team activity.
   - **"Evolutionary Design"**: This activity is undertaken for "regular changes." An arrow connects this box to the "Test Driven Development Practice" box, indicating that evolutionary design precedes or leads into TDD.
   - **"Test Driven Development Practice"**: This activity is performed for "trivial changes" directly, or after "Evolutionary Design" for "regular changes."
   - **"Integrate System"**: This final activity is reached when a "work item complete," leading to the end state.

5. **Third Decision Point (Design Feedback):** Below "Test Driven Development Practice" is another diamond shape. This decision point evaluates the outcome of the development practice:
   - **"further design required" path:** An arrow labeled "further design required" loops left and upwards from this diamond back to the "Evolutionary Design" activity, indicating that TDD might reveal the need for additional design work.
   - **"increment complete" path:** An arrow labeled "increment complete" leads right from this diamond to a fourth diamond shape.

6. **Fourth Decision Point (Work Item Completeness):** This diamond on the right receives input from the "increment complete" path and assesses the overall work item status:
   - **"work item incomplete" path:** An arrow labeled "work item incomplete" loops upwards from this diamond back to the very first decision point, signifying that if an increment is complete but the entire work item is not, the process returns to an earlier stage for further iterations.
   - **"work item complete" path:** An arrow labeled "work item complete" leads downwards from this diamond to the "Integrate System" activity box.

7. **End Node:** The process concludes at the bottom with a solid blue circle surrounded by an outer circle, representing the final state after system integration.

**Meaning and Implications:**

The diagram illustrates an agile or iterative software development methodology. It emphasizes:
- **Adaptability:** The flow adapts based on the complexity of changes (regular vs. trivial).
- **Iterative Design:** "Evolutionary Design" is triggered by "regular changes" and can be revisited if "further design is required" after "Test Driven Development Practice," highlighting a continuous refinement approach.
- **Test-Driven Development (TDD):** TDD is a central practice, occurring for both trivial and regular changes, underscoring its role in ensuring quality.
- **Feedback Loops:** Explicit feedback loops exist for "further design required" and "work item incomplete," promoting continuous improvement and task completion.
- **Integration:** System integration is the final step upon the successful completion of a work item.

The visual representation effectively conveys a dynamic process that continuously evaluates progress and makes decisions to guide development towards system integration.

## For LLMs

This sidecar file provides text-based description of the image to enable understanding without visual processing.

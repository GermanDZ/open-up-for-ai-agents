---
title: "Image: ed_in_context.jpg"
image_file: "../ed_in_context.jpg"
source: "practice.tech.evolutionary_design.base/guidances/supportingmaterials/resources/ed_in_context.jpg"
---

# Image Description: ed_in_context.jpg

## Description

This image is an activity diagram or flowchart illustrating a software development process, specifically focusing on handling changes and iterations within a development lifecycle. It outlines decision points and key development practices.

**High-Level Description:**

The diagram depicts a circular process for implementing changes, distinguishing between "regular" and "trivial" changes, and incorporating practices like "Evolutionary Design" and "Test Driven Development." It includes a feedback loop for incomplete work items and concludes with system integration upon completion.

**Components and Flow:**

1. **Start Node:** The process begins at the top with a solid blue circle, representing the initial state or entry point into the workflow.

2. **First Decision Point (Top Diamond):**
   - An arrow from the start node leads to the first diamond-shaped decision node. This node represents an initial evaluation or decision point in the process.
   - There is a large loop back to this node from a later decision point, labeled "work item incomplete," indicating that if a work item is not finished, the process returns here for re-evaluation or continuation.

3. **Second Decision Point (Middle Diamond):**
   - From the first decision point, an arrow leads to a second diamond-shaped decision node. This node evaluates the nature of the change.
   - **"regular change" path:** An arrow labeled "regular change" points to the left, leading to an activity box with a person-and-document icon labeled "**Evolutionary Design**." This suggests that significant changes go through a more iterative design process.
   - **"trivial change" path:** An arrow labeled "trivial change" points downwards, leading to an activity box with a person-and-document icon labeled "**Test Driven Development Practice**." This indicates that minor changes might directly proceed with TDD.

4. **Activity Nodes:**
   - **Evolutionary Design:** This activity node (with a person-and-document icon) is reached for "regular changes." An arrow from "Evolutionary Design" leads down to "Test Driven Development Practice," implying that Evolutionary Design might feed into TDD.
   - **Test Driven Development Practice:** This activity node (with a person-and-document icon) is central to the process. It is reached either directly from a "trivial change" or after "Evolutionary Design."

5. **Third Decision Point (Bottom Diamond):**
   - An arrow from "Test Driven Development Practice" leads to a third diamond-shaped decision node. This node likely evaluates the completion status of an increment.
   - **"further design required" path:** An arrow labeled "further design required" points left and then upwards, looping back to the "Evolutionary Design" activity. This indicates that the TDD practice might reveal the need for more design work, sending the process back to that stage.
   - **"increment complete" path:** An arrow labeled "increment complete" points right, leading to another diamond-shaped decision node.

6. **Fourth Decision Point (Right Diamond):**
   - This diamond is reached when an "increment complete."
   - **"work item incomplete" path:** An arrow labeled "work item incomplete" points upwards and left, looping all the way back to the very first decision point. This is a critical feedback loop, signifying that even if an increment is complete, the overall work item might not be, requiring further iterations.
   - **"work item complete" path:** An arrow labeled "work item complete" points downwards, leading to an activity box with a person-and-document icon labeled "**Integrate System**." This signifies the final stage when the entire work item is done.

7. **End Node:**
   - From "Integrate System," an arrow leads to a solid blue circle with a darker blue border, representing the final end state of the process.

**Icons:**

The recurring icon of a person with a document appears next to "Evolutionary Design," "Test Driven Development Practice," and "Integrate System." This typically denotes a specific role, practice, or structured activity in the context of a process diagram.

**Overall Flow Summary:**

The diagram describes a continuous development cycle where changes are categorized and handled accordingly. Both paths lead to "Test Driven Development Practice." After TDD, if more design is needed, it loops back to "Evolutionary Design." If an increment is complete, it's checked if the overall work item is complete. If not, the process loops back to the start. If the work item is complete, the system is integrated, and the process ends.

## For LLMs

This sidecar file provides text-based description of the image to enable understanding without visual processing.

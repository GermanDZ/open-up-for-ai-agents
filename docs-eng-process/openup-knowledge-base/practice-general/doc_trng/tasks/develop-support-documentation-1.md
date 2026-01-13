---
title: Develop Support Documentation
source_url: practice.gen.doc_trng.base/tasks/develop_support_documentation_A3136BBB.html
type: Task
uma_name: develop_support_documentation
page_guid: _-zfOp-B8EeC1y_NExchKwQ
keywords:
- develop
- documentation
- support
related:
  roles:
  - technical-writer-1
---


 This type of documentation is used by production support and IT operations personnel on a regular basis to answer end users' questions about a particular product, to troubleshoot issues, or to determine if an incident is a result of a defect or missed requirements.
---
Disciplines: [Deployment](../../../core/cat/disciplines/deployment-1.md)

Purpose

The purpose of this task is to ensure that the personnel who are tasked with supporting the system have enough information about the product to perform their jobs effectively after the product has been placed into production.
---

Relationships

Roles| Primary Performer:
  * [Technical Writer](../../../core/role/roles/technical-writer-1.md)

| Additional Performers:
---|---|---
Inputs| Mandatory:
  * None

| Optional:
  * [Product Documentation](../workproducts/product-documentation-2.md)
  * [User Documentation](../workproducts/user-documentation-2.md)


Outputs|
  * [Support Documentation](../workproducts/support-documentation-2.md)



Main Description

Support documentation often is the most overlooked aspect of a documentation effort. Anyone who has had the opportunity to provide end user support for a particular application can appreciate how important effective, well-written support documentation can be. This documentation very often is technical in nature and differs significantly from user or product documentation, which normally is written for the lay person.  The development team should do its best to make sure that personnel who perform an IT support role have the right amount and the relevant type of information necessary to support the application, whether they provide Tier 1, Tier 2, or Tier 3 support. Support documentation often is developed based on these three different support categories. How effectively the code base is commented and the ease with which those comments are found and understood contributes to the quality and quantity of support documentation.
---

Steps

Determine support documentation contents |  This step is often challenging for development teams because they must put themselves in the position of IT support personnel to develop the right kind and right amount of useful content. It is advantageous to visit the support organization and ask them what types of documentation they would want delivered to them at each Release. You might be surprised at what they say, and it could make your documentation tasks easier if you know exactly what type of information they want.  Because every product is different, and because each program or IT support organization has unique needs, it is impossible to list recommended contents for support documentation. However, each program should create support documentation standards for the development teams that support its program.
---

Leverage available materials

Use the development team's Release Plan as a mechanism to define the scope of the support documentation. Source materials that can contribute effectively to support documentation content include:
  * Component Design Specifications
  * Architecture Notebook
  * User Stories
  * Test Cases
  * Test Scenarios
  * Storyboards and Wireframes
  * Defect Records
  * Lessons Learned
  * Data Dictionary
  * Logical and Physical Data Models
  * Coding Standards
  * Acceptance Tests
  * Test Harness
---

Write support documentation

Based on the previous steps, write the support documentation. One way to do this is to assign sections of the document \(determined in the step "Determine Support Documentation Contents" above\) to development team members as sprint/iteration tasks in the release sprint/iteration.
---

Perform quality review

As the support documentation is integrated, plan and conduct a quality review during the release sprint/iteration to ensure that the documentation is of sufficient quantity and quality. Update and improve the support documentation based on the results of the quality review.
---

Deliver support documentation

At the end of a release, deliver the completed support documentation to the deployment manager. Ensure that the program has a plan for communicating the support documentation to the IT operations support organization in a timely manner.
---

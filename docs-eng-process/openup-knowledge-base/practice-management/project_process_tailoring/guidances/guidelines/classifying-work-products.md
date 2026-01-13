---
title: Classifying Work Products
source_url: practice.mgmt.project_process_tailoring.base/guidances/guidelines/classifying_work_products_4250A298.html
type: Guideline
uma_name: classifying_work_products
page_guid: '7.27749388241665E-306'
keywords:
- classifying
- products
- work
related:
  concepts:
  - development-case
---


 This guideline offers a classification scheme for documenting the importance of individual work products and whether or not they will be used.
---

Relationships

Related Elements|
  * [Development Case](../concepts/development-case.md)
---|---

Main Description

###  Introduction

These classifications can be used to describe how to use work products \(and reports\) when tailoring the process for a project. These values can be complemented with a separate classifier to define the review procedures for the work product.  |  Classification  |  Explanation
---|---
Must have  |  You must use this work product. It is a key work product and may cause problems later in development if it's not produced.
Should have  |  You should have this work product, if at all possible, but it is negotiable. If you do not produce this work product, you should be able to justify why not.
Could have  |  Could have means that this work product doesn't have to be produced. It's only produced if it adds value and if there's enough time.
Won't have  |  This means you won't use this work product. This may occur where a Rational Unified Process work product is replaced by a local work product.


This classification scheme can be extended or customized to reflect your organization's individual culture.

An example of when this classification scheme may be adjusted depends on the level of tailoring that is being performed. For example, when tailoring a process for a specific project, the decision of whether or not a specific work product is to be used is made as part of the tailoring effort. In such cases, the above classification scheme may be reduced to "Required" and "Not Required". In other cases, say when you are tailoring a process for an organization and further tailoring for individual projects is expected, a more extensive classification scheme as described in the above table becomes important.

###  Impact of Classification

All work products classified as _Must have_ or _Should have_ must have their review procedures, tools, templates and configuration management practices defined.

The specification of these procedures is optional for work products classified as _Could have_ -these decisions could be left to the developers or projects that decide to produce these work products.

All work products classified as _Won't have_ must have their omission justified.

The major benefit of adopting this classification scheme is that it clearly denotes how the process has been customized, and where there are options for negotiation and local decision making.

###  Examples of Usage

One way to think about the work product classification scheme is that it sets constraints on how the work products are used.

For example, if you decide that the project could have an Analysis Model, then further customization could adjust these values by deciding that the project will meet one of the following criteria:
  * It will have an Analysis Model
  * It won't have an Analysis Model
  * It will stay in its current state \(an Analysis Model is optional\)

The classification scheme can even be used dynamically-allowing the status of the work product to change depending upon which phase the project is in.

The following table shows different ways of treating the Analysis Model. The **How to use** column defines how the work product is used in each of the phases.

Work Product  |  How to use  |  Comment
---|---|---
Incep  |  Elab  |  Const  |  Trans
Analysis Mode  |  Won't  |  Won't  |  Won't  |  Won't  |  No Analysis Model is developed
Analysis Model  |  Could  |  Could  |  Could  |  Could  |  Normal
Analysis Model  |  Could  |  Should  |  Won't  |  Won't  |  An evolutionary approach where the Analysis Model is replaced by the Design Model
Analysis Model  |  Must  |  Won't  |  Won't  |  Won't  |  An evolutionary approach where the Analysis Model is mandatory during the Inception phase to help scope the project but is replaced by the Design Model during Elaboration
Analysis Model  |  Should  |  Must  |  Must  |  Must  |  A formal process where the Analysis Model is a mandatory, preserved work product that is optional in the inception phase

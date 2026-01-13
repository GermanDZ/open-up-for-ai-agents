---
title: Requirement Attributes
source_url: core.tech.common.extend_supp/guidances/concepts/requirement_attributes_4AC73153.html
type: Concept
uma_name: requirement_attributes
page_guid: _VQ268O0KEdqHTdbLTmC5IQ
keywords:
- additional
- attributes
- information
- requirement
related:
  tasks:
  - develop-technical-vision-1
---


 Requirements attributes capture additional information, such as risk, planned iteration, source of requirement, about each requirement. This additional information is used to manage the project.
---

Relationships

Related Elements|
  * [Develop Technical Vision](../../../../practice-technical/shared_vision/tasks/develop-technical-vision-1.md)
---|---

Main Description

Attributes are a very important source of requirements information. Just as every person has attributes \(age, hair color, gender\), each requirement has a source, a relative importance, and time it was created. Attributes do more than simply clarify a requirement. If created properly, they can yield significant information about the state of the system. Just as you can run a database query to find all men with brown hair over age 30, given our human example, you can run queries on the status of requirements to find all high-priority requirements from the customer in the last 30 days. [\[TEL06\]](./../../../core.default.nav_view.base/guidances/supportingmaterials/references_C6FF2A8D.html)

####  Examples of attributes

Listed below is a partial list of some common attributes and a brief description of their meaning. Some attributes are best described as a number, date, Boolean \(true or false\) or a text field for entering free format comments. Other attributes can be expressed as lists. For instance, priority type is a list of high, medium, and low; Weekday is a list which includes Monday, Tuesday, and so on.  _Source_ \- Person, document or other origin of a given requirement. This is useful for determining whom to call for questions or for grouping requirements according to the person making the demands.  _Priority_ \- Statement of relative importance of the requirement, either to the system \(mandatory, critical, optional\) or to other requirements \(high, medium, low\). It is good to track the mandatory or high-priority items as an indication of how well the system will meet the greatest needs or for compliance-related metrics.  _Assigned to_ \- Who in the organization is responsible for making sure the requirement is met \(person's name or organizational name\).  _Comments_ \- Reviewer's or writer's comments on a requirement.  _Difficulty_ \- An indication of the level of effort needed or how hard it will be to implement the requirement \(high, medium, low\).  _Status_ \- Degree of completeness \(completed, partial, not started\).  _Risk_ \- Confidence measure on the likelihood of meeting \(or not meeting\) a requirement. Could be high, medium, low or the integers one through ten.  _Due By_ \- Date the requirement must be provided.  _Method of verification_ \- Qualification type to be used to verify that a requirement has been met: analysis, demonstration, inspection, test, and walkthrough.  _Level of Test_ \- Describes the verification lifecycle stage at which the requirement is determined to be met: unit test, component, system or product.  _Subsystem Allocation_ \- Name of system or subsystem a requirement is to be assigned to \(for instance, flight control module, wing assembly, passenger cabin\).  _Test Number_ \- Identification of a specific test or other method of verification.
---

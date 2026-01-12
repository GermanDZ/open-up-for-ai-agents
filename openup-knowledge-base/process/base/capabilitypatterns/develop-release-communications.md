---
title: Develop Release Communications
source_url: process.openup.base/capabilitypatterns/develop_release_communications_6364D822.html
type: TaskDescriptor
uma_name: develop_release_communications
page_guid: _y7a0AJiLEeGOvpP1fVrVNA
keywords:
- communications
- develop
- release
related:
  other:
  - deployment-engineer-1
---


 Stakeholders should be notified when a product \(or feature set\) is placed into production.
---

Purpose

The purpose of this task is to create the content and criteria to identify who is notified and to describe how they are notified after a release is deployed successfully to the production environment.
---

Relationships

Roles| Primary:
  * [Deployment Engineer](deployment-engineer-1.md)

| Additional: | Assisting:
---|---|---|---
Inputs| Mandatory:
  * [Deployment Plan](deployment-plan-1.md)

| Optional:
  * [Release Controls](release-controls-1.md)

| External:
  * None


Outputs|
  * [Release Communications](release-communications.md)



Main Description

When a release is pushed to production, all the stakeholders of that product should be notified that the event has happened and what the release means to each of the stakeholders. Often, the output of this task does not need to be created from scratch; for products that plan multiple releases, just updating the communique details for each release might be enough. However, if any of the stakeholder groups change, or there is a significant difference in the product distribution, more significant content might need to be developed.  In any case, communicating effectively to the end user community is important. A development team can develop high quality software, but if messaging to the stakeholders is conducted poorly or not at all, the end user experience might be degraded. By simply answering the questions "who, what, when, where, why, and how" in a format appropriate for each stakeholder group, a product release can become a more satisfying experience for all those involved.
---

Steps

Identify stakeholders for this release | The development team should know exactly which stakeholder groups will benefit from the upcoming release. First, identify the stakeholders for this release. Next, determine how each stakeholder group is expected to benefit from the release based on the components that will be delivered to production.
---

Draft communique for each stakeholder group

For each stakeholder group, document the following:
  * The features that will be deployed to production that those stakeholders are expected to benefit from
  * The business value that stakeholder group will obtain from the feature set being released
  * How, when, and where that stakeholder group will be able to access the new functionality and what special credentials or permissions are required
  * Any additional constraints or information that the stakeholder group should be aware of, such as availability restrictions, geographical restrictions, server limitations, regulatory requirements, etc.
---

Provide commiques to deployment manager

After drafting the communiques for each stakeholder group, the development team should provide those drafts to the deployment manager. Typically, release communications are consolidated and released at the program level. The deployment manager and deployment engineers normally are responsible for ensuring that all release communications are consistent and concise. The deployment manager will determine the appropriate time to communicate information about the upcoming release to the appropriate stakeholders.
---

Properties

Multiple Occurrences| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Event Driven| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Ongoing| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
Planned|
Repeatable| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

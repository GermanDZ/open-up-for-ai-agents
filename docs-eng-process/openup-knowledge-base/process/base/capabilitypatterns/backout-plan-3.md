---
title: Backout Plan
source_url: process.openup.base/capabilitypatterns/backout_plan_31075C71.html
type: WorkProductDescriptor
uma_name: backout_plan
page_guid: _DaTjoplXEeGlkdGl1HQlDA
keywords:
- backout
- plan
related:
  other:
  - deployment-engineer-3
---


 A backout plan defines the criteria and procedures to be followed if a release into production needs to be rolled back.
---

Purpose

The purpose of this work product is for the development team to provide, in one document, all the information needed by the production support organization to determine if a rollback is needed, who will authorize it, how it will be performed, etc.
---

Relationships

Roles| Responsible:
  * [Deployment Engineer](deployment-engineer-3.md)

| Modified By:
---|---|---

Main Description

While someone on the development team normally authors a draft version of the Backout Plan, the Deployment Engineer is ultimately responsible for its contents and existence. A backout plan typically answers the following questions:
  * Under what circumstances will a rollback be required? Or conversely, under what circumstances will the deployment be considered a success?
  * What is the time period within which a rollback can take place?
  * Which authorizing agent will make the decision to revert?
  * Who will perform the rollback and how soon after the decision has been made will the rollback be performed?
  * What procedures \(manual and automated\) will be followed to execute the rollback?
  * What other contingency measures or available workarounds should be considered?
  * What is the expected time required to perform a reversion?
  * What are the communication procedures required in the event of a backout?
  * Has the Backout Plan been successfully tested?
---

Properties

Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Planned| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

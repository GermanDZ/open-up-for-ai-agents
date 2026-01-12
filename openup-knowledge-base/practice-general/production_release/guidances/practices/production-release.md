---
title: Production Release
source_url: practice.gen.production_release.base/guidances/practices/production_release_D5DD627B.html
type: Practice
uma_name: production_release
page_guid: _IAG5wOB-EeC1y_NExchKwQ
keywords:
- production
- release
related:
  other:
  - how-to-adopt-the-production-release-practice
  concepts:
  - release-iteration
  workproducts:
  - backout-plan-4
  - deployment-plan-4
  - infrastructure-2
  - release-communications-4
  - release-controls-2
  - release-4
  tasks:
  - review-and-conform-to-release-controls-1
  - install-and-validate-infrastructure-1
  - plan-deployment-1
  - develop-backout-plan-1
  - develop-release-communications-1
  - package-the-release-1
  - execute-deployment-plan-1
  - verify-successful-deployment-1
  - execute-backout-plan-if-necessary-1
  - deliver-release-communications-1
  checklists:
  - deployment-plan-5
---


 This practice describes how to prepare and execute the release of a product \(or subset thereof\) into the production environment.
---

Relationships

Content References|
  * [How to Adopt the Production Release Practice](../roadmaps/how-to-adopt-the-production-release-practice.md)
  * [Release Iteration](../concepts/release-iteration.md)
  * Work Products
    * [Backout Plan](../../workproducts/backout-plan-4.md)
    * [Deployment Plan](../../workproducts/deployment-plan-4.md)
    * [Infrastructure](../../workproducts/infrastructure-2.md)
    * [Release Communications](../../workproducts/release-communications-4.md)
    * [Release Controls](../../workproducts/release-controls-2.md)
    * [Release](../../workproducts/release-4.md)
  * Tasks
    * [Review and Conform to Release Controls](../../tasks/review-and-conform-to-release-controls-1.md)
    * [Install and Validate Infrastructure](../../tasks/install-and-validate-infrastructure-1.md)
    * [Plan Deployment](../../tasks/plan-deployment-1.md)
    * [Develop Backout Plan](../../tasks/develop-backout-plan-1.md)
    * [Develop Release Communications](../../tasks/develop-release-communications-1.md)
    * [Package the Release](../../tasks/package-the-release-1.md)
    * [Execute Deployment Plan](../../tasks/execute-deployment-plan-1.md)
    * [Verify Successful Deployment](../../tasks/verify-successful-deployment-1.md)
    * [Execute Backout Plan \(if necessary\)](../../tasks/execute-backout-plan-if-necessary-1.md)
    * [Deliver Release Communications](../../tasks/deliver-release-communications-1.md)
  * [Deployment Plan](../checklists/deployment-plan-5.md)
---|---

Purpose

Releasing a finished or emerging product into production is no trivial matter. Sometimes, business operations are interrupted or shut down because a release has somehow corrupted the production environment. Because the release activity can have such a dramatic impact on the business, the purpose of the Production Release practice is to ensure that the application developed is properly prepared to be released into production without any unintended consequences.
---

Main Description

Mike Cohn, noted author on Scrum, states:

> ..."Some large or complex projects will require the use of "release Sprint/Iteration" or "hardening Sprint/Iteration" at the end of a release cycle \(say 6 two-week Sprint/Iterations then a 2-week release Sprint/Iteration\). The release Sprint/Iteration is not a dumping ground for sloppy work; rather it is a place where some hardening of the system can occur."

There are two components of the Production Release practice: 1\) Release Preparation, and 2\) Deployment. Release preparation establishes a release baseline and produces all the necessary supporting material necessary to deploy \(and back out, if necessary\) the release.  Deployment involves the act of delivering the release into the production environment, verifying that the integration of the release package into the existing environment was successful, and notifying all relevant stakeholders that the features of the release are available for use.  Unfortunately, there is little guidance available today regarding the practice of releasing to production. Although there is wealth of information documented in the Information Technology Infrastructure Library \(ITIL\) set of process books on this topic, those reference materials are used primarily by members of Production Support and IT Operations organizations and not application development groups.  This practice is designed to fill some of the void in this area for product development teams.
---

How to read this practice

The best way to read this practice is to become familiar with its overall structure, what is in it, and how it is organized.  Start with the tasks for preparing the release for production, then review the work products that result from those tasks. Next, review the tasks of the deployment activity. Although these tasks sound straightforward, there is much skill and effort that goes into them. That is why a seasoned Deployment Engineer should execute these tasks.
---

Additional Information

For additional information about Production Release, see:  Dean Leffingwell. _Agile Software Requirements: Lean Requirements Practices for Team, Programs, and the Enterprise_. Addison Wesley, 2011.

> Introduces the "Big Picture" of Scaled Agile and describes various aspects of that model, some in more detail than are covered in this method. Overall, a refinement of his previous works with the addition of Lean IT practices adopted from Lean Manufacturing.

Dean Leffingwell. _Scaling Software Agility: Best Practices for Large Enterprises_. Addison Wesley, 2007.

> The first major work on scaling Agile that was based on key implementation experiences at several international companies.
---

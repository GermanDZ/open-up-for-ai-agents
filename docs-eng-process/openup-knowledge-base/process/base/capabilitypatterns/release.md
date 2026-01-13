---
title: Release
source_url: process.openup.base/capabilitypatterns/release_F69FDFDB.html
type: WorkProductDescriptor
uma_name: release
page_guid: _N5I-gUVEEeK93ZZqiMLBsA
keywords:
- into
- release
related:
  other:
  - deployment-engineer
---


 A release is the transition of an increment of potentially shippable product from the development group into routine use by customers based on a successful placement of a release sprint's output into the production environment.
---

Purpose

The purpose of this work product is to:
  * At the team level, bring closure to a sprint/iteration or series of sprint/iterations by delivering working, tested software that can be potentially used by the end user community for whom the system was \(or is being\) developed
  * At the program level, deliver an integrated, value-added product increment to customers that was developed in parallel by multiple, coordinated, and synchronized development team members
---

Relationships

Roles| Responsible:
  * [Deployment Engineer](deployment-engineer.md)

| Modified By:
---|---|---

Main Description

A release consists of integrated, compiled code that runs cleanly, independently, and in its entirety. This is an important rule because in order to be released or even "potentially shippable," a release increment must be able to stand on its own, otherwise it is not shippable. Releases can be created at either the program or team level.  There are three potential uses for a release:
  * **It is not used outside of the program:** It has been produced to minimize risks linked to technology and a program's capability to integrate components and to produce a Build. This situation usually happens at the beginning of a new product lifecycle.
  * **It is used by beta customers and the program manager:** It allows end users to test it in a Beta test environment, which provides immediate feedback and reduces risks associated with user interface ergonomics. customer feedback will influence the program backlog for later consideration.
  * **It is deployed or shipped and used by end users:** This result provides immediate value to the end users.

In many organizations, a program release typically is timeboxed to 2 to 3 months of development effort and 2 to 4 weeks of hardening which results in a scheduled release approximately every 90 days. Releases for individual development teams usually occur more often than those for programs, but there are no hard and fast rules regarding how often releases should be scheduled. The only requirement is that working software should be delivered "frequently" by both development teams and programs. Although the example timeframe described above is arbitrary, empirical evidence suggests it is about right for most companies and fits nicely into quarterly planning cycles.  Each release has a set of release objectives and a projected delivery date; it also has a planned number of sprint/iterations. For example, a brief description of a release might be: "The goal of Release 2 is to provide B2B scheduling capability for the Ordering and Logistics Department. The release is targeted for June 31 and will consist of five 2-week feature development sprint/iterations and one 2-week release sprint/iteration."
---

Properties

Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Planned| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

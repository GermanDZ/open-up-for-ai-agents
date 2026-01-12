---
title: How to adopt the Continuous Integration practice
source_url: practice.tech.continuous_integration.base/guidances/roadmaps/how_to_adopt_continuous_integration_DBC46C5D.html
type: Roadmap
uma_name: how_to_adopt_continuous_integration
page_guid: _4qbzQPnTEdyLA5PXdgVJXw
keywords:
- adopt
- continuous
- integration
- practice
---

 This roadmap describes how to adopt the Continuous Integration practice.
---

Main Description

###  Getting started

The ultimate goal of continuous integration \(CI\) is to integrate and test the system on every change to minimize the time between injecting a defect and correcting it. If the team is new to continuous integration, though, it is best to start small and then incrementally add subpractices, as identified in the subsection that follows. For example, start with a simple daily integration build and incrementally add tests and automated inspections \(code coverage, and so forth\) to the build process, over time. As the team begins to adopt the sub-practices increase the build frequency. The following subpractices provide guidance in adopting CI.

####  Developer practices
  * **Make changes available frequently.** For CI to be effective, [Change Set](../../../../core/common/guidances/concepts/change-set.md)s need to be small, complete, cohesive, and _available_ for integration. Keep change sets small so that they can be completed and tested in a relatively short time span.
  * **Don't break the build.** Test your changes by using a private build before making your changes available.
  * **Fix broken builds immediately.** When a problem is identified, fix it as soon as possible, while it is still fresh in your mind. If the problem cannot be quickly resolved, back out \(do not complete\) the changes.

####  Integration practices

A build is more than a compile \(compilation\). A build consists of compilation, testing, inspection, and deployment.
  * **Provide feedback** as quickly as possible.
  * **Automate the build process** so that it is fast and repeatable and so that issues are identified and conveyed to the appropriate person for resolution as quickly as possible.

####  Automation
  * Commit your test scripts to the CM repository so they are controlled and available to the rest of the team. Automated testing is highly recommended, both for developer tests and integration tests. Tests need to be repeatable and fast.
  * Commit your build scripts to the CM repository so they are controlled and available to the rest of the team. Automated builds are highly recommended, both for private builds and integration builds. Builds need to be repeatable and fast.
  * Invest in a CI server.The goal of continuous integration is to integrate, build, and test the software in a clean environment any time that there is a change to the implementation. Although a dedicated CI server is not essential, it will greatly reduce the overhead required to integrate continuously and provide the required reporting.

###  Common pitfalls
  * **A build process that doesn't identify problems.** A build is more that a simple compilation \(or its dynamic language variations\). Sound testing and inspection practices, both developer testing and integration testing, must be adopted also to ensure the right amount of coverage.
  * **Integration builds that take too long to complete.** The build process must balance coverage with speed. You don't have to run every system level acceptance test to meet the intent of CI. Staged builds will provide a useful means to organize testing to get the balance coverage and speed.
  * **Change sets that are too large.** Developers must develop the discipline and skills to organize their work into small, cohesive change sets. This will simplify testing, debugging, and reporting. It will also ensure that changes are made available frequently enough to meet the intention of continuous integration.
  * **Failure to commit defects to the CM repository.** Ensure adequate testing by developers before making change sets available.
---

More Information

Concepts|
  * [Change Set](../../../../core/common/guidances/concepts/change-set.md)
---|---

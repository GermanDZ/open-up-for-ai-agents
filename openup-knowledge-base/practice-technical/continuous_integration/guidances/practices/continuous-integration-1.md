---
title: Continuous Integration
source_url: practice.tech.continuous_integration.base/guidances/practices/continous_integration_58673D65.html
type: Practice
uma_name: continous_integration
page_guid: _rJNiMB4rEd2bS8fFOQ7WWA
keywords:
- continuous
- integration
related:
  other:
  - how-to-adopt-the-continuous-integration-practice
  concepts:
  - change-requests
  - change-set
  - workspace
  workproducts:
  - build
  tasks:
  - integrate-and-create-build-1
  guidelines:
  - continuous-integration
  - promoting-changes
---


 In a Continuous Integration practice, team members integrate their work frequently \(at least daily\).
---

Relationships

Content References|
  * [How to adopt the Continuous Integration practice](../roadmaps/how-to-adopt-the-continuous-integration-practice.md)
  * Key Concepts
    * [Change Requests](../concepts/change-requests.md)
    * [Change Set](../../../../core/common/guidances/concepts/change-set.md)
    * [Workspace](../concepts/workspace.md)
  * [Build](../../../../core/common/workproducts/build.md)
  * [Integrate and Create Build](../../tasks/integrate-and-create-build-1.md)
  * [Continuous Integration](../guidelines/continuous-integration.md)
  * [Promoting Changes](../guidelines/promoting-changes.md)
---|---
Inputs|
  * [\[Technical Implementation\]](./../../../core.tech.slot.base/workproducts/technical_implementation_slot_E92F6A39.html)



Purpose

The effort required to integrate a system increases exponentially with time. By integrating the system more frequently, integration issues are identified earlier, when they are easier to fix, and the overall integration effort is reduced. The result is a higher-quality product and more predictable delivery schedules.  Continuous integration provides the following benefits:
  * **Improved feedback.** Continuous integration shows constant and demonstrable progress.
  * **Improved error detection.** Continuous integration enables you to detect and address errors early, often minutes after they've been injected into the product. Effective continuous integration requires automated unit testing with appropriate code coverage.
  * **Improved collaboration.** Continuous integration enables team members to work together safely. They know that they can make a change to their code, integrate the system, and determine very quickly whether or not their change conflicts with others.
  * **Improved system integration.** By integrating continuously throughout your project, you know that you can actually build the system, thereby mitigating integration surprises at the end of the lifecycle.
  * **Reduced number of parallel changes** that need to be merged and tested.
  * **Reduced number of errors** found during system testing. All conflicts are resolved before making new change sets available and by the person who is in the best position to resolve them.
  * **Reduced technical risk.** You always have an up-to-date system to test against.
  * **Reduced management risk.** By continuously integrating your system, you know exactly how much functionality that you have built to date, thereby improving your ability to predict when and if you are actually going to be able to deliver the necessary functionality.
---

Main Description

###  The essence of continuous integration

The essence of continuous integration can be described by the following activities:
  * Developers make small changes to the latest integration-tested implementation in their workspaces, and they unit test them before making the changes available to the team.
  * Change sets from all developers are integrated in an integration workspace and tested frequently \(at least daily-- ideally any time a new change set is available\).

The first activity ensures that changes are made to a configuration that is known to be good and tested before making the changes available. The second activity identifies integration issues early so that they can be corrected while the change is still fresh in the developer's mind.
---

How to read this practice

The best way to read this practice is to first familiarize yourself with its overall structure: what is in it and how it is organized. Then begin by reviewing the key concepts to understand the terminology. Next, review the [Integrate and Create Build](../../tasks/integrate-and-create-build-1.md) task [Integrate and Create Build](../../tasks/integrate-and-create-build-1.md) to learn what needs to be done. Finally, review the associated guidelines for more information on the overall workflow.  For step-by-step instructions on how to adopt this practice, see [How to adopt the Continuous Integration practice](../roadmaps/how-to-adopt-the-continuous-integration-practice.md).
---

Additional Information

###  Books and articles


|  Martin Fowler. "Continuous Integration," [www.martinfowler.com/articles/continuousIntegration.html](http://www.martinfowler.com/articles/continuousIntegration.html) \(2006\).
---
|  Seminal paper on continuous integration. Great overview of the benefits and practices.
Paul M. Duval with Steve Matyas and Andrew Glover. _Continuous Integration: Improving Software Quality and Reducing Risk._ Addison-Wesley \(2007\).
|  Comprehensive guidance on the practice and subpractices of continuous integration \(CI\). Great overview of motivation and benefits of the practice. Detailed discussion of more than 40 CI-related subpractices, with examples of scripts and code segments. Appendix provides an overview of tools available to support the practice.

---
title: Detail Use Cases and Scenarios
source_url: practice.tech.use_case_driven_dev.base/guidances/guidelines/detail_ucs_and_scenarios_6BC56BB7.html
type: Guideline
uma_name: detail_ucs_and_scenarios
page_guid: _4BJ_YCxSEdqjsdw1QLH_6Q
keywords:
- cases
- detail
- scenarios
related:
  tasks:
  - detail-use-case-scenarios-1
---


 This guideline provides help on detailing use cases and scenarios.
---

Relationships

Related Elements|
  * [Detail Use-Case Scenarios](../../tasks/detail-use-case-scenarios-1.md)
---|---

Main Description

####  Most efficient way to write use cases

Because use cases model requirements, they are highly dynamic by nature. The more we examine a requirement, the more we learn, and the more things change. To further complicate the issue, changes to one use case can lead to changes in others. Therefore, we want a flexible, highly efficient method for writing use cases that eliminates unnecessary work and rewriting.  An iterative, breadth-first approach, in which the use case is continuously evaluated before adding detail, is an effective way to write use cases. This breadth-first approach involves two aspects: writing the set of use cases and writing individual use cases.  **Writing sets of use cases:** Use cases exist in sets, and the relationships between the various use cases and Actors are important. As you learn more about the Actors, you also learn more about the system's boundaries and transactions. Likewise, as you learn more about the system's transactions, you learn more about its Actors. Therefore, it is more efficient to write several use cases simultaneously than to write them sequentially. This way, you can identify and understand the effects of the various use cases upon each other as you write them, rather than as afterthoughts that require rewriting or elimination of previous work.  **Writing individual use cases.** Similarly, it makes sense to write each individual use case iteratively. Starting with the main scenario, you can then identify various alternative and error flows that the use case might follow, then evaluate, rearrange or eliminate them, and then add the details of the surviving scenarios.  Consider factors that can influence the format and level of detail for your use case description.

####  Detail the flow of events of the main scenario

As a starting point, use the step-by-step description of the use-case main scenario. Then, gradually add details to this scenario, describing **what** the use case does, **not how** to solve problems internal to the system.  A flow of events description explores:
  * How and when the use case starts
  * When the use case interacts with the Actors, and what data they exchange
  * When the use case uses data stored in the system or stores data in the system
  * How and when the use case ends

It does not describe:
  * The GUI
  * Technical details of hardware or software
  * Design issues

####  Identify alternate flows

A use case consists of a number of scenarios, each representing specific instances of the use case that correspond to specific inputs from the Actor or to specific conditions in the environment. Each scenario describes alternate ways that the system provides a behavior, or it can describe failure or exception cases.  As you detail the main scenario, identify alternate flows by asking these questions:
  * Are there different options available, depending on input from the Actor? \(for example, if the Actor enters an invalid PIN number while accessing an ATM\)
  * What business rules can come into play? \(For instance, the Actor requests more money from the ATM than is available in her account\)
  * What could go wrong? \(Such as no network connection available when required to perform a transaction\)

It is best to develop these scenarios iteratively, as well. Begin by identifying them. Examine each possible scenario to determine whether it is relevant, that it can actually happen, and that it is distinct from other scenarios. Eliminate redundant or unnecessary scenarios, and then start elaborating on the more important ones.

####  Structure the use case

It is useful to structure the use case according to scenarios. This helps both to simplify communication and maintenance and to permit the use cases to be implemented iteratively.  In addition to structuring the use cases according to scenarios, it is often useful to structure the scenarios themselves into sub-flows. This provides an additional level of granularity for planning work and tracking progress. Unless a sub-flow involves only a minor part of the complete flow of events \(which can be described in the body of the text\), it is recommended that you describe each sub-flow in a separate section to the Flow of Events section. Sub-flows that need to be in a separate section include these examples:
  * Sub-flows that occupy a large segment of a given flow of events.
  * Exceptional and alternate flows of events. This helps the use case's basic flow of events to stand out more clearly.
  * Any sub-flow that can be executed at several intervals in the same flow of events.

####  Describe special requirements

You must also capture any requirements that are related to the use case, but are not taken into consideration in the flow of events of the use case. Such requirements are likely to be nonfunctional.  Typically, nonfunctional requirements that refer to a specific use case are captured in the special requirements section of the use case. If there are nonfunctional requirements that apply to more than one use case, capture these in the system-wide requirements specification.

####  Describe preconditions and postconditions

A **precondition** on a use case explains the state that the system must be in for the use case to be able to start. Be careful in describing the system state. Avoid describing the detail of other, incidental activities that might already have taken place.  A **postcondition** on a use case lists possible states that the system can be in at the end of the use case execution. The system must be in one of those states. A postcondition also states actions that the system performs at the end of the use case, regardless of what occurred in the use case. Post-Conditions can be categorized as Minimal Guarantees or Success Guarantees. A Minimal Guarantee represents a condition that will be true when the use case ends, regardless of how it terminates. A Success Guarantee represents a condition that will be true when the use case ends successfully, regardless of which path it took.  Neither preconditions nor postconditions need to be used to create a sequence of use cases. As a general rule, there must never be a case where you have to first perform one use case and then another to have a meaningful flow of events. If that is the case, correct the problem by reviewing the use cases.
---

More Information

Concepts|
  * [Use Case](../../../../core/common/guidances/concepts/use-case-2.md)
---|---

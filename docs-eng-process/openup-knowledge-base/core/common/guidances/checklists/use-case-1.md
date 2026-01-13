---
title: Use Case
source_url: core.tech.common.extend_supp/guidances/checklists/use_case_C5362874.html
type: Checklist
uma_name: use_case
page_guid: _0kNwINk1Edq2Q8qZoWbvGA
keywords:
- case
related:
  workproducts:
  - use-case
---


 This checklist provides questions to verify that use cases are described in a consistent and complete manner.
---

Relationships

Related Elements|
  * [Use Case](../../workproducts/use-case.md)
---|---

Check Items

The use-case name is meaningful and un-ambiguous |  Does the use case have a unique name?  Is the name a verb + noun phrase \(for example, Withdraw Cash\)?  Does the name accurately summarize the main goal of the use case?  Is the name "actor independent"?
---

The brief description clearly describes the primary goal of the use case

Is it clear from the brief description what the main purpose of the use case is?  Is the "observable result of value" obvious?
---

Associated actors and information exchanged are clearly defined

Is the use case associated with one or more actors?  Is the primary, or initiating actor, defined?  Is it clear who wishes to perform the use case?  Is all information exchanged between the actor\(s\) and the system clearly specified?  If a "time" actor is used, are you sure you did not miss an important actor and associated use cases \(such as administrative or maintenance personnel that define schedule events\)?
---

Pre-conditions have been specified

Does each pre-condition represent a tangible state of the system \(for example, the Withdraw Cash use case for an automated teller machine has a precondition that the user has an account\)?
---

The Basic Flow and Alternate Flows are complete, correct and consistent

Is it clear how the use case is started?  Is the triggering event clearly described?  Does the flow have a definite ending?  Does each step in the scenario contain the same level of abstraction?  Does each step in the scenario describe something that can actually happen and that the system can reasonably detect?  Does each step make progress towards the goal?  Are there any missing steps? Is it clear how to go from one step to the next? Does the sequence of communication between the actors and the use case conform to the user's expectations?  Does each step describe how the step helps the actor achieve their goal?  Is each step technology independent? Is it free of technical details, and design decisions?  Are the steps correctly numbered?  For each alternate flow is the condition\(s\) for initiation of the flow clearly defined?  For each alternate flow is it clear how the use case ends or where in the basic flow that the use case resumes?
---

Post-conditions have been specified

If "Minimal Guarantees" are present, do they always happen when the use case completes, regardless of success? \(A Minimal Guarantee represents a condition that will be true when the use case ends, regardless of how it terminates.\)  If "Success Guarantees" are present, do they always happen when the use case completes successfully? \(A Success Guarantee represents a condition that will be true when the use case ends successfully, regardless of which path it takes.\)
---

Applicable non-functional requirements have been captured

Are non-functional requirements \(such as performance criteria\) that are applicable to the use case captured in the use case?  Are these non-functional requirements applicable to many use cases? It they are, consider capturing them in the system-wide requirements specification to simplify maintenance.
---

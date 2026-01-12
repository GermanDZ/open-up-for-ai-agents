---
title: Identify and Outline Actors and Use Cases
source_url: practice.tech.use_case_driven_dev.base/guidances/guidelines/identify_and_outline_actors_and_ucs_BB5516A9.html
type: Guideline
uma_name: identify_and_outline_actors_and_ucs
page_guid: _eyL0wCu-EdqSxKAVa9kmvA
keywords:
- actors
- cases
- identify
- outline
related:
  tasks:
  - identify-and-outline-requirements-1
---


 This guideline describes how to find and outline actors and use cases.
---

Relationships

Related Elements|
  * [Identify and Outline Requirements](../../tasks/identify-and-outline-requirements-1.md)
---|---

Main Description

####  Identifying actors

Find the external entities with which the system under development must interact. Candidates include groups of users who will require help from the system to perform their tasks and run the system's primary or secondary functions, as well as external hardware, software, and other systems.  Define each candidate actor by naming it and writing a brief description. Includes the actor's area of responsibility and the goals that the actor will attempt to accomplish when using the system. Eliminate actor candidates who do not have any goals.  These questions are useful in identifying actors:
  * Who will supply, use, or remove information from the system?
  * Who will use the system?
  * Who is interested in a certain feature or service provided by the system?
  * Who will support and maintain the system?
  * What are the system's external resources?
  * What other systems will need to interact with the system under development?

Review the list of stakeholders that you captured in the Vision statement. Not all stakeholders will be actors \(meaning, they will not all interact directly with the system under development\), but this list of stakeholders is useful for identifying candidates for actors.

####  Identifying use cases

The best way to find use cases is to consider what each actor requires of the system. For each actor, human or not, ask:
  * What are the goals that the actor will attempt to accomplish with the system?
  * What are the primary tasks that the actor wants the system to perform?
  * Will the actor create, store, change, remove, or read data in the system?
  * Will the actor need to inform the system about sudden external changes?
  * Does the actor need to be informed about certain occurrences, such as unavailability of a network resource, in the system?
  * Will the actor perform a system startup or shutdown?

Understanding how the target organization works and how this information system might be incorporated into existing operations gives an idea of system's surroundings. That information can reveal other use case candidates.  Give a unique name and brief description that clearly describes the goals for each use case. If the candidate use case does not have goals, ask yourself why it exists, and then either identify a goal or eliminate the use case.

####  Outlining Use Cases

Without going into details, write a first draft of the flow of events of the use cases identified as being of high priority. Initially, write a simple step-by-step description of the basic flow of the use case. The step-by-step description is a simple ordered list of interactions between the actor and the system. For example, the description of the basic flow of the Withdraw Cash use case of an automated teller machine \(ATM\) would be something like this:

  1. The customer inserts a bank card.
  2. The system validates the card and prompts the person to enter a personal identification number \(PIN\).
  3. The customer enters a PIN.
  4. The system validates the PIN and prompts the customer to select an action.
  5. The customer selects Withdraw Cash.
  6. The system prompts the customer to choose which account.
  7. The customer selects the checking account.
  8. The system prompts for an amount.
  9. The customer enters the amount to withdraw.
  10. The system validates the amount \(assuming sufficient funds\), and then issues cash and receipt.
  11. The customer takes the cash and receipt, and then retrieves the bank card.
  12. The use case ends.

As you create this step-by-step description of the basic flow of events, you can discover alternative and exceptional flows. For example, what happens if the customer enters an invalid PIN? Record the name and a brief description of each alternate flow that you identified.

####  Representing relationships between actors and use cases

The relationship between actors and use cases can be captured, or documented. There are several ways to do this. If you are using a use-case model on the project, you can create use-case diagrams to show how actors and use cases relate to each other. Refer to [Guideline: Use-Case Model](use-case-model-9.md) for more information.  If you are not using a use-case model for the project, make sure that each use case identifies the associated primary and secondary actors.
---

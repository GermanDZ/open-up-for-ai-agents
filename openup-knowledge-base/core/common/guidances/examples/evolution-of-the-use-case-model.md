---
title: Evolution of the Use-Case Model
source_url: core.tech.common.extend_supp/guidances/examples/uc_model_evolve_960F136B.html
type: Example
uma_name: uc_model_evolve
page_guid: _t4QdAMNqEdu2IdAIaWZyAw
keywords:
- case
- evolution
- minimize
- model
related:
  workproducts:
  - use-case-model
  other:
  - use-case-specification
---


 This example illustrates how the use-case model evolves over time when you use a "breadth before depth" approach to maximize value and minimize risk early in the lifecycle and to minimize re-work later.
---

Relationships

Related Elements|
  * [Use-Case Model](../../workproducts/use-case-model.md)
  * [Use-Case Specification](use-case-specification.md)
---|---

Main Description

###  Introduction

This example illustrates how the use-case model and associated use-case specification will evolve during the lifecycle. It shows the state of the use case model at two points in the lifecycle: early inception and towards the end of elaboration. The purpose is to illustrate how one would identify, outline and detail requirements so as to maximize stakeholder value and minimize risk early in the project, as well as to minimize re-work later.  The example uses an Automated Teller Machine as the example system, because it is familiar to most people. This familiarity simplifies understanding the principles without getting lost in domain specific terminology.

####  Early inception

Assume you have just started on the project as the Analyst. You have identified the key stakeholders and met with them to discuss their needs. During your meetings, you identified a number of key actors, use cases, and supporting requirements for the ATM system. You captured the use cases and actors, with names and brief descriptions only, in the use-case model. An example of this work is given in the document **ATM UC Model Inception**.  Prior to committing significant time to detailing these use cases now, you recognize that a "breadth before depth" approach can save you valuable time and permit you to identify the highest value and highest risk items so that you can concentrate on those first.  You hold a brainstorming session with the stakeholders and outline the basic flow of each of the main use cases. As you are working through, you may identify some additional alternative flows. Fight the urge to "dive-in" to the details on these alternative flows at this point, simply list them and come back later when you have a better understanding of the "big picture".  Examples of the notes you took during this exercise are attached \(**Withdraw Cash Outline** , **Deposit Funds Outline** and **Transfer** **Funds Outline**\).
**Note:** the choice of font is intentional to illustrate that these are notes, not formal documents.  Reviewing your notes, you recognize that there is some behavior that is common to most of the use cases, namely the steps required to validate the Bank Customer. Factoring this behavior out into an <<included>> use case will simplify communications, iteration planning, and maintenance.  You update the use case model accordingly: **ATM UC Model Elaboration**.

####  Elaboration

With a better understanding of the system, you can now prioritize your effort to maximize value and minimize risk. You start by detailing the common behavior captured in the use case: Validate User. This use case captures key architectural requirements that will exercise a significant portion of the system \(communications with the Bank, card reader interface, and so on\). Implementing this one key scenario will go a long way to reducing risk.  An example of the Validate User use-case specification is attached: **Use Case Spec - Validate User.** Note that there may still be some un-answered questions, but that's OK. Capture these directly in the use-case specification and get them answered \(see Section 5.6 of the **Validate User UC Specification** , for an example\).  Continuing with another architecturally significant thread, you detail the basic flow and some key alternative flows of the use case: Withdraw Cash. You know that if the team can implement this, much of the other functionality will be low risk.  An example of the Withdraw Cash use-case specification is attached: **Use Case Spec - Withdraw Cash**.

###  Summary

By following a breadth before depth approach to outlining and detailing use cases, you can make better decisions on priorities. Start by identifying actors. Then for each actor, ask "What is the main purpose this actor would like to use the system?". This will lead to the identification of the use cases. Capture the actors and use cases in the use-case model along with a brief description.  Prioritize the use cases, and then draft the main scenario or basic flow. As you are working through this you may identify alternate flows \(what can go wrong, what options are available, and so on\). Capture these, along with a brief description.  Review the use-case model and reprioritize and assess risk. For the high priority \(based on value to the stakeholders\) or high risk use cases, detail the main scenario and the critical alternate flows.  If you follow this approach, you will increase the likelihood of delivering value early, minimizing risk, and minimizing re-work.
---

More Information

Examples|
  * [Use Case - Deposit Funds Outline](use-case-deposit-funds-outline.md)
  * [Use Case - Model Elaboration Phase](use-case-model-elaboration-phase.md)
  * [Use Case - Model Inception Phase](use-case-model-inception-phase.md)
  * [Use Case - Specification Validate User](use-case-specification-validate-user.md)
  * [Use Case - Transfer Funds Outline](use-case-transfer-funds-outline.md)
  * [Use Case - Withdraw Cash Outline](use-case-withdraw-cash-outline.md)
---|---

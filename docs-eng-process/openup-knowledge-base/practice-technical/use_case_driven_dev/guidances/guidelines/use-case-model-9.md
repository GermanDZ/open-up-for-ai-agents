---
title: Use-Case Model
source_url: practice.tech.use_case_driven_dev.base/guidances/guidelines/use_case_model_4C64E97D.html
type: Guideline
uma_name: use_case_model
page_guid: _0VAUsMlgEdmt3adZL5Dmdw
keywords:
- case
- model
---

 This guideline describes how to develop and evolve the use-case model to capture the functional requirements for the system under development.
---

Main Description

###  Introduction

The key to successful iterative development is ensuring that the development team maximizes stakeholder value and minimizes risk early in the lifecycle, while minimizing re-work later. This imposes some constraints on how we develop the use-case model.  At one extreme is the classical waterfall approach, which attempts to detail all of the requirements prior to design and implementation. This approach delays delivery of stakeholder value and risk reduction unnecessarily.  At the other extreme is beginning development prior to understanding what the system must do. This approach results in significant, and costly, re-work later in the lifecycle.  A better approach is to detail only those requirements which will be the focus of development in the next iteration \(or two\). Selection of these requirements is driven by value and risk, and thus requires as a minimum an abstract understanding of the "big-picture".  The following discussion will outline the approach used to evolve the use-case model to achieve these goals.

###  How the Use-Case Model Evolves

The recommended approach to evolving the use-case model takes a "breadth before depth" approach. In this approach, one identifies the actors and use cases and outlines them quickly. Based on this knowledge, one can then perform an initial assessment of risk and priorities and thus focus the effort of detailing the use cases on the right areas.

####  Inception

The purpose of inception is to understand the scope of the system. We need to understand the main purpose of the system, what is within the scope of the system, and what is external to the system. We must strive to list all the primary actors and use cases, however we don't have the luxury of being able to detail all of these requirements at this time. Strive to identify by name ~80% of the primary actors and use cases and provide a brief description \(one - three sentences\) for each.

> #####  Identify stakeholders
>
> Begin by listing all the external stakeholders for the system. These individuals will be the source of the requirements.
>
> #####  Identify Actors
>
> Name and describe the primary actors. See [Guideline: Identify and Outline Actors and Use Cases](identify-and-outline-actors-and-use-cases.md).
>
> #####  Identify Use Cases
>
> For each actor, ask "what does this actor want to accomplish with the system"? This will reveal the primary use cases for the system. Name and describe each of these as you discover them.
>
> #####  Update the Use-Case Model
>
> Update the use case model to capture the actor and use case names and brief description. Capture the relationship between the actors and use cases.
>
> #####  Outline the Basic Flows
>
> For those use cases that are considered high priority by the stakeholders, or high risk by the development team, capture a step-by-step description of the Basic Flow. Don't worry about structuring the flow at this point. Focus on capturing the dialogue between the actor and the system and the key requirements for the system.
>
> #####  Identify Alternate Flows
>
> As you work through the Basic Flows, ask: "What can go wrong?"; "What options are available at this point?"; etc. These types of questions will reveal alternate flows. Capture these, giving each a name and brief description. Fight the urge to detail these alternate flows at this time.
>
> #####  Refactor the Use Case Model
>
> Based on the Basic Flows you have identified, determine if there is common behavior that could be factored out into <<include>> use cases. Refactor the Use Case model accordingly.
>
> #####  Prioritize Use Cases
>
> Given the abstract description you now have of the requirements, work with stakeholders to prioritize the use cases. This will be the primary input to iteration planning.

####  Elaboration

> The purpose of elaboration is to demonstrate the feasibility of the solution prior to committing additional resources. To be successful, one must demonstrate that stakeholder value can be delivered and that the risk of continuing is acceptable. We must strive to detail and implement ~20% of the scenarios. These scenarios must be selected to achieve good coverage of the architecture \(for example, a vertical slice through the architecture, touching as many components and interfaces as possible, is preferred to elaborating the GUI only\).
>
> #####  Detail Basic Flow
>
> For those UC selected for the next iteration, spend the time to detail the basic flow now. See [Guideline: Detail Use Cases and Scenarios](detail-use-cases-and-scenarios.md).
>
> #####  Detail Alternate Flow
>
> For those alternate flows selected for the next iteration, spend the time to detail the flows now.
>
> #####  Update the Use-Case Model
>
> Update the Use-Case Model to capture any refinements made as a result of your work. Depending upon the complexity of the system, you might want to introduce packages to group the use cases in a logical manner to simplify communications, iteration planning, and parallel development.

####  Construction

> The purpose of construction is to incrementally deliver functionality \(and value\). Working from the iteration plan, continue detailing the remaining requirements. Shoot for completion of ~90 - ~95% of use cases by the end of construction.
>
> #####  Detail Basic Flows
>
> For those UC selected for the next iteration, spend the time to detail the basic flow now. See [Guideline: Detail Use Cases and Scenarios](detail-use-cases-and-scenarios.md).
>
> #####  Detail Alternate Flows
>
> For those alternate flows selected for the next iteration, spend the time to detail the flows now.
>
> #####  Update the Use-Case Model
>
> Update the Use-Case Model to capture any refinements made as a result of your work.

####  Transition

The purpose of transition is to make the system operational in its intended environment. Some requirements will not be covered at this point. But the requirements must clearly not stress the design. The remaining ~5% to ~10% of use cases must be detailed and implemented in this phase.

###  Avoiding Functional Decomposition

A common pitfall for those new to use-case models is to perform a functional decomposition of the system. This results in many small "use cases", that on their own do not deliver the "observable result of value" to the actor. To avoid this, watch for the following symptoms:
  * **Small** use cases, meaning that the description of the flow of events is only one or a few sentences.
  * **Many** use cases, meaning that the number of use cases is some multiple of a hundred, rather than a multiple of ten.
  * Use-case names that are constructions such as "do this operation on this particular data" or "do this function with this particular data". For example, "Enter Personal Identification Number in an ATM machine" must not be modeled as a separate use case for the ATM machine, because no one would use the system to do just this. A use case is a complete flow of events that results in something of value to an actor.

To avoid functional decomposition, make sure that the use-case model helps answer these kinds of questions:
  * What is the context of the system?
  * Why are you building this system?
  * What does the user want the system to do?
  * How do the users benefit from the system?

###  Structuring the Use-Case Model

There are three main reasons for structuring the use-case model:
  * To make the use cases easier to understand.
  * To partition common behavior described within many use cases.
  * To make the use-case model easier to maintain.

Structuring is not the first thing you do, however. There is no point in structuring the use cases until you know a bit more about their behavior than a one-sentence description. Establishing a step-by-step outline of the flow of events can assure your decisions are based on an accurate understanding of the behavior  There are several advanced modeling concepts available in the literature for structuring the use-case model, however, following the principle of "keep-it-simple" only the most useful of these, namely the <<include>> relationship is discussed in this process. This relationship permits one to factor out common behavior into a separate use case that is "include" in other use cases. See [Concept: Use-Case Model](../../../../core/common/guidances/concepts/use-case-model-2.md) for more details.  Another aspect of structuring the use-case model for easier understanding is grouping the use cases into packages. The use-case model can be organized as a hierarchy of use-case packages. For more information on use-case packages, see [Concept: Use-Case Model](../../../../core/common/guidances/concepts/use-case-model-2.md).

###  Relationship Between Use Cases and Actors

Running each use case includes communication with one or more actors. A use-case instance is always started by an actor asking the system to do something. This implies that every use case must have communicates-associations with actors. The reason for this rule is to enforce that the system provides only the functionality that users need and nothing else. Having use cases that no one requests is an indication that something is wrong in the use-case model or in the requirements.  However, there are some exceptions to this rule:
  * An "included" use case might not interact with an actor if the base use case does.
  * A use case can be initiated according to a schedule \(for example, once a week or once a day\), which means that the system clock is the initiator. The system clock is internal to the system; therefore, the use case is not initiated by an actor but by an internal system event. If no other actor interaction occurs in the use case, it will not have any associations to actors. However, for clarity, you can use "time" as an actor to show how the use case is initiated in your use-case diagrams. **CAUTION:** if you have a lot of "time" actors in your model, challenge them. Perhaps you missed a real actor, such as an administrator responsible for scheduling reports, etc.
---

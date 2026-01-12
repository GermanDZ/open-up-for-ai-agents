---
title: Developing System-Wide Requirements Specification
source_url: practice.tech.use_case_driven_dev.base/guidances/guidelines/system_wide_requirements_8ED0BB6B.html
type: Guideline
uma_name: system_wide_requirements
page_guid: _wr24gNcGEdqz_d2XWoVt6Q
keywords:
- developing
- requirements
- specification
- system
- wide
related:
  tasks:
  - detail-system-wide-requirements-1
  - identify-and-outline-requirements-1
---


 This guideline explains how to develop and use the system-wide requirements specification.
---

Relationships

Related Elements|
  * [Detail System-Wide Requirements](../../tasks/detail-system-wide-requirements-1.md)
  * [Identify and Outline Requirements](../../tasks/identify-and-outline-requirements-1.md)
---|---

Main Description

There is a finite set of requirements to consider when it comes to gathering system-wide requirements, qualities, or constraints. Many of them are unfamiliar to stakeholders; therefore, they might find it difficult to answer questions related to topics such as availability, performance, scalability, or localization. You can use this guideline and the associated checklist [Checklist: System-Wide Requirements \(FURPS+\)](../../../../core/common/guidances/checklists/system-wide-requirements-furps.md) when speaking to stakeholders to ensure that all topics are discussed. Make sure that stakeholders understand the costs of their selections and do not end up wanting everything that is on the list.

###  Functional
  * **Auditing:** Is there a need to track who used the system and when they used it? State requirements for providing audit trails when running the system.
  * **Authentication:** Will access to the system be controlled? State requirements for authentication.
  * **Licensing:** Will the system or parts of the system be licensed? If open-source software has been used in the system, have all open-source agreements been respected? State requirements for acquiring, installing, tracking, and monitoring licenses.
  * **Printing:** Will printing capability be required? State requirements for printing.
  * **Reporting:** Is reporting capability required? State requirements for reporting.
  * **Scheduling:** Will certain system actions need to be scheduled? State requirements for scheduling capability.
  * **Security:** Will elements of the system or system data need to be secure? State requirements to protect access to certain resources or information.

###  Usability

Usability requirements are critical to the success of any system. Unfortunately, usability requirements are often the most poorly specified requirements. Consider this common requirement: The system shall be easy to use. This doesn't help much, because it cannot be verified.  While capturing usability requirements, it is a good idea to identify issues and concerns first, and then refine these into verifiable requirements later \(see [Guideline: Writing Requirements Statements](../../../../core/common/guidances/guidelines/writing-requirements-statements.md)\). According to a traditional definition, usability consists of five factors:
  * **Ease of learning:** A user with a specified level of experience must be able to learn how to use the system in a specified amount of time.
  * **Task efficiency:** A user must be able to complete a specified task in a specified time \(or number of mouse clicks\).
  * **Ease of remembering:** A user must be able to remember how to accomplish specified tasks after not using the system for a specified period of time.
  * **Understandability:** A user must be able to understand system prompts and messages and what the system does.
  * **Subjective satisfaction:** A specified percentage of the user community must express satisfaction with using the system.

You might want to use the following method to identify and specify usability requirements:

  1. Identify the key usability issues by looking at critical tasks, user profiles, system goals, and previous usability problems.
  2. Choose the appropriate style to express the requirements:
     * **Performance style:** Specify how fast users can learn various tasks and how fast they can perform the tasks after training.
     * **Defect style:** Rather than measuring task times, identify usability defects and specifies how frequently they can occur.
     * **Guideline style:** Specify the general appearance and response time of the user interface by reference to an accepted and well-defined standard
  3. Write the actual requirements, including performance criteria \(see [Guideline: Writing Requirements Statements](../../../../core/common/guidances/guidelines/writing-requirements-statements.md) for more information\).

###  Reliability

Reliability includes the system's ability to continue running under stress and adverse conditions. In the case of an application, reliability relates to the amount of time that the software is available and running as opposed to time unavailable. Specify reliability acceptance levels, as well as how they will be measured and evaluated. Describe reliability criteria in measurable terms. This is usually expressed as the allowable time between failures or the total allowable failure rate. Other important reliability considerations include:
  * **Accuracy:** Specify requirements for the precision \(resolution\) and the accuracy \(by some known standard\) that is required in any calculation performed or in system output.
  * **Availability:** Specify requirements for the percentage of time the system is available for use, hours of use, maintenance access, and degraded-mode operations. Availability is typically specified in terms of the Mean Time Between Failures \(MTBF\).
  * **Recoverability:** Specify requirements for recovery from failure. This is typically specified in terms of the Mean Time to Repair \(MTTR\).
  * **Frequency and severity of failures:** Specify the maximum defect rate \(typically expressed as defects/KSLOC or defects/function-point\) and severity of failures. Severity can be categorized in terms of **minor** , **significant** , and **critical** defects. The requirements must define each of these terms unambiguously. For example, a **critical** defect could be defined as one that results in loss of data or complete inability to use certain functionality of the system.

###  Performance
  * **Response times:** Specify the amount of time available for the system to complete specified tasks and transactions \(average, maximum\). Use units of measurement. _Examples:_
    * Any interface between a user and the system shall have a maximum response time of 2 seconds.
    * The product shall download the new status parameters within 5 minutes of a change.
  * **Throughput:** Specify the capacity of the system to support a given flow of information \(for example, transactions per second\).
  * **Capacity:** Specify on the volumes that the product must be able to deal with and the numbers of data stored by the product. Make sure that the requirement description is quantified, and thus can be tested. Use unit of measurement such as: the number of customers or transactions the system can accommodate, resource usage \(memory, disk, . . . \), or degradation modes \(what is the acceptable mode of operation when the system has been degraded in some manner\) _Examples:_
    * The product shall cater for 300 simultaneous users within the period from 9:00 AM to 11 AM.
    * Maximum loading at other periods will be 150.
  * **Start-up:** The time for the system to start up.
  * **Shut-down:** The time for the system to shut down.

###  Supportability
  * **Adaptability:** Are there any special requirements regarding adaptation of the software \(including upgrading\)? List requirements for the ease with which the system is adapted to new environments.
  * **Compatibility:** Are there any requirements regarding this system and its compatibility with previous versions of this system or legacy systems that provide the same capability?
  * **Configurability:** Will the product be configured after it has been deployed? In what way will the system be configured?
  * **Installation:** State any special requirements regarding system installation
  * **Level of Support:** What is the level of support that the product requires? This is often performed using a Help desk. If there are to be people who provide support for the product, is that support considered part of what you are providing to the customer? Are there any requirements for that support? You might also build support into the product itself, in which case this is the place to write those requirements. Consider the level of support that you anticipate providing and what forms it might take.
  * **Maintainability:** Are there any special requirements regarding system maintenance? What are the requirements for the intended release cycle for the product and the form that the release will take? Quantify the time necessary to make specified changes to the product. There can also be special requirements for maintainability, such as a requirement that the product must be able to be maintained by its end-users or developers who are not your development team. This has an effect on the way that the product is developed, and there can be additional requirements for documentation or training. Describe the type of maintenance and the amount of effort required. _Examples:_
  *     * A new weather station must be able to be added to the system overnight.
    * The maintenance releases will be offered to end-users once a year.
  * **Scalability:** What volumes of users and data will the system support? This specifies the expected increases in size that the product must be able to handle As businesses grow \(or are expected to grow\), the software products must increase their capacities to cope with the new volumes. This can be expressed as a profile over time.
  * **Testability:** Are there any special requirements regarding the testability of the system?

###  Constraints \(+\)
  * **Design constraints:** Are there any design decisions that have been mandated that the product must adhered to?
  * **Third-party components:** Specify any mandated legacy, COTS, or open-source components to be used with the system.
  * **Implementation languages:** Specify requirements on the implementation languages to be used
  * **Platform support:** Specify requirements on the platforms that the system will support
  * **Resource limits:** Specify requirements on the use of system resources, such as memory and hard disk space
  * **Physical Constraints:** Specify requirements on the shape, size, and weight of the resulting hardware to house the system

###  Interface Requirements \(+\)

Describe both the user interface and interfaces with external systems.

####  User interface

Describe requirements related to user interfaces that are to be implemented by the software. The intention of this section is to state the requirements, but not to describe the user interface itself, because interface design can overlap the requirements-gathering process. This is particularly true if you are using prototyping as part of your requirements gathering process. As you develop prototypes, it is important to capture the requirements that relate to the look and feel of the user interface. In other words, be sure that you understand your client's intentions for the product's look and feel. Record these as requirements, rather than merely using a prototype for approval.
  * **Look and feel:** A description of the aesthetic appearance and layout of the interface. Your client might have given you particular demands, such as style, colors, degree of interaction, and so on. This section captures the requirements for the interface, rather than the design for the interface. The motivation is to capture the expectations, the constraints, and the client's demands for the interface before designing it. _Examples:_
    * The product shall have the same layout as the district maps from the engineering department.
    * The product shall use the company color.
  * **Layout and navigation requirements:** Specify requirements on major screen areas and how they must be grouped together.
  * **Consistency:** Consistency in the user interface enables users to predict what will happen. This section states requirements on the use of mechanisms to be employed in the user interface. This applies both within the system, and with other systems and can be applied at different levels: navigation controls, screen areas sizes and shapes, placements for entering / presenting data, terminology
  * **User personalization and customization requirements:** Requirements on content that must automatically displayed to users or available based on user attributes. Sometimes users allowed to customize the content displayed or to personalize displayed content.

####  Interfaces to external systems or devices
  * **Software interfaces:** Are there any external systems with which this system must interface? Are there any constraints on the nature of the interface between this system and any external system, such as the format of data passed between these systems? Do they use any particular protocol? Describe software interfaces with other components. These can be purchased components, components reused from another application, or components being developed for subsystems outside of the scope of the system under consideration, but with which this it must interact. For each system, consider both provided and required interfaces.
  * **Hardware interfaces:** Define any hardware interfaces that are to be supported by the software, including logical structure, physical addresses, expected behavior, and so on.
  * **Communications interfaces:** Describe any communications interfaces to other systems or devices, such as local area networks \(LANs\), remote serial devices, and so on.

###  Business Rules \(+\)

Besides technical requirements, also consider the particular business domain in which the system needs to fit.  Business rules or policies that the system must conform to can constrain system functionality. Business rules are referred to by system use cases and can be in the form of decision tables, computation rules, decision trees, algorithms, and so forth. Describing the rules in the flows of the use cases usually clutters the use-case specifications. Therefore, they are normally captured in separate artifacts or as annexes related to the use-case specifications. In many cases, a business rule applies to more then one use case. Shared business rules must be stored in a single repository or document.
---

More Information

Checklists|
  * [System-Wide Requirements \(FURPS+\)](../../../../core/common/guidances/checklists/system-wide-requirements-furps.md)
---|---

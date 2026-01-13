---
title: System-Wide Requirements
source_url: core.tech.common.extend_supp/guidances/concepts/system_wide_requirements_B2C4D610.html
type: Concept
uma_name: system_wide_requirements
page_guid: _VXZ5wO0IEdqHTdbLTmC5IQ
keywords:
- requirements
- system
- wide
related:
  tasks:
  - identify-and-outline-requirements-1
---


 This concept describes the system-wide requirements.
---

Relationships

Related Elements|
  * [Identify and Outline Requirements](../../../../practice-technical/use_case_driven_dev/tasks/identify-and-outline-requirements-1.md)
---|---

Main Description

###  Definition

System-wide requirements are requirements that define necessary system quality attributes such as performance, usability and reliability, as well as global functional requirements that are not captured in behavioral requirements artifacts such as use cases.

###  System-wide Requirements Categories

System-wide requirements are categorized according to the FURPS+ model \(Functional, Usability, Reliability, Performance, Supportability + constraints\). Constraints include design, implementation, interfaces, physical constraints, and business rules. A description of each of these types of requirements follows.  System-wide requirements and use cases, together, define the requirements of the system. These requirements support the features listed in the vision statement. Each requirement should support at least one feature, and each feature should be supported by at least one requirement.  In general, **functional** requirements describe behavior and can be captured as use cases. **Non-functional** requirements are captured in a system-wide requirements specification. However, nonfunctional requirements that are closely associated with a particular use case are often captured within the use-case specification itself to simplify communication and maintenance. Similarly, there are global, or system-wide functional requirements that are often captured among the system-wide requirements for the same reasons.

####  Functional requirements

Functional requirements include all the over-arching, system-wide functional requirements that are not expressed as use cases. These functional requirements represent the main system features that are familiar within the business domain or technically oriented requirements such as auditing, licensing, localization, e-mail, online help, printing, reporting, security, system management, or workflow.

####  Usability requirements

Usability requirements include requirements based on human factors and user-interface issues such as accessibility, interface aesthetics, and consistency within the user interface.

####  Reliability requirements

Reliability requirements include aspects such as availability, accuracy, predictability, frequency of failure or recoverability of the system from shut-down failure.

####  Performance requirements

Performance requirements address concerns such as throughput of information through the system, system response time and resource usage.

####  Supportability requirements

Supportability requirements include requirements such as compatibility and the abilities to test, adapt, maintain, configure, install, scale, and localize the system.

####  \+ Constraints

The **+** of the FURPS+ acronym allows you to specify constraints, such as design, implementation, interfaces, physical constraints, and business rules:
  * **Design constraints** limit the design and state requirements on the approach that should be taken in developing the system.
  * **Implementation constraints** put limits on coding or construction \(required standards, languages, tools, or platform\)
  * **Interface constraints** are requirements to interact with external systems, describing protocols or the nature of the information that is passed across that interface.
  * **Physical constraints** affect the hardware or packaging housing the system \(shape, size, and weight\).
  * **Business rules** are policies or decisions that govern how the business operates. They may constrain the steps described in the us-case flow.
---

---
title: System-Wide Requirements (FURPS+)
source_url: core.tech.common.extend_supp/guidances/checklists/system_wide_rqmts_furps_3158BF2F.html
type: Checklist
uma_name: system_wide_rqmts_furps
page_guid: _Vael8CGMEdu3VKXZx45D3A
keywords:
- furps
- requirements
- system
- wide
related:
  guidelines:
  - developing-system-wide-requirements-specification
---


 This check list is used to verify that the different types of system-wide requirements covered by FURPS+ have been considered.
---

Relationships

Related Elements|
  * [Developing System-Wide Requirements Specification](../../../../practice-technical/use_case_driven_dev/guidances/guidelines/developing-system-wide-requirements-specification.md)
---|---

Check Items

Global functional requirements have been captured and validated |
  * Are functional requirements that affect multiple use cases identified? For example, all use cases may be subject to access control, audit trails, general responses to abnormal situations \(overflow, communication facilities, error handling and recovery and so on\).
  * For each of these requirements, are they behavioral and could be better captured in a common use case?
  * For each of these functions, is it clear how input and shared data generate output and shared data?
---

Usability requirements have been captured and validated
  * Have the efficiency and usability factors of user tasks been considered?
  * Are the requirements specified in a way that is verifiable, including metrics and target values?
  * Have novice as well as expert users been considered?
---

Reliability requirements have been captured and validated
  * Have reliability requirements been specified as measurable requirements or prioritized design goals?
  * Is error checking and recovery required?
  * Are undesired events considered and their required responses specified?
  * Are initial or special states considered \(such as cold starts or abnormal termination\)?
---

Performance requirements have been captured and validated
  * Have the resource and performance margin requirements been stated \(for example speed, response time, recovery time of various software functions\)?
---

Supportability requirements have been captured and validated
  * Are there any requirements that will enhance the supportability or maintainability of the system being built?
---

Constraints have been captured and validated
  * Are there any required standards in effect, implementation language, policies for database integrity, resource limits, operating environments, and so forth?
  * Has the use of inherited design or code or pre-selected tools been specified?
---

External interfaces have been identified
  * Is it clear how the software interacts with people, the system's hardware, other hardware, and other software?
  * Have all critical data elements that cross system boundaries been identified for those scenarios that will be implemented next?
---

Business rules have been captured and validated
  * Are the rules relevant to the use cases identified \(data validation rules, formulas, flow decisions\)?
---

Applicable standards and regulatory compliance requirements have been identified
  * Have all requirements derived from existing standard and regulations been specified?
---

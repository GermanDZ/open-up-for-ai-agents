---
title: Development Case for a Project
source_url: practice.mgmt.project_process_tailoring.base/guidances/examples/development_case_project_BA55BE59.html
type: Example
uma_name: development_case_project
page_guid: _uWZwAF3gEd-8pIBWBGuz7w
keywords:
- case
- development
- project
related:
  templates:
  - development-case-1
  workproducts:
  - project-defined-process-1
---


 This is an example of a development case for a project.
---

Relationships

Related Elements|
  * [Development Case](../templates/development-case-1.md)
  * [Project Defined Process](../../../../core/common/workproducts/project-defined-process-1.md)
---|---

Main Description

###  The XYZ Project Process

###  1\. Introduction

####  1.1 Purpose

This document describes the process followed by project XYZ.

####  1.2 Definitions, Acronyms, and Abbreviations

See the _XYZ Project Glossary_ \(XYZ-GLO\) for a comprehensive list of terms used on this project.

####  1.3 Overview

Project XYZ generally follows the _Disciplined Agile Delivery for ABC V2.0_ \(DAD-ABC\) process configuration, which is the default software development process for most projects at Company ABC.  The remainder of this development case addresses how this project deviates from the standard process. It explains how the lifecycle model, discipline workflows, work products usage, and associated roles are customized for the needs of XYZ Project.

###  2\. Lifecycle

The XYZ Project modifies the standard lifecycle described in DAD-ABC as follows:
  * Drop "Elaboration" phase and the "Lifecycle architecture" milestone, in order to follow a more evolutionary architecture approach. However, weekly project status reporting will report progress on architecture risks.

Thus the phases and milestones will be as follows:
  * Inception phase
  *     * stakeholder consensus achieved
  * Construction phase:
  *     * Sufficient functionality
  * Transition phase
  *     * Production ready

###  3\. Practices

Project XYZ follows all the practices in DAD-ABC, with the exception of "Staged Integration". The project is small enough that only a single integration stream is required, and no dedicated integrator role is required.

###  4\. Work Products

With regards to work products, the XYZ project has some deviations from DAD-ABC as listed below:
  * Formal-Internal reviews and approvals are made by the Product Manager role, as opposed to the external Project Review Authority established by the _ABC Governance Process_ \(ABC-GOV\).
  * Globalization Plan is waived: the XYZ product will be initially marketed in North America, and therefore a waiver for translation is requested.
  * Software Architecture Document is not produced; instead, we generate automated reports from our visual modeling tool.
  * Added new artifact for Storyboards, which are maintained in Rational Requirements Composer tool
  * Rational Team Concert tool is used to capture User Stories description and related work. The User Stories in Rational Team Concert are linked to the respective Storyboards in Rational Requirements Composer.

###  5\. Reports

In addition to standard metrics required by ABC-GOV, the Team Lead gathers Requirements Traceability Coverage metrics and use Rational Insight tool to generate them, as there is a need to be aware of high level system requirements that were allocated to and refined by the XYZ project team.  The team lead takes snapshots of all metrics every 2 weeks as opposed to once a month, as indicated by ABC-GOV.

###  6\. Roles

Added Course Developer role to the team - as part of the project we need to produce training material.  Team Lead on this project will be referred to as covering both the Project Manager and Architect roles.  Note: The assignment of specific individuals to particular roles or job positions is documented in the _XYZ Project Plan_ \(XYZ-PPLAN\).

###  7\. Project-Specific Guidelines and Procedures
  * _Getting started on the XYZ Development Environment_
  * _ABC Architectural Guidelines_
  * _Q Language Programming Guidelines_
  * _Requirements Management Guidelines_
  * _Configuration and Change Management Guidelines_
---

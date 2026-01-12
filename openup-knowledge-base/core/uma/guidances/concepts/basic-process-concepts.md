---
title: Basic Process Concepts
source_url: core.default.uma_concept.base/guidances/concepts/basic_process_concepts_C90EF089.html
type: Concept
uma_name: basic_process_concepts
page_guid: _FxJEkFUKEd2_rMtRMt_EMg
keywords:
- basic
- concepts
- process
related:
  other:
  - resources-for-customizing-methods
---


 All users of a process should be familiar with these basic process concepts.
---

Relationships

Related Elements|
  * [Resources for Customizing Methods](../../../tool/guidances/supportingmaterials/resources-for-customizing-methods.md)
---|---

Main Description

###  The Basic Elements

The basic elements of a process website are:
  * **Work product** : what is produced
  * **Task** : how to perform the work
  * **Role** : who performs the work
  * **Process** : used to define work breakdown and workflow
  * **Guidance** : templates, checklists, examples, guidelines, concepts, and so on.

These "basic elements" are the building blocks from which processes are composed.

###  Organizing Elements

The basic elements are organized using the following elements.

####  Practice

A practice is a documented approach to solving one or several commonly occurring problems. Practices are intended as "chunks" of process for adoption, enablement, and configuration. Practices are built from the basic elements described above.

####  Configuration

From the end-user perspective, a configuration is a selection of method content to be published. Most configurations consist of a selection of practices plus some content to tie the practices together. The published configuration is often loosely referred to as a process website.

###  Details and Examples

The following provides more detail about the basic elements and provides some examples.

####  Work product

Work products may take various shapes or forms, such as:
  * Documents, such as a Vision, or a Project Plan.
  * A model, such as a Use-Case Model or a Design Model. These can contain model elements \(sub-artifacts\) such as Design Classes, Use Cases, and Design Subsystems.
  * Databases, spreadsheets, and other information repositories.
  * Source code and executables.

Work products can be classified as "artifacts" if they are concrete things, "outcomes" if they are not concrete, and "deliverables" if they are a packaging of artifacts.

####  Role

A role defines the behavior and responsibilities of an individual, or a set of individuals working together as a team, within the context of a software engineering organization.
Note that roles are not individuals; instead, roles describe responsibilities. An individual will typically take on several roles at one time, and frequently will change roles over the duration of the project.  Some examples:
  * **Analyst -** Represents customers and end users, gathers input from stakeholders and defines requirements.
  * **Developer -** Develops a part of the system, including designing, implementing, unit testing, and integrating.

####  Task

A task is work performed by a role. It is usually defined as a series of steps that involve creating or updating one or more work products.  Some examples:
  * **Develop a vision -** Develop an overall vision for the system, including capturing the problem to be solved, the key stakeholders, the scope and boundary of the system, the system's key features, and any constraints.
  * **Plan Iteration -** Define the scope and responsibilities of a single iteration.



####  Process

Processes pull together tasks, work products, and roles, and add structure and sequencing information. Tasks or work products can be grouped into higher level activities, called a work breakdown structure \(WBS\). Activities or tasks can be marked as "planned" to identify work that you expect to assign and track.

![This is an example work breakdown structure, showing a hierarchy of activities with sub-activities and tasks.](../../../../images/wbs_example.jpg) [📄](../../../../images/descriptions/wbs_example.md "Image description")
Figure 1: Example Work Breakdown

Diagrams can be added to providing sequencing information. The following example shows an initial activity, "Plan Test Cycle", followed by two activities that go in parallel, "Monitor and Control Test" and "Test".

![Example UML activity diagram, showing a start, an initial activity, then two activities in parallel, and an end.](../../../../images/activity_diag_ex.jpg) [📄](../../../../images/descriptions/activity_diag_ex.md "Image description")
Figure 2: Example Activity Diagram

Note that a reusable partial process is sometimes referred to as a capability pattern.

###  For More Information

More in-depth material on these concepts is generally found in articles on EPF Composer and Rational\(R\) Method Composer, which use these concepts as building blocks.
  * To learn more about the Eclipse Process Framework Project and EPF Composer, visit <http://www.eclipse.org/epf> and <http://www-128.ibm.com/developerworks/rational/library/05/1011_kroll/index.html>
  * For more information on Rational Method Composer, see:
    * The RMC Product Page on developer works <http://www-306.ibm.com/software/awdtools/rmc/>
    * Article: "IBM Rational Method Composer: Part 1: Key concepts" at <http://www.ibm.com/developerworks/rational/library/dec05/haumer/index.html>
  * For an in-depth explanation of the meta-model on which EPF Composer and Rational Method Composer are based, see:
  *     * OMG, "Software Process Engineering Meta model," version 1.1, formal/2005-01-06, 2005. <http://www.omg.org/technology/documents/formal/spem.htm>
---

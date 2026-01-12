---
title: Testing Qualitative Requirements
source_url: core.tech.common.extend_supp/guidances/concepts/testing_qualitative_rqmts_CAE80710.html
type: Concept
uma_name: testing_qualitative_rqmts
page_guid: _0aJ6cMlgEdmt3adZL5Dmdw
keywords:
- different
- qualitative
- requirements
- testing
related:
  workproducts:
  - test-case
---


 This concept covers some of different types of testing that is applicable to test the different qualitative requirements based on FURPS.
---

Relationships

Related Elements|
  * [Test Case](../../workproducts/test-case.md)
---|---

Main Description

###  Introduction

There is much more to testing computer software than simply evaluating the functions, interface, and response-time characteristics of a target-of-test. Additional tests must focus on characteristics and attributes, such as the target-of-test.
  * integrity \(resistance to failure\)
  * ability to be installed and executed on different platforms
  * ability to handle many requests simultaneously

To achieve this, many different types of tests are implemented and executed. Each test type has a specific objective and support technique. Each technique focuses on testing one or more characteristics or attributes of the target-of-test.  The following sections list the types of test based on the most obvious quality attributes they address.

###  Types of test for Functionality
**Function test:** Tests focused on validating the target-of-test functions as intended, providing the required services, methods, or use cases. This test is implemented and executed against different targets-of-test, including units, integrated units, applications, and systems.  **Security test:** Tests focused on ensuring the target-of-test data \(or systems\) are accessible only to those actors for which they are intended. This test is implemented and executed on various targets-of-test.  **Volume test:** Tests focused on verifying the target-of-test's ability to handle large amounts of data, either as input and output or resident within the database. Volume testing includes test strategies such as creating queries that would return the entire contents of the database, or that would have so many restrictions that no data is returned, or where the data entry has the maximum amount of data for each field.

###  Types of test for Usability
**Usability test:** Tests that focus on:
  * human factors
  * esthetics
  * consistency in the user interface
  * online and context-sensitive help
  * wizards and agents
  * user documentation
  * training materials
**Integrity test:** Tests that focus on assessing the target-of-test's robustness \(resistance to failure\), and technical compliance to language, syntax, and resource usage. This test is implemented and executed against different targets-of-tests, including units and integrated units.  **Structure test** : Tests that focus on assessing the target-of-test's adherence to its design and formation. Typically, this test is done for Web-enabled applications ensuring that all links are connected, appropriate content is displayed, and no content is orphaned.

###  Types of test for Reliability
**Stress test:** A type of reliability test that focuses on evaluating how the system responds under abnormal conditions. Stresses on the system could include extreme workloads, insufficient memory, unavailable services and hardware, or limited shared resources. These tests are often performed to gain a better understanding of how and in what areas the system will break, so that contingency plans and upgrade maintenance can be planned and budgeted for well in advance.  **Benchmark test:** A type of performance test that compares the performance of a new or unknown target-of-test to a known reference-workload and system.  **Contention test:** Tests focused on validating the target-of-test's ability to acceptably handle multiple actor demands on the same resource \(data records, memory, and so on\).

###  Types of test for Performance
**Load test:** A type of performance test used to validate and assess acceptability of the operational limits of a system under varying workloads while the system-under-test remains constant. In some variants, the workload remains constant and the configuration of the system-under-test is varied. Measurements are usually taken based on the workload throughout and in-line transaction response time. The variations in workload usually include emulation of average and peak workloads that occur within normal operational tolerances.  **Performance profile:** A test in which the target-of-test's timing profile is monitored, including execution flow, data access, function and system calls to identify and address both performance bottlenecks and inefficient processes.  **Configuration test:** Tests focused on ensuring the target-of-test functions as intended on different hardware and software configurations. This test might also be implemented as a system performance test.

###  Types of test for Supportability
**Installation test:** Tests focused on ensuring the target-of-test installs as intended on different hardware and software configurations, and under different conditions \(such as insufficient disk space or power interruptions\). This test is implemented and executed against applications and systems.
---

---
title: Test Log
source_url: core.tech.common.extend_supp/workproducts/test_log_CBA2FDF4.html
type: Artifact
uma_name: test_log
page_guid: _0ZlSsMlgEdmt3adZL5Dmdw
keywords:
- test
---

 This artifact collects the raw output that is captured during a unique run of one or more tests for a single test cycle run.
---
Domains: [Test](../../cat/domains/test.md)

Purpose
  * To provide verification that a set of tests was run
  * To provide information that relates to the success of those tests
---

Relationships

Fulfilled Slots|
  * [\[Technical Test Results\]](./../../core.tech.slot.base/workproducts/technical_test_results_slot_7B0CA334.html)
---|---
Roles| Responsible:
  * [Tester](../../role/roles/tester-5.md)

| Modified By:
  * [Developer](../../role/roles/developer-11.md)
  * [Tester](../../role/roles/tester-5.md)


Tasks| Input To:
  * [Assess Results](../../../practice-management/iterative_dev/tasks/assess-results-1.md)

| Output From:
  * [Run Developer Tests](../../../practice-technical/test_driven_development/tasks/run-developer-tests-1.md)
  * [Run Tests](../../../practice-technical/concurrent_testing/tasks/run-tests-1.md)



Description

Main Description| This artifact provides a detailed, typically time-based record that both verifies that a set of tests were run, and provides information that relates to the success of those tests. The focus is typically on providing an accurate audit trail, which enables you to undertake a post-run diagnosis of failures. This raw data is subsequently analyzed to determine the results of an aspect of the test effort.
---|---

Tailoring

Impact of not having|  Without this or similar documentation, there is no record of which tests were run, what variances were discovered, and what action was taken. If this information is not available:
  * There is no way to know which tests passed and which failed.
  * There is no way to assess the status of testing and the quality of the product at that level of testing.
  * It is difficult to know how many tests remain outstanding.
  * There can be contractual and legal issues.
---|---
Reasons for not needing|  When you execute automated tests, test logs are automatically produced. Typically, the issue is not whether to produce the test log, but whether to keep a record, and where to keep the records. For manual testing, the issue is whether to keep a separate test log or to summarize the test results in another form.
Representation Options|  Because this is a collection of raw data for subsequent analysis, it can be represented in a number of ways:
  * For manual tests, log the actual results on a copy of the manual Test Script
  * For automated tests, direct the output to log files that you can trace back to the automated Test Script
  * Track raw results data in a test management tool

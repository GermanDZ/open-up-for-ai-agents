---
title: Test Log
source_url: process.openup.base/capabilitypatterns/test_log_3288A196.html
type: WorkProductDescriptor
uma_name: test_log
page_guid: _N2c24UVEEeK93ZZqiMLBsA
keywords:
- test
related:
  other:
  - tester
---


 This artifact collects the raw output that is captured during a unique run of one or more tests for a single test cycle run.
---

Purpose
  * To provide verification that a set of tests was run
  * To provide information that relates to the success of those tests
---

Relationships

Roles| Responsible:
  * [Tester](tester.md)

| Modified By:
---|---|---

Main Description

This artifact provides a detailed, typically time-based record that both verifies that a set of tests were run, and provides information that relates to the success of those tests. The focus is typically on providing an accurate audit trail, which enables you to undertake a post-run diagnosis of failures. This raw data is subsequently analyzed to determine the results of an aspect of the test effort.
---

Properties

Optional| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")
---|---
Planned| ![](../../../images/indent.png) [📄](../../../images/descriptions/indent.md "Image description")

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

---
title: Metrics
source_url: core.mgmt.common.extend_supp/guidances/concepts/metrics_37698708.html
type: Concept
uma_name: metrics
page_guid: _0mYYkMlgEdmt3adZL5Dmdw
keywords:
- metrics
related:
  tasks:
  - manage-iteration-1
---


 A metric is used to interpret measurements so that team members and stakeholders can know the state of the project.
---

Relationships

Related Elements|
  * [Manage Iteration](../../../../practice-management/iterative_dev/tasks/manage-iteration-1.md)
---|---

Main Description

###  What is a Metric?

We distinguish between measure and metric. To clarify, let's start by defining what is meant by measure and by metric.
  * **Measure** : A raw data item that is directly measured, and that will be used to calculate a metric.
  * **Metric** : An interpretation of a measure or a set of measures that you use to guide your project. For example, recording how many test cases have passed and how many have failed are measures. Interpreting what level of quality this indicates and how it reflects the team's progress within the current iteration is a metric.

###  Why Measure?

Measurements will mainly help you to:
  * **Communicate effectively**. Measurement supports effective communication among team members and project stakeholders.
  * **Identify and correct problems early**. Measurement enables you to identify and manage potential problems early in the development lifecycle.
  * **Make informed trade-offs**. Measurement helps objectively assess the impact of decisions, helping the team make trade-off decisions to best meet project goals.
  * **Tune estimations**. Recording schedule, progress, and expenditures for projects will help team members to make more reliable estimations in the future.

###  Potential Challenges

There are several dangers when it comes to metrics:
  * **They can be too costly**. The benefit provided by the metric must exceed the cost of collecting it. Keep your measurements simple and easy to collect.
  * **They're a poor substitute for communication**. Do not use metrics as a substitute for communication. Team members may help to decide which metrics make sense for the project. Apply metrics not so much to control the project but to help team to collaborate better. Asking people about their progress is a co-dependent way of gaining insight into progress.
  * **They can be misleading**. No metric or collection of metrics is perfect. Furthermore, the measurements upon which they are based can be manipulated by the people capturing them. Don't rely simply upon metrics to manage a project.

Effective metrics programs can be challenging to implement, though typically not because of the statistics and complex analysis often associated with metrics. Rather, the challenge lies in understanding which metrics add value to the project and to the company, and which procedures are most efficient for collecting and using these metrics.  Consider implementing only a handful metrics. Importantly, do not collect metrics unless they help contribute to a goal of improving a defined area of your software development process. If you will not act on a metric, do not collect it. It is much more important to focus on a small number of metrics that are important to what you are trying to achieve right now, versus a larger set of metrics that may be "good to track".

###  Common Metrics

Below are some common measures and associated metrics used in software development projects. These metrics help teams communicate, identify and correct problems early, make informed trade-offs, and tune estimations. Example of metrics coverage areas are listed below.
  * Software quality
    * Defect backlog: Number of defects discovered respectively resolved per iteration
    * Test case coverage: Number of test cases executed over total number of test cases
    * Code coverage: % of code that have been tested
  * Development productivity
    * Velocity: Number of delivered points by iteration \(see [Agile Estimation](../guidelines/agile-estimation.md)\)
  * Development process effectiveness
    * Responsiveness to quality issues: Number of defects discovered versus resolved per iteration
    * Responsiveness to process improvement proposal: Number of process enhancements proposed versus implemented
  * Cost and schedule estimate and variance
    * Effort: Actual effort spent per iteration
    * Cost: Cost per iteration
    * Effort remaining: Track project burndown

There are many other measures and metrics that may make sense, based on what you are trying to accomplish. For example, if you want to measure the quality of your architecture, you may choose to collect metrics related to coupling between different software packages \(groups of related classes\) by measuring extensibility, dependency, and responsibility of each package.
---

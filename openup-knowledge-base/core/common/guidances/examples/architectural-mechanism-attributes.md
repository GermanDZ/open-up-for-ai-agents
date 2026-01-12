---
title: Architectural Mechanism Attributes
source_url: core.tech.common.extend_supp/guidances/examples/architectural_mechanism_attributes_B0ECA2F7.html
type: Example
uma_name: architectural_mechanism_attributes
page_guid: _eQ_s8Om5Edupia_tZIXEqg
keywords:
- architectural
- attributes
- mechanism
related:
  concepts:
  - analysis-mechanism
  - architectural-mechanism
---


 This example illustrates how to represent attributes for Architecture Mechanisms.
---

Relationships

Related Elements|
  * [Analysis Mechanism](../concepts/analysis-mechanism.md)
  * [Architectural Mechanism](../concepts/architectural-mechanism.md)
---|---

Main Description

The following shows an example of how to capture information for [Architectural Mechanism](../concepts/architectural-mechanism.md). The attributes of two possible mechanisms are shown: Persistence and Communication.

###  Persistence

For all classes with instances that may become persistent, you need to identify:
  * **Granularity****:** What is the range of size of the objects to keep persistent?
  * **Volume****:** How many objects \(number\) do you need to keep persistent?
  * **Duration****:** How long does the object typically need to be kept?
  * **Retrieval mechanism****:** How is a given object uniquely identified and retrieved?
  * **Update frequency****:** Are the objects more or less constant? Are they permanently updated?
  * **Reliability****:** Do the objects need to survive a crash of the process, the processor, or the whole system?

###  Communication

For all model elements that need to communicate with components or services that are running in other processes or threads, you need to identify:
  * **Latency****:** How fast must processes communicate with another?
  * **Synchronicity****:** Asynchronous communication
  * **Size of message****:** A spectrum might be more appropriate than a single number
  * **Protocol:** Flow control, buffering, and so on

Notice that there is no design-level information or specification here. Instead, this is more about collating and refining architecturally significant requirements.
---

---
title: Analysis Mechanism
source_url: core.tech.common.extend_supp/guidances/concepts/analysis_mechanism_8369C159.html
type: Concept
uma_name: analysis_mechanism
page_guid: _0gvqoMlgEdmt3adZL5Dmdw
keywords:
- analysis
- mechanism
related:
  other:
  - architectural-mechanism
  - design-mechanism
---


 An Analysis Mechanism is a conceptual representation of an Architectural Mechanism.
---

Relationships

Related Elements|
  * [Architectural Mechanism](architectural-mechanism.md)
  * [Design Mechanism](design-mechanism.md)
---|---

Main Description

An Analysis Mechanism is a conceptual representation of an [Architectural Mechanism](architectural-mechanism.md). Over time, Analysis Mechanisms are refined into [Design Mechanism](design-mechanism.md)s and, later, into [Implementation Mechanism](implementation-mechanism.md)s.  Analysis Mechanisms allow the developer to focus on understanding the requirements without getting distracted by the specifics of a complex implementation. They are a way of abstracting away the complexity of the solution, so people can better comprehend the problem.  Analysis Mechanisms are described in simple terms:
  * **Name:** Identifies the mechanism.
  * **Basic attributes:** Define the requirements of the mechanism.

You can identify Analysis Mechanisms top-down, from previous knowledge, or bottom-up, meaning that you discover them as you proceed.  In the top-down mode, you are guided by experience -- you know that certain problems are present in the domain and will require certain kinds of solutions. Examples of common architectural problems that might be expressed as mechanisms during analysis are: persistence, transaction management, fault management, messaging, and inference engines. The common aspect of all of these is that each is a general capability of a broad class of systems, and each provides functionality that interacts with or supports the basic application functionality. The Analysis Mechanisms support capabilities required in the basic functional requirements of the system, regardless of the platform that it is deployed upon or the implementation language. Analysis Mechanisms also can be designed and implemented in different ways. Generally, there will be more than one design mechanism that corresponds with each Analysis Mechanism. There may also be more than one way of implementing each design mechanism.  The bottom-up approach is where Analysis Mechanisms ultimately originate. They are created as the you see, perhaps faintly at first, a common theme emerging from a set of solutions to various problems. For example: There is a need to provide a way for elements in different threads to synchronize their clocks, and there is a need for a common way of allocating resources. [Analysis Mechanism](analysis-mechanism.md)s, which simplify the language of analysis, emerge from these patterns.  Identifying an Analysis Mechanism means that you identify a common, perhaps implicit subproblem, and you give it a name. Initially, the name might be all that exists. For example, the system will require a persistence mechanism. Ultimately, this mechanism will be implemented through the collaboration of various classes, some of which do not deliver application functionality directly, but exist only to support it. Very often these support classes are located in the middle or lower layers of a layered architecture, thereby providing a common support service to all application-level classes.  If the subproblem that you identify is common enough, perhaps a pattern exists from which the mechanism can be instantiated, probably by binding existing classes and implementing new ones, as required by the pattern. An Analysis Mechanism produced this way will be abstract, and it will require further refinement throughout design and implementation work.  You can see examples of how Architectural Mechanisms can be represented in [Example: Architectural Mechanism Attributes](../examples/architectural-mechanism-attributes.md).
---

More Information

Concepts|
  * [Architectural Mechanism](architectural-mechanism.md)
  * [Design Mechanism](design-mechanism.md)
  * [Implementation Mechanism](implementation-mechanism.md)
---|---
Examples|
  * [Architectural Mechanism Attributes](../examples/architectural-mechanism-attributes.md)

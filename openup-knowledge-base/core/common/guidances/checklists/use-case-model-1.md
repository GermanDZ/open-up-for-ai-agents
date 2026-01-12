---
title: Use-Case Model
source_url: core.tech.common.extend_supp/guidances/checklists/use_case_model_27A2D1CF.html
type: Checklist
uma_name: use_case_model
page_guid: _0U6OEMlgEdmt3adZL5Dmdw
keywords:
- case
- model
related:
  workproducts:
  - use-case-model
---


 This checklist provides questions to verify that the use-case model is described in a consistent and complete manner.
---

Relationships

Related Elements|
  * [Use-Case Model](../../workproducts/use-case-model.md)
---|---

Check Items

It is easy to understand what the system does by reviewing the model |
  * Does the use-case model provide a clear, concise overview of the purpose and functionality of the system?
  * Are there no long chains of _include_ relationships, such as when an included use case includes other use cases? These can obscure comprehension.
  * Are included use cases independent of the use cases that include them?
  * If several use cases contain similar subflows, have you investigated whether factoring this common behavior into an included use case will simplify the model?
---

All use cases have been identified
  * Do the use cases identified collectively account for all required behavior of the system?
  * Have all features identified in the vision document been addressed by at least one use case?
  * Have all nonfunctional requirements that must be satisfied by a specific use case been captured in that use case?
  * Have you verified that the use-case model contains no superfluous behavior \(known as "gold-plating"\)?
  * Is each concrete use case associated with at least one actor, as it should be?
  * Is every actor associated with at least one use case?
---

The model is consistent
  * Is the system behavior consistent under the same conditions and with the same input?
---

All relationships between use cases are required
  * Does each included use case make the model easier to understand, implement, and maintain?
  * Is each concrete use case \(not an included use case\) independent of other use cases?
---

Use-case packages are used appropriately
  * Have cross-package dependencies been reduced or eliminated to prevent model ownership conflicts
  * Is packaging intuitive? Does the packaging make the model easier to understand and implement?
---

All model elements have appropriate names
  * Have you verified that no two use cases have the same name?
  * Does each actor have a name that effectively describes that person's role?
---

Individual use cases are properly specified
  * Have you reviewed the quality of each use-case specification using the [Checklist: Use Case](use-case-1.md)?
---

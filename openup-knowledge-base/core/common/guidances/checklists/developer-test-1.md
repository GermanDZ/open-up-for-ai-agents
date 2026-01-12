---
title: Developer Test
source_url: core.tech.common.extend_supp/guidances/checklists/developer_test_4E2C0EF5.html
type: Checklist
uma_name: developer_test
page_guid: _dxaPUF-BEd2T0JdVjRyaQA
keywords:
- developer
- test
related:
  workproducts:
  - developer-test
---



---

Relationships

Related Elements|
  * [Developer Test](../../workproducts/developer-test.md)
---|---

Check Items

The test coverage is acceptable |  100% test coverage is the ideal, but there may occasionally be places where it's impossible to achieve total coverage. For instance, some code may only be executable when exotic system conditions occur that are not feasible to replicate on a developer's machine. Every reasonable effort should be made to cover all the code.
---

Developer test names or IDs are consistent with project naming conventions
---

The test logic is correct

Assure the test themselves are correct.
---

Branch coverage is acceptable.

Assure conditional logic been tested in all combinations.
---

The test is easy to maintain.

Has the test been implemented to account for expected ongoing changes in the application state, such as system date fields, transaction numbers, and so on?
---

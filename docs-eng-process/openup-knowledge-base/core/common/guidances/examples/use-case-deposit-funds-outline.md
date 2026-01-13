---
title: Use Case - Deposit Funds Outline
source_url: core.tech.common.extend_supp/guidances/examples/uc_deposit_funds_outline_AB06FCD4.html
type: Example
uma_name: uc_deposit_funds_outline
page_guid: _jiwo4IHGEd6NhZnUM27HMQ
keywords:
- case
- deposit
- funds
- outline
related:
  other:
  - evolution-of-the-use-case-model
---


 This is an outline of a use case to deposit funds using an Automated Teller Machine.
---

Relationships

Related Elements|
  * [Evolution of the Use-Case Model](evolution-of-the-use-case-model.md)
---|---

Main Description

###  Step-­by-­step outline

  1. Insert card
  2. Enter PIN
  3. Select deposit
  4. Select amount
  5. Put money in envelope
  6. Receive envelope ­ print transaction id on envelope
  7. Send deferred transaction
  8. Print receipt
  9. Eject card
  10. The next day ­ open security box
  11. Count money
  12. Commit transactions

Is the counting and committing within our system? Is this a part of some other system at the bank? Where is the boundary?

###  List of Alternative flows

A1 Wrong PIN
A2 Invalid "to account"
A3 No envelope inserted
A4 Two envelopes inserted \(or more\)
A5 No money in envelope
A6 Too much money in envelope
A7 Envelopes missing
---

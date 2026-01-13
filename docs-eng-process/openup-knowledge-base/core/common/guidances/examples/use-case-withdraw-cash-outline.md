---
title: Use Case - Withdraw Cash Outline
source_url: core.tech.common.extend_supp/guidances/examples/uc_withdraw_cash_outline_98D0EC9A.html
type: Example
uma_name: uc_withdraw_cash_outline
page_guid: _7MzegIHVEd6NhZnUM27HMQ
keywords:
- case
- cash
- outline
- withdraw
related:
  other:
  - evolution-of-the-use-case-model
---


 This is an outline of a use case to withdraw funds using an Automated Teller Machine.
---

Relationships

Related Elements|
  * [Evolution of the Use-Case Model](evolution-of-the-use-case-model.md)
---|---

Main Description

###  Step-­by-­step outline

  1. Insert Card
  2. Validate card
  3. Enter pin
  4. Select withdraw
  5. Select account
  6. Select amount
  7. Send transaction
  8. Receive ok
  9. Dispense money
  10. Print receipt
  11. Eject card

###  List of Alternative flows

A1 Wrong PIN
A2 No money
A3 Attempt to withdraw more than daily amount
A4 No contact
A5 Link goes down ­
i\) If the link goes down before the transaction reaches the actual account. ­ Not a big problem.
ii\) ­ If the transaction reaches the account and then the link is down. The money is withdrawn but never dispensed\! ­ Do we need some kind of two- phase- commit?
A6 Stolen card
A7 Out of money
---

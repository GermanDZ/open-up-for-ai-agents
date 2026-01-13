---
title: Use Case - Model Elaboration Phase
source_url: core.tech.common.extend_supp/guidances/examples/uc_model_elaboration_phase_70035F60.html
type: Example
uma_name: uc_model_elaboration_phase
page_guid: _MNZ2kIHHEd6NhZnUM27HMQ
keywords:
- case
- elaboration
- model
- phase
related:
  other:
  - evolution-of-the-use-case-model
---


 An example of a Use-Case Model as it would appear in Elaboration.
---

Relationships

Related Elements|
  * [Evolution of the Use-Case Model](evolution-of-the-use-case-model.md)
---|---

Main Description

###  1 Introduction

This is an example of a Use-Case Model as it would appear in Elaboration. Primary actors and use cases are identified, and key scenarios \(those that will be implemented first\) are detailed. Each use case has an associated use-case specification.

###  2 Overview

The Automated Teller Machine is a remote unit connected to the bank computer systems. The purpose of the system is to bring regular bank services closer to the customer and increase the working hours to around the clock. It is also important to decrease the amount of bank cashiers. An ATM withdrawal is less expensive for the Bank than a withdrawal from a teller.

The ATM system requires that each bank customer has an ATM card and remembers his PIN code. The whole security of this system builds on the PIN code.

###  3 Use-Case Diagram

The figure below shows the use-case diagram for the ATM.

![ATM Use-Case Diagram](../../../../images/atm_elab_uc_diagram.png) [📄](../../../../images/descriptions/atm_elab_uc_diagram.md "Image description")

###  4 Actors

####  4.1 Bank Customer

This actor represents a person with a valid Bank Card. The Bank Card is theirs and they know the PIN Code.

####  4.2 Cashier

From the ATM system point of view, the Cashier's only responsibility is to count the money in the security box to verify all deposits.

####  4.3 Bank

This actor represents the financial institution that provides services to the ATM. Responsible for verifying Bank Customers, authorizing transactions and recording completed transactions.

####  4.4 Maintenance Person

This actor represents the person responsible for maintaining the Automated Teller Machine, refilling paper, and replenishing cash.

###  5 Use Cases

#####  5.1.1 Validate User

This use case describes general behavior for the ATM to validate the Bank Customer. It includes all steps that are the same no matter what kind of transaction the Bank Customer does.

#####  5.1.2 Withdraw Cash

This use case describes how the Bank Customer uses the ATM to withdraw money his/her bank account.

#####  5.1.3 Transfer Funds

This use case describes how the Bank Customer uses the ATM to transfer money between different bank accounts.

#####  5.1.4 Deposit Funds

This use case describes how the Bank Customer deposits money to an account.

#####  5.1.5 Refill Machine

This use case describes how the Maintenance Person refills money, receipt paper and envelopes.
---

---
title: Use-Case Specification
source_url: core.tech.common.extend_supp/guidances/examples/use_case_spec_CD5DD9B1.html
type: Example
uma_name: use_case_spec
page_guid: _JLOiIMNvEdu2IdAIaWZyAw
keywords:
- case
- specification
related:
  workproducts:
  - use-case
  templates:
  - use-case-specification-1
---


 An example of a completed use-case specification for the Withdraw Cash use case for an Automated Teller Machine.
---

Relationships

Related Elements|
  * [Use Case](../../workproducts/use-case.md)
  * [Use-Case Specification](../templates/use-case-specification-1.md)
---|---

Main Description

###  1 Brief Description

This use case describes how the Bank Customer uses the ATM to withdraw money to his/her bank account.

###  2 Actors

####  2.1 Bank Customer

####  2.2 Bank

###  3 Preconditions

There is an active network connection to the Bank.

The ATM has cash available.

###  4 Basic Flow of Events

> 1\. The use case begins when Bank Customer inserts their Bank Card.  2\. Use Case: Validate User is performed.  3\. The ATM displays the different alternatives that are available on this unit. \[See Supporting Requirement SR-xxx for list of alternatives\]. In this case the Bank Customer always selects "Withdraw Cash".  4\. The ATM prompts for an account. See Supporting Requirement SR-yyy for account types that shall be supported.  5\. The Bank Customer selects an account.  6\. The ATM prompts for an amount.  7\. The Bank Customer enters an amount.  8\. Card ID, PIN, amount and account is sent to Bank as a transaction. The Bank Consortium replies with a go/no go reply telling if the transaction is ok.  9\. Then money is dispensed.  10\. The Bank Card is returned.  11\. The receipt is printed.  12\. The use case ends successfully.

###  5 Alternative Flows

####  5.1 Invalid User

If in step 2 of the basic flow Bank Customer the use case: Validate User does not complete this successfully, then

> 1\. The use case ends with a failure condition.

####  5.2 Wrong account

If in step 8 of the basic flow the account selected by the Bank Customer is not associated with this bank card, then  1\. The ATM shall display the message "Invalid Account – please try again".  2\. The use case resumes at step 4.

####  5.3 Wrong amount

If in step 7 in the basic flow, the Bank Customer enters an amount that can't be 'created' with the kind of in the ATM \(See Special Requirement WC-1 for valid amounts\), then

> 1\. The ATM shall display a the message indicating that the amount must be a multiple of the bills on hand, and ask the Bank Customer to reenter the amount.  2\. The use case resumes at step 7.

####  5.4 Amount Exceeds Withdrawal Limit

If in step 7 in the basic flow, the Bank Customer enters an amount that exceeds the withdrawal limit \(See Special Requirement WC-2 for maximum amount\), then  1\. the ATM shall display a warning message, and ask the Bank Customer to reenter the amount  2\. The use case resumes at step 7

####  5.5 Amount Exceeds Daily Withdrawal Limit

If in step 8 in the basic flow, the Bank response indicates the daily withdrawal limit has been exceeded \(this is determined by the Bank and depends upon the specific account\), then

> 1\. The ATM shall display a warning message, and ask the Bank Customer to reenter the amount.  2\. The use case resumes at step 7.

####  5.6 Insufficient Cash

If in step 7 in the basic flow, the Bank Customer enters an amount that exceeds the amount of cash available in the ATM, then

> 1\. The ATM will display a warning message, and ask the Bank Customer to reenter the amount.  2\. The use case resumes at step 7.

####  5.7 No Response from Bank

If in step 8 of the basic there is no response from the Bank within 3 seconds, then

> 1\. The ATM will re-try, up to three times.  2\. If there is still no response from the Bank, the ATM shall display the message "Network unavailable – try again later".  3\. The ATM shall return the card.  4\. The ATM shall indicate that it is "Closed".  5\. The use case ends with a failure condition.

####  5.8 Money Not Removed

If in step 9 of the basic flow the money is not removed from the machine within 15 seconds, then

> 1\. the ATM shall issue a warning sound and display the message "Please remove cash".  2\. If there is still no response from the Bank Customer within 15 seconds the ATM will re-tract the money and note the failure in the log.  3\. the use case end with a failure condition.

####  5.9 Quit

If at point prior to step 8 in the basic flow the Bank Customer selects Quit, then

> 1\. The ATM shall print a receipt indicating the transaction was canceled.  2\. The ATM shall return the card.  3\. The use case ends.

###  6 Key Scenarios

####  6.1 No Response from Bank

###  7 Post-conditions

####  7.1 Successful Completion

The user has received their cash and the internal logs have been updated.

####  7.2 Failure Condition

The logs have been updated accordingly.

###  8 Special Requirements

\[SpReq:WC-1\] The ATM shall dispense cash in multiples of $20.  \[SpReq2:WC-2\] The maximum individual withdrawal is $500.  \[SpReq:WC-1\] The ATM shall keep a log, including date and time, of all complete and incomplete transactions with the Bank.
---

More Information

Examples|
  * [Evolution of the Use-Case Model](evolution-of-the-use-case-model.md)
---|---

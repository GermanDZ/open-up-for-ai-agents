---
title: Use Case - Specification Validate User
source_url: core.tech.common.extend_supp/guidances/examples/uc_spec_validate_user_85DF99C7.html
type: Example
uma_name: uc_spec_validate_user
page_guid: _BkKmAIHSEd6NhZnUM27HMQ
keywords:
- case
- specification
- user
- validate
related:
  other:
  - evolution-of-the-use-case-model
---


 Describes general behavior for the Automated Teller Machine to validate the user.
---

Relationships

Related Elements|
  * [Evolution of the Use-Case Model](evolution-of-the-use-case-model.md)
---|---

Main Description

###  1 Brief Description

This use case describes general behavior for the ATM to validate the user. It includes all steps that are the same no matter what kind of transaction the Bank Customer does.

###  2 Actors

####  2.1 Bank Customer

####  2.2 Bank

###  3 Preconditions

There is an active network connection to the Bank.

###  4 Basic Flow of Events

> 1\. The use case begins when the Bank Customer inserts their Bank Card.  2\. The ATM reads the code from the magnetic strip of the Bank Card and checks with the Bank to see if it is an acceptable Bank Card. The Bank confirms the card is valid.  3\. The ATM asks for the customer PIN code \(4 digits\).  4\. The Bank Customer enters a PIN.  5\. The ATM validates the PIN with the Bank. The Bank confirms the PIN is valid.  6\. The ATM displays the different alternatives that are available on this unit.  7\. The use case ends. \(The flow continues according to the flow of the specific transaction\).

###  5 Alternative Flows

####  5.1 Not a valid card

If in step 2 of the basic flow the card is invalid, then

> 1\. The ATM shall display a "sorry not a valid card" message and return the card.  2\. The use case ends with an indication of the failure.

####  5.2 Wrong PIN \(1st and 2nd time\)

If in step 5 of the basic flow the PIN is invalid, then

> 1\. The ATM shall display a "sorry invalid PIN" message.  2\. The use case resumes at step 3.

####  5.3 Wrong PIN \(third time\)

If in step 5 of the basic flow an incorrect PIN is entered for the third time, then

> 1\. The ATM shall display a "sorry invalid PIN – Please contact your branch" message.  2\. The card is kept by the ATM and a receipt is printed telling how and where to get a new card.  3\. The use case ends with an indication of the failure.

####  5.4 No Response from Bank

If in steps 2 or 5 of the basic flow there is no response from the Bank within 3 seconds, then

> 1\. The ATM will re-try, up to three times.  2\. If there is still no response from the Bank, the ATM shall display the message "Network unavailable – try again later".  3\. The ATM shall return the card.  4\. The ATM shall indicate that it is "Closed".  5\. The use case ends with an indication of the failure.

####  5.5 No Response from Bank Customer

If in step 4 of the basic flow there is no response from the Bank Customer within 15 seconds, then

> 1\. The ATM shall issue a warning sound and display the message "Please enter PIN".
>
>  2\. If there is still no response from the Bank Customer within 15 seconds the ATM will store the card internally.  3\. The use case ends with an indication of the failure.

####  5.6 Stolen Card

If in step 2, the Bank indicates that this is a stolen card, then

> 1\. What shall we do? Take a picture of the user? Notify the police?

\[This is a typical way to use Use Cases. You can write your questions right down in the text ­ and when you get your answers you'll have to correct it. Another way to do it: is to assume one way ­ either they like it or they tell you how it should be\]

###  6 Post-conditions

####  6.1 Successful Completion

If the use case ends in success, the user is validated and may continue with the specific transaction.

####  6.2 Failure Condition

If there is a failure to validate the user, the ATM shall log the event including the reason for the failure.

###  7 Special Requirements

\[SpReq:VU-1\] The ATM shall keep a log, including date and time, of all complete and incomplete transactions with the Bank.
---

---
title: "Image: atm_incept_uc_diagram.png"
image_file: "../atm_incept_uc_diagram.png"
source: "core.tech.common.extend_supp/guidances/examples/resources/atm_incept_uc_diagram.gif"
---

# Image Description: atm_incept_uc_diagram.png

## Description

This image displays a UML Use Case diagram titled "ATM Use Cases Inception" with "package OpenUP (1/2)" in the top right corner. The diagram illustrates the functional requirements of an ATM system.

**High-Level Description:**

The diagram presents three actors: 'Bank Customer', 'Maintenance Person', and 'Bank'. These actors interact with the primary system, labeled "atm: ATM," which is enclosed within a rectangular boundary. Inside this system boundary, there are four use cases: 'Withdraw Cash', 'Transfer Funds', 'Deposit Funds', and 'Refill Machine'. The diagram uses lines to show the associations between the actors and the use cases.

**Detailed Description:**

1. **Title and Context:**
   - The main title at the top left is "ATM Use Cases Inception".
   - In the top right, it indicates "package OpenUP (1/2)", suggesting this is part of a larger system description or a multi-page diagram.

2. **System Boundary and Name:**
   - A large rectangle represents the system under consideration, labeled "atm: ATM" at the top center of the rectangle. This boundary encapsulates the core functionalities of the ATM.

3. **Actors:**
   - **'Bank Customer'**: Located on the left side of the diagram, depicted as a stick figure.
     - This actor is associated with three use cases: 'Withdraw Cash', 'Transfer Funds', and 'Deposit Funds'. Lines connect the 'Bank Customer' to each of these use case ellipses.
   - **'Maintenance Person'**: Located below the 'Bank Customer' on the left side, also a stick figure.
     - This actor is associated with one use case: 'Refill Machine'. A line connects the 'Maintenance Person' to this use case ellipse.
   - **'Bank'**: Located on the right side of the diagram, depicted as a stick figure.
     - This actor is associated with three use cases: 'Withdraw Cash', 'Transfer Funds', and 'Deposit Funds'. Lines connect the 'Bank' to each of these use case ellipses.

4. **Use Cases (within the 'atm: ATM' system boundary):**
   - **'Withdraw Cash'**: An oval shape at the top, representing the action of a customer withdrawing money.
     - It is connected to both 'Bank Customer' and 'Bank'.
   - **'Transfer Funds'**: An oval shape below 'Withdraw Cash', representing the action of a customer moving money between accounts.
     - It is connected to both 'Bank Customer' and 'Bank'.
   - **'Deposit Funds'**: An oval shape below 'Transfer Funds', representing the action of a customer depositing money.
     - It is connected to both 'Bank Customer' and 'Bank'.
   - **'Refill Machine'**: An oval shape at the bottom, separate from the customer-facing transactions, representing the action of replenishing the ATM with cash or supplies.
     - It is connected only to the 'Maintenance Person'.

**Relationships/Flows:**

The 'Bank Customer' initiates actions like withdrawing, transferring, and depositing funds, which involve the 'Bank' (presumably for verification, transaction processing, and account updates). The 'Maintenance Person' is responsible for maintaining the physical operation of the ATM, specifically refilling it.

The diagram clearly separates the end-user (customer) interactions from the administrative/maintenance interactions with the ATM system.

## For LLMs

This sidecar file provides text-based description of the image to enable understanding without visual processing.

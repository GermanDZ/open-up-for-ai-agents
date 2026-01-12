---
title: "Image: fig1_atm_ex.png"
image_file: "../fig1_atm_ex.png"
source: "core.tech.common.extend_supp/guidances/concepts/resources/fig1_atm_ex.gif"
---

# Image Description: fig1_atm_ex.png

## Description

This image is a UML Use Case Diagram illustrating the functionalities of an Automated Teller Machine (ATM) system.

**High-level Description:**

The diagram depicts the interactions between various actors and the ATM system, outlining the core use cases (functions) provided by the ATM. It clearly separates customer-facing operations from maintenance tasks and shows the involvement of the bank for financial transactions.

**Detailed Description:**

**1. System Boundary:**

A large rectangle forms the system boundary, labeled "atm:ATM" at its top center. This rectangle encloses all the primary use cases that belong to the ATM system.

**2. Actors:**

There are three actors represented as stick figures outside the system boundary:
- **'Bank Customer'**: Positioned on the left side, above the midpoint. This actor represents an individual interacting with the ATM for personal banking needs.
- **'Maintenance Person'**: Positioned on the left side, below the midpoint. This actor represents personnel responsible for the physical upkeep and supply of the ATM.
- **'Bank'**: Positioned on the right side. This actor represents the external banking system that the ATM interacts with to process financial transactions.

**3. Use Cases:**

Inside the "atm:ATM" system boundary, there are four oval-shaped use cases, each representing a distinct function:
- **'Withdraw Cash'**: Located at the top, inside the system boundary.
- **'Transfer Funds'**: Located in the middle, below 'Withdraw Cash'.
- **'Deposit Funds'**: Located below 'Transfer Funds'.
- **'Refill Machine'**: Located at the bottom, inside the system boundary, separated from the customer-facing use cases.

**4. Relationships (Associations):**

Lines connect the actors to the use cases, indicating an association or participation in that specific use case:
- **'Bank Customer'** is connected to 'Withdraw Cash', 'Transfer Funds', and 'Deposit Funds'. This indicates that a bank customer can perform these three actions.
- **'Maintenance Person'** is connected only to 'Refill Machine', indicating their responsibility for this specific task.
- **'Bank'** is connected to 'Withdraw Cash', 'Transfer Funds', and 'Deposit Funds'. This signifies that these customer transactions involve interactions with the central banking system (e.g., updating balances, verifying accounts).

**5. Meaning and Flow:**

The diagram illustrates the primary user stories or functionalities of an ATM. Bank customers can manage their money by withdrawing, transferring, or depositing funds, all of which require interaction with the Bank's system. Separately, a maintenance person can refill the machine, a task not directly involving the bank for transaction processing. The clear delineation shows different user roles and their respective system interactions, providing a high-level overview of the ATM's functionality and its external dependencies.

## For LLMs

This sidecar file provides text-based description of the image to enable understanding without visual processing.

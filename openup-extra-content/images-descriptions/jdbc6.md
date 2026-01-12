---
title: "Image: jdbc6.png"
image_file: "../jdbc6.png"
source: "core.tech.common.extend_supp/guidances/guidelines/resources/jdbc6.gif"
---

# Image Description: jdbc6.png

## Description

This image is a UML sequence diagram illustrating a database deletion operation. It shows the interaction between four participants: `myPersistencyClient`, `myDB Class`, `Connection`, and `Statement`.

**High-Level Description:**

The diagram depicts a client requesting the deletion of a persistent class. This request is handled by a database class, which then interacts with a database `Connection` to create a `Statement`, and subsequently executes an update statement using this `Statement` to perform the actual SQL deletion.

**Detailed Description:**

1. **Participants (Lifelines):**
   - **:myPersistencyClient:** Located at the far left, depicted by a brown rectangular header, representing the client initiating the delete operation. Its lifeline is a vertical dashed line.
   - **:myDB Class:** Adjacent to the `myPersistencyClient`, also with a brown rectangular header, representing a database abstraction or handling class. Its lifeline is a vertical dashed line.
   - **:Connection:** Next to `myDB Class`, with a yellow rectangular header, likely representing a database connection object. Its lifeline is a vertical dashed line.
   - **:Statement:** The rightmost participant, with a yellow rectangular header, representing a database statement object (e.g., for executing SQL). Its lifeline is a vertical dashed line.

2. **Interaction Flow (Messages and Activation Bars):**
   - **Message 1: `1. delete(myPersistent Class)`**
     - Initiated by `:myPersistencyClient` and sent to `:myDB Class`.
     - This message triggers an activation bar on the `:myDB Class` lifeline, indicating that the `myDB Class` object becomes active to process this request.
   - **Message 1.1: `1.1. create Statement()`**
     - Sent from the active `:myDB Class` (from its activation bar) to `:Connection`.
     - Upon receiving this message, a small activation bar appears on the `:Connection` lifeline, suggesting that the `Connection` object briefly becomes active to handle the request to create a statement.
   - **Message 1.2: `1.2. execute Update (String)`**
     - Sent from the active `:myDB Class` (from its activation bar) to `:Statement`.
     - This message also triggers a small activation bar on the `:Statement` lifeline, indicating that the `Statement` object becomes active to execute the update.

3. **Notes/Comments:**
   - A dashed line extends from the `1.2. execute Update (String)` message to a comment box positioned to the right of the diagram.
   - The comment box contains the text: "Execute SQL statement", clarifying the purpose of the `execute Update` call.

**Meaning:**

The diagram illustrates a common pattern for performing database operations, specifically a deletion. The client delegates the persistence logic to a `myDB Class`. This class then manages the low-level database interactions, first obtaining a `Statement` object via a `Connection`, and then using that `Statement` to perform an `execute Update` call, which is explicitly noted as executing an SQL statement. This modular design separates concerns, with the client only interacting with the persistence layer, and the persistence layer abstracting the details of database connectivity and statement execution. The numbering (`1`, `1.1`, `1.2`) indicates a nested sequence of calls.

## For LLMs

This sidecar file provides text-based description of the image to enable understanding without visual processing.

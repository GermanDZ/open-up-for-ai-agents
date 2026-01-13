---
title: "Image: jdbc4.png"
image_file: "../jdbc4.png"
category: "illustration"
dimensions: "627x352"
source: "core.tech.common.extend_supp/guidances/guidelines/resources/jdbc4.gif"
---

# Image Description: jdbc4.png

## Description

The image displays a UML sequence diagram illustrating the process of retrieving persistent data from a database and populating a list of persistent objects.

**High-Level Description:**

The diagram visualizes the interaction flow between a persistence client, a database access class, standard JDBC components (Connection, Statement, Result Set), and classes representing persistent data (a list and individual persistent objects). The primary goal is to show how a client requests data, how that request is translated into database queries, how results are fetched, and how they are used to instantiate and populate a collection of persistent objects.

**Detailed Description:**

1. **Participants (Lifelines from left to right):**
   - `:myPersistencyClient`: The initiating client or module that requests persistent data.
   - `:myDBClass`: A class responsible for handling database interactions, acting as an intermediary.
   - `:Connection`: Represents a database connection.
   - `:Statement`: Represents an SQL statement to be executed.
   - `:Result Set`: Represents the tabular data returned by an SQL query.
   - `:myPersistentClassList`: A collection or list designed to hold multiple instances of `myPersistentClass`.
   - `:myPersistentClass`: Represents a single persistent object, corresponding to a row or record in the database.

2. **Flow of Operations:**

   - **Initiation (Step 1):**
     - `myPersistencyClient` initiates the process by sending a `1. read(string)` message to `:myDBClass`.
     - A note beside `myPersistencyClient` states: "Passes the criteria used to access data for the persistent class". This indicates the `string` argument contains parameters for data retrieval (e.g., a WHERE clause, an ID).

   - **Database Query Preparation and Execution (Steps 1.1 - 1.2):**
     - `myDBClass` then sends a `1.1. createStatement()` message to `:Connection`.
     - A note beside `:Statement` indicates that `:Connection` "Returns a statement" back to `myDBClass`.
     - `myDBClass` uses this returned statement to send a `1.2. executeQuery(String)` message to `:Statement`.
     - A note above `:Result Set` clarifies: "The SQL statement built by the myDBClass object using the given criteria is passed to executeQuery()". This `String` argument is the actual SQL query.
     - The `executeQuery()` method returns a `:Result Set` object to `myDBClass`.

   - **Result Processing Loop:**
     - A large note spanning below `myPersistencyClient` and `myDBClass` describes the subsequent steps: "Repeat these operations for each element returned from the executeQuery() command. The PersistentClass List is loaded with the data retrieved from the database." This indicates a loop for iterating through each record in the `Result Set`.

   - **Inside the Loop (Steps 1.3 - 1.7):**
     - **1.3. Object List Creation:** `myDBClass` sends a `1.3. new()` message to `:myPersistentClassList`. A note next to `:myPersistentClassList` explains: "Create a list to hold all retrieved data". This likely means the list is initialized or cleared.
     - **1.4. Individual Object Creation:** For each element (row) in the `Result Set`, `myDBClass` sends a `1.4. new()` message to `:myPersistentClass`, creating a new instance of the persistent object.
     - **1.5. Data Retrieval from Result Set:** `myDBClass` then repeatedly sends `1.5. getString()` messages to the `:Result Set` to extract data for the current row.
     - A note next to `:myPersistentClass` clarifies: "Called for each attribute in the class". This means `getString()` (or similar getter methods for other data types) is invoked for every field/property that needs to be populated in `myPersistentClass`.
     - **1.6. Object Population:** After retrieving data for all attributes of the current row, `myDBClass` sends a `1.6. setData()` message to the newly created `:myPersistentClass` object, passing the retrieved data to its attributes.
     - **1.7. Adding to List:** Finally, `myDBClass` sends a `1.7. add(myPersistentClass)` message to `:myPersistentClassList`, adding the fully populated persistent object to the collection.

The sequence diagram concludes after the loop has processed all elements from the `Result Set` and added them to `myPersistentClassList`.

## For LLMs

This sidecar file provides text-based description of the image to enable understanding without visual processing.


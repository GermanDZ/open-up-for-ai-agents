# Architecture Notebook Rubric

Use this rubric to assess whether an architecture notebook is complete and correct.
Grade each criterion: ✅ satisfied / ❌ gap — [specific description of what's missing]

---

## 1. Architectural Goals and Constraints
**Satisfied when:** The document states the top non-functional requirements (performance, scalability, security, availability) that drive architectural decisions, and any external constraints (technology mandates, compliance requirements, integration boundaries).

## 2. Key Architectural Decisions
**Satisfied when:** At least 3 significant architectural decisions are documented. Each decision includes: the decision made, the alternatives considered, and the rationale for the choice.

## 3. System Structure / Component Overview
**Satisfied when:** The major components or layers of the system are described with their responsibilities. A diagram or structured list shows how components relate to each other. No internal implementation details — only public interfaces and responsibilities.

## 4. Technology Stack
**Satisfied when:** The chosen technologies (languages, frameworks, databases, infrastructure) are listed with a brief justification for each non-obvious choice.

## 5. Data Architecture
**Satisfied when:** The document describes the main data entities, how data flows through the system, and where data is persisted. Storage technology choices are identified.

## 6. Key Interfaces and Integration Points
**Satisfied when:** External systems, APIs, and integration points are documented with their protocols and data formats. Internal component interfaces that cross architectural boundaries are identified.

## 7. Risk Areas and Mitigations
**Satisfied when:** At least 2 technical risks are identified (e.g., "third-party API may have rate limits", "data migration complexity"). Each risk has a proposed mitigation or accepted tradeoff.

## 8. Open Issues
**Satisfied when:** Unresolved architectural questions are explicitly listed with their expected resolution approach or timeline. If none exist, the document states "No open architectural issues."

---

## Grading Instructions

For each criterion above, write one of:
- `✅ [criterion name]` — fully satisfied
- `❌ [criterion name] — [specific gap]` — e.g., "❌ Key Architectural Decisions — only 1 decision documented, need at least 3"

After grading all criteria, output:
- **Result**: `satisfied` (all ✅) or `needs_revision` (any ❌)
- **Summary**: one sentence on the most critical gap if `needs_revision`

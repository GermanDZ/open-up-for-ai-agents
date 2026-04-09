# Use Case Rubric

Use this rubric to assess whether a use case document is complete and correct.
Grade each criterion: ✅ satisfied / ❌ gap — [specific description of what's missing]

---

## 1. Primary Actor
**Satisfied when:** The use case names a single primary actor (human role or external system) who initiates the interaction. The actor's goal in this use case is stated.

## 2. Trigger / Preconditions
**Satisfied when:** There is a clear trigger event that starts the use case (e.g., "user clicks X", "system receives Y event"). Preconditions state what must be true before the use case begins.

## 3. Main Success Scenario (Basic Flow)
**Satisfied when:** A numbered step-by-step flow describes the happy path from trigger to goal achieved. Each step is a single actor or system action. The flow has at least 3 steps and terminates with a clear outcome.

## 4. Alternate Flows
**Satisfied when:** At least one alternate flow (a variation or extension of the main flow) is documented with a reference to the step it branches from, the condition, and the alternate steps.

## 5. Exception / Error Flows
**Satisfied when:** At least one exception flow handles a failure condition (invalid input, system error, etc.) with the condition and recovery steps documented.

## 6. Postconditions
**Satisfied when:** The success postcondition states what is true after the use case completes successfully. If there are failure postconditions, they are listed separately.

## 7. Scope and Boundaries
**Satisfied when:** The use case clearly indicates what the system does vs. what is out of scope. It does not describe UI layout or implementation details — only externally observable behavior.

## 8. Traceability
**Satisfied when:** The use case references the related requirement, feature, or roadmap task ID that motivated it (e.g., `Implements: T-012`).

---

## Grading Instructions

For each criterion above, write one of:
- `✅ [criterion name]` — fully satisfied
- `❌ [criterion name] — [specific gap]` — e.g., "❌ Alternate Flows — no alternate flows documented; at minimum need a flow for cancelled action"

After grading all criteria, output:
- **Result**: `satisfied` (all ✅) or `needs_revision` (any ❌)
- **Summary**: one sentence on the most critical gap if `needs_revision`

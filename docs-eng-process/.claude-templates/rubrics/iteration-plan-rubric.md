# Iteration Plan Rubric

Use this rubric to assess whether an iteration plan is complete and correct.
Grade each criterion: ✅ satisfied / ❌ gap — [specific description of what's missing]

---

## 1. Iteration Goal
**Satisfied when:** A single, clear goal sentence states what the iteration is trying to achieve and why it matters to the project at this point. The goal is measurable — it can be objectively determined as met or not met.

## 2. Acceptance Criteria
**Satisfied when:** At least 3 specific, testable acceptance criteria are listed. Each criterion describes an observable outcome (e.g., "Users can log in with email/password and receive a session token"). Vague criteria like "feature works correctly" are not acceptable.

## 3. Task List with Estimates
**Satisfied when:** All planned tasks are listed with task IDs matching the roadmap. Each task has a brief description and an effort estimate (story points, hours, or T-shirt size). The total estimated effort is stated.

## 4. Risk Coverage
**Satisfied when:** Any risks from the risk list that are relevant to this iteration are referenced, and the plan describes how this iteration addresses or mitigates them.

## 5. Dependencies and Blockers
**Satisfied when:** Any external dependencies (other tasks, teams, decisions) that could block iteration completion are identified. Known blockers have a resolution plan or are escalated.

## 6. Definition of Done
**Satisfied when:** The plan states explicitly what "done" means for this iteration: which tests must pass, what documentation must exist, what review must be completed before the iteration is marked complete.

## 7. Phase Alignment
**Satisfied when:** The iteration plan is consistent with the current OpenUP phase's objectives. Inception iterations should not include construction work; construction iterations should not be re-doing architecture baseline work unless explicitly justified.

---

## Grading Instructions

For each criterion above, write one of:
- `✅ [criterion name]` — fully satisfied
- `❌ [criterion name] — [specific gap]` — e.g., "❌ Acceptance Criteria — only 1 criterion listed and it's vague"

After grading all criteria, output:
- **Result**: `satisfied` (all ✅) or `needs_revision` (any ❌)
- **Summary**: one sentence on the most critical gap if `needs_revision`

# Vision Rubric

Use this rubric to assess whether a project vision document is complete and correct.
Grade each criterion: ✅ satisfied / ❌ gap — [specific description of what's missing]

---

## 1. Problem Statement
**Satisfied when:** The document clearly describes the problem being solved: who experiences it, what pain it causes, and why existing solutions are insufficient. A reader unfamiliar with the domain should understand the problem without additional context.

## 2. Proposed Solution
**Satisfied when:** The solution is described at a high level: what the system does (not how it does it technically), what makes it different from alternatives, and how it addresses the stated problem.

## 3. Stakeholders and Users
**Satisfied when:** All stakeholder groups are identified (end users, sponsors, operators, integrators). For each group: their role, their primary need from the system, and their success criteria are described.

## 4. Key Features / Scope
**Satisfied when:** The top 5–10 key features or capabilities are listed. The document clearly distinguishes "in scope for this project" from "out of scope / future". Features are described in user-value terms, not technical terms.

## 5. Success Metrics
**Satisfied when:** At least 3 measurable success metrics are defined that indicate whether the project has achieved its goal (e.g., "Reduce time-to-X by 50%", "Support 1,000 concurrent users", "NPS score > 40"). Metrics are specific and quantified where possible.

## 6. Constraints and Assumptions
**Satisfied when:** Key constraints (budget, timeline, technology, compliance) and assumptions that the project depends on are explicitly listed. If any assumption is violated, the impact on the project is noted.

## 7. Risks Overview
**Satisfied when:** At least 3 high-level project risks are identified (not just technical — also business, market, team risks). Each risk has a brief impact statement.

## 8. Vision Alignment
**Satisfied when:** The document connects the project to broader organizational goals or strategy. A reader should understand why this project is being done now and why it matters beyond the immediate deliverable.

---

## Grading Instructions

For each criterion above, write one of:
- `✅ [criterion name]` — fully satisfied
- `❌ [criterion name] — [specific gap]` — e.g., "❌ Success Metrics — no quantified metrics; 'improve user experience' is not measurable"

After grading all criteria, output:
- **Result**: `satisfied` (all ✅) or `needs_revision` (any ❌)
- **Summary**: one sentence on the most critical gap if `needs_revision`

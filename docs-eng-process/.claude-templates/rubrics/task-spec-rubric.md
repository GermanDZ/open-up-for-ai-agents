# Task Spec Rubric

Use this rubric to assess whether a task spec (REASONS Canvas) is complete and
correct before marking it `ready` for implementation.

Grade each criterion: ✅ satisfied / ❌ gap — [specific description of what's missing]

---

## 1. Front-matter Completeness

**Satisfied when:** Front-matter includes `id` (T-XXX format), `title`, `status`
(one of: proposed/ready/in-progress/done/verified), `priority` (critical/high/medium/low),
and `estimate`. `plan`, `depends-on`, `blocks`, and `last-synced` are present
when applicable (empty arrays / strings are acceptable defaults).

## 2. Story INVEST-fit

**Satisfied when:** The Story section is in As-a / I-want / So-that form, names a
specific role (not "user" generically when a more specific role applies), states
a concrete capability, and an outcome that is *not just the capability restated*.
At least four of the six INVEST dimensions are credibly satisfied.

## 3. Requirements Testability

**Satisfied when:** Each numbered requirement is a single, checkable assertion
(can be verified by reading code, running a test, or inspecting an artifact).
No vague verbs like "improve", "enhance", "support better" without a concrete
target. At least one requirement maps to an observable end-state.

## 4. Entities Accuracy

**Satisfied when:** Each entity is annotated with its change-mode (new / modified
/ read-only) and a path or symbol. The list contains the load-bearing entities
only — not every file the agent might glance at. Missing entities that obviously
must change are a gap.

## 5. Approach Clarity

**Satisfied when:** The Approach section is 3–5 lines (or close) describing
*design intent* — what shape the solution takes, what existing patterns it
mirrors, what is being deliberately chosen vs deferred. It does NOT contain
imperative steps (those belong in Operations).

## 6. Structure Scope-fit

**Satisfied when:** The Add/Modify/Do-not-touch lists name concrete paths.
"Do not touch" items are credible scope-creep candidates with a brief why,
not defensive padding. The total set of touched files matches the estimate
in front-matter (a "0.5 session" task with 30 modified files is a gap).

## 7. Operations Testability

**Satisfied when:** Operations are ordered, 3–8 steps, each independently
verifiable. Each step states an action *and* something checkable that results
from it. No "and then implement the rest" hand-waves.

## 8. Norms / Safeguards Inheritance

**Satisfied when:** Norms section *references* `conventions.md` (and other
sources) by path; it does NOT inline rules from those files. Safeguards
section names invariants specific to this task (token budgets, reversibility,
no-go zones) without restating architecture-notebook content. Inline duplication
of rules from referenced sources is a gap (silent drift hazard, per SPDD).

---

## Grading Instructions

For each criterion above, write one of:
- `✅ <criterion name>` — fully satisfied
- `❌ <criterion name> — <specific gap>`

After grading all criteria, output:
- **Result**: `satisfied` (all ✅) or `needs_revision` (any ❌)
- **Summary**: one sentence on the most critical gap if `needs_revision`
- **Next action**: which sections to revise, by name

A spec must be `satisfied` before its status moves from `proposed` to `ready`.

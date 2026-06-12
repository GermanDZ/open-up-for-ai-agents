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

## 9. Ambiguity Resolution

**Satisfied when:** The Ambiguity Gate was applied — open questions the request
left unanswered are accounted for, not silently guessed. Any **blocking**
question (one whose answer would change scope, requirements, or acceptance
criteria) was raised via `/openup-request-input` rather than assumed; any
**non-blocking** default appears as an explicit `**Assumption:**` line in
Analysis Context (stating the choice, marked vetoable). A spec whose
Requirements depend on an unstated judgement call — no assumption named, no
question raised — is a gap. "No open questions" is acceptable only when the
request is genuinely unambiguous.

## 10. Behavior Delta Completeness

**Satisfied when:** The Behavior Delta section accounts for how the task changes
*existing* Ring-1 product behavior, grouped under Added / Modified / Removed. Every
**Modified** and **Removed** entry cites the Ring-1 artifact **and section** it changes
(e.g. `docs/product/use-cases/UC-3.md §main-flow`) — a bare behavior description with no
citation is a gap, because `/openup-sync-spec` relies on that citation to locate the
artifact to update. A genuinely greenfield task is explicitly marked `n/a — all Added`
rather than left blank. Listing a Modified/Removed behavior whose cited artifact does not
exist, or omitting a behavior the Structure/Requirements clearly change, is a gap.

## 11. Scenario Coverage

**Satisfied when:** Every numbered requirement carries at least one acceptance
scenario in `Given / When / Then` form, written with the bold markers
`**Given**` / `**When**` / `**Then**` (inline or split across lines). The
scenario must be *concrete* — naming the precondition, the action, and an
observable outcome — not a restatement of the requirement. A requirement with no
scenario, or a scenario missing one of the three clauses, is a gap. This is what
`scripts/openup-spec-scenarios.py check <plan>` enforces deterministically on the
`standard` and `full` tracks; a `quick`-track spec is exempt and this criterion
is marked `n/a (quick track)`.

## 12. Success Measure Falsifiability

**Satisfied when:** The `## Success Measures` section states **one falsifiable
expectation**: a named measure, a direction **and** magnitude ("weekly active
editors +10%", not "engagement improves"), a time window, the instrumentation
that will produce the number (an event, metric, or query — named concretely),
and a read-back date (absolute, or relative to release). Impact / engagement /
returned value are prompts, not required slots — one honest expectation
satisfies this. Gaps: a measure with no direction or magnitude; a vanity
expectation with no instrumentation ("users will like it"); instrumentation
that nothing in the Structure/Operations actually creates or already provides;
no read-back date. A `quick`-track spec — or genuinely unmeasurable internal
work — may write `n/a — <reason>`; an unargued `n/a`, or `n/a` on user-facing
`standard`/`full` work without a credible reason, is a gap.

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

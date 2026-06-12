---
name: openup-create-task-spec
description: Produce a REASONS-Canvas task spec from a roadmap line or feature description, ready for developer-role consumption
model: inherit
fit:
  great: [decomposing iteration-plan tasks into executable specs, formalizing ad-hoc work before coding starts]
  ok: [retrofitting specs onto in-progress work that lacks one]
  poor: [trivial doc-only edits (overhead exceeds value), exploratory spikes]
arguments:
  - name: task_id
    description: Task ID (T-XXX). Auto-allocates next free ID if not provided.
    required: false
  - name: title
    description: One-line task title. Required if task_id is new; reads from roadmap if existing.
    required: false
  - name: source
    description: "Where the task comes from: 'roadmap' (default), 'plan' (with plan path), or 'adhoc'."
    required: false
  - name: plan_ref
    description: "Path + section to the originating plan, e.g. 'docs/plans/2026-04-28-foo.md#3'"
    required: false
---

# Create Task Spec (REASONS Canvas)

This skill produces a per-task REASONS Canvas — the executable blueprint a
developer-role agent reads verbatim before generating code. It bridges the gap
between coarse roadmap lines / use cases and implementation.

## When to Use

Use this skill when:
- A roadmap task is about to enter implementation and has no spec yet.
- A plan item needs to be decomposed before assignment.
- Existing in-progress work needs a retroactive spec for handoff.

## When NOT to Use

Do NOT use this skill when:
- The change is a trivial typo / config tweak — use `/openup-quick-task`.
- The task spec already exists at `docs/changes/T-XXX/plan.md` — update via this
  skill (re-run), do not hand-edit (per the spec-first rule in `CLAUDE.openup.md`).
- You're at the *idea* stage and don't yet have requirements — run
  `/openup-plan-feature` first.

## Success Criteria

After this skill completes, ALL of these must be true:
- [ ] File exists at `docs/changes/T-XXX/plan.md` matching the template at
      `docs-eng-process/templates/task-spec.md`.
- [ ] Front-matter is fully populated (`id`, `title`, `status`, `priority`, `estimate`).
- [ ] Status is `ready` (not `proposed`) — the rubric grades to all-✅.
- [ ] All thirteen rubric criteria in `.claude/rubrics/task-spec-rubric.md` are ✅.
- [ ] Every requirement carries a Given/When/Then scenario (standard/full tracks):
      `python3 scripts/openup-spec-scenarios.py check docs/changes/T-XXX/plan.md` exits 0.
- [ ] `docs/roadmap.md` references the new task with a status entry.

## Process

### Load Project Config (context + rules — do this first)

Before drafting, layer in project-owned context and rules so the artifact reflects
facts and standards the framework can't infer. Full mechanism + precedence:
`docs-eng-process/project-config.md`.

1. If `docs/project-config.yaml` exists, read it. If it is **absent, skip this
   step** — framework defaults apply unchanged.
2. Inject `context:` into your working prompt wrapped in
   `<project-context>…</project-context>`, and `rules.<TYPE>` (if present) wrapped
   in `<project-rules>…</project-rules>`. For this skill `<TYPE>` is **`task-spec`**.
3. Project rules are **additive** to the framework rubric — precedence is
   **framework rubric → project rules → task-spec safeguards**. A project rule may
   add a criterion but may **not** waive a framework rubric criterion or a safeguard.
4. Before marking this artifact complete, confirm every injected `<project-rules>`
   item is satisfied alongside the framework rubric.

The skill is a two-round multi-role handoff. Use the token-efficiency protocol
(`.claude/CLAUDE.openup.md`): one orchestrator, compact handoffs, one specialist
per round.

### 1. Allocate Task ID and Read Context

- If `task_id` is missing, scan `docs/changes/*/plan.md` and
  `docs/changes/archive/*/plan.md` for the highest existing ID and allocate `T-{n+1}`.
- Read `docs/roadmap.md`, the originating plan (if `plan_ref` provided), and the
  use case(s) implicated.
- Generate path: `docs/changes/<task_id>/plan.md`; create the `docs/changes/<task_id>/`
  folder if it does not exist.
- Copy `docs-eng-process/templates/task-spec.md` to that path.

### 2. Ambiguity Gate — MANDATORY before drafting

Before any role drafts, list the open questions the request leaves unanswered
and classify each:

- **Blocking** — the answer would change scope, requirements, or acceptance
  criteria (you would build a different thing depending on it). **Stop.** Raise
  it via `/openup-request-input` (related_task = this task ID) and do not draft
  the affected sections until it is answered. Guessing here is the exact waste
  this gate exists to prevent.
- **Non-blocking** — a default is reasonable and the cost of being wrong is low.
  Pick the default and record it as a `**Assumption:**` line in the spec's
  **Analysis Context** (state the choice; note it is vetoable at review). Do not
  silently bake it into Requirements without naming it.

If there are no open questions, say so in one line and proceed. The point is an
explicit pass, not invented doubt.

> A blocking question silently guessed is rework discovered after code. A
> non-blocking question silently guessed is a decision no one got to veto. The
> gate converts both into something the requester can see and correct.

### 3. Round 1 — Analyst + Architect

Brief one analyst-role agent and one architect-role agent in compact form (max
6 bullets each). Inputs: roadmap line, plan section, use case excerpt.

- **Analyst** drafts: Story (INVEST), Analysis Context, Requirements (each with
  ≥1 `Given / When / Then` scenario), **Behavior Delta**, **Success Measures**,
  Entities.
- **Architect** drafts: Approach (3–5 lines), Structure (Add/Modify/Do-not-touch),
  **Rollout**, Safeguards (invariants, no-go zones, token budgets).

Both write directly to the task-spec file under their respective sections. They
do NOT inline rules from `conventions.md` or the architecture notebook —
references only.

For **Behavior Delta**, the analyst groups every change to *existing* Ring-1 product
behavior under Added / Modified / Removed, citing the Ring-1 artifact + section on each
Modified/Removed entry (`docs/product/use-cases/UC-3.md §main-flow`); a greenfield task
renders `n/a — all Added`. This list is what `/openup-sync-spec` consumes to know exactly
which Ring-1 artifacts a behavior change must back-propagate to — so a missing or vague
citation is a real gap, not a formality.

For **Success Measures**, the analyst writes a `## Success Measures` section
containing **one falsifiable expectation** for the feature:

> We expect **\<measure X\>** to move by **\<direction + magnitude Y\>** within
> **\<window Z\>** of release. Instrumentation: **\<the event / metric / query
> that will be read\>**. Read-back: **\<date or "Z after release"\>**.

Use *impact*, *engagement*, and *returned value* as **prompts** to find the right
measure — they are not three required slots; one honest, checkable expectation
beats three vanity metrics. A measure nobody will read back is worse than none:
on the `quick` track (or for genuinely unmeasurable internal work) write
`n/a — <reason>` instead, and the reason must survive review. Add the section
when drafting — the OpenUP-derived template at `docs-eng-process/templates/task-spec.md`
does **not** carry it (OpenUP artifacts are read-only; this section is a
claude-templates layer concern enforced by rubric criterion 12).

For **Rollout**, the architect writes a `## Rollout` section stating how the
change reaches users (KB framing: a feature flag is the modern, cheaper
implementation of OpenUP's *Develop Backout Plan* deployment task — toggling
off beats redeploying):

- **Flagged?** yes/no **with a reason** either way ("config-read at startup,
  flag adds no safety" is a fine reason for no).
- If flagged: **flag name**, **default state per environment** (use the names
  from `docs/project-config.yaml` `environments:` if defined, else
  local/production), **kill-switch behavior** (what turning it off does to
  in-flight users/data), and — **mandatory** — the named **flag-removal
  follow-up** (one line; `/openup-complete-task` enqueues it into the roadmap,
  because a flag is temporary debt, not a permanent switch).
- Not user-facing at all (pure refactor, internal tooling): `n/a — <reason>`.

Add the section when drafting — the OpenUP-derived template does **not** carry
it (read-only per the guardrail); rubric criterion 13 enforces it.

For **Requirements**, the analyst writes each numbered assertion *with* at least one
acceptance scenario in `Given / When / Then` form (bold markers `**Given**` / `**When**`
/ `**Then**`, inline or split across lines). The scenario must name a concrete
precondition, action, and observable outcome — drafting it is the test that the
requirement is unambiguous; if a clean scenario can't be written, the requirement is
still too vague. (Exempt on the `quick` track only.) `/openup-assess-completeness`
runs `scripts/openup-spec-scenarios.py` to enforce this deterministically.

### 4. Round 2 — Developer

Brief one developer-role agent with the partially-filled task spec.

- **Developer** drafts: Operations as a **checkbox list** (`- [ ] <step>`,
  ordered, 3–8 testable steps). Tag a step `- [ ] (role) …` only where it hands
  off to a different role hat (tester, analyst, …); untagged steps default to
  the `developer` hat. The first unchecked box is what `/openup-next` reads as
  the lane's `next_action` — so each step must be a concrete, executable action,
  not a heading. (Legacy numbered steps still parse but yield no `next_action`.)
- Developer also fills the Norms section with file references only (no copies).

### 5. Rubric Grading

Run `/openup-assess-completeness artifact: task-spec` (or apply
`.claude/rubrics/task-spec-rubric.md` inline). Grade each of 13 criteria. That
skill also runs `scripts/openup-spec-scenarios.py check docs/changes/T-XXX/plan.md`
— criterion 11 (Scenario Coverage) cannot be ✅ unless the script exits 0 (it is
auto-skipped on the `quick` track).

- All ✅ → set `status: ready` in front-matter.
- Any ❌ → keep `status: proposed`, list gaps for revision, loop back to the
  responsible role for fixes.

### 6. Roadmap Update

Add or update the roadmap row for this task ID with status `ready` and a link
to the spec file.

## Output

Returns:
- Path to the created task spec
- Rubric grade summary (criteria satisfied / gaps)
- Final status (`ready` or `proposed`)

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Template not found | Path moved | Verify `docs-eng-process/templates/task-spec.md` exists |
| Norms section duplicates conventions.md content | Specialist inlined rules | Replace inline text with a path reference |
| Operations step is multi-action | Step bundles "implement X and Y" | Split into separate steps |
| Estimate doesn't match Structure scope | Misjudged size | Either tighten Structure or revise estimate |

## References

- Template: `docs-eng-process/templates/task-spec.md`
- Rubric: `.claude/rubrics/task-spec-rubric.md`
- Format origin: Martin Fowler, "Structured Prompt-Driven Development"
- Index: `docs/changes/README.md`

## See Also

- [openup-create-iteration-plan](../create-iteration-plan/SKILL.md) — produces the roadmap lines this skill expands
- [openup-assess-completeness](../../openup-workflow/assess-completeness/SKILL.md) — rubric grading
- [openup-orchestrate](../../openup-orchestrate/SKILL.md) — runs the multi-role rounds

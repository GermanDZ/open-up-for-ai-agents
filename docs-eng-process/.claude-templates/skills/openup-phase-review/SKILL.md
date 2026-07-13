---
name: openup-phase-review
description: Run the phase milestone go/no-go — prepare derived evidence, pause for the human decision via an input-request, and record the milestone (never advance the phase itself)
model: inherit
fit:
  great: [end-of-phase milestone go/no-go, the loop's milestone-review pause, recording a stakeholder LCO/LCA/IOC/PR decision]
  ok: [a human mid-phase sanity check on completion criteria]
  poor: [within-iteration progress checks, single-task decisions, planning the next iteration (use /openup-start-iteration)]
arguments:
  - name: phase
    description: The phase to review (optional — derived from openup-lifecycle.py when omitted)
    required: false
---

# Phase Review (milestone go/no-go)

The **project-lifecycle** gate: at a phase boundary OpenUP pauses for a human
go/no-go (LCO → LCA → IOC → PR) before advancing. This skill prepares the
derived evidence, **pauses for that human decision** via the T-074 input-request
machinery, and — once answered — **records the milestone**. It is the loop's
`milestone-review` path.

> **It never advances a phase itself.** The source of truth for "phase advanced"
> is the milestone decision record in `docs/product/milestones/<phase>-<cycle>.md`
> (T-075); `openup-lifecycle.py status` derives the current phase *from* that
> record. This skill only prepares evidence, pauses, and writes the record the
> human decided — it does not set `phase` in state.

## When NOT to Use

- Just starting a phase → the phase skill (`/openup-inception` …).
- A lane finished / iteration to assess → `/openup-complete-task` /
  `/openup-assess-iteration` (assess-iteration is what *precedes* and triggers
  this at a phase boundary).
- The phase is clearly not done → keep delivering; `resolve` returns
  `plan-iteration`, not `milestone-review`, until the roadmap is drained and the
  exit criteria are met.

## Success Criteria

- [ ] The phase + cycle and per-criterion state are read from
      `openup-lifecycle.py status` (derived, not hand-judged).
- [ ] A milestone **input-request** carries the go/no-go to the human; the loop
      exits DONE ("milestone-review pending human input") while it is unanswered.
- [ ] On an answered **GO**, `docs/product/milestones/<phase>-<cycle>.md` is
      written; the phase is **not** set directly.
- [ ] On **NO-GO / CONDITIONAL**, the decision is recorded and the follow-on work
      is re-queued (Construction resumes in `cycle`+1 on NO-GO).
- [ ] The request is archived after it is processed.

## Process

### 1. Derive the phase, cycle, and criteria

```bash
python3 scripts/openup-lifecycle.py status --json   # {phase, cycle, criteria:[{id,desc,state}]}
```

Use `$ARGUMENTS[phase]` only to override the derived phase for a human-run
review. Each criterion's `state` is `met` / `unmet` / `human-judgment`; the
milestone this skill gates is exactly the `human-judgment` decision. If any
criterion is still `unmet`, say so — the phase is not actually ready and the loop
should keep delivering (this skill still records nothing).

### 2. Find (or create) the milestone input-request

Look for a milestone input-request for this phase+cycle under
`docs/input-requests/` (topic `milestone-<phase>-<cycle>`). Branch on its status:

- **None exists** → prepare the go/no-go evidence and raise it. Compose
  `/openup-request-input` with:
  - `title`: `Milestone go/no-go — <phase> (cycle <cycle>)`
  - `context`: the derived criteria states (step 1), plus the iteration's
    **Assessment** (the `## Assessment` section `/openup-assess-iteration` wrote:
    what was demoed, criteria met/unmet, work fed back) — the evidence the human
    needs to decide.
  - `questions`: one multiple-choice — `GO` (advance the phase) / `NO-GO` (not
    yet — resume this phase in the next cycle) / `CONDITIONAL` (advance once named
    conditions are met).
  - **No `related_task`** — a milestone is a phase-level decision, not a lane, so
    it suspends no change folder. The loop's DONE sentinel is what stops it.

  Then **stop**: the loop exits `DONE — milestone-review pending human input`. The
  next cycle re-reaches `milestone-review` (no record yet) and re-runs this skill,
  which now finds the request.

- **Pending** (created, not yet answered) → nothing to do; **stop** with the same
  `DONE — pending human input`. Do not write a record.

- **Answered** → go to step 3.

### 3. Record the answered decision (the only place a milestone record is written)

Read the human's answer. Write `docs/product/milestones/<phase>-<cycle>.md` with
frontmatter exactly as `openup-lifecycle.py` reads it — `phase`, `cycle` (int),
`milestone` (the phase's milestone name), `decision` (`GO` | `NO-GO` |
`CONDITIONAL`), `date`, `decided-by` (the respondent) — and the evidence/rationale
in the body:

```yaml
---
phase: <phase>
cycle: <cycle>
milestone: <e.g. Lifecycle Architecture Milestone>
decision: <GO | NO-GO | CONDITIONAL>
date: <YYYY-MM-DD>
decided-by: <respondent>
---

<one-paragraph rationale + link to the iteration Assessment and criteria states>
```

- **GO** → the record exists → `openup-lifecycle.py status` now derives the
  **next** phase. Nothing else to set.
- **NO-GO** → record it, and **re-queue** the phase's remaining work for
  `cycle`+1 (enqueue pending roadmap items / a `/openup-plan-feature` for the gap)
  so Construction resumes next cycle without pretending the product shipped. The
  derived phase stays put (only a GO advances it).
- **CONDITIONAL** → record it, and enqueue the named conditions as pending items;
  treat as not-yet-advanced until they are met and a GO is recorded.

Then archive the request (`status: processed` → `docs/input-requests/archive/`).

### 4. Report

State the decision recorded, the record path, the resulting derived phase
(unchanged on NO-GO/CONDITIONAL; advanced on GO), and any re-queued follow-on
work.

## Phase milestones (reference)

The KB milestone each phase gates — the derived `criteria` in step 1 evaluate
these mechanically; the human decision covers the `human-judgment` ones:

| Phase | Milestone | Human judgment covers |
|---|---|---|
| Inception | Lifecycle Objectives (LCO) | scope/vision agreed, business case viable |
| Elaboration | Lifecycle Architecture (LCA) | architecture validated by a tested skeleton |
| Construction | Initial Operational Capability (IOC) | stable enough for beta; alpha results accepted |
| Transition | Product Release (PR) | ready to release; stakeholder sign-off |

## References

- Milestone records + derived phase: `scripts/openup-lifecycle.py` (T-075)
- Phase Milestones concept: `docs-eng-process/openup-knowledge-base/practice-management/risk_value_lifecycle/guidances/concepts/phase-milestones.md`

## See Also

- [openup-assess-iteration](../assess-iteration/SKILL.md) — the iteration Assess Results that triggers this at a phase boundary.
- [openup-request-input](../request-input/SKILL.md) — the async pause machinery this composes.
- [openup-next](../next/SKILL.md) — the loop that reaches this via the `milestone-review` decision.

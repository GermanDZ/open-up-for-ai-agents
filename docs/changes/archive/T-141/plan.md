---
id: T-141
title: "Retrospective must verify and retire carried action items before authoring new ones"
status: done
priority: high
estimate: 1 session
plan: ""
depends-on: []
blocks: []
last-synced: ""
touches:
  - docs-eng-process/procedures/openup-retrospective.md
  - docs-eng-process/.claude-templates/skills/openup-retrospective/SKILL.md
  - docs-eng-process/skills-guide.md
---

# T-141 — Retrospective action items are never verified or retired

## Story

> **As an** agent or human choosing what to work on from `docs/project-status.md`
>   and the retrospective trail
> **I want** action items that have already been satisfied to be struck through
>   with evidence
> **So that** a resolved blocker cannot keep reading as a live, high-priority one
>   and push real work down the queue

INVEST check:
✅ Independent — a procedure-pack change to one skill; no dependency on T-145 or
T-146.
✅ Negotiable — *where* the verification lives (this skill vs a shared carried-
items helper) is explicitly left open; the spec fixes only that it happens, and
happens first.
✅ Valuable — a downstream project found three carried items, two of them its
highest-priority entries, that had been satisfied 2–11 days before still being
read as blocking.
✅ Estimable — `openup-retrospective.md` is 124 lines and was read in full; the
existing Action Items tables in `docs/iteration-retrospectives/` were read to fix
the strike-through format against real rows.
✅ Small — one new step plus edits to two existing steps.
✅ Testable — the acceptance is textual and mechanically checkable (the step
exists, it precedes step 6, it names the three verdicts and the evidence kinds);
the deterministic guards are `check-skills-guide.py --check` and
`render-skills-mirror.py --check`.

## Analysis Context

- **Domain.** `/openup-retrospective`'s authoring flow, and the append-only
  Action Items tables it produces in `docs/iteration-retrospectives/`.
- **Scope boundaries.** No script, no new validator, no state or gate. The items
  are hand-written prose in hand-written tables; a mechanical retirement pass is
  not possible without first imposing an item-id scheme, which would be a much
  larger change (and is the shape the carried open question points at). This task
  makes the retirement pass *happen and be evidenced*, not automated.
- **Definition of done.** `/openup-retrospective` cannot author a new Action
  Items table without first assigning every carried open item one of three
  verdicts, and satisfied/obsolete items are struck through **in place, with
  evidence**, never deleted.

**Confirmed this session, before writing**: `openup-retrospective.md` step 6
authors `**Action Items**: specific action, owner, due date, priority` and step 7
writes them into `docs/project-status.md` — and no step between 1 and 8 reads a
prior retrospective's items at all. Verified against the real trail: this repo's
`iteration-86-retrospective.md` has a 4-row Action Items table and no reference
to `iteration-77-retrospective.md`'s 5 items — and across all five retrospective
files, **not one row has ever been struck through** (15 open items reaching back
to iteration 9). The section is append-only in practice as well as in design, so
signal-to-noise degrades monotonically past a project's second retrospective —
exactly as reported downstream.

> **Assumption:** the retrospective *document that authored* an item is where it
> gets struck through, not the newest one. That keeps each retrospective an
> accurate record of its own items' fate, and means a reader who lands on an old
> retrospective from a link sees the resolution rather than a stale demand. The
> newest retrospective carries only a summary table of what it retired plus the
> items still open. *(Vetoable at review.)*

> **Assumption:** verification is a *judgment* step performed by the agent
> running the retrospective, using mechanical checks as its evidence — not a
> script. There is no item id, no machine-readable due date, and no link from an
> item to the artifact that would satisfy it, so nothing can be derived; imposing
> that structure is the larger change the carried open question names.
> *(Vetoable at review.)*

## Requirements

1. `/openup-retrospective` gains a verification step that runs **before** new
   action items are authored.
   - **Given** a reader following `openup-retrospective.md` in order, **When**
     they reach the step that creates the retrospective document (the step
     authoring `**Action Items**`), **Then** a carried-item verification step has
     already appeared earlier in the document, and that step states explicitly
     that it runs before new items are authored.

2. The step collects carried items from the durable trail, not from memory.
   - **Given** a project with several files in `docs/iteration-retrospectives/`,
     **When** the agent runs the verification step, **Then** the step directs it
     to read every prior retrospective's Action Items table (plus any carried
     list in `docs/project-status.md`) and treat every not-yet-struck row as
     open.

3. Every carried open item receives exactly one of three verdicts — **satisfied**,
   **obsolete**, or **still open** — each with a defined written form.
   - **Given** a carried item whose requested artifact now exists, **When** the
     agent grades it, **Then** the step's format has it struck through **in the
     retrospective that authored it** with a `satisfied <date> — <evidence>`
     annotation.
   - **Given** a carried item that is no longer wanted because a later decision
     superseded it, **When** the agent grades it, **Then** it is struck through
     as `obsolete <date> — <what superseded it>`, not silently dropped.

4. Evidence is mandatory and mechanically checkable; an assertion is not a
   verdict.
   - **Given** an agent about to mark an item satisfied, **When** it has no
     commit SHA, artifact path, task id, or command-and-observed-output to cite,
     **Then** the step requires the item to stay **open** rather than be struck
     through on belief.

5. Nothing is ever deleted, and still-open items carry forward with their
   original date so age is visible.
   - **Given** an item that has been open across three retrospectives, **When**
     the newest retrospective is authored, **Then** it appears in the carried
     table with its original authoring date preserved, and the step forbids
     authoring a new item that duplicates it (the carried one is extended or
     re-dated instead).

6. The retrospective document and the project-status update reflect the pass.
   - **Given** the step that creates the retrospective document, **When** a
     reader follows its section list, **Then** it includes a carried-action-items
     section covering what was retired (with evidence) and what remains open; and
     the project-status step mirrors only the **still-open** items.

7. The open design question — verification in this skill vs a shared carried-items
   helper reusable by other skills — is **carried, not resolved**.
   - **Given** a maintainer reading the new step, **When** they reach its end,
     **Then** a note states that the pass lives in this skill today, names the
     condition that would justify extracting a shared helper (a second skill
     needing the same pass), and does not pretend the question is settled.

## Behavior Delta

**Modified:**
- `/openup-retrospective`'s process — `docs-eng-process/procedures/openup-retrospective.md`
  (the governing artifact; the `.claude-templates/` SKILL.md and
  `docs-eng-process/skills-guide.md` are generated mirrors of it). Its step 6
  document-section list and step 7 project-status update both change; a new step
  is inserted ahead of both.

**Added:**
- The carried-item verification step itself.

**Removed:** none. No Ring-1 `docs/product/` artifact describes the
retrospective flow — the skill's own procedure file is the spec.

## Success Measures

We expect **zero unstruck action items in `docs/iteration-retrospectives/` that
are provably satisfied** at the end of the next retrospective — measured against
the concrete backlog this task inherits, counted at completion time: **15 open
items across 4 files, 0 struck** (iteration-9: 3, iteration-20: 3, iteration-77:
5, iteration-86: 4). The next run must give each of the 15 a verdict.
Instrumentation: rows under each `## Action Items` heading vs
`grep -c '~~' docs/iteration-retrospectives/*.md` — a countable before/after in
the repo itself. Read-back: the next `/openup-retrospective` run (retro counter
is at 3 of 5 after this branch's three lanes, so within two more completions).

## Rollout

**Flagged?** No — `n/a`. This is a procedure-pack (prose) change to a skill a
human invokes deliberately; there is no runtime surface to flag, and no deployed
code path changes. Backing it out is a revert of the pack file plus a mirror
regeneration.

## Entities

- **`openup-retrospective.md`** (modified) — `docs-eng-process/procedures/` —
  the pack file, the only hand-edited source
- **`openup-retrospective/SKILL.md`** (generated mirror) —
  `docs-eng-process/.claude-templates/skills/` — written by
  `render-skills-mirror.py --write`
- **`skills-guide.md`** (generated) — `docs-eng-process/` — written by
  `check-skills-guide.py --write`
- **Action Items tables** (read/annotated, not restructured) —
  `docs/iteration-retrospectives/*.md`

## Approach

Insert one step between metrics collection and document authoring, so the
ordering constraint ("before new items are authored") is enforced by position
rather than by a reminder. The step is a three-verdict disposition pass —
satisfied / obsolete / still open — over every not-yet-struck row in the prior
retrospectives, with strike-through applied **in the authoring document** so each
retrospective stays an accurate record of its own items. Evidence is mandatory
and is enumerated by kind (commit SHA, artifact path, task id, command +
observed output), with the explicit fallback that an item with no citable
evidence stays open — which is what stops the pass from degrading into a
rubber-stamp. Deletion is forbidden: the struck row plus its evidence is the only
thing that makes a wrong "satisfied" provable later. Step 6's section list and
step 7's project-status write are updated to consume the pass's output.

## Structure

**Add:**
- Step 5b (carried-item verification) in
  `docs-eng-process/procedures/openup-retrospective.md`

**Modify:**
- The same file's step 6 (document sections) and step 7 (project-status update),
  plus its Output section
- Generated mirrors: `docs-eng-process/.claude-templates/skills/openup-retrospective/SKILL.md`
  and `docs-eng-process/skills-guide.md` — regenerated, never hand-edited

**Do not touch:**
- The existing Action Items tables in `docs/iteration-retrospectives/` — the
  first *run* of the new step disposes of them; doing it here would be the
  retrospective's work done in the wrong lane, and would consume the evidence
  this task's own success measure is counted against
- Step 4b (Measure Read-Back) — a related but distinct loop-closing pass, already
  present and working
- `docs/project-status.md` — a derived shared view; this task changes only what
  the skill is instructed to write there

## Operations

- [x] Author step 5b in `docs-eng-process/procedures/openup-retrospective.md`:
      collect carried items → three verdicts → struck format with mandatory
      evidence → no deletion → carry-forward with original date
- [x] Add the evidence-kinds list and the explicit "no evidence ⇒ stays open"
      rule to that step
- [x] Add the carried open question (skill-local vs shared helper) as a closing
      note on the step
- [x] Update step 6's section list (carried-action-items section) and step 7's
      project-status instruction (still-open items only), plus the Output section
- [x] Regenerate the mirrors (`render-skills-mirror.py --write`,
      `check-skills-guide.py --write`, `sync-templates-to-claude.sh`)
- [x] (tester) Run the full test suite — the deterministic guards for this change
      are `test_render_skills_mirror` and `test_check_skills_guide`'s live-repo
      sync assertions

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, pre-commit housekeeping
- `.claude/CLAUDE.openup.md` — "edit the pack, not the skill mirror"
- The existing prose idiom of `openup-retrospective.md`'s other steps
  (numbered sub-steps, an explicit blocking statement where one applies)

## Safeguards

Invariants and limits that must hold:
- **Never delete an item.** Strike-through with evidence is the whole point; a
  silent deletion destroys exactly the trail that would let a wrong verdict be
  caught later.
- **No evidence ⇒ no retirement.** The step must not offer a "probably done"
  path; an item with nothing citable stays open.
- **Position, not exhortation.** The step has to sit physically before the
  authoring step — a note saying "remember to check old items" inside step 6 is
  the failure mode being fixed.
- **Pack-first.** Only `docs-eng-process/procedures/openup-retrospective.md` is
  hand-edited; both mirrors are regenerated by their scripts.
- **Reversibility.** Revert of the pack file plus a mirror regeneration; no data,
  no state, no migration.

## Verification

- The new step appears before step 6 in the rendered skill
  (`docs-eng-process/.claude-templates/skills/openup-retrospective/SKILL.md`)
- `python3 scripts/render-skills-mirror.py --check` and
  `python3 scripts/check-skills-guide.py --check` exit 0
- Full test suite green
- `python3 scripts/check-docs.py` and `python3 scripts/openup-fence.py check`
  exit 0
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅ or a
  clear gap call-out

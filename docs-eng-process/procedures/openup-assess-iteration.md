---
name: openup-assess-iteration
description: Run OpenUP Assess Results at iteration end — check evaluation criteria, demo only completed acceptance-tested work, feed discovered work back, and trigger the milestone review at a phase boundary
tier: authoring
capabilities: {required: [read_write_files, exec], optional: []}
fit:
  great: [closing a phase-aware iteration, the loop's convergence step, deciding whether a phase is ready for its milestone]
  ok: [a human manually assessing an iteration mid-program]
  poor: [single-task wrap-ups (use /openup-complete-task), the whole-project retro (use /openup-retrospective), planning the next iteration (use /openup-start-iteration)]
arguments:
  - name: iteration_id
    description: "The minted iteration to assess (e.g. C3). Optional — the board's assess-iteration decision supplies it; omit to assess the active iteration."
    required: false
---

# Assess Iteration (Assess Results)

**The back half of the iteration lifecycle (KB §3: Plan → Manage → Assess).**
This is what makes the loop *converge* instead of draining a queue: when a
phase-aware iteration's committed work items are all delivered, verify what was
achieved, demo only what is genuinely done, feed discovered work back, and — at
a phase boundary — hand off to the human milestone go/no-go.

The loop reaches this via `openup-board.py resolve` returning
`path: "assess-iteration"` (its `lane.task` is the iteration id, `lane.plan` the
iteration-plan instance). A human may also run it directly against an exhausted
iteration. It **records evidence and prepares a decision; it never advances a
phase itself** — that is the milestone review (§5).

## When NOT to Use

- A single lane finished → `/openup-complete-task` (this assesses the *whole
  iteration*, after all its lanes are complete).
- The iteration still has unfinished work items → keep working them (`resolve`
  would return `pick`/`resume`, not `assess-iteration`).
- Whole-project reflection / cadence retro → `/openup-retrospective` (this skill
  *composes* it for the retro half — see step 5 — rather than replacing it).

## Success Criteria

- [ ] The iteration-plan instance's **evaluation criteria** are each graded met /
      unmet against repo evidence.
- [ ] The demo scope lists **only completed, acceptance-tested** work items;
      anything incomplete or untested is excluded and re-queued.
- [ ] Discovered work / defects are enqueued as pending roadmap items.
- [ ] An **`## Assessment`** section is written into the iteration-plan instance
      (the assessed marker `resolve` reads to stop re-offering this path).
- [ ] If the Development Case marks the phase's exit criteria met, the next move
      named is `/openup-phase-review` — the phase is **not** advanced here.

## Process

### 1. Read the iteration-plan instance (the loop contract)

Open the instance named by the decision's `lane.plan` (or find the active
iteration's plan under `docs/iteration-plans/` / `docs/phases/`). Read its
**objectives**, **committed work-item ids** (`traces-from`, the `C3-NNN` lanes),
and **evaluation criteria**. This is the contract you assess against — not the
roadmap at large.

### 2. Check evaluation criteria against repo evidence

For each evaluation criterion, grade **met / unmet** from what is actually in the
repo — completed lanes (archived change folders, `status: done/verified`), passing
tests, landed artifacts. Do not grade from memory or intention; cite the evidence
(a test command, an archived folder, an artifact path). An unmet criterion is a
finding, not a failure to hide.

### 3. Demo only completed, acceptance-tested work

List the work items to **demo** — restricted to those that are both complete
**and** acceptance-tested (their spec's Verification / scenarios pass). Explicitly
**exclude** any committed item that is incomplete or not acceptance-tested, and
name why. Demoing half-done work is exactly what this gate prevents.

### 4. Feed discovered work and defects back

Anything surfaced during the iteration that is not yet captured — new
requirements, defects, the excluded-from-demo items from step 3 — is enqueued as
**pending roadmap items** so the next Plan Iteration picks them up. Use
`/openup-plan-feature` for a real new feature/requirement; a one-line pending
roadmap row for a small defect. Nothing important may live only in this session.

### 5. Write the `## Assessment` into the iteration-plan instance

Append an **`## Assessment`** section to the iteration-plan instance recording:
the criteria grades (met/unmet + evidence), the demo scope (what was demoed / what
was excluded and why), the fed-back items (step 4), and a one-line verdict
(objectives met? partially? carried forward?). This section is a **record of what
happened**, so appending it is sanctioned progress state (like ticking an
Operations box) — it does not need `/openup-create-iteration-plan` re-run unless
the iteration's *objectives or committed items* themselves changed. Its presence
is the assessed marker `resolve` keys on.

For the reflection half (what went well / to improve, cadence counter), compose
`/openup-retrospective` — do not duplicate its logic here.

### 6. Phase-end trigger — hand off to the human milestone (never advance it)

Read the derived lifecycle status and the Development Case:

```bash
python3 scripts/openup-lifecycle.py status --json   # phase, cycle, criteria
```

If the phase's exit criteria are met per the Development Case
(`docs/project-config.yaml` `process:` — the archetype's per-phase exit), the
next move is a **milestone go/no-go**: name `/openup-phase-review` (the loop
reaches it as `resolve`'s `milestone-review` path). **Do not** write a milestone
record or set `phase` here — that is the human decision `/openup-phase-review`
records. If the phase is not done, the next move is the next Plan Iteration.

## Output

A compact summary (≤6 bullets): the iteration id, criteria grades (n met / n
unmet), the demo scope (demoed vs excluded), the fed-back items, whether the
`## Assessment` section was written, and the next move (`/openup-phase-review` at
a phase boundary, else the next Plan Iteration).

## See Also

- [openup-next](../next/SKILL.md) — the loop that reaches this via the `assess-iteration` decision.
- [openup-phase-review](../phase-review/SKILL.md) — the human milestone go/no-go this hands off to at a phase boundary.
- [openup-retrospective](../retrospective/SKILL.md) — the reflection/cadence half this composes (does not replace).
- [openup-create-iteration-plan](../openup-artifacts/create-iteration-plan/SKILL.md) — authors the iteration-plan instance this assesses.
- `scripts/openup-lifecycle.py` — derived phase/cycle/criteria (T-075).
- `scripts/openup-board.py` — emits the `assess-iteration` / `milestone-review` decisions (T-078).

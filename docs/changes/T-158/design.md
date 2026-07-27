# T-158 — design decisions

## DD1 — Numbered `5c`, not `6a`

The spec first called the new step `6a`. Built as **`5c`**: it must sit beside 5b and
physically *ahead* of step 6, because 5b's own stated rationale is that "a reminder inside
the authoring step is exactly the failure mode being fixed". A `6a` label implies it runs
within or after authoring, contradicting the step's whole point. `plan.md` §Structure was
corrected before the edit landed.

The pairing is deliberate and now symmetric: **5b asks of a carried item *is this still
true?*, 5c asks of a new one *was it ever true?*** Same BLOCKING idiom, same
mechanical-check bias, same strike-with-evidence output.

## DD2 — No rubric file, no validator script

Rejected both, for the reason T-152 recorded for its own criterion: *"is this premise
real?"* is not mechanically parseable. A name-matcher would pass any phrasing while
answering nothing, and a `.claude/rubrics/retrospective-rubric.md` created for a single
criterion is abstraction ahead of demand — the same judgment the pack already applies to
its own carried-items helper ("until that second caller exists, a shared helper would be
abstraction ahead of demand").

What makes the check usable instead is the **failure-mode table**: three named modes, each
with a real citation (`A2`/T-142, `A3`/T-151, `T-153`+`T-147`). An author can recognise
their own item in the table; they cannot recognise it in an abstract instruction to
"verify the premise".

## DD3 — 20.2 retired obsolete, not implemented

The item asked for a **convention** (a checklist line in `/openup-start-iteration`) because
in iteration 20 no mechanism existed. In the 83 iterations since, both halves became
**enforcement**:

- *dependencies-first* — `openup-claims.py preflight` refuses an unmet dependency with exit
  3 (`scripts/openup-claims.py:53`), `openup-board.py` computes `depends_ok` and never
  surfaces a blocked lane, and the T-079 partitioner clusters on the `depends-on` graph;
- *explorations-first* — `/openup-explore` is now a first-class sanctioned mode.

Adding the checklist line would restate what the tooling already refuses to let you get
wrong. Owner decision 2026-07-27: retire obsolete. **Struck in place, not deleted** — this
item was re-derived from scratch twice (mis-recorded as handled by T-154, then resurrected
in iteration-103), and the record of *why* it is closed is what prevents a third.

## DD4 — 77.5 decided on the dangling-promise argument, not on scale

Iteration-77 framed this as a scale question ("may be an intentional `n/a` for this
project's scale"), and that framing is what left it open for 26 iterations — it has no
falsifiable answer. The deciding evidence was different and checkable: **five live
documents already referenced `docs/risk-list.md` as though it existed**
(`getting-started.md`, `QUICK-REFERENCE.md`, `skills-guide.md`, `USER-GUIDE.md`, and the
`/openup-retrospective` skill). Docs promising a missing artifact is the same defect class
T-157 had just fixed in the conflict-recovery recipe.

So step 4 of the retrospective needs no `n/a` branch: the file it reads is now there.
Verified by path check (req. 6), not by assertion.

## DD5 — The risk list is deliberately untyped

`risk-list` is **not** one of the v1 spine work-product types (`vision · requirement ·
work-item · iteration-plan · use-case · test-case · decision`), and `check-docs.py`
discovers instances *iff* frontmatter `type` is in the spine
(`scripts/check-docs.py:434-438`). So `docs/risk-list.md` is skipped by the validator.

Left untyped rather than labelled with a spine type to attract validation — that would
misdescribe the artifact to every consumer of the trace web. Requirement 5's
"`check-docs.py` exits 0 over it" is therefore satisfied *trivially* (the file is skipped,
the suite stays green); stating that plainly here so nobody later reads the green as
evidence the risk list was schema-checked.

## DD6 — Risks carry the evidence they were identified from

Every entry names its source (a retrospective line, a task id, an observed incident) and
states a **residual** after mitigation. Two are deliberately uncomfortable:

- **R3 (ceremony outgrows its value)** — residual **high**, with the honest note that
  nothing currently *removes* a gate and there is no measure on per-lane overhead. Writing
  "mitigated by tracks" would have been false comfort.
- **R5 (stale leases)** — residual **high, mechanism not understood**. Observed twice on
  2026-07-27: six dead claims blocked T-157, then **T-075's claim reappeared** with an
  mtime minutes old but `claimed_at` of 2026-07-13 and a repo-wide surface, blocking T-158.
  The same claim had already been released once during T-142/T-143. A claim file being
  *rewritten* for a completed task is unexplained and the reaper did not catch it. **Filed
  as a risk rather than silently worked around** — and it is the most concrete open defect
  on the list, a candidate for its own lane.

## DD7 — Verification (complete-task steps 1a / 1b)

### Step 1a — requirements graded against the diff

| # | Verdict | Evidence |
|---|---|---|
| 1 | ✅ | `### 5c … — BLOCKING` in the pack; "An item with no Evidence element is a gap and blocks the retrospective" |
| 2 | ✅ | Failure-mode table names all three modes with citations (`A2`/T-142, `A3`/T-151, `T-153`, `T-147`) |
| 3 | ✅ | Explicit scope block: "grades the `## Action Items` (new-only) table. Carried items are step 5b's business" |
| 4 | ✅ | `iteration-20-retrospective.md:49` struck in place with the four-mechanism evidence; iteration-103 row points at it |
| 5 | ✅ | `docs/risk-list.md` exists (7 risks); `check-docs.py` exits 0 — *trivially, see DD5*; `iteration-77-retrospective.md:51` struck `satisfied` |
| 6 | ✅ | Path check over all referencing docs: every reference resolves; `test -f docs/risk-list.md` true |
| 7 | ✅ | `## Open Action Items` rewritten; external items (`10.1`, `86.3`, `86.4`) and rider (`9.2`) byte-unchanged |
| 8 | ✅ | `render-skills-mirror.py --write` (1 updated) + `check-claude-sync` exit 0; new step present in both mirrors |

**Result: 8/8 ✅.** Full suite **884 passed, 1 skipped, 20 subtests** — identical to the
pre-lane baseline, as required for a lane that touches no script.

### Step 1b — success-measure instrumentation

`✅ instrumentation` — the measure reads the **Carried Action Items — retired this cycle**
table of this repo's retrospectives, which already records a verdict plus cited evidence
per item, cross-checked against the `## Action Items` table that authored them. **Read-back
environment: this repo** — action items are authored and disposed of here and nowhere else;
the instrument demonstrably pre-exists (iteration-98 and iteration-103 both carry the
table). **Read-back: the second retrospective after landing**, backstop **2026-10-31**.
Fewer than 5 new items authored by then must be reported as *insufficient data*.

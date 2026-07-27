---
id: T-158
title: "Retrospective action items must carry a verified premise — and close 20.2 / 77.5"
status: ready
priority: high
estimate: 1 session
plan: ""
depends-on: []
blocks: []
last-synced: ""
touches:
  - docs-eng-process/procedures/openup-retrospective.md
  - docs-eng-process/.claude-templates/skills/openup-retrospective/SKILL.md
  - docs/iteration-retrospectives/iteration-20-retrospective.md
  - docs/iteration-retrospectives/iteration-77-retrospective.md
  - docs/iteration-retrospectives/iteration-103-retrospective.md
  - docs/risk-list.md
  - docs/project-status.md
---

# T-158 — Retrospective action items must carry a verified premise — and close 20.2 / 77.5

## Story

> **As a** framework maintainer reading a retrospective's action items
> **I want** each new item to state the evidence that its problem is real, checked when it was written
> **So that** a promoted item is work worth doing rather than a plausible-sounding guess that a later lane has to spend a session disproving

INVEST check:
✅ Independent — one skill pack + three retrospectives + one new artifact · ✅ Negotiable — the shape of the evidence field is open · ✅ Valuable — 2 of 5 recent promotions were false and 2 more shrank · ✅ Estimable — one BLOCKING step + two strike-throughs + one skill run · ✅ Small · ✅ Testable — the pack either requires the field or it doesn't

## Analysis Context

- **Domain.** `/openup-retrospective`'s action-item authoring, and the two carried items (`20.2`, `77.5`) whose survival across 83 and 26 iterations is the evidence that the gap is real.
- **Scope boundaries.** This does NOT add a retrospective rubric (none exists, and one criterion does not justify inventing the file), does NOT change step 5b's carried-item retirement pass (which already works), and does NOT sweep other carried items — `10.1`, `86.3`, `86.4` are external and `9.2` is a deliberate opportunistic rider.
- **Definition of done.** `/openup-retrospective` refuses to author an action item without a verified premise; `20.2` and `77.5` are each closed with a recorded decision in their authoring retrospective; `docs/risk-list.md` exists.

**Premise for B2, verified before drafting (applying B2's own rule to B2).** Of the five action items iteration-98 filed and promoted: **A2 was obsolete** (T-142 had already shipped the fix — `docs/status-notes/`, iteration 100) and **A3 was wrong** (T-151 disproved it in an isolated fixture and labelled it WRONG, not "done"); **T-153's scope shrank** (two of its three sub-items already had real coverage; the genuine gap was none of the three) and **T-147's** owner noted it did not reproduce locally. So 2 false + 2 shrunk of 5, exactly as the iteration-103 retrospective claims. `docs-eng-process/procedures/openup-retrospective.md` has a **BLOCKING step 5b** for *retiring carried* items but nothing at all validating a **new** item's premise — step 6 asks only for "specific action, owner, due date, priority".

**Premise for 77.5, verified.** No risk-list instance exists anywhere under `docs/` (`find docs -iname "*risk*"` returns nothing), yet `docs-eng-process/getting-started.md`, `QUICK-REFERENCE.md`, `skills-guide.md`, `USER-GUIDE.md` and the retrospective skill all reference `docs/risk-list.md` as though it does. Live docs promising a missing artifact is the same defect class T-157 just fixed. **Owner decision (2026-07-27): instantiate it.**

**Premise for 20.2 — measured, and it has shrunk to nothing.** Its iteration-98 wording was "Dependency-ordering convention (deps/explorations before implementation)", evidence "No checklist item added to `/openup-start-iteration`". In the 83 iterations since, both halves acquired machinery: task-dependency ordering is *enforced*, not merely conventional (`openup-claims.py preflight` refuses with exit 3 on an unmet dependency; `openup-board.py` computes `depends_ok` and will not surface a blocked lane; the T-079 partitioner clusters on the `depends-on` graph), and "explorations before implementation" became `/openup-explore`, a sanctioned first-class mode. **Owner decision (2026-07-27): retire as obsolete, struck in place with this evidence.**

> **Assumption:** The premise field is added to the **pack** (`docs-eng-process/procedures/openup-retrospective.md`) and the rendered mirror, not to a new retrospective rubric — no such rubric exists, and creating one for a single criterion is abstraction ahead of demand (the same reasoning the pack already applies to its own carried-items helper). *(Vetoable at review.)*

> **Assumption:** The strike-throughs land in each item's **authoring** retrospective (iteration-20, iteration-77), per the rule already stated in step 5b — "the strike lands in the authoring retrospective, so a reader arriving from an old link sees the resolution instead of a stale demand". The iteration-103 carried table gets a pointer, not a duplicate resolution. *(Vetoable at review.)*

> **Assumption:** `docs/project-status.md`'s `## Open Action Items` is **authored** content, not derived — `sync-status.py` regenerates only the header fields and `## Notes` — so editing it here is in-bounds and is not a shared-view hand-edit. *(Vetoable at review.)*

## Requirements

1. `/openup-retrospective`'s action-item authoring requires each **new** item to carry a **verified premise**: a one-line statement of the evidence that the problem is real, and where it was checked.
   - **Given** the pack's `## Action Items` authoring step, **When** an author drafts a new item with an action, owner, priority and due date but no evidence line, **Then** the step names that as a gap and blocks the item, in the same BLOCKING idiom step 5b already uses.

2. The step names the specific failure modes it exists to catch, so the check is applicable rather than aspirational.
   - **Given** the new step's text, **When** a reader looks for what counts as an unverified premise, **Then** it names at least the two observed modes — *already fixed* (A2/T-142) and *disproved on inspection* (A3/T-151) — plus *shrunk on measurement* (T-153/T-147), each with its citation.

3. The check applies only to items the retrospective **authors**; it does not re-open carried items, which step 5b already disposes of.
   - **Given** a retrospective carrying open items from a prior cycle, **When** the new step runs, **Then** it grades only the `## Action Items` (new-only) table and leaves the carried tables to step 5b.

4. `20.2` is retired as obsolete, struck in place in its authoring retrospective with the disproving evidence, not deleted.
   - **Given** `docs/iteration-retrospectives/iteration-20-retrospective.md`, **When** the retirement lands, **Then** item `20.2` is struck through **in place** with the evidence (preflight exit 3, board `depends_ok`, T-079 partitioner, `/openup-explore`) and labelled `obsolete`, and the iteration-103 carried table points at that resolution instead of restating it.

5. `77.5` is closed by instantiating the artifact: `docs/risk-list.md` exists, authored through `/openup-create-risk-list` so its rubric is applied.
   - **Given** no risk-list instance exists anywhere under `docs/`, **When** the task completes, **Then** `docs/risk-list.md` exists, `python3 scripts/check-docs.py` exits 0 over it, and `77.5` is struck in `iteration-77-retrospective.md` as `satisfied` citing the file.

6. The live references to `docs/risk-list.md` resolve — no doc promises an artifact that does not exist.
   - **Given** `docs-eng-process/getting-started.md`, `QUICK-REFERENCE.md`, `skills-guide.md` and `USER-GUIDE.md` all name `docs/risk-list.md`, **When** the task completes, **Then** each of those references resolves to the real file (verified by path check, not by assertion).

7. `docs/project-status.md`'s `## Open Action Items` reflects the new disposition without touching any derived region.
   - **Given** the section listing B1/B2/B3 and the two open items, **When** the task completes, **Then** B1, B2, B3, `20.2` and `77.5` are recorded closed with their outcomes, the remaining external items (`10.1`, `86.3`, `86.4`) and the rider (`9.2`) are unchanged, and every line above `## Open Action Items` plus the whole `## Notes` body is byte-identical apart from what `sync-status.py` itself rewrites.

8. The rendered skill mirror matches the pack — the edit is made in the pack, never in the mirror.
   - **Given** the pack edit, **When** `render-skills-mirror.py --write` and `sync-templates-to-claude.sh` run, **Then** `check-claude-sync` exits 0 and `.claude/skills/openup-retrospective/SKILL.md` carries the new step.

## Behavior Delta

**Added** — behavior that did not exist before:
- A BLOCKING premise-verification requirement on newly-authored retrospective action items.
- `docs/risk-list.md` as a Ring-1 work-product instance for this project.

**Modified** — behavior that changes; cited artifact + section:
- Action-item authoring gains a required element — `docs-eng-process/procedures/openup-retrospective.md §Create Retrospective Document` (the `## Action Items` bullet) and its rendered mirror.
- `20.2` moves from *open* to *retired (obsolete)* — `docs/iteration-retrospectives/iteration-20-retrospective.md §Action Items`.
- `77.5` moves from *open* to *retired (satisfied)* — `docs/iteration-retrospectives/iteration-77-retrospective.md §Action Items`.

**Removed** — none. No existing step, gate, or skill invocation is removed; step 5b is untouched.

## Entities

- **Retrospective pack** (modified) — `docs-eng-process/procedures/openup-retrospective.md`; the single source, per the edit-the-pack-not-the-mirror rule.
- **Rendered mirror** (modified, generated) — `docs-eng-process/.claude-templates/skills/openup-retrospective/SKILL.md`.
- **Step 5b** (read-only) — the existing BLOCKING carried-item pass whose idiom the new step mirrors.
- **Risk list** (new) — `docs/risk-list.md`, authored via `/openup-create-risk-list`.
- **Authoring retrospectives** (modified) — `iteration-20-retrospective.md`, `iteration-77-retrospective.md`; `iteration-103-retrospective.md` gets pointers only.
- **Open action items** (modified) — `docs/project-status.md` `## Open Action Items` (authored, not derived).

## Approach

Mirror step 5b rather than invent a new idiom: it is already a BLOCKING pass over action items with a verdict-plus-evidence shape, so the new check is its forward-looking twin — 5b asks *"is this carried item still true?"*, the new step asks *"was this new item ever true?"*. The requirement is a single required element on each authored item (evidence + where it was checked), described with the three observed failure modes so an author can recognise them, deliberately **not** a new rubric file or a validator script: the question *"is this premise real?"* is not mechanically parseable, and a name-matcher would pass any phrasing while answering nothing — exactly the reasoning T-152 recorded for its own criterion. The two carried items are then closed the way T-151 closed its pair: struck in place in the authoring retrospective with the disproving evidence, so a reader arriving from an old link sees the resolution rather than a stale demand.

## Structure

**Add:**
- `docs/risk-list.md` — via `/openup-create-risk-list`.
- A `### 6a. Verify New Action Items' Premises — BLOCKING` step in the retrospective pack.

**Modify:**
- `docs-eng-process/procedures/openup-retrospective.md` — the new step + the `## Action Items` bullet in §Create Retrospective Document.
- `docs-eng-process/.claude-templates/skills/openup-retrospective/SKILL.md` — regenerated, never hand-edited.
- `docs/iteration-retrospectives/iteration-20-retrospective.md` — strike `20.2` obsolete.
- `docs/iteration-retrospectives/iteration-77-retrospective.md` — strike `77.5` satisfied.
- `docs/iteration-retrospectives/iteration-103-retrospective.md` — carried table points at both resolutions.
- `docs/project-status.md` — `## Open Action Items` disposition.

**Do not touch:**
- Step 5b of the pack — it already works; the new step is additive beside it, and editing it risks the carried-item pass that is currently the only thing pruning debt.
- `.claude/rubrics/` — no retrospective rubric exists; creating one for a single criterion is abstraction ahead of demand.
- The other carried items (`10.1`, `86.3`, `86.4`, `9.2`) — external or deliberately opportunistic; closing them is not this lane's scope.
- `scripts/tests/test_t011_retro.py` — tests the retro *cadence counter*, unrelated to action-item authoring; a failure here would be a real regression.
- `docs/roadmap.md` Status cells and `docs/project-status.md`'s header + `## Notes` — derived; `sync-status.py` owns them.

## Operations

- [ ] Add the `### 6a. Verify New Action Items' Premises — BLOCKING` step to the retrospective **pack**, mirroring step 5b's idiom, naming the three observed failure modes with citations; confirm it grades only the new-only `## Action Items` table (req. 3).
- [ ] Update the `## Action Items` bullet in the pack's §Create Retrospective Document so the required element is visible where the table is described.
- [ ] Re-render the mirror (`render-skills-mirror.py --write`) and sync (`sync-templates-to-claude.sh`); confirm `check-claude-sync` exits 0 and the new step is present in `.claude/skills/` (req. 8).
- [ ] Strike `20.2` in place in `iteration-20-retrospective.md` as **obsolete**, citing preflight exit 3, board `depends_ok`, the T-079 partitioner and `/openup-explore`; add the pointer in the iteration-103 carried table (req. 4).
- [ ] (analyst) Author `docs/risk-list.md` through `/openup-create-risk-list` so its rubric is applied; confirm `check-docs.py` exits 0 over it (req. 5).
- [ ] Strike `77.5` in place in `iteration-77-retrospective.md` as **satisfied**, citing the new file; then verify every live reference to `docs/risk-list.md` resolves by path check, not assertion (reqs. 5, 6).
- [ ] Update `## Open Action Items` in `docs/project-status.md` with the B1/B2/B3 + `20.2`/`77.5` disposition, leaving the external items and the rider untouched (req. 7).
- [ ] (tester) Run the full `scripts/tests/` suite and confirm the pre-existing count still passes — this lane changes no script, so any delta is a real regression.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions.
- `docs-eng-process/procedure-frontmatter.md` — the edit-the-pack-not-the-mirror rule.
- `docs-eng-process/parallel-lanes.md` — which files are derived views.

## Safeguards

- **Edit the pack, not the mirror.** `.claude-templates/skills/` and `.claude/skills/` are generated; hand-edits get clobbered by the next render.
- **Strike, never delete.** A retired item stays auditable in place with its evidence (T-141). Deleting `20.2` would destroy the record proving it was disposed of rather than forgotten — and re-derivation from scratch is exactly what happened to it twice already.
- **No new rubric file, no validator script.** "Is this premise real?" is graded prose; a parser would pass any phrasing while answering nothing.
- **No-go zone: step 5b** and the derived regions of the two shared views.
- **Reversibility.** Every change is a doc edit plus one new file; revert the commit.
- **Size budget.** No script changes at all — if this lane finds itself editing `scripts/`, the scope was misread.

## Success Measures

We expect the share of newly-authored retrospective action items that are later found **false or materially shrunk** to fall from **4 of 5** (iteration-98's promoted set: A2 obsolete, A3 wrong, T-153 shrunk, T-147 shrunk) to **at most 1 of the next 5** authored under the new step. Instrumentation: the **Carried Action Items — retired this cycle** table of this repo's retrospectives, which already records a verdict (`satisfied` / `obsolete`) plus cited evidence per item, cross-checked against the `## Action Items` table that authored them. Read-back environment: **this repo** — action items are authored and disposed of here and nowhere else. Read-back: **the second retrospective after landing** (absolute backstop **2026-10-31**).

If fewer than 5 new action items have been authored by the read-back date, report the count as *insufficient data* rather than declaring the measure met — a low denominator is not evidence the check works.

## Rollout

`n/a — not user-facing.` The change is a required element in a process document plus one new project artifact; there is no runtime code path, so no flag applies and there is nothing to toggle off. It reaches agents through the rendered skill mirror at the next `sync-templates-to-claude.sh`, and downstream consumers via their existing `sync-from-framework.sh`. No flag-removal follow-up is owed.

## Verification

- `bash scripts/check-claude-sync.sh` exits 0 and `.claude/skills/openup-retrospective/SKILL.md` contains the new step.
- `python3 scripts/check-docs.py` exits 0 (covers the new `docs/risk-list.md` instance).
- `test -f docs/risk-list.md` and each live reference to it resolves.
- `python3 -m pytest scripts/tests/ -q` — pre-existing count unchanged (no script touched).
- `python3 scripts/openup-fence.py check` exits 0.
- Grade the final artifact against `.claude/rubrics/task-spec-rubric.md`.

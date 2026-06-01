# SPDD Evaluation — `2026-05-13-openspec-ideas-for-openup.md`

**Evaluated:** 2026-05-13
**Method:** SPDD self-application — grade the plan against the same eight
dimensions used on `2026-04-28-spdd-evaluation.md`.

## Per-Dimension Grading

| Dimension | Grade | Notes |
|---|---|---|
| **Abstraction first** | ✅ | Plan separates "OpenUP already covers better" from "real gaps" *before* proposing solutions. Resists importing OpenSpec's artifact set verbatim and its forkable-schema abstraction. |
| **Alignment** | ✅ | Six "Explicitly Out of Scope" items reject plausible-but-wrong moves (artifact rename, npm CLI, schema system, tool-portability, telemetry, implicit quality model). Each rejection has a stated reason. |
| **Requirements clarity** | ✅ | Each idea has: stated gap, concrete proposal, files-touched list, and value/effort rating. |
| **Operations testability** | ✅ | Per-item "Verification" section names a specific reproducible check (re-edit dependency → STALE; add fake rule → injected; etc.). Stronger than the 2026-04-28 plan's ⚠️ on this dimension. |
| **Norms** | ✅ | Plan respects OpenUP idiom (rubrics framework-owned, project rules additive; folders convention-not-enforcement; advisory readiness, not blocking). Points at existing files for inheritance. |
| **Safeguards** | ✅ | Per-item "Out of scope here" guards (e.g. #1 stays advisory; #2 starts unvalidated; #3 doesn't migrate existing files; #5 closes a loophole rather than opening one). Filled in the per-item ⚠️ that the prior plan had to address in task specs. |
| **Iterative review** | ✅ | Sequencing #1 → #2 → … defers #4 behind #3 and explicitly ties #1 to T-002's un-deferral. YAGNI guards in place (schemas, telemetry, CLI rejected outright). |
| **Suitability fit** | ✅ | OpenUP framework dev remains high-fit for SPDD-style planning. The plan applies SPDD to itself (gap-first, alignment-first, out-of-scope-explicit). |

**Overall:** SPDD-grade at the plan level. No ⚠️ requiring downstream task
specs to patch; verification is per-item testable.

## Differences from `2026-04-28-spdd-evaluation.md`

- The 2026-04-28 evaluation flagged two ⚠️s (Operations testability,
  Safeguards) that had to be addressed in the per-task specs (T-001..T-003).
  This plan absorbs both lessons up-front: each item has a per-item Verification
  block and a per-item "Out of scope here" safeguard.
- Item-level value/effort ratings (HIGH / MED / LOW) are made explicit, which
  makes the sequencing rationale auditable.

## Status of Plan Items

| Item | Status | Tracker |
|---|---|---|
| #1 Readiness DAG | `proposed` | (no task yet — create when scheduled) |
| #2 `project-config.yaml` | `proposed` | (no task yet) |
| #3 Per-task folders | `proposed` | (no task yet) |
| #4 Archive flow | `proposed` (gated on #3) | (no task yet) |
| #5 Explore mode | `proposed` | (no task yet) |

No tasks are created at this stage. Per the token-efficiency protocol, task
decomposition belongs to a fresh session when an item is scheduled for
implementation. The roadmap entry tracks plan-level status only.

## Relationship to the 2026-04-28 SPDD Plan

- **Independent:** #1, #2, #3, #4.
- **Complementary to SPDD #2 ("fix-spec-first"):** OpenSpec #5 (explore mode)
  tells users where *pre-spec* work lives, closing a loophole the SPDD rule
  exposes.
- **Precondition for SPDD T-002 (`/openup-sync-spec`):** OpenSpec #1
  (readiness DAG) provides the dependency metadata sync needs. Do #1 before
  un-deferring T-002.

## Why Not Implement Anything Now

- The user asked for the analysis doc, not implementation.
- Per the token-efficiency protocol, this session has produced one
  deliverable (the plan + evaluation) and should close. Implementation belongs
  to a future iteration when an item is prioritised.
- Items #2 and #5 are the lowest-risk / highest-value pair (analogous to SPDD
  items #2 and #5 in the 2026-04-28 plan) and are the natural first picks.

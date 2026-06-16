# Iteration 20 Retrospective

**Iteration**: 20  
**Date Range**: 2026-06-12 to 2026-06-16  
**Goal**: T-044 — Remote-aware claim preflight for `openup-next` (Option B: branch-as-claim) — cross-machine duplicate-start early-warning + counter  
**Participant**: Claude Opus 4.8 (solo, standard track, in-place)  
**Phase**: construction  
**Status**: completed  

## Summary

**Iteration 20 successfully delivered T-044**, closing the cross-machine coordination gap revealed during TallyFox's duplicate-PR incident (#462 vs #463 for T-1102). The local lease (`openup-claims.py`) lives under `.git/` and is never pushed, so parallel agents running `openup-next` on separate clones have no way to see each other's claims — they only discover the duplicate at PR merge time.

T-044 implements **Option B (branch-as-claim)** from the exploration (2026-06-16-cross-machine-claim-coordination.md): a remote-check preflight that asks `origin` if another branch already encodes the task, and refuses the start (exit 9) if so. It's **advisory and fail-open** — no remote, unreachable, or auth errors exit 0 — so offline and solo work are never blocked. The hard gate stays the local lease + PR review. The *key innovation* is the `duplicate_start_blocked` counter: every refusal logs a clock-stamped event. That counter is the evidence that decides whether the heavier atomic `refs/openup/claims/*` ref-lock (Option A) ever gets built — ship cheap, measure, escalate on evidence.

**Shipped**: PR #35 merged to main.  
**Tests**: 5 new hermetic local-bare-remote tests; 36/36 claims suite green.  
**Gating**: write-fence ✓, check-docs ✓, all requirements (R1–R5) graded ✅.

## What Went Well

1. **Orthogonal design** — `remote-check` is purely advisory; the hard gate remains the local lease + human review. This avoided the temptation to build Option A upfront (which would have been over-engineered before seeing real parallel work).
2. **Measurement-first** — the counter is baked in from day 1, not retrofitted. Any team running parallel `openup-next` will generate events; the retrospective can then cite data, not opinion, when deciding whether to build the lock.
3. **Rapid execution** — from exploration disposition to shipped in one iteration, orthogonal to T-043 (scope note + exploration), no scope creep. Deliverable is complete and merge-ready.
4. **Hermetic testing** — local-bare-remote test setup makes cross-machine behavior testable without a real multi-clone environment. All five scenarios (duplicate, no-match, self-branch exclusion, token accuracy, missing remote) are covered and deterministic.

## What to Improve

1. **T-043 dangling ref** — T-044 shipped with a link to `docs/explorations/2026-06-16-cross-machine-claim-coordination.md` and the scope note in `parallel-lanes.md`, but **both files are still on the unmerged `docs/T-043-parallelism-scope-note` branch**. The branch should have been merged **before** T-044 (or T-044 should have been reordered to follow it). The link is not broken (GitHub renders it fine), but the file isn't on main, violating the "docs on main" assumption. **Action: merge T-043 immediately.**

2. **Iteration timing** — I started T-044 before finishing T-043. Both were in-scope for the cross-machine coordination investigation, but T-043 (exploration + scope note) should have been completed and merged first to establish the foundation. Going forward, order tasks such that references resolve on main before work that cites them ships.

3. **Retro counter at 6** — this retrospective was triggered by the counter hitting the threshold (5 completed tasks). With only T-044 in this iteration, the count was incremented to 6 after completion, which is correct, but the threshold design expects multiple tasks per iteration. Iteration 20 was a *focused* one (one deep task), not a *typical* one. Consider whether the cadence (5 tasks → retrospective) is right for single-deep-task iterations vs multi-feature ones.

## Measure Read-Back

**T-044 Success Measure**: "Falsifiable expectation: once shipped, `duplicate_start_blocked` events in the run log directly count how often two clones target the same task."

- **Expectation**: the counter will be non-zero if parallel work actually happens, and zero if solo work is the norm.
- **Actual**: [awaiting real-world parallel work to generate events; tool just shipped, no events yet]
- **Verdict**: instrumentation deployed and ready. **Read-back date: revisit at the next retrospective (iteration 21+) with parallel-work activity.**
- **Interpretation**: If the count remains zero over the next 1-2 iterations of actual parallel work, Option A (ref-lock) stays dropped. If events accumulate, the count is the evidence to build Option A. This is the "measure to decide" pattern working as designed.

## Action Items

| Item | Owner | Due | Priority |
|---|---|---|---|
| **Merge T-043 to resolve dangling refs** — branch `docs/T-043-parallelism-scope-note` contains the scope note (parallel-lanes.md) and exploration (2026-06-16-cross-machine-claim-coordination.md) that T-044 now links to. Merge before next task ships. | framework-pm | 2026-06-17 | high |
| **Review iteration 20 timing for T-043/T-044** — reflect on whether ordering dependencies-first (scope note → implementation) is a convention worth enforcing; consider a checklist item for `/openup-start-iteration` ("do dependencies, explorationsit on main?"). | retrospective-scribe | 2026-06-20 | medium |
| **Monitor `duplicate_start_blocked` counter** — will only be meaningful once multiple clones are in flight in parallel. Set a reminder to review the counter at iteration 22+ retrospective. | product-manager | at-iteration-22 | medium |

## Metrics

- **Iteration span**: 4 days (2026-06-12 to 2026-06-16)
- **Tasks completed**: 1 (T-044)
- **Completion rate**: 100% (1 of 1 planned)
- **Test coverage**: 5 new tests added; 36/36 claims suite green (pre-existing 1-suite failure in test_docs_index unrelated)
- **Commits**: 3 main commits (feat + grade + archive)
- **Lines of implementation**: openup-claims.py + 140 lines (remote-check subcommand + matcher); skills updated; parallel-work.md + script-cli-reference.md documented
- **PR**: #35 (merged)

## Next Iteration Considerations

1. **T-043 must merge first** — before any new tasks ship that might link to the exploration or scope note.
2. **Start real parallel work** — the `duplicate_start_blocked` counter only matters if multiple clones run `openup-next` concurrently. Consider setting up a test scenario (two clones, two agents, both pick the same task) to validate the warning path and generate the first counter events.
3. **Retro cadence mismatch** — at 1 task per 4 days, the "5 tasks = trigger retro" cadence may fire too often on deep/focused iterations. No change needed yet, but monitor whether iterations 21–22 match the "1 deep task" or "3–5 feature tasks" pattern. The cadence is data-driven; let it prove itself.
4. **Product-manager role check** — iteration 20 had no Value re-ranking step (no prior measures due for read-back). As the retrospective measure-read-back loop matures, upcoming iterations will have read-back verdicts to inform re-ranking. Confirm the product-manager role understands the handoff.

---

**Retrospective completed**: 2026-06-16T14:30:00Z  
**Retro counter reset**: ready for next 5-task cadence to begin.

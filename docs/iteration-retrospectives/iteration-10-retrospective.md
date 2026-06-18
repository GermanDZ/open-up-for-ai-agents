# Iteration 10 Retrospective (Cadence 2)

**Dates:** 2026-06-12 to 2026-06-18  
**Iteration Range:** Iterations 23–24 (T-048, T-049, T-052) — three tasks, three days  
**Phase:** construction  
**Participants:** Claude (solo agent, no team)  

## Summary

A short, focused maintenance cycle addressing three downstream bugs discovered in the live parallel-lane framework:

1. **T-048**: A false dependency block where archived plans weren't deferred to the roadmap status (affecting multiple live dependent tasks), plus worktree-promote board-blindness (lanes created in a fresh worktree were invisible to the board until committed).
2. **T-049**: Board surface gaps for active leases on unmerged branches (cross-machine duplicate detection was advisory; the board should show the **existing** lease holder so parallel lanes see why a task is already claimed elsewhere).
3. **T-052**: Framework syncs left tracked CLIs uncommitted, triggering `on-stop.py`'s whole-tree dirty guard in the next lane session — observed looping to the override cap in tallyfox-app.

All three were **high-impact, low-risk fixes**: precise root causes (archived-status defer, board source of truth, sync self-commit), deterministic solutions (frontmatter logic, commit the spec folder, partial-commit the manifest CLIs), and comprehensive testing (6 + 11 + 3 new tests respectively).

## What Went Well

### Root-Cause Precision
Each task started with a clear bug report from the field (T-048 from es-invoices audit, T-049/T-052 from the tallyfox on-stop loop), and the investigation isolated a single architectural issue, not a symptom. E.g., T-048 part A wasn't "archived plans break dependencies" but specifically "`dep_satisfied` logic consulted plan.md `status:` instead of deferring to the roadmap" — pinpointing the exact line to rewrite.

### High-Leverage Fixes
All three unblock common patterns:
- T-048: **any dependent task** blocked by a false archived-status upstream.
- T-049: **any cross-machine parallel session** now sees the lease holder, not just a failed preflight message.
- T-052: **every project syncing the framework** on a live lane no longer loops on-stop.

### Integration Testing
T-048 added 6 hermetic tests to the claims suite; T-049 and T-052 each added 11 and 3 integration tests respectively. All three test the *real* scenario (not mocked), reducing the risk of edge-case regressions — especially T-049 (multi-branch board construction) and T-052 (git operations in a scratch repo).

### Single-Agent Efficiency
No team, no elaborate handoffs. Each task was analyzed, implemented, tested, and completed by one agent assuming roles as needed (analyst → developer → tester). Spec authoring was minimal (each task already had a clear spec from T-051/T-050 readiness).

## What to Improve

### T-048 Archive-Status Migration
The fix was sound, but **implementing a one-shot data migration (`openup-claims.py migrate-archived-status`) was necessary** to repair the existing stale corpus. A project/consumer applying the framework will have no stale data, but the framework itself had to backfill — leaving the migration as a manual optional step for downstream repos. **Lessons:**
- When a logic error affects historical data, consider a repair path as part of the fix (not just "new code is correct").
- Document the migration clearly (it's idempotent, `--dry-run`-safe) so maintainers know it's safe to run.

### Board-Elsewhere Surface Completeness (T-049)
The fix surfaces leases on unmerged branches — **but assumes the branch name is derivable from the lease**. If a worktree is deleted or the branch is in an atypical state, the board won't show it. This is acceptable (the lease still blocks, the preflight refuses), but **a more robust signal (e.g. reading the lease file directly for status, not inferring from git) would be cleaner**. Deferred as out-of-scope for T-049.

### Docs Lag
Each fix touched `docs-eng-process/updating.md` or analogous, but the docs were updated *after* the fix landed, not as part of the spec. **Spec-first would have drafted the doc changes before coding, making the "what does this feature mean to users" question explicit.** Not a blocker for internal framework fixes (the impact is contained), but worth noting for the product-practice layer.

## Measure Read-Back

None of the three tasks had success measures with read-back dates due in this period. (T-052's read-back is 30 days post-release; T-048 and T-049 are internal framework fixes with `n/a — internal dev tooling` measures.)

No product-manager re-ranking triggered.

## Action Items

1. **Backfill T-048 archive repair in live repos** — es-invoices and tallyfox-app should run `python3 scripts/openup-claims.py migrate-archived-status --dry-run` to check for stale archived plans, then run without `--dry-run` to repair. (Non-blocking: these repos' current work isn't affected, only *future* dependent tasks would fail.)
   - Owner: GermanDZ  
   - Due: next scheduled maintenance (within 1 week)  
   - Priority: low

2. **T-052 read-back: on-stop loop gone in 30 days** — after 2026-07-18, check `.claude/memory/bypass-log.md` and session transcripts in es-invoices/tallyfox for on-stop override-cap loops. If zero occurrences, success measure met. If any, diagnose why the fix didn't land.
   - Owner: GermanDZ  
   - Due: 2026-07-18  
   - Priority: medium (success signal for a high-impact fix)

## Metrics

| Metric | Value |
|--------|-------|
| **Tasks planned** | 3 |
| **Tasks completed** | 3 |
| **Completion rate** | 100% |
| **Estimated time** | 3 sessions (1 per task) |
| **Actual time** | 3 days (2026-06-16…2026-06-18) |
| **New tests** | 20 (6 + 11 + 3) |
| **Test suite total** | 256 pass (241 pre-existing + 20 new, 1 pre-existing macOS fail remains) |
| **Git commits** | 13 (main implementation commits + completion logistics) |
| **Files changed** | 9 (spec files, code, tests, docs, archives) |

## Conventions Established / Confirmed

1. **Archived-plan logic**: the Plan instance `status:` is advisory only; dependency resolution always defers to the live roadmap, else archived deps never clear their non-satisfied states.
2. **Board spec-materialization (T-048 part B)**: the board reads the **committed** spec (not the worktree state), so `/openup-start-iteration` step 6c must commit the spec folder **before** the board is run (`/openup-next` step 0 or later) — else a fresh worktree sees no lane.
3. **Cross-machine parallel awareness**: the board now surfaces `elsewhere` lanes (live leases on unmerged branches), giving agents visibility into *why* a task is already claimed elsewhere, not just a preflight refusal.
4. **Sync self-commitment**: framework tooling that writes tracked files should commit exactly those paths (partial-commit form, never blanket `git add -A`) with `chore(process) [openup-skip]`, so the tree is clean on return and downstream stop guards never mistake an upgrade for abandoned work.

## Next Iteration Considerations

- **T-052 30-day read-back**: in 12 days (2026-06-30), start checking for the signal. The measure is concrete (on-stop loops: zero) and achievable (the fix is already live in updated projects).
- **T-048 archive migration**: backfill this in live projects soon (idempotent, safe). No blocking dependency, but it clears a technical debt tail.
- **Board-elsewhere robustness**: T-049 is minimal viable — it surfaces leases, but doesn't defend against edge cases (deleted worktrees, atypical branch states). If this causes friction, revisit with a more robust signal (read lease file state directly).
- **No process blockers** — retro counter reset, all lanes released, no hanging input-requests or unmet gates. The framework is stable for the next cycle of feature work.

---

**Retrospective completed:** 2026-06-18  
**Cadence**: T-011 counter was 3/5; now reset to 0. Next retrospective due after 5 more completions.

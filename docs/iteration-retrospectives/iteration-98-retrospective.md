# Iteration 98 Retrospective

## Iteration Overview

- **Iterations covered**: 87–98 (2026-07-25 → 2026-07-27), since [iteration-86-retrospective.md](iteration-86-retrospective.md)
- **Phase**: Construction
- **Goal of the closing iteration**: T-140 — run-log records must stop dirtying the tree
- **Participants**: owner (GermanDZ) + solo agent lanes (standard track throughout)
- **Cadence trigger**: retro counter reached threshold after T-140; run before starting T-147/T-148

## Summary

Twelve iterations of mostly small, sharply-scoped correctness work: entropy measurement
(T-127/T-128/T-132), lane hygiene (T-131), classifier precision (T-135), task-def
convergence (T-124), and a run of process-defect fixes sourced from a downstream
hand-off (T-140–T-149 series). Quality of individual lanes was high — full suite grew
from ~700 to 918 tests with no sustained red.

**This is the first retrospective to run a disposition pass over carried action items**
(T-141's step 5b, shipped in iteration 97). It immediately paid: of **17 open items
reaching back to iteration 9**, three were retirable with citable evidence, and two more
turned out to be *sharper* than their authors knew — one names a concrete pending repair
in a specific repo, another is unanswerable as written. That is exactly the rot the step
was built to stop.

The dominant theme across these iterations is **the framework debugging itself**. That is
productive but self-referential: nearly every lane fixed OpenUP rather than delivering
product capability. Worth a deliberate decision rather than drift.

## What Went Well

**Process**
- The disposition pass (T-141) worked on first contact and found real signal, not busywork.
- Fix-spec-first held under pressure. T-140's roadmap posed an open design question; it was
  resolved *in the spec* as a named, vetoable Assumption with the reason it was forced,
  rather than silently in code.
- Two legal exits were respected across every lane; no raw commits.

**Technical**
- T-140 identified a genuine impossibility (a commit cannot contain its own log record —
  the record carries the SHA, the SHA hashes the tree holding it) and redirected the design
  instead of implementing the roadmap's stated-but-unbuildable direction. Catching that at
  spec time rather than mid-implementation is the cheapest possible place to catch it.
- T-127/T-128 refused to ship a decay gate the data did not license, and said so explicitly.
  Report-only was the right call and was defended.
- T-140's six pre-existing `AutoLogCommitTests` were *strengthened*, not weakened, when their
  contract changed — they now additionally assert the post-commit hook leaves the shard alone.

**Verification**
- Isolating hook verification in a scratch fixture after discovering the live old hook was
  contaminating assertions (it matches on the literal command text) turned an unreliable check
  into 13/13 deterministic ones.

## What to Improve

**A deployment ordering hazard that can lock the repo (new, highest severity)**
`.claude/settings.json` is tracked and merges instantly; `.claude/scripts/hooks/*` is
gitignored and only appears after `sync-templates-to-claude.sh`. Between merge and sync,
`settings.json` references a script that does not exist — the missing hook blocks **every
Bash call**, and `gate-edits` blocks **Write** (no active iteration post-completion). Both
escape hatches shut simultaneously and the owner had to run the sync by hand. Hit live
merging T-140; **any** future hook addition reproduces it.

**The retro cadence counter is not trustworthy**
Three findings, all surfaced during T-140's completion:
1. ~~`openup-session.py end` increments the counter *and* `/openup-complete-task` step 7a
   increments it again — double-count per completion.~~ **Obsolete 2026-07-27 (T-151)** —
   fixed by T-142 (`177ee42`) before this was written; the lane that observed it was running
   a pre-merge skill mirror.
2. ~~`retro.json` stores disagree and `reset` only reaches one of them.~~ **Retracted
   2026-07-27 (T-151) — this was wrong.** `reset` writes the same store `get` reads; the
   legacy file is a one-time migration seed that is ignored once the authoritative file
   exists. See the A3 row for the measurement.
3. This makes carried items 9.1 and 77.2 (both about cadence-gate semantics) materially
   harder to answer — they have been open since iteration 9 and 77 respectively.

**Action-item hygiene was catastrophic until 97**
17 open items, oldest from iteration 9, none ever retired before today. Several are
"decide X" items with no decision artifact, which is why they never closed — an item whose
completion condition is a *thought* has nothing to grep for.

**Self-referential work**
Almost every iteration in this window improved OpenUP itself. Legitimate for a framework
repo, but it means the success measures are mostly process metrics with no external
consumer confirming value.

## Measure Read-Back

| Measure | Expectation | Actual | Verdict | Interpretation |
|---|---|---|---|---|
| **T-052** — on-stop override-cap loop eliminated (due 2026-07-18) | Zero on-stop override-cap loops in es-invoices / tallyfox-app within 30 days | `grep -c "override-cap"` → **0** in both, but **neither repo has a `.claude/memory/bypass-log.md` at all** | **can't tell** | The named instrumentation does not exist in the target repos, so "0" cannot be distinguished from "not logging". Per step 4b this is a finding, not a pass — the measure was specified against an artifact that was never guaranteed to be present downstream. |
| **T-060** — `/openup-fan-out` wall-clock benefit | Two disjoint READY lanes exercised, wall-clock captured (due by iteration 90) | No evidence of any real two-lane fan-out run | **missed → measure retired** | Overdue by 8 iterations, never exercised for its stated purpose. **Disposition 2026-07-27 (owner decision):** the measure is retired as `n/a` rather than manufacturing a run nobody will act on. The feature remains available; a fresh measure would be authored if fan-out is ever used in earnest. Carried item 77.3 struck through in iteration-77. |
| **T-120/T-123** — orchestration economics | Read-back when owner endpoint stable | Endpoint stability not established this window | **can't tell** | Carried item 86.3, unchanged. |
| **T-140** — sweep commits per lane → 0 | 0 logs-only commits per lane, within 3 lanes post-merge | Not yet due (merged 2026-07-27) | **pending** | Read back after T-147/T-148 complete. Caveat recorded: only valid once `sync-templates-to-claude.sh` has run on main (done 2026-07-27). |

**Product-manager re-rank:** no re-rank of pending roadmap entries. Two measures are
`can't tell` because instrumentation is missing rather than because the underlying work
failed, and one (`T-060`) concerns a feature with no pending downstream entries. The
evidence does not support moving anything; it supports **fixing the measures** — captured
as new action items A2 and A3.

## Carried Action Items

### Retired this cycle (3)

| Item | Origin | Verdict | Evidence |
|---|---|---|---|
| Fix `test_init_creates_valid_file` to assert `schema == CURRENT_SCHEMA` (or `2`) | iter-77 | **satisfied** | `scripts/tests/test_openup_state.py:58` asserts `data["schema"] == 2`; commit `c27f7c1` |
| Merge T-043 to resolve dangling refs | iter-20 | **satisfied** | Both files on `main`: `docs-eng-process/parallel-lanes.md`, `docs/explorations/2026-06-16-cross-machine-claim-coordination.md` (commit `f7c1647`); no `T-043` branch remains |
| Monitor `duplicate_start_blocked` counter at iteration 22+ | iter-20 | **satisfied** | Review performed at iteration 98: `grep -rh duplicate_start_blocked docs/agent-logs/runs/*.jsonl \| wc -l` → **0**. Guard has never fired; precondition (parallel clones) still not met, so no successor item |

### Still open (14) — carried with original authoring date

| # | Item | Origin (date) | Age | Note from this pass |
|---|---|---|---|---|
| 9.1 | Clarify retro cadence gate boundary (block on 4→5 or 5→6?) | iter-9 | 89 iterations | Code is still `count >= threshold` (default 5); no decision artifact exists. **Now urgent** — see the double-increment finding below |
| 9.2 | First real `/openup-sync-spec` use on a live refactor diff | iter-9 | 89 | Mentions in status notes are about *editing* the skill, not exercising it |
| 9.3 | Skills altitude / prose-vs-executable survey | iter-9 | 89 | No artifact found |
| 10.1 | Backfill T-048 archive repair in live repos | iter-10 | 88 | **Sharpened**: `migrate-archived-status --dry-run` → es-invoices has exactly **1** stale plan (`T-009: in-progress → done`); tallyfox-app clean. One concrete repair pending, owner's call to run it |
| 10.2 | T-052 read-back (on-stop loop gone in 30 days) | iter-10 | 88 | **Unanswerable as written** — no `bypass-log.md` exists in either target repo. See Measure Read-Back |
| 20.2 | Dependency-ordering convention (deps/explorations before implementation) | iter-20 | 78 | No checklist item added to `/openup-start-iteration` |
| 77.2 | Should `gates.retro_due` be checked outside `full`-track starts | iter-77 | 21 | Related to 9.1; both blocked on the same unmade decision |
| 77.3 | Exercise `/openup-fan-out` for real **or** retire its success measure | iter-77 | 21 | **Overdue** (due by iteration 90). Forcing a decision is now the point |
| 77.4 | Why did July under-log run shards relative to commit volume | iter-77 | 21 | `cycle.py` does emit (`log-event`, `_sweep_run_logs`), so the mechanism exists; the discrepancy is unexplained |
| 77.5 | Decide if `docs/risk-list.md` is worth instantiating, else treat absence as `n/a` | iter-77 | 21 | File absent **and** skill step 4 unchanged — neither branch taken |
| 86.1 | Consumer-smoke check exercising the install path | iter-86 | 12 | No such test exists |
| 86.2 | Audit "am I the framework repo?" markers keyed on distributed artifacts | iter-86 | 12 | No audit artifact found |
| 86.3 | T-120/T-123 success-measure read-back when endpoint stable | iter-86 | 12 | Endpoint stability not established |
| 86.4 | Commit kaze-webapp `sync-from-framework.sh` bump | iter-86 | 12 | Sibling repo, owned by kaze lead, on their schedule — not actionable here |

## Action Items (new only)

| # | Action | Owner | Priority | Due |
|---|---|---|---|---|
| A1 | **Fix the hook deployment deadlock**: make a missing hook script a no-op (warn, exit 0) rather than an error, **or** track hook scripts alongside the `settings.json` that references them. Today a merged settings change can lock both Bash and Write simultaneously | framework maintainer | **critical** | before the next hook is added |
| A2 | ~~**Fix the retro-counter double-increment**: `openup-session.py end` and `/openup-complete-task` step 7a both increment. Pick one owner and add a regression test~~ | ~~framework maintainer~~ | ~~high~~ | **obsolete 2026-07-27 (T-151)** — already fixed by **T-142, commit `177ee42`**, which merged as PR #93 *during* iteration 98. The pack's step 7a now reads *"Do **not** issue a separate `retro increment` here"*, and T-142 already ships `test_archive_advances_cadence` + `test_failed_archive_does_not_advance_cadence`. The double-increment observed while closing T-140 was real **for that lane** — it was executing a `.claude/skills/` mirror rendered before #93 merged. Accurate observation, wrong diagnosis |
| A3 | ~~**Reconcile the `retro.json` stores** — main `.openup/` and shared `.git/openup/` are independent; `reset` appeared not to reach the store `get` reads~~ | ~~framework maintainer~~ | ~~high~~ | **WRONG — retracted 2026-07-27 (T-151)**. Measured in an isolated fixture: after `retro reset`, the authoritative store **and** `get` both read 0 — `reset` writes exactly the store `get` reads. The legacy `.openup/retro.json` is a deliberate one-time migration seed (T-143), read **only** when the authoritative file is absent; rewriting it to 4 left `get` still reporting 100. The original claim was inferred from two direct file reads, never from `get`'s behaviour, and the hand-zeroing of `.openup/retro.json` was unnecessary (harmless). Retained struck-through, not deleted, so the error stays auditable |
| A4 | **Require every success measure to name instrumentation that provably exists at completion time** — T-052 was specified against a `bypass-log.md` that does not exist downstream, making its read-back unanswerable. Tighten `/openup-complete-task` step 1b to reject an instrument that cannot be demonstrated in the *target* environment, not just the framework repo | framework maintainer | medium | next architecture pass |
| A5 | **Force a disposition on the six "decide X" carried items** (9.1, 9.3, 20.2, 77.2, 77.5, plus 77.3's retire-or-exercise). Each has no greppable completion condition, which is why none has closed in up to 89 iterations. Convert each to a concrete artifact or retire it as obsolete | owner | medium | next retrospective |

## Metrics

- **Iterations covered**: 87–98 (12)
- **Test suite**: ~700 → **918 passed, 1 skipped** at iteration 98
- **Tasks completed this window**: T-127, T-128, T-131, T-132, T-134, T-135, T-136, T-138, T-141, T-142, T-143, T-145, T-146, T-140
- **Carried action items**: 17 open at start → **3 retired, 14 carried**, 5 new authored
- **Oldest open item**: iteration 9 (89 iterations old)

## Next Iteration Considerations

- **Carry forward**: the 14 open items above, with age now visible.
- **Do A1 before adding any further hook.** It is the only item here that can hard-block a
  working repo, and it will recur silently otherwise.
- **Next lanes**: T-147 (fence allowlist — owner notes it does not reproduce in this repo)
  and T-148 (`/openup-start-iteration` never passes `--plan`; hand-patched again during
  T-140, making it at least the sixth occurrence).
- **Risk to monitor**: the self-referential work ratio. Twelve consecutive iterations of
  framework-fixing with no external consumer validating the value. Worth an explicit
  product-manager decision on whether to keep draining the process-defect backlog or
  return to capability work.
- **T-140 read-back** falls due after the next two lanes — check that no lane produces a
  logs-only commit.

## Post-Retrospective Triage (2026-07-27, same day)

Every action item — the 5 new and the 14 carried — was triaged into *resolve now*,
*needs a lane*, or *not ours*. Nothing was left in the list without a destination.

### Resolved on the spot (3 more retired, by investigation)

| Item | Verdict | Evidence |
|---|---|---|
| `86.2` Audit framework-identity markers | **satisfied** | The one real detection site (`scripts/sync-from-framework.sh:217-221`) already keys on the framework-exclusive `scripts/sync-templates-to-claude.sh` and names this hazard inline (commit `bbfa984`, T-126). Verified neither consumer carries `docs-eng-process/.claude-templates`. The other `docs-eng-process` tests are project/template checks, not identity checks |
| `77.4` Why did July under-log run shards | **satisfied — premise overturned** | There is no under-logging. On 2026-07-13 (167 commits / 90 records): 91 commits were **logs-only** (deliberately skipped by the self-reference guard) and 27 were **merges** (never logged), leaving 49 loggable against 90 records. A further 17 records point at SHAs rebased away and unreachable from `main`, while `git log` buckets by post-rebase committer date — the two counts were never comparable quantities |
| `10.2` T-052 read-back | **obsolete** | Unanswerable as specified: neither target repo has a `bypass-log.md`, so "0 occurrences" ≠ "no loops". Superseded by **T-152**, which fixes the class rather than this instance |

**Disposition total for iteration 98: 6 of 17 carried items retired** (3 in the main pass,
3 in triage), all with citable evidence.

### Filed as roadmap entries (needs a delivery lane)

| Task | Covers | Priority |
|---|---|---|
| **T-150** | A1 — a merged `settings.json` naming a not-yet-synced hook script locks both Bash and Write | **critical** |
| **T-151** | A2 + A3 + carried `9.1` + carried `77.2` — retro counter double-increment, split stores, and the two undecided gate-semantics questions, folded because they are one decision on one number | high |
| **T-152** | A4 (+ retires `10.2`'s class) — a success measure may not name instrumentation absent from the environment where it is read back | medium |
| **T-153** | carried `86.1` — consumer-smoke check over the install path. Depends on T-150 | high |
| **T-154** | A5 residue — the four "decide X" items (`77.3`, `77.5`, `20.2`, `9.3`) plus `9.2` opportunistically; each must produce an artifact or an explicit obsolete retirement | medium |

### Not ours to close

- `10.1` — **one concrete repair pending**: es-invoices has exactly one stale archived plan
  (`T-009: in-progress → done`); tallyfox-app is clean. Deliberately **not run** — it mutates
  a repo outside this one, so it is the owner's call. `python3 scripts/openup-claims.py migrate-archived-status`
  in es-invoices closes it.
- `86.3` — T-120/T-123 read-back, genuinely blocked on owner endpoint stability.
- `86.4` — kaze-webapp `sync-from-framework.sh` bump, owned by the kaze lead on their schedule.

**Net effect on the carried list: 14 open → 3 open**, and the three that remain are all
external dependencies rather than unowned residue.

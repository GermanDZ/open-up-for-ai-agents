# Iteration 109 Retrospective

## Iteration Overview

- **Covers**: the lanes completed since the iteration-103 retrospective — **T-147, T-148, T-149, T-155, T-157, T-158**, plus one quick lane (`quick-r5-stale-lease`)
- **Dates**: 2026-07-27 (all lanes; the recorded iteration numbers 103–109 were assigned out of order, so this retrospective scopes coverage **by task id**, not by the header counter — see *What to Improve*)
- **Goal**: close the standing process defects surfaced by iteration-103, and clear the carried action-item backlog
- **Participants**: solo (framework maintainer + agent), `standard` track throughout, one `quick`

## Summary

**The strongest cycle so far on closing loops rather than opening them.** All three action
items iteration-103 authored (B1–B3) were closed **in the cycle that authored them** — a
first — and with them the last two carried items that were actionable in this repo, `20.2`
(open 83 iterations) and `77.5` (26). Carried-item count went 6 → 4, and the four that
remain are genuinely blocked on things outside this repo or on an opportunity that has not
arisen.

Two defects of the same shape were fixed: **a recovery tool needing a precondition the
situation had already destroyed.** T-157 fixed it for the conflict-recovery recipe
(`sync-status.py` required the state file that completion archives). The stale-lease
backlog was the same shape at the operations layer — `reap` skips heartbeat-less claims by
design, so the population most likely to go stale was the one it would never touch.

The cycle also produced the first **self-application** of a rule shipped within it: T-158's
new step 5c demanded a verified premise for every new action item, and running it below
**changed one item before it was filed** (see C1).

## What Went Well

- **Premise-checking before building repeatedly changed the work.** `20.2` was going to be
  implemented as a checklist item; measuring showed both halves had become *enforcement*
  in the intervening 83 iterations, so it was retired instead. `77.5` had sat open for 26
  iterations behind an unfalsifiable question ("is it worth it at this project's scale?");
  reframing it around a checkable fact (five live docs referenced a file that did not
  exist) closed it in one lane.
- **T-157 and T-158 were bite-checked honestly.** Both reported how many new tests fail
  against the pre-change code, and both *excluded vacuous passes from the count* rather
  than inflating it (T-157: "9 of 11, and here is why the other 2 do not count").
- **Fix-spec-first held under pressure, three times.** T-155 moved its `touches`/Structure
  before the code when the first draft contradicted a file's own convention; T-157 and
  T-158 each added a file to the spec mid-lane *before* editing it.
- **Findings were filed, not silently worked around.** The stale claims blocked two lanes
  and were cleared — but the mechanism was investigated and recorded rather than treated
  as a chore, which is what surfaced C1 below.
- **Already-closed loops were not re-filed as work.** T-148's own measure reads back as met
  (below), so the recurring "start-iteration never passes `--plan`" complaint — hand-patched
  in five consecutive lanes — is genuinely gone and is recorded here rather than as an item.

## What to Improve

- **"Full suite" has meant a subset.** T-155, T-157 and T-158 each reported a "full suite"
  figure (873 → 884) that covers **`scripts/tests/` only**. The repo also has `./tests/`
  with **114 passing tests**, never run by those lanes; full collection is **999**. No
  regression resulted — `./tests/` passes — but the verification claims were narrower than
  their wording, and `tests/test_claims_heartbeat_reap.py` (directly relevant to C1) sat in
  the unrun directory. Filed as **C2**.
- **The iteration counter is not a reliable coverage index.** Recorded numbers ran 103–109
  out of order (T-148 is labelled 103 yet postdates the 99–103 retrospective; T-147 is 104,
  T-149 is 105). Coverage in this document is therefore scoped by task id. Not filed as an
  item — the header is a derived field with several writers and no consumer depends on its
  ordering; the cost is confined to writing retrospectives.
- **Two success measures could not be read at all**, because the environment they correctly
  name is not present on this machine. This is *not* T-152's failure recurring — T-152
  forced the environment to be named, and it was — but naming is not access. Filed as **C4**.
- **One observation remains unexplained.** T-075's claim *reappeared* mid-session with a
  fresh mtime and a preserved `claimed_at` of 2026-07-13, having already been released once
  during T-142/T-143. It has not recurred. **Deliberately not filed as an action item**: I
  cannot state what would make it true, so per step 5c there is no premise to verify and an
  item would be a guess. Recorded in `docs/risk-list.md` R5 as an open question instead.

## Measure Read-Back

| Measure | Expectation | Actual | Verdict | Interpretation |
|---|---|---|---|---|
| **T-148** — manual `set-gate plan_persisted` | 5-of-5 → **0**, within the next 5 standard/full lanes | 3 of 5 lanes elapsed (T-155, T-157, T-158); **all 3 carry `plan_gate_autoresolved`, 0 manual recoveries** | **met (partial window)** | Directly corroborated: neither T-157 nor T-158 needed the workaround. Window completes in 2 more lanes; no reason to expect reversal |
| **T-149** — header clobber | **0** occurrences of `Iteration` unchanged while `Status` moves completed→in-progress, over ~10 iterations | **0 across the 25 most recent commits** to `docs/project-status.md` | **met** | The guard holds. Signature checked mechanically, not by inspection |
| **T-152** — unanswerable measures | 1 (T-052) → **0** for every measure authored after the change, at the next two retrospectives | **0** — every post-change measure names a read-back environment | **met** | This is the second of the two assessments. But see C4: it surfaced an *adjacent* failure the criterion does not cover |
| **T-153** — consumer-only breakage | 2 known → **0** across the next 3 install-path / `.claude-templates/` changes | ≥3 qualifying changes landed (T-148, T-149, T-157, T-158); 0 breakages; `test_consumer_smoke.py` green | **can't tell** | **A 0 here is not evidence.** No downstream repo synced during the window, so "none reached downstream" is indistinguishable from "not exercised". Re-read when a consumer actually syncs |
| **T-147** — kaze-webapp hand-declared `touches` | 8 of 37 → **0** of the first 3 new lanes | Unreadable | **can't tell (environment inaccessible)** | kaze-webapp is not present on this machine. The measure is correctly specified; the number cannot be produced from here. → **C4** |
| **T-155** — `bypass-log.md` merge commits | 3-of-3 → 0 in kaze-webapp | Unreadable | **can't tell (environment inaccessible)** | Same cause as T-147. T-155 itself predicted a `0` would mean "not delivered" — it cannot even reach that check |
| **T-150** — hook-wiring lockouts | 0 sessions unusable, next 3 hook-touching merges | **0 qualifying merges** since landing | **not due** | Neither T-157 nor T-158 touched `settings.json` or `.claude/scripts/hooks/` |
| **T-157** — view hand-repairs | 2-of-2 → 0 of next 3 view-conflicting PRs | Not due | **pending** | Read back at the second retrospective after landing (backstop 2026-09-30) |
| **T-158** — false/shrunk action items | 4-of-5 → ≤1 of next 5 authored | Not due | **pending** | Backstop 2026-10-31. This retrospective authors 4 of that denominator |

**Product-manager re-rank:** **no re-rank.** Every readable measure came back *met*, and the
three `can't tell` verdicts are all blocked on downstream access rather than on any signal
that the delivered work was misprioritised. The evidence supports the current order; T-073
remains the next pending entry.

## Carried Action Items

### Retired this cycle (5)

| Item | Verdict | Evidence |
|---|---|---|
| **B1** — give `sync-status.py` a no-lane path | **satisfied** | T-157, PR #105. Verified live on trunk: plain run exits `3`, `--views-only` exits `0` |
| **B2** — verify a retrospective item's premise before promoting | **satisfied** | T-158, PR #106 — step 5c in `docs-eng-process/procedures/openup-retrospective.md`; applied for the first time in this document |
| **B3** — decide `20.2` and `77.5` | **satisfied** | T-158; both decided below, neither carried again |
| **20.2** — dependency-ordering convention (83 it.) | **obsolete** | Struck in place in `iteration-20-retrospective.md`. Both halves became enforcement: `openup-claims.py:53` (exit 3), board `depends_ok`, T-079 partitioner, `/openup-explore` |
| **77.5** — instantiate `docs/risk-list.md` (26 it.) | **satisfied** | Struck in place in `iteration-77-retrospective.md`. `docs/risk-list.md` exists, 7 ranked risks |

### Still open (4)

| # | Item | Authored | Age | Check performed this cycle |
|---|---|---|---|---|
| ~~`10.1`~~ | ~~es-invoices archived-plan status repair~~ | iter-10 | 94 it. | **Retired obsolete 2026-07-27, hours after this document was written** — owner decision: the target repos are too old to migrate (es-invoices dormant since 2026-06-23). Resolution in [`iteration-10-retrospective.md`](iteration-10-retrospective.md). Original finding, still accurate: **Still true, and reclassified.** `../es-invoices` **is present on this machine** — previously filed as "external, not closable here". `docs/changes/archive/T-009/plan.md` still reads `status: in-progress`; it is the only one. Fix is one command (`openup-claims.py migrate-archived-status`) in a repo this session does not own — **actionable with owner consent**, not external |
| `86.3` | T-120/T-123 read-back when endpoint stable | iter-86 | 18 it. | Still open. Blocked on owner endpoint stability; unchanged |
| `86.4` | kaze-webapp `sync-from-framework.sh` bump | iter-86 | 18 it. | Still open. kaze-webapp not present on this machine (same blocker now formalised as C4) |
| `9.2` | first real `/openup-sync-spec` use on a live refactor diff | iter-9 | 95 it. | Still open. No lane this cycle produced a pure-refactor diff (T-157 and T-158 were both behaviour/process changes). Two archived lanes *mention* the skill, which is not evidence of a run — per step 5b, an item with no citable evidence stays open |

## Action Items (new only)

| # | Action | Owner | Priority | Due | **Evidence** |
|---|---|---|---|---|---|
| **C1** | **Make `openup-claims.py claim` stamp `last_heartbeat`**, as `begin` already does — so no code path can create a permanently un-reapable claim | framework maintainer | **high** | next iteration | **Checked in this repo, empirically.** Claimed a throwaway id into an isolated `--claims-dir`: the written payload keys are `base_sha, branch, claimed_at, session_id, task_id, touches, worktree` — **no `last_heartbeat`** (`scripts/openup-claims.py:944-952`). `reap` skips heartbeat-less claims by design (`:1146-1147`), so such claims are never auto-reaped. **The documented re-claim recovery hits this path**: the T-157 and T-158 re-claims performed today each created one |
| **C2** | **Make "full suite" mean the whole suite** — either run `scripts/tests/` *and* `tests/` in the completion check, or rename what lanes report | framework maintainer | medium | next iteration | **Checked in this repo.** `pytest scripts/tests/ -q` → **884 passed**; `pytest tests/ -q` → **114 passed**; full collection → **999**. T-155/T-157/T-158 each reported the 884-family number as "full suite". `tests/test_claims_heartbeat_reap.py` — the reap coverage relevant to C1 — is in the unrun directory |
| **C3** | **`sync-status.py` must not report success for a task it cannot find** — have `update_roadmap()` report whether it matched, and warn when it did not | framework maintainer | medium | next iteration | **Observed live during T-158.** With no roadmap entry for the task, the run printed `Synced roadmap + project-status for T-158 (status=completed)` while writing nothing: `update_roadmap()` returns the text unchanged when neither a table row nor a `## T-NNN:` section matches, but `main()` prints its success line unconditionally. Recorded in `docs/changes/archive/T-158/design.md` DD8 |
| **C4** | **Decide how downstream-environment measures get read** — either keep a read-only checkout of the consumer repos reachable from here, or require such measures to name *who* will read them and when | product-manager | medium | next retrospective | **Checked on this machine.** `kaze-webapp`, `cqecho-app`, `tallyfox-app` are **not present**; `es-invoices` is. T-147 and T-155 both correctly name kaze-webapp as their read-back environment (T-152 working as designed) and both come back **`can't tell`** in this document's table — the second consecutive cycle a downstream measure has gone unread |

**Deliberately not filed:** the T-075 claim reappearance. Step 5c requires stating what would
make the problem real and checking it; for a one-off, non-recurring file rewrite I cannot do
either, so an item would be a guess dressed as work. It is recorded as an open question in
`docs/risk-list.md` R5.

## Metrics

- **Lanes completed**: 7 (T-147, T-148, T-149, T-155, T-157, T-158 + 1 quick)
- **Track mix**: 6 `standard`, 1 `quick`, 0 `full`; solo throughout, no team deployed
- **Tests**: `scripts/tests/` **884 passed**, 1 skipped, 20 subtests · `tests/` **114 passed** · **999 collected** repo-wide
- **Carried action items**: 6 open at cycle start → **4 open** (5 retired: B1, B2, B3, `20.2`, `77.5`)
- **Oldest item closed**: `20.2`, open **83 iterations**
- **Measures read back**: 9 assessed — 3 met, 3 `can't tell`, 1 not due, 2 pending
- **Stale claims**: 12 → **0** (claims dir empty)
- **Items authored by iteration-103 and closed in the same cycle**: 3 of 3 (first occurrence)
- **New action items whose scope changed during premise verification**: 1 of 4 (C1)

## Next Iteration Considerations

- **C1 first.** It is the only new item that can silently re-create the condition this cycle
  spent two lanes working around, and its fix is small and at the source — strictly better
  than the age-based reaping fallback recorded in R5 before the premise was checked.
- **C2 is cheap and changes what every future lane's verification claim means.** Worth doing
  before the next measure read-back depends on it.
- **The next roadmap entry is T-073** (FastAPI wrapper over the reference driver), the only
  genuinely READY pending task; T-156 remains gated on its own premise, per its entry.
- **Risk to monitor: R1 is unchanged and remains critical.** Fifteen consecutive cycles with
  no external consumer validating value — and this cycle produced direct evidence of the
  cost, in three `can't tell` verdicts that all trace to downstream repos being out of
  reach. C4 is the narrow, checkable slice of that risk; R1 itself is not closable by any
  action item here.
- **Ceremony (R3) stayed high but did not grow.** No new gate was added this cycle; step 5c
  is a required *element*, not a new gate, and it deleted more work than it created by
  turning one action item into a smaller one before it was filed.

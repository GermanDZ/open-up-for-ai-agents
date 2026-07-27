# Iteration 103 Retrospective

## Iteration Overview

- **Iterations covered**: 99–103 (2026-07-27), since [iteration-98-retrospective.md](iteration-98-retrospective.md)
- **Phase**: Construction
- **Work**: T-150, T-151, T-152, T-153, plus a quick lane retiring T-154 and two carried items
- **Participants**: owner (GermanDZ) + solo agent lanes, `standard` track throughout (one `quick`)
- **Cadence trigger**: counter reached 5 after the retirement lane

## Summary

Five lanes in one day, all sourced from the previous retrospective's own action items — the
first time this project has run the loop *retrospective → roadmap → delivery → retrospective*
end to end. It worked, and it worked partly by **not** doing what it was told:

- **T-150** shipped a real fix (hook commands guarded) for a real lockout.
- **T-151** shipped **zero code**, because measuring first showed both its premises were false.
- **T-152** shipped a rubric element after verifying the criterion actually discriminates.
- **T-153** found that two of its three sub-items were already covered, and the residual gap
  was better than any of them.
- The retirement lane closed T-154 without working it, because its items had dispositions by
  the time it reached the queue.

**Three of five lanes changed shape after measurement.** That is the headline. The previous
retrospective authored five action items in good faith; two turned out to be misdiagnoses and
two more were partly already done. The corrective is not "write better action items" — it is
**verify a premise before promoting it to a task**, which is now the standing lesson.

## What Went Well

**Measuring before building, repeatedly**
- T-151's double-increment was already fixed by T-142 (`177ee42`), merged mid-session. The
  split-store claim was simply false — measured in a fixture, `reset` writes exactly the store
  `get` reads.
- T-153 checked existing coverage first and avoided duplicating two real test suites.
- T-152 counted whether its new criterion discriminates (48/48 fail, 0/48 pass) rather than
  assuming.

**Root causes measured, not inferred**
- T-150's real cause was that `python3` exits **2** on a missing file — the same code the
  harness reads as "block this tool call". That single fact explained why the failure was
  total rather than noisy, and ruled out three plausible guards in one step.

**Rejections made durable**
- T-150 asserts the rejected `|| true` guard *in a test*, so the rejection survives a future
  "simplification". T-152 records why no validator exists. A rejection that lives only in a
  commit message gets re-litigated.

**Honest retraction**
- Two published findings were struck through as **obsolete** and **wrong** with the
  disproving measurements inline, rather than quietly deleted.

## What to Improve

**Action items were promoted to roadmap tasks without verifying their premises**
Five items became T-150–T-154 within one turn. Two (A2, A3) were false, and T-153's and
T-154's scopes had both shrunk. Filing is cheap; a wrongly-filed task costs a full lane to
discover. **Verify the premise at filing time, not at implementation time.**

**A retrospective's own disposition pass caught an accounting error in the same session**
The T-154 cancellation note listed the wrong four items — it named 9.1 and 77.2 (real
closures, but never part of T-154) and silently dropped **77.5** and **20.2**, which remain
open. Corrected in the roadmap entry. The lesson is that hand-written cross-references
between items rot within *hours*, not iterations.

**The shared-view merge wave**
Merging four PRs that each touched `docs/project-status.md` left `## Notes` assembled from
whichever copy won, with three notes on disk but absent from the block. Two PRs went
`CONFLICTING` mid-wave and needed rebasing.

**`sync-status.py` cannot regenerate the views once a lane is done** *(new, and the sharpest)*
The documented conflict fix is "rebase onto trunk and re-run `sync-status.py`". But
`sync-status.py` requires an active `.openup/state.json`, which `openup-session.py end`
archives at completion — so the procedure is impossible in exactly the situation it is
written for. `--reconcile` only checks roadmap Status cells, not the Notes assembly. The
recovery here was to call the module's own `assemble_notes` / `update_notes_section`
directly. **Same shape as T-150's deadlock: the recovery tool needs a precondition the
situation has already destroyed.**

## Measure Read-Back

| Measure | Expectation | Actual | Verdict | Interpretation |
|---|---|---|---|---|
| **T-140** — sweep commits per lane → 0 | 0 logs-only commits per lane within 3 lanes post-merge | Across T-150/151/152/153: **0** logs-only sweep commits. Post-commit `git status -- docs/agent-logs/` clean throughout | **met** | The queue+drain design holds in practice. Note the caveat from its own DD5 held too: it only took effect after `sync-templates-to-claude.sh` ran on main |
| **T-060** — fan-out wall-clock benefit | Two disjoint lanes exercised | Never exercised | **retired** | Measure retired as `n/a` by owner decision (see iteration-77, item 77.3). Feature untouched |
| **T-052** — on-stop loop gone | Zero loops in downstream repos | No `bypass-log.md` in either repo | **retired** | Retracted as obsolete; superseded by T-152, which fixes the class |
| **T-150** — hook-wiring lockouts → 0 | 0 sessions made unusable, next 3 hook-touching merges | Not yet due (1 merge since) | **pending** | Read back after two more hook-touching merges |
| **T-152** — unanswerable measures → 0 | 0 `can't tell` verdicts for missing instrumentation | Not yet due | **pending** | Read back at the second retrospective after landing |
| **T-153** — consumer-only breakage → 0 | 0 reaching downstream, next 3 install-path changes | Not yet due | **pending** | — |

**Product-manager re-rank:** no re-rank. The one *met* measure (T-140) confirms the design it
was written for; the two retirements were deliberate decisions, not failures; the three
pending measures are too young to inform ordering. Evidence supports the current order.

## Carried Action Items

### Retired this cycle (3)

| Item | Origin | Verdict | Evidence |
|---|---|---|---|
| Clarify retro cadence gate boundary | iter-9 (94 it.) | **satisfied** | T-151 — decision recorded in `state-file.md`: gate fires at `count >= 5` |
| Should `retro_due` apply outside `full` starts | iter-77 (26 it.) | **satisfied** | T-151 — hard block stays `full`-only, with an explicit revisit condition |
| Consumer-smoke check over the install path | iter-86 (17 it.) | **satisfied** | T-153 — `scripts/tests/test_consumer_smoke.py`, verified to bite |

Plus, in the same window but recorded in the previous cycle: `9.3` and `77.3` retired by owner
decision, and **A2 / A3 retracted** as misdiagnoses.

### Still open (6) — carried with original authoring date

| # | Item | Origin | Age | Note |
|---|---|---|---|---|
| 9.2 | First real `/openup-sync-spec` use on a live refactor diff | iter-9 | 94 it. | **Opportunistic rider, deliberately not a task** — needs a real refactor diff to audit |
| 10.1 | T-048 archive repair in live repos | iter-10 | 93 it. | **External.** es-invoices has exactly 1 stale plan (`T-009`); tallyfox-app clean |
| 20.2 | Dependency-ordering convention for `/openup-start-iteration` | iter-20 | 83 it. | **Was wrongly recorded as handled by T-154** — still open; see the roadmap correction |
| 77.5 | Instantiate `docs/risk-list.md` or treat its absence as `n/a` | iter-77 | 26 it. | **Same wrongly-dropped pair as 20.2** — still open |
| 86.3 | T-120/T-123 read-back when endpoint stable | iter-86 | 17 it. | **External** — blocked on owner endpoint stability |
| 86.4 | kaze-webapp `sync-from-framework.sh` bump | iter-86 | 17 it. | **External** — kaze lead's schedule |

Four of the six are external or deliberately opportunistic. Only `20.2` and `77.5` are
genuinely actionable here — and only because a bookkeeping error resurrected them.

## Action Items (new only)

| # | Action | Owner | Priority | Due |
|---|---|---|---|---|
| B1 | **Give `sync-status.py` a no-lane path** so the documented "rebase and re-run" fix works after `openup-session.py end` archives state — e.g. `--views-only` that reassembles `## Notes` and reconciles Status cells without requiring `.openup/state.json` | framework maintainer | high | next iteration |
| B2 | **Verify a retrospective action item's premise before promoting it to a roadmap task.** Two of five filed this way were false and two more had shrunk. Add the check to `/openup-retrospective` step 6 (author) or to the promote path in `/openup-next` | framework maintainer | high | next retrospective |
| B3 | **Decide `20.2` and `77.5`** — the two items T-154's cancellation dropped. Each needs a recorded decision or an explicit retirement, not another carry | owner | medium | next retrospective |

Deliberately **not** authored as new items: nothing about T-140/T-150/T-152/T-153, whose
measures are pending and will be read back on schedule.

## Metrics

- **Iterations covered**: 99–103 (5 lanes: 4 standard + 1 quick)
- **Test suite**: 918 → **946 passed**, 1 skipped (+28: 12 hook guards, 7 consumer smoke, plus T-140's carryover)
- **Tasks completed**: T-150, T-151, T-152, T-153 (+ T-154 cancelled unworked)
- **Carried action items**: 14 open at the start of iteration 98 → **6 open**, of which 4 are external/opportunistic
- **Lanes that changed shape after measurement**: 3 of 5
- **Code shipped by T-151**: zero — the correct outcome

## Next Iteration Considerations

- **B1 first.** It is the only item that leaves the repo in a state a human has to hand-repair,
  and it recurs on every multi-PR merge wave.
- **The next lane is T-147** (fence allowlist; owner notes it does not reproduce here) or
  **T-148** (`/openup-start-iteration` never passes `--plan` — hand-patched again in every
  lane this session, now at least the eighth occurrence). T-148 has the stronger evidence.
- **Risk to monitor**: still no external consumer validating value — fourteen consecutive
  iterations of framework self-improvement. Worth a deliberate product-manager decision.
- **Cadence**: the counter resets here. Note that the previous window's cadence overrun was
  counted by an untrustworthy number; this is the first clean measurement.

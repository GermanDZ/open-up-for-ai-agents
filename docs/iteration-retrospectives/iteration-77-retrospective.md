# Iteration 77 Retrospective

## Iteration Overview

- **Retrospective triggered at**: Iteration 77 (2026-07-14), task T-111 (retro-cadence counter at 14, threshold 5)
- **Actual coverage**: Iterations 21–77 (2026-06-16 → 2026-07-14, 28 days), tasks T-045 through T-111 (67 tasks)
- **Goal**: no single goal — this window contains the tail of hardening/hygiene work (T-045–T-070) followed by three back-to-back programs: **harness-optional / reference driver** (T-071–T-074, T-080–T-088), **phase-aware Construction loop** (T-075–T-079), and the **deterministic cycle engine** (T-089–T-111, culminating in `scripts/next-cycle`).
- **Participants**: solo owner-driven delivery (98.7% of commits by GermanDZ across two emails; 1.2% by Claude commits), Claude Code sessions doing the actual implementation work under `/openup-next` / `/openup-agent.py cycle`.
- **Status**: iteration 77 (T-111) completed 2026-07-14.

## Summary

This is the **first retrospective document written since iteration 20** (2026-06-16, T-044) — see [What to Improve #1](#what-to-improve). The 57-iteration gap is itself the headline finding, not a footnote: the retro-cadence counter did its job (it sat past-threshold at 14), but nothing consumed the signal until this run.

Substantively, the window was extremely productive: the project shipped the entire arc that turns OpenUP from an LLM-narrated loop into a **deterministic cycle engine** — `openup-agent.py cycle` composes existing scripts (board/session/state/sync/fence/check-docs) as a script-step executor, calling the LLM only at genuine judgment points, with `scripts/next-cycle` as the one-command entry point from an empty project to a running delivery loop. The final two days (2026-07-13/14) alone closed 17 tasks, including a self-correction: T-103 deleted the T-096/T-098 LLM-navigator and hardcoded-bootstrap scaffolding once T-100–T-102 generalized the same capability through the process-map schema — a sign the team is willing to remove its own recent work rather than let it calcify.

## What Went Well

1. **Deterministic-first architecture held up under its own program.** The cycle engine's design principle — ceremony as code, LLM only at judgment points — was validated by the benchmark harness (T-080–T-088), which measured the token-cost claim directly (hermetic run: 2 LLM calls vs 37–50 live-`/openup-next` iterations for an equivalent scenario) rather than asserting it.
2. **Self-correcting scope.** T-103 removed T-096's LLM navigator and T-098's hardcoded bootstrap path in the same program that made them obsolete (T-100–T-102's process-map-driven scaffold generalized both). The roadmap shows deletion-as-a-task-type being used deliberately, not left as cleanup debt.
3. **Crash-safe resumability by construction.** The cycle engine's inter-step state lives entirely in the repo (board/state/lease), so a killed or interrupted run resumes for free — this was a design goal (T-089) that later tasks (T-092, T-094 recovery modes) built on rather than retrofitted.
4. **Measured claims, not asserted ones.** Where a design decision made a falsifiable claim (T-072's live-model acceptance, the ≥5× token-cost claim), the team built the instrumentation to check it before calling the task done, continuing the "measure to decide" pattern this retrospective series started in iteration 20.

## What to Improve

1. **Retro cadence silently lapsed for 57 iterations.** The durable counter (`.openup/retro.json`) is designed to survive iteration boundaries specifically so this can't happen, but nothing forces a `full`-track start (the only path that reads `gates.retro_due`) during a run of `quick`/`standard` solo work — which is exactly what T-045–T-111 was. **The gate only fires on a track this project stopped using.** Worth deciding: either lower the enforcement point (e.g., `/openup-next` or `openup-agent.py cycle` checks `retro_due` regardless of track) or accept that retro is opt-in for solo `standard`/`quick` streaks and rely on periodic manual invocation like this one.
2. **A genuine measure read-back is overdue and nothing flagged it.** T-060's success measure ("wall-clock time for 2 disjoint READY lanes ≤ `max(cycle_time_A, cycle_time_B) + 10%`... within 2 iterations or by 2026-07-05") has no recorded outcome, and no evidence of a real multi-lane `/openup-fan-out` run was found in agent-logs or status-notes since T-060 shipped (2026-06-21). T-079 later built a *different* multi-lane mechanism (Plan-Iteration clustering) but didn't exercise or retire T-060's fan-out skill's measure. See [Measure Read-Back](#measure-read-back).
3. **Agent-log capture thinned out exactly when task volume spiked.** July agent-logs (`docs/agent-logs/runs/`) contain far fewer entries than the ~24 tasks completed 2026-07-12–14 would suggest, while git commits stayed dense (479 commits in the window). The audit trail held up (commits + roadmap Notes + design.md), but the richer per-run log (decisions, duration, test counts) that made writing this retrospective easy for T-089 was largely absent for its neighbors. Worth checking whether `openup-agent.py cycle`'s judgment sub-runs are supposed to write to `docs/agent-logs/runs/` and aren't.
4. **One stale test slipped through a schema bump.** `scripts/tests/test_openup_state.py::test_init_creates_valid_file` still asserts `schema == 1`; T-078 (2026-07-13) bumped `CURRENT_SCHEMA` to 2 and added migration coverage elsewhere but didn't update this assertion. Currently the only failure in the suite (583 passed / 1 failed). Low-risk, but it's a live example of the "check-docs is the safety net, tests can still drift" gap — the suite doesn't have a "no hardcoded schema literals" convention. **Action item below.**
5. **No risk register exists.** `docs/risk-list.md` was never created (or was removed) — `/openup-retrospective` step 4 could not read it as designed. Risk is implicitly encoded in roadmap task dependencies, but nothing captures cross-cutting risk (e.g., "solo delivery model = bus-factor 1", "no risk owner for the reference-driver's live-model acceptance"). Not necessarily a gap worth fixing (see Action Items — may be an intentional n/a for this project's scale).

## Measure Read-Back

| Task | Expectation | Read-back date | Actual | Verdict |
|---|---|---|---|---|
| T-060 (fan-out) | Wall-clock for 2 disjoint READY lanes ≤ `max(A,B) + 10%` vs serial `A+B` | within 2 iterations or by 2026-07-05 | No `/openup-fan-out` run found in agent-logs or status-notes since 2026-06-21 | **Can't tell — instrumentation exists (run-log start/completed timestamps), never exercised on a real multi-lane run** |
| T-072 (reference driver) | Non-Anthropic local-model round trip through the procedure-agnostic driver | on owner live run | **Met 2026-07-13** — `qwen/qwen3.6-35b-a3b` via LM Studio, recorded by T-086 in `docs/changes/archive/T-072/design.md` | **Met** |
| T-074 (human-in-loop input) | Driver-created request resumes through the unchanged `resumable` path | optional owner check | Round-trip test covers it; no live-model manual check recorded | **Met (automated proxy); live check still optional/outstanding** |
| T-078 (assess+milestone) | Live multi-lane run is provably unchanged | deferred to T-079 | T-079 shipped a *different* multi-lane mechanism (Plan-Iteration clustering, not `/openup-fan-out`); single-lane path verified by full suite | **Met for single-lane; multi-lane claim still unverified by a live run** |

**No re-rank performed.** The one genuinely overdue, unresolved measure (T-060) doesn't block or devalue any pending roadmap entry — `/openup-fan-out` is shipped and available, just unused in practice so far. Recommend the product-manager role note this at the next roadmap ordering pass rather than re-rank now: if `/openup-fan-out` stays unused through another retro cycle, that itself is evidence to consider deprecating the parallel-lanes fast path rather than continuing to carry it as unverified.

## Action Items

| Item | Owner | Due | Priority |
|---|---|---|---|
| Fix `test_init_creates_valid_file` to assert `schema == CURRENT_SCHEMA` (or `2`) instead of the stale `1` | next `/openup-quick-task` | next iteration | low |
| Decide whether `gates.retro_due` should be checked outside `full`-track starts (e.g., in `openup-agent.py cycle` or `/openup-next`) so a long solo `quick`/`standard` streak can't silently outrun the cadence again | project-manager / owner | next architecture pass | medium |
| Either exercise `/openup-fan-out` for real (two disjoint READY lanes, capture the wall-clock numbers T-060 specified) or explicitly retire/mark-n/a its success measure | owner | by iteration 90 or next retrospective, whichever first | medium |
| Confirm whether `openup-agent.py cycle`'s judgment sub-runs are expected to write to `docs/agent-logs/runs/`; if yes, find why July's high-volume days under-logged relative to commit volume | owner | next iteration | medium |
| Decide if `docs/risk-list.md` is worth instantiating for this project's scale, or if the retrospective skill's step 4 should treat its absence as `n/a` rather than a silent skip | owner | next retrospective | low |

## Metrics

- **Span**: 28 days (2026-06-16 → 2026-07-14), 57 iterations, 67 tasks completed
- **Commits**: 479 total in window; 203 (42%) touched `docs/changes/`
- **Contributors**: GermanDZ 98.7% (two git identities), Claude 1.2%
- **Peak velocity**: 17 tasks closed in the final 2 calendar days (2026-07-13/14) — the deterministic-cycle-engine and process-map programs landing back-to-back
- **Test suite**: 583 passed / 1 failed (`test_init_creates_valid_file`, stale schema literal — see action items) / 7 subtests passed
- **Retro-cadence counter**: was 14 (threshold 5) going into this run; reset to 0 as part of this retrospective (step 8)

## Next Iteration Considerations

1. **Carry forward**: fix the stale schema test; decide the retro-cadence enforcement question; either exercise or retire T-060's fan-out measure.
2. **Watch**: agent-log capture rate relative to commit/task volume — if it stays thin, the next retrospective will have to lean on git history alone, which is workable but loses the per-run decision record that made this one tractable for the T-089 example.
3. **Risk to monitor**: bus-factor — delivery is ~99% single-owner. Not actionable for a framework-development project of this shape, but worth naming so it isn't invisible.
4. **Program state**: the deterministic-cycle-engine program (T-089→T-111) reads as complete per the roadmap and this project's own memory notes; the phase-aware Construction loop (T-075–T-079) and reference-driver/benchmark harness (T-071–T-088) likewise read as complete. No open program threads found mid-flight in this window — the next iteration is a good point to either pick a new program or return to steady-state maintenance.

---

**Retrospective completed**: 2026-07-14
**Retro counter reset**: ready for the next 5-task cadence to begin (see caveat in What to Improve #1 about `full`-track-only enforcement).

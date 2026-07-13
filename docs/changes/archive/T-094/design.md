# T-094 — design notes & test record

## In-flight decisions

- **DD1 — recovery restructured into a bounded loop.** Case B runs once; then
  up to two rounds of (Case A | replenishment), each followed by one
  re-resolve. `replenished` guards the single ask/replenish per invocation;
  the Case A path that previously returned exit 7 on a blocked lane
  (`EXIT_UNSUPPORTED`) now routes to the stuck check first — every other Case
  A failure code still propagates immediately.
- **DD2 — the consent memory lives in `.openup/cycle.json`** (Ring-3, next to
  the T-089 branch record) under `replenish: {request, consumed, answer}`.
  Missing request file ⇒ record cleared and the ask happens anew (a human
  deleting the request is a legible "ask me again"). An `answered` request
  whose yes/no cannot be parsed is treated as still pending (re-suspend, log)
  — never guessed.
- **DD3 — interactive decline is not persisted** (the human is present; asking
  again next run is cheap and arguably desired); the *request* decline is
  durable per the spec assumption. Both print the same DONE-declined sentinel.
- **DD4 — replenishment instruction bypasses the change-folder briefing** via
  a new additive `instruction=` override on `run_judgment_step` /
  `_dispatch_judgment` (default path unchanged) — the PM pass belongs to no
  lane, so the standard `docs/changes/<task>/plan.md` briefing lines would
  mislead a weak model.
- **DD5 — acceptance gate order**: `openup-roadmap.py next --no-remote-check`
  (hermetic, fail-open remote guard not exercised) then `check-docs.py`; only
  then `git add docs/roadmap.md docs/input-requests` + the `[openup-skip]`
  commit — an unproductive pass commits nothing (Req 6).
- **DD6 — Req 7 amended fix-spec-first BEFORE the code** (applying the T-092
  DD7 learning proactively this time): the ask changes the noop-with-roadmap
  default, so exactly one pre-existing test
  (`test_noop_with_roadmap_has_no_hint`) switched to `recover=False`. The
  predicted single failure was the only one observed.
- **DD7 — `--auto-replenish` deferred** (spec assumption): the consent gate is
  the control point protecting the product-manager value-ordering authority;
  revisit only after live experience.

## Verification record (tester hat, 2026-07-13)

- `python3 -m unittest scripts.tests.test_openup_agent
  scripts.tests.test_openup_agent_tools scripts.tests.test_openup_agent_bench
  scripts.tests.test_openup_agent_cycle scripts.tests.test_openup_roadmap`
  → **123 tests, OK** (9 new in `ReplenishmentTest`; 1 sanctioned edit per
  DD6; fixture gained fake `openup-input.py` + `openup-roadmap.py`).
- Covered: stuck→request+suspend exit 5 (request is yes/no multiple-choice,
  recorded in cycle.json); no-roadmap hints instead of asking; `--no-recover`
  never asks; pending request re-suspends with zero duplicates; interactive
  yes runs the PM sub-run with no request file (and an unproductive pass fails
  typed exit 8); interactive no declines cleanly; answered-no durable across
  two runs; answered-yes full chain — replenish (product-manager hat) →
  plan-iteration → spec author (analyst hat) → pick → deliver, ending
  `OPENUP-NEXT: ADVANCED — T-902` in ONE invocation with the roadmap commit
  older than the spec commit; unproductive yes exits 8 with no roadmap commit.
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-094/plan.md` → exit 0.
- `python3 scripts/check-docs.py` → OK (8 instances).
- `python3 scripts/openup-fence.py check --base harness-optional` → 6 changed
  file(s) within lane.

## Success-measure read-back (pending, owner-side)

✅ instrumentation — driver stderr `recovery:` lines + `docs/input-requests/`
files + the `[openup-skip]` roadmap commit are all observable without new
plumbing. Expectation: on the owner's next live my-product session, draining
the roadmap produces an ask (not a dead stop) and one approved replenishment
resumes delivery to the next `ADVANCED`. Record the outcome here after that
session (no endpoint in this sandbox — T-089/T-092 precedent).

## Requirement grade vs implementation (complete-task §1a)

1. ✅ stuck detection + one ask (`test_stuck_creates_request_and_suspends`,
   `test_no_roadmap_hints_instead_of_asking`, `test_no_recover_never_asks`)
2. ✅ interactive consent (`test_interactive_yes_runs_pm_subrun_without_request`,
   `test_interactive_no_declines_cleanly`)
3. ✅ pending never duplicates (`test_pending_request_never_duplicates`)
4. ✅ answered-yes same-cycle chain (`test_answered_yes_replenishes_then_delivers_same_cycle`
   — hats `[product-manager, analyst]`, roadmap commit precedes spec commit)
5. ✅ answered-no durable (`test_answered_no_is_durable`)
6. ✅ deterministic acceptance (`test_unproductive_yes_exits_8_uncommitted`)
7. ✅ non-stuck invariance (123-test run with only the DD6 sanctioned edit)

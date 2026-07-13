# T-092 — design notes & test record

## In-flight decisions

- **DD1 — recovery order: closure before authoring.** Case B (unclosed-lane
  reconcile) runs before Case A on `plan-iteration`/`noop`, because a stale
  satisfied lane can change what the board considers promotable; each case
  triggers at most one re-resolve (bounded, no loops).
- **DD2 — Case B safety rails.** Dirty working tree ⇒ skip closure with a
  warning (never sweep unrelated work into a recovery commit); merge conflict
  ⇒ typed exit 8 with the branch left intact; no branch deletion, ever.
- **DD3 — Case A reuses the T-089 judgment machinery verbatim** — a synthetic
  `analyst` box through the new shared `_dispatch_judgment` helper (also
  adopted by the executor, removing the seam-handling duplication). The spec
  contract lives in `SPEC_CONTRACT` (engine-side, same rationale as T-089 DD2;
  pack-side contracts are T-091).
- **DD4 — spec gating composes the real validators**: `check-docs.py` always
  (when present), `openup-spec-scenarios.py check` when present. The spec
  commit (`docs(<id>): author spec via cycle recovery [<id>]`) stages ONLY the
  change folder — no `-A` sweep before a lane exists.
- **DD5 — a pre-existing folder that still resolves `plan-iteration` is NOT
  re-authored** (the lane is blocked by something authoring can't fix —
  dependency/collision/suspension) → exit 7 with an explanatory log.
- **DD6 — fresh-project noop hint.** A `noop` decision on a project with no
  `docs/roadmap.md` appends "Inception first: author vision + roadmap (see
  getting-started-reference-driver.md)" to the DONE sentinel — motivated live
  by the user's freshly bootstrapped my-product run (2026-07-13, post-T-093).
  Recovery cannot invent the product; it can say what rebuilds the state.
- **DD7 — spec Req 6 amended (fix-spec-first)** before touching tests: exactly
  one pre-existing test (`test_unsupported_paths_exit_typed_without_begin`)
  asserted the old `plan-iteration` default; it now passes `recover=False`
  (the T-089 baseline this task deliberately changes; Req 5 keeps it
  reachable). No other pre-existing test changed.
- **DD8 — test fake board became dynamic** (a READY lane wins over the canned
  decision) so a recovery round's re-resolve observes repo changes — mirroring
  the real board's derivation, and leaving all prior fixtures' behavior
  intact.

## Verification record (tester hat, 2026-07-13)

- `python3 -m unittest scripts.tests.test_openup_agent
  scripts.tests.test_openup_agent_tools scripts.tests.test_openup_agent_bench
  scripts.tests.test_openup_agent_cycle scripts.tests.test_openup_roadmap`
  → **114 tests, OK** (12 new: 5 Case B, 5 Case A, 2 noop-hint; 1 sanctioned
  edit per DD7).
- Case B covered: closure with zero LLM (failing seam), side-branch merge to
  trunk (ends on `main`, archive visible from trunk), dirty-tree skip,
  `--no-recover` untouched-lane, assess-iteration no-side-effects.
- Case A covered: spec authored → same-cycle pick → `OPENUP-NEXT: ADVANCED —
  T-901` with exactly ONE sub-run (analyst hat; instruction carries the id,
  frontmatter contract, Given/When/Then; no session begun before the spec; the
  `docs(T-901): author spec via cycle recovery` commit precedes the claim);
  no-spec-produced → exit 8, no begin; non-advancing `proposed` spec → exit 7;
  failing `openup-spec-scenarios.py` → exit 8; `--no-recover` → exit 7 with no
  sub-run and no folder.
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-092/plan.md` → exit 0.
- `python3 scripts/check-docs.py` → OK (8 instances).
- `python3 scripts/openup-fence.py check --base harness-optional` → 7 changed
  file(s) within lane.
- Live my-product expectation: the fixture tests reproduce both live cases —
  the T-001 done-but-unclosed shape (Case B test) and the missing-T-002-spec
  shape (Case A test); the user's fresh-project noop run motivated + validated
  DD6's hint path.

## Success-measure read-back (pending, owner-side)

✅ instrumentation — driver stderr decision logs (`decision:`/`recovery:`
lines) + `OPENUP_AGENT_USAGE_LOG` call counts pre-exist (T-080/T-089); the
expectation (first `ADVANCED` on a fresh my-product-shaped project without
human intervention, ≤1 bounded sub-run over baseline) is checked on the
owner's first post-merge my-product retest with a live endpoint. Record the
result here and in the roadmap program block.

## Requirement grade vs implementation (complete-task §1a)

1. ✅ Case B reconcile, zero LLM (`test_unclosed_lane_closed_zero_llm`,
   `test_side_branch_merged_to_trunk` — merge rule; dirty-tree + on-trunk
   variants)
2. ✅ Case A one bounded sub-run, analyst hat, no session before spec
   (`test_spec_authored_then_same_cycle_delivers` record assertions)
3. ✅ spec gated + committed before continue (`test_no_spec_produced_exits_8`,
   `test_spec_scenarios_gate_blocks`, commit-precedes-claim assertion)
4. ✅ same-cycle continuation, bounded (`…_same_cycle_delivers` ends ADVANCED;
   `test_non_advancing_spec_exits_7`)
5. ✅ opt-out restores T-089 behavior (`test_no_recover_keeps_typed_exit_7`,
   `test_no_recover_leaves_lane_untouched`, baseline test under
   `recover=False`)
6. ✅ non-recovery paths unchanged (`test_assess_iteration_untouched_by_recovery`;
   114-test suite with only the DD7 sanctioned edit)

# T-119 design / verification

## Requirement grade (complete-task step 1a) — against the diff
- ✅ **R1** glob guard — `tools.py glob` returns "ERROR: …" for empty/whitespace/None
  and wraps `root.glob` in try/except; `test_glob_empty_pattern_is_error_not_crash`.
- ✅ **R2** direct requires ≥1 task — `openup-process-map.py validate` rule replaced;
  `test_direct_requires_at_least_one_task` + `test_direct_with_multiple_skills_is_fine`
  + `DirectRequiresTaskTests` in the wiring test.
- ✅ **R3** three Inception activities direct — `process-map.yaml`; `activities-for
  inception` shows all four direct; shipped-map validate green.
- ✅ **R4** no regression — full suite 724 pass (updated only the assertions the
  flip/rule change touched).

## Key decisions
- Scoped the flip to the four Inception activities (initiate-project already
  direct + agree-technical-approach / identify-refine-requirements /
  plan-manage-iteration). develop-architecture + test-solution (elaboration/
  construction) left spec-then-execute to contain blast radius — a later decision.
- The iteration-plan instance already handles all-direct (empty `traces-from: []`
  validated by check-docs; "Directly-run activities" section).
- glob guard generalizes the observed empty-pattern crash: any ValueError/
  IndexError/OSError from a bad pattern returns an error to the model.

## Success measure / rollout
- Read-back: next `inception-taskdef --runs 5` on the owner endpoint — full-cycle
  clean-pass 0/5 → ≥4/5 expected (spec-lane 50-turn timeout + glob crash removed).
- Rollout: n/a — internal driver behavior, no flag.

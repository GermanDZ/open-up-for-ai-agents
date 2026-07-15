# T-117 design / in-flight decisions

## Requirement verification (complete-task step 1a) — graded against the diff

- ✅ **R1** auto findings carry `fix_class`/`fix_cmd` — `Finding` gains both fields
  (`openup-doctor.py`); `check_aggregate` + `check_section_status_drift` +
  `check_plan_gate` tag `AUTO` with the owning argv. Asserted in
  `test_auto_derived_view_drift_heals` / `test_auto_plan_gate_heals`.
- ✅ **R2** `--fix` invokes owning script then re-detects — `apply_fixes()` runs the
  fix argv via `run()` and returns `detect_all()`. `test_auto_derived_view_drift_heals`
  asserts INDEX regenerated + drift gone.
- ✅ **R3** single-valued unset `plan_persisted` gate heals — `check_plan_gate` detects,
  fix is `openup-state.py set-gate`. `test_auto_plan_gate_heals` asserts gate set; the
  no-plan boundary in `test_plan_gate_not_flagged_when_no_plan`.
- ✅ **R4** confirm/human never applied without `--confirm` — `apply_fixes` gates on
  class; `test_confirm_and_human_boundary` asserts confirm/human sentinels absent
  without `--confirm`, confirm runs with it, human never.
- ✅ **R5** default run stays read-only — no `--fix` branch never calls `apply_fixes`;
  `test_default_run_is_read_only` asserts the stale file is untouched.

## Success measure / rollout
- Success Measures: `n/a` — internal tooling; boundary test is the falsifiable proof.
- Rollout: `n/a` — internal CLI, opt-in `--fix` flag, no feature flag.

## Key decisions
- **DD1 honored:** doctor invokes owning scripts; gate-set is itself an owning-script
  call (`openup-state.py set-gate`). No detection/fix logic reimplemented.
- **Fix ordering:** `_FIX_ORDER` runs `build-trace-model` before `docs-index` (index
  reads the model). Fixes deduped by argv.
- **`settings.json` no-op reorder deferred** — no detector/serializer yet; out of scope.

# T-105 design / in-flight decisions

## Key decisions
- **Skeleton vs authored split.** Deterministically extractable fields (`name`,
  `role`=primary performer, `inputs`=Inputs-section workproduct names) form the
  `--check`-diffed skeleton. `artifact`/`output_path` are the framework's
  primary-spine-output decision (authored, validated against the spine enum);
  `judgment` is distilled prose (drift advisory). This mirrors
  `build-trace-model.py` diffing only the derived part.
- **Library parser.** A dedicated 2-level block parser (`load_tasks`) in
  `openup-process-map.py` — not the flow-map parser — so `judgment` prose bullets
  stay one-per-line readable. Still stdlib-only (no pyyaml).
- **Distillation offline.** This sandbox can't reach an LLM endpoint, so the
  committed `judgment` bullets were authored + reviewed in-session (the sanctioned
  strong-model-reviewed-committed step); `--offline` prompt emission is the
  reproducible path and is tested.
- **Doctor wiring deferred to T-107** (its own deliverable) — `build-task-library.py
  --check` needs the vendored KB, which a downstream project lacks, so wiring it
  into doctor now would false-positive. T-105 ships the `--check` CLI only.

## Requirement verification (complete-task step 1a) — graded against the diff
- ✅ **R1** eight-field defs, `artifact` spine-typed — `task-library.yaml` (8 defs);
  `validate_tasks` enforces. `test_parses_all_fields`.
- ✅ **R2** `tasks --validate` hard-gates malformed defs — `validate_tasks` +
  `tasks` subcommand; `test_bad_artifact_enum`/`test_missing_field`/etc. exit-2 path.
- ✅ **R3** Stage-1 deterministic extraction — `extract_skeleton`;
  `test_skeleton_fields` (role/inputs/name from KB fixture), verified live on the
  real vision + plan-iteration KB files.
- ✅ **R4** distillation + `--offline` no-network — `distill_judgment` +
  `distillation_prompt`; `test_offline_emits_prompts_no_network`.
- ✅ **R5** `--check` drift, exit 1 on mutation / 0 in-sync — `check_drift`;
  `test_detects_mutated_skeleton` + `test_in_sync` + subprocess CLI test; shipped
  library `--check` green.
- ✅ **R6** zero engine behavior change — no `openup_agent/*` touched; repo-root
  suite 106 pass, scripts/tests 603 pass. (2 pre-existing failures on
  harness-optional, NEITHER caused by T-105: `test_openup_state::test_init` is
  stale [expects schema 1; init now writes schema 2, T-078];
  `test_openup_doctor::test_json_shape` is a T-117 regression — `as_dict` gained
  `fix_class`/`fix_cmd` — to be fixed separately on harness-optional.)

## Success measure / rollout
- Success Measures: `n/a` — inert object code; program measure read at T-106.
- Rollout: `n/a` — internal build tooling + committed data, unconsumed until T-106.

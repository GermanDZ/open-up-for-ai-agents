# T-106 design / in-flight decisions

## Key decisions
- **Injected seam.** Replaced the `run_procedure(skill, instruction)` injected
  callable with `run_task(task_def, instruction)` + a `task_defs` map. plan_iteration
  stays LLM-free and hermetically testable; cycle.py wires the real `run_task`
  (builds the generic system prompt, calls `loop.run(system_prompt=…, model=…)` —
  the T-089 file-skipping seam — then stamps via the def).
- **Generic system-prompt shell** (`_task_system_prompt`) frames role + sentinel
  (`OPENUP-TASK: DONE`, matches `loop.SENTINEL_RE`); the def specifics
  (judgment/inputs/output) travel in the instruction. No procedure file is read.
- **Authoring tier.** `run_task` resolves the `authoring` tier (what the create-*
  procedures declared) explicitly, since `system_prompt` bypasses procedure-tier
  resolution; falls back to the step model if absent.
- **Stamping keyed off the def.** `stamp_for_task(root, def)` uses `artifact` +
  `output_path`; a plain view (`author-initial-roadmap` → `docs/roadmap.md`) stamps
  nothing (`PLAIN_VIEW_PATHS`). Retired the interim `PROCEDURE_ARTIFACTS` table.
- **Roadmap format = data.** The T-099 pinned format now lives in the
  `author-initial-roadmap` def's `judgment` bullets; `ROADMAP_FORMAT` constant
  removed. openup-roadmap.py's parser matches header columns by name, so the def's
  5-col `| ID | Title | Status | Priority | Depends on |` is promotable.
- **One commit per activity.** All of an activity's ordered tasks author into the
  same gated `docs/` commit (T-108 discipline preserved).

## Requirement verification (complete-task step 1a) — graded against the diff
- ✅ **R1** `tasks:` field + validate join — `_activity_record`/`activities_for` expose
  it; `validate(mp, task_ids)` rejects unresolved ids; `test_task_map_wiring` +
  shipped-map join test.
- ✅ **R2** ordered task iteration, generic system prompt, no procedure read —
  plan_iteration direct branch loops `lane["tasks"]`; cycle `run_task` uses
  `system_prompt`; `test_direct_activity_runs_ordered_tasks_no_lane` asserts both
  tasks run in order.
- ✅ **R3** stamping off def artifact/output_path — `stamp_for_task`;
  `test_task_def_stamps_its_artifact` + `test_roadmap_plain_view_is_never_stamped`.
- ✅ **R4** roadmap format in the def, constant retired —
  `test_roadmap_task_carries_pinned_format` asserts the header reaches the roadmap
  task instruction AND `not hasattr(pi, "ROADMAP_FORMAT")`.
- ✅ **R5** bench scenario wired to usage/debug logs — `inception-taskdef`
  (`command: cycle`, deliverable `docs/product/vision.md`); the bench sets
  `OPENUP_AGENT_USAGE_LOG`; scenario description names the debug-log restart check.
- ✅ **regression** full suite green — 718 passed, 0 failed. `spec-then-execute`
  lane path unchanged.

## Success measure / rollout
- Success Measure: the **live behavioral acceptance** (qwen batch: zero mid-run
  restarts, ≤6 iters/sub-run, ≥80%/5 runs, ≤⅓ context) is read by the OWNER post-merge
  via the `inception-taskdef` bench — this sandbox has no LLM endpoint. **T-107 stays
  gated on it.** The hermetic acceptance (no procedure read, engine-stamped, roadmap
  promotable) is proven here.
- Rollout: `n/a` — internal driver behavior on harness-optional; no flag; Claude Code
  path unchanged.

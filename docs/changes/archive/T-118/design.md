# T-118 design / verification

## Requirement grade (complete-task step 1a) — against the diff
- ✅ **R1** concrete path named — `render_task_instruction(input_path=...)` emits
  "Read the provided input file at `<path>` FIRST"; direct branch passes the
  lane's `requires_input.path`. `test_task_instruction_names_concrete_input_path`.
- ✅ **R2** no-requires_input unchanged — falls back to "Inputs to read:";
  `test_no_requires_input_uses_plain_inputs_line`.
- ✅ **R3** workproduct names kept as secondary — "Additional inputs to consider: Vision";
  asserted in both new tests.

## Evidence / motivation
Live qwen-27b run (2026-07-15): the vision sub-run spent 5 globs / 4 turns hunting
for `docs/inputs/stakeholder-brief.md` before reading it — the def's `inputs`
carry KB workproduct display-names, not paths. This names the concrete
`requires_input.path` so the model reads it in one call.

## Success measure / rollout
- Success measure read-back: the next `inception-taskdef` batch (owner endpoint) —
  vision sub-run should reach its input in ≤1 tool call.
- Rollout: n/a — internal driver instruction text.

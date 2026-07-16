# T-120 — in-flight design + completion verification

## Completion verification (step 1a) — requirements graded against the diff

Graded against `git diff harness-optional...HEAD` and the passing test suite
(the Given/When/Then **Then**-checks are the hermetic tests). All ✅.

1. ✅ **Judgment-box briefings inline the change folder's content** —
   `cycle.build_step_instruction(root, plan_text=…)` inlines plan/design/
   resumable-input via `plan_iteration.inline_file`; the executor threads the
   already-read `plan_text` through `_dispatch_judgment`/`run_judgment_step`.
   Then: `test_judgment_instruction_inlines_plan_and_design`,
   `…_inlines_resumable_input` pass.
2. ✅ **Task-def inputs resolve to concrete paths + inline** —
   `_input_path_map` (keyed by artifact slug + output stem) + the resolve/inline
   loop in `render_task_instruction`; `run_plan_iteration` passes `task_defs`.
   Then: `test_task_instruction_resolves_and_inlines_workproduct_input`,
   `…_absent_input_file_degrades`, `…_unresolvable_name_degrades` pass.
3. ✅ **Spec lanes carry engine-read vision** — `vision_block` read once before
   the lane loop, inlined into every `LANE_SPEC_CONTRACT` via `%(context)s`.
   Then: `test_spec_lane_instruction_inlines_vision` (asserts inlined into all
   lanes; directive dropped) passes.
4. ✅ **Assess grading carries a deterministic evidence bundle** —
   `assess._iteration_evidence` (delivered lanes + status + touches paths) fed
   into `render_grading_instruction(evidence=…)`; wired in `run_assess`.
   Then: `test_grading_instruction_includes_evidence`,
   `test_iteration_evidence_lists_delivered_lanes` pass.
5. ✅ **Every inlined block is size-capped with a path marker** —
   `inline_file` caps at `INLINE_CAP` (12k) and appends
   `… [truncated — full file at \`<path>\`]`. Then:
   `test_inline_file_caps_with_path_marker` passes.
6. ✅ **No regression on absent context** — `inline_file` returns '' on
   absent/blank; each builder degrades to the pre-T-120 path-naming lines.
   Then: `test_judgment_instruction_degrades_without_root`,
   `…_degrades_when_plan_absent`, `test_spec_lane_instruction_degrades_without_vision`,
   `test_task_instruction_without_library_is_unchanged` pass.

Full suite: 634 passed (0 fail). Gates: check-docs OK · spec-scenarios 6/6
G/W/T · fence clean (base harness-optional).

## Success-measure instrumentation (step 1b)

✅ **Instrumentation pre-exists** — the falsifiable measure (median ≤3 turns per
authoring/judgment sub-run, zero `read_file` of engine-inlined files) is read
from `OPENUP_AGENT_DEBUG_LOG` (per-call tool-call trace, `loop._append_debug`,
T-098) + `OPENUP_AGENT_USAGE_LOG` (per-call tokens/latency, `loop._append_usage`,
T-080). No new instrumentation needed — this change makes the traces *improve*;
it does not need to add a meter.

**Read-back**: the next live bench batch on the owner's endpoint
(`inception-taskdef` / `cycle-quick-doc` scenarios) — same gate as T-107's live
qwen batch. Expected: sub-runs stop `read_file`-ing the inlined plan/vision/
inputs; median sub-run turns drop toward ≤3.

## Design decisions

- **Helper home** — `inline_file` lives in `plan_iteration.py`; `cycle.py`
  imports it (already depends on `plan_iteration`). `assess.py` keeps its own
  self-contained `_iteration_evidence` + minimal frontmatter reader rather than
  importing, preserving its "imports nothing from cycle" property.
- **Name→path resolution excludes self** — a def never resolves its own output
  as an input (avoids an authoring task reading its own prior artifact).
- **Cap = 12k chars** (~3k tokens) per file — bounds the first prompt while
  fitting a whole vision/plan; the marker names the path so the remainder is
  still reachable by `read_file`.

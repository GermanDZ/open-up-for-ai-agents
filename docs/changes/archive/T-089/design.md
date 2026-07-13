# T-089 — design notes & test record

## In-flight decisions

- **DD1 — gates-then-tick (deviation from the exploration's pseudocode order).**
  Exploration §3 sketched "tick the box; gates"; the engine runs **gates before
  ticking** so a gate failure (exit 6) leaves the box unchecked and a resumed
  cycle retries the step. Ticking first would mark a step done whose output the
  gates rejected, and resume would skip it. Stated in spec Req 4.
- **DD2 — sub-run step contract lives in the engine, not the pack.**
  `cycle.py` carries `STEP_SYSTEM_PROMPT` and calls `loop.run()` with the new
  additive `system_prompt=`/`model=` params (default path byte-unchanged;
  `run`'s 55 pre-existing tests pass unmodified). Moving step contracts into
  the procedure pack is T-091's ceremony/judgment split. (Spec assumption.)
- **DD3 — command extraction rule.** Backtick spans win (a span starting
  `python3 `/`git ` runs verbatim; a bare `scripts/<x>.py` span gets `python3`
  prepended); otherwise the first `python3 `/`git ` token to end-of-line is the
  command. Convention documented in `reference-driver.md`: keep script-step
  boxes command-only — trailing prose after an unquoted command becomes part of
  the command line. A box that names a script with no extractable command falls
  back to judgment (safe: the sub-run may still run it via `exec`).
- **DD4 — sync-status.py is fail-open at completion.** A genuinely bootstrapped
  project (the T-085 bench fixture shape) has no `docs/roadmap.md` /
  `docs/project-status.md`; the views regeneration logs a warning and the cycle
  continues. The hard gates (fence, check-docs) stay blocking. Mirrors the
  driver's absent-gate skip spirit.
- **DD5 — completion ceremony order** mirrors `/openup-complete-task` §4–§7:
  plan `status: done` → status-note shard → `log-event task_completed` +
  `set-gate log_written` → `sync-status.py` (fail-open, DD4) → final gates →
  `retro increment` (fail-open) → `session end --archive-to <change
  folder>/state.json` → `git mv` to archive → one completion commit → merge
  `task/<id>-cycle` back to the starting branch (`--no-ff`). PR/auto-merge
  ceremony (skill §8–§9) is deliberately absent — the driver targets a
  no-remote world; the merge-back is its local equivalent. `verified` stays
  reserved for rubric-graded full-track completions; the engine writes `done`.
- **DD6 — engine composes, never reimplements.** Board/session/state/sync/gates
  all run as subprocesses under `--dir`. The engine's only repo readers are a
  20-line scalar frontmatter reader, the state/cycle sidecar JSON, and the
  Operations box parser. `.openup/cycle.json` (Ring-3 sidecar, next to
  state.json) records `{task, branch, base_branch}` for crash-safe merge-back.
- **DD7 — `--max-iterations` maps to the per-step cap in bench cycle runs**
  (`--step-max-iterations`), keeping one knob across both commands.

## Verification record (tester hat, 2026-07-13)

- `python3 -m unittest scripts.tests.test_openup_agent scripts.tests.test_openup_agent_tools scripts.tests.test_openup_agent_bench scripts.tests.test_openup_agent_cycle`
  → **76 tests, OK** (55 pre-existing — unmodified except two additive bench
  cases — + 19 new cycle tests + 2 new bench-cycle tests).
- New cycle tests cover: all five decision-path dispatches (noop sentinel,
  3× unsupported exit 7 with no begin, pick acquires via one `begin` with zero
  LLM), script-step exec + failure (exit 8, box unticked), judgment instruction
  content (box text + hat + change-folder briefing), gate failure (exit 6, box
  unticked), suspend propagation (exit 5), resume-at-second-box with no
  re-begin, classification matrix (plain/backtick/bare-span/prose/markers/hats),
  full completion ceremony (sentinel parity, archive, state archived+removed,
  shard, ceremony order, merge-back) and the whole judgment path through
  `loop.run` with a scripted LLM (tier `authoring` → `OPENUP_MODEL_MID`;
  sub-run stdout kept off the engine's stdout).
- Bench `CycleScenarioTest`: one `cycle-quick-doc` run through the REAL harness
  + REAL fixture scripts against a mock endpoint → outcome `pass`, sentinel
  `OPENUP-NEXT: ADVANCED — BENCH-001`, deliverable produced, lane archived,
  fence + check-docs recomputed green, **2 LLM calls total** (vs the scripted
  `next` baseline's 3 minimum and a live model's 37–50).
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-089/plan.md` → exit 0.
- `python3 scripts/check-docs.py` → OK (8 instances).
- `python3 scripts/openup-fence.py check --base harness-optional` → 14 changed
  file(s) within lane.
- Fresh-dir manifest install (`install_process_clis` → temp dir): 30 CLIs
  installed, `openup_agent/cycle.py` lands, `import openup_agent.cycle` OK (Req 9).

## Success-measure read-back (pending, owner-side)

✅ instrumentation — `OPENUP_AGENT_USAGE_LOG` per-call capture pre-exists (T-080, `scripts/openup_agent/loop.py::_append_usage`); this diff adds the `cycle-quick-doc` scenario + bench `command` support that produce the comparable `summary.json` batches. Read-back: owner's next live bench batch after merge (record here + roadmap program block).

The ≥5× token claim is measured on a live local model: run
`python3 scripts/openup-agent-bench.py --scenario scripts/bench-scenarios/cycle-quick-doc --runs 5`
and compare `summary.json` `tokens_total` against a same-model `quick-doc`
batch (T-080 baseline: 1–2M tokens/run). Record the numbers here and in the
roadmap program block. This sandbox cannot reach a local endpoint (T-080/T-086
precedent).

## Requirement grade vs implementation (complete-task §1a)

1. ✅ deterministic decision + acquire (`resolve` → `begin`, zero LLM — test:
   `test_pick_acquires_via_session_begin_without_llm`)
2. ✅ script-step dispatch (`test_script_step_runs_as_code_no_llm`)
3. ✅ judgment dispatch, fresh + bounded, instruction carries box/hat/briefing
   (`test_judgment_instruction_carries_box_hat_and_briefing`,
   `test_scripted_llm_subrun_end_to_end`)
4. ✅ gates-then-tick, resumable on failure (`test_gate_failure_exits_6_box_unticked`)
5. ✅ deterministic completion + sentinel parity (`test_full_completion_ceremony_and_sentinel`)
6. ✅ crash-safe resume (`test_resume_starts_at_first_unchecked_box`)
7. ✅ unsupported paths degrade cleanly / noop parity
   (`test_unsupported_paths_exit_typed_without_begin`, `test_noop_prints_done_sentinel`)
8. ✅ benchmarkable + regression-free (`CycleScenarioTest` + 55 pre-existing tests OK)
9. ✅ shipped via manifest (fresh-install verify above)

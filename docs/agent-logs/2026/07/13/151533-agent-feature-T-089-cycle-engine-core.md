# Agent Run — T-089 (feature/T-089-cycle-engine-core)

- **Task**: T-089 — Cycle engine core: deterministic pick/resume + Operations-step executor
- **Phase**: construction (iteration 59, standard track, solo, worktree)
- **Start**: 2026-07-13T14:49:47Z
- **End**: 2026-07-13T15:15:33Z
- **Commits**: 391ef19 docs(T-089): grade success-measure instrumentation (1b) [T-089];2554209 test(T-089): verification record + design decisions [T-089];a3a6a25 docs(T-089): document cycle engine in reference-driver + CLI reference [T-089];ae021a1 feat(T-089): ship cycle via manifest + cycle-quick-doc bench scenario/support [T-089];c0dd753 feat(T-089): cycle engine core — deterministic pick/resume + step executor + completion [T-089];
- **Files changed**: scripts/openup_agent/cycle.py (new), scripts/openup_agent/loop.py, scripts/openup_agent/tiers.py, scripts/openup-agent.py, scripts/openup-agent-bench.py, scripts/bench-scenarios/cycle-quick-doc/ (new), scripts/tests/test_openup_agent_cycle.py (new), scripts/tests/test_openup_agent_bench.py, scripts/process-manifest.txt, docs-eng-process/reference-driver.md, docs-eng-process/script-cli-reference.md, docs/changes/T-089/
- **Decisions**: DD1 gates-before-tick (resume retries a gate-failed step); DD2 step contract in the engine via additive loop.run(system_prompt=, model=); DD3 command-extraction convention (backticks win, token-to-EOL fallback, command-only boxes); DD4 sync-status fail-open on bootstrapped trees; DD5 completion mirrors complete-task with local merge-back instead of PR; DD6 compose-never-reimplement; DD7 one iteration knob across run/cycle in bench. Full detail: docs/changes/T-089/design.md.
- **Verification**: 76 driver+bench+cycle tests OK; spec-scenarios, check-docs (+ --coverage), fence (--base harness-optional) green; fresh-dir manifest install verified (30 CLIs).

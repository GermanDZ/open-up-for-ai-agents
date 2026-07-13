# T-095 — design notes & test record

## In-flight decisions

- **DD1 — stdout captured-then-re-emitted, stderr streamed.** The driver's
  progress lives on stderr (inherited fd, streams live); its stdout is only
  the sentinel, so the wrapper pipes it, re-emits byte-exact, and reads it to
  pick the right guidance (ADVANCED vs DONE). Outer-loop contract preserved:
  sentinel on stdout, guidance stderr-only, exit code passthrough.
- **DD2 — the wrapper never overwrites a brief**, even one still carrying the
  template marker (a half-filled brief is human work in progress); it only
  creates the template when the file is absent.
- **DD3 — env precedence: exported beats `.openup/agent.env`** (`setdefault`
  fold), so a one-off `LLM_API_URL=… ./scripts/next-cycle` override works.
  Interactive setup persists only on an explicit "yes".
- **DD4 — TTY detection (`sys.stdin.isatty()`) drives both** the env prompt
  and the `--interactive` flag passed to the driver — a human at a terminal
  gets asked things; CI/cron gets suspends and setup blocks.
- **DD5 — exec bit ships through the manifest installer as-is** (`cp`
  preserves mode); verified by a test running the real
  `install_process_clis` and asserting `S_IXUSR` + shebang — no installer
  change needed.
- **DD6 — Inception instruction asks create-vision for vision + initial
  roadmap in one run** (5–8 pending rows, table shape `openup-roadmap.py`
  parses) so the very next `next-cycle` lands in the T-092/T-094 pipeline.

## Verification record (tester hat, 2026-07-13)

- `python3 -m unittest scripts.tests.test_next_cycle
  scripts.tests.test_openup_agent scripts.tests.test_openup_agent_tools
  scripts.tests.test_openup_agent_cycle scripts.tests.test_openup_agent_bench
  scripts.tests.test_openup_roadmap` → **136 tests, OK** (13 new; every
  pre-existing test unmodified — the wrapper is purely additive).
- Covered: agent.env reaches the driver / exported wins / off-TTY missing env
  → setup block + exit 2 + zero invocations; interactive prompt sets + persists
  (ask seam); fresh project → template brief + stop (no driver call);
  template-marked brief untouched; filled brief → exactly one `run
  --procedure openup-create-vision` whose instruction names the brief,
  vision, and roadmap; started project → exactly one `cycle` without
  `--interactive` off-TTY with exit passthrough; suspend (5) → sentinel on
  stdout verbatim + answer-flow guidance on stderr; ADVANCED → "run again";
  every typed exit (2/3/4/6/7/8) yields `[next-cycle]` guidance; not-a-project
  → exit 2; real `install_process_clis` lands `next-cycle` executable with the
  python3 shebang.
- `openup-spec-scenarios.py check` exit 0; `check-docs.py` OK; fence
  (`--base harness-optional`) — 8 files, all in lane.
- Live guided-stage walk on my-product (endpoint-free stages) recorded in the
  completion summary: template-brief stage and cycle passthrough verified on
  the real project after ship.

## Success-measure read-back (pending, owner-side)

✅ instrumentation — none needed beyond the session transcript: the measure is
"every stage transition reached by re-running `./scripts/next-cycle` alone".
Record the outcome of the owner's next live my-product session here
(endpoint-dependent stages — Inception, judgment steps — can't run in this
sandbox; T-089/T-092/T-094 precedent).

## Requirement grade vs implementation (complete-task §1a)

1. ✅ env loading + guidance (`test_agent_env_reaches_the_driver`,
   `test_exported_env_wins_over_file`,
   `test_missing_env_offtty_guides_and_exits_2`,
   `test_interactive_prompt_sets_and_persists`)
2. ✅ fresh project → template brief, human turn
   (`test_writes_template_brief_and_stops`,
   `test_template_brief_not_overwritten`)
3. ✅ filled brief → Inception run (`test_filled_brief_runs_inception` —
   procedure + instruction contents asserted)
4. ✅ normal state → one TTY-aware cycle
   (`test_started_project_runs_one_cycle_no_interactive_offtty`)
5. ✅ exit translation + sentinel passthrough
   (`test_sentinel_passthrough_and_suspend_guidance`,
   `test_advanced_suggests_running_again`,
   `test_every_typed_exit_has_guidance`)
6. ✅ shipped + executable (`test_manifest_install_lands_executable_with_shebang`
   — real installer, exec bit, shebang)

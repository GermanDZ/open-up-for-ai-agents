# T-074 — Design decisions (in-flight)

## Base branch / lane
Branched off `harness-optional` (in-place), standard track, iteration 44. PR targets
`harness-optional`.

## Decisions
- **DD1 — Reuse, don't fork, the async-input contract.** The resume half
  (`openup-input.py resumable`, board `suspended`, `/openup-next` step 0) is untouched.
  T-074 only adds a *producer*: a deterministic `openup-input.py request` subcommand that
  writes a well-formed request (same frontmatter the Claude skill produces) and inserts the
  `awaiting-input:` line. A driver-created request is indistinguishable to `resumable` from
  a skill-created one — proven by `test_round_trip_answered_request_is_resumable`.
- **DD2 — Creation is a script, not inline driver code.** `openup-input.py request` makes
  request-creation harness-agnostic (any harness can raise a blocking question, not just
  Claude Code) and unit-testable. The driver's async path just shells out to it via the
  allowlisted `exec` surface — the driver stays thin.
- **DD3 — `ask_user` is loop-intercepted, not Tools-dispatched.** It is the 7th advertised
  tool (`TOOL_NAMES`, `TOOL_DEFS`) but needs stdin / the creator / the active task, so
  `loop._dispatch_tool_calls` handles it and `Tools.dispatch` guards on the 6-entry
  `DISPATCH_TOOL_NAMES`. Interactive → answer returned as the tool result; async → create
  request, print `OPENUP-AGENT: SUSPENDED — <path>`, return exit 5.
- **DD4 — Active lane from `.openup/state.json`.** The async path reads `task_id` from
  state under `--dir` to know which lane to suspend; absent → request created, no lane
  suspended (still a clean suspend for a lane-less run).
- **DD5 — Async is the default; `--interactive` opts into TTY.** Blocking on a TTY is wrong
  for CI/service, so unattended runs suspend cleanly. The same `--interactive` flag is the
  intended future home for plan-gate approval (the exploration's open question) — wired for
  `ask_user` now, hook left for the gate.
- **DD6 — Distinct exit code 5.** So an outer loop tells "suspended, awaiting human" apart
  from success (0) / config (2) / endpoint (3) / max-iter (4).

## Verification
- 48 hermetic tests green (10 new: `test_openup_input_request.py` = 7, driver `AskUserTest`
  = 2, tools coverage = 1). Round-trip (driver-created → answered → `resumable`) proven.
- check-docs clean.

## Read-back for the Success Measure
Falsifiable expectation met by the round-trip test: a driver-created request resumes through
the *unchanged* `resumable` path. Manual driver suspend/resume against a live model is an
optional owner check (record here if run).

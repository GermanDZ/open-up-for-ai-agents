# T-044 — Design / Completion grade

## DD1 — remote-check is advisory/fail-open, not a hard gate

The local lease fail-*closes* on a corrupt claim (unknowable surface). The
remote check is the opposite: it consults the network, which can be absent
(offline), unreachable, or auth-gated. Blocking work on any of those would make
the framework unusable on a plane or a fresh clone. So every remote error exits
`0`. The hard gate stays the local lease + PR-time review; this only adds a
warning the lease structurally cannot give (it never sees other clones).

## DD2 — branch name as the cross-machine claim signal

Of the exploration's options, branch-as-claim reuses a signal lanes already push
(`fix/T-NNN-*`), needs no new refspace or ledger, and ships in one subcommand.
Matching is token-bounded (regex lookarounds) so `T-44` ≠ `T-044`. The heavier
atomic `refs/openup/claims/*` ref-lock (Option A) is deliberately NOT built — it
is gated behind the `duplicate_start_blocked` counter this task emits.

## Completion grade (step 1a) — requirements vs diff (a634a8b)

- ✅ **R1** remote-check subcommand — `cmd_remote_check` + `remote_check()` in
  openup-claims.py; argparse `remote-check` parser with `--remote/--no-fetch/
  --self-branch`. All four R1 scenarios are covered by tests
  `test_remote_duplicate_refused` (exit 9), `test_no_match_is_ready` (exit 0),
  `test_self_branch_excluded` (exit 0), `test_missing_remote_fails_open` (exit 0).
- ✅ **R2** token-accurate matching — `task_branch_match()` with non-alphanumeric
  lookarounds; verified by `test_token_accuracy_no_false_positive` and the inline
  matcher checks (`T-44`/`T-0440`/`xT-044` all reject).
- ✅ **R3** wired before claim — `openup-start-iteration` step 6b runs remote-check
  as step 0 (exit 9 → abort before preflight/claim); `openup-next` step 2 notes
  the delegated guardrail. (Skill prose change; graded by reading the diff.)
- ✅ **R4** duplicate-start counter — step 6b emits `openup-state.py log-event
  --event duplicate_start_blocked` on exit 9 (clock-stamped, append-only JSONL).
- ✅ **R5** fail-open — `remote_check()` returns `(EXIT_OK, "SKIP (advisory)…")`
  on missing/unreachable remote; `test_missing_remote_fails_open` asserts exit 0.

No ❌. The 1 suite-wide failure (`test_docs_index…test_write_creates_index_file`)
is the pre-existing macOS `/var`↔`/private/var` path assertion, unrelated to this
diff (docs-index.py is not touched).

## Success-Measure grade (step 1b)

✅ Instrumentation exists: the `duplicate_start_blocked` event is emitted by the
wired skill step (R4) and lands in `docs/agent-logs/agent-runs.jsonl` via the
deterministic logger. Counting `grep duplicate_start_blocked` over the run log is
the falsifiable read-back that decides whether Option A is ever justified.
Read-back: revisit at the next retrospective with parallel-work activity.

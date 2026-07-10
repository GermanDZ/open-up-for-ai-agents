# T-066 — in-flight decisions + completion verification

## Context

Surfaced live: `/openup-next` re-promoted T-065 (delivered in the still-open PR #64).
Root cause: `openup-roadmap.py cmd_next`'s in-flight guard is **local-only**
(`_active_folder` OR live lease); a task delivered-but-unmerged has neither on trunk
(archived folder + lease live on the branch), so it read as promotable. Fix = a remote
branch-as-claim guard, reusing the T-044 mechanism.

## Key decision (deviation from spec Operations wording)

The spec's first Operations bullet named `claims.remote_task_branches(id, …)` **per
candidate**. That would run one `ls-remote` per candidate, violating Requirement 3
(one round-trip per invocation). I instead fetch **all** `origin` heads **once** (cached,
mirroring `remote_task_branches`'s fail-open probe) and filter each candidate with the
**reused** `claims.task_branch_match`. Behaviour-equivalent, honours req 3, and avoids
touching `openup-claims.py` (out of lane). The Operations text was reconciled to match.

## 1a. Requirement verification (graded vs the diff `origin/main...HEAD`)

- ✅ **R1** (path precedence + remote skip) — `cmd_next` loop calls `remote_branch_for()`
  after the local/dep checks; `test_matching_branch_skipped` (branch → next task) and
  `test_no_matching_branch_promotes` (no branch → promoted) both green.
- ✅ **R2** (fail-open) — `_remote_head_branches` returns `(…, error)`; `remote_branch_for`
  returns None on any error → promote. `test_missing_remote_fails_open` +
  existing non-git-repo `Next.*` tests still green (they hit the error path).
- ✅ **R3** (reuse T-044 matcher + one ls-remote) — filter uses `claims.task_branch_match`;
  `_heads_cache` single-slot → `test_ls_remote_called_once_across_candidates` asserts
  exactly 1 `ls-remote` across 2 remote-checked candidates.
- ✅ **R4** (`--no-remote-check`) — flag on the `next` subparser;
  `test_no_remote_check_bypasses_guard` returns the matching-branch candidate.
- ✅ **R5** (remote-specific reason) — `remote_skipped` → exit-3 reason names the branch +
  "merge its PR instead of re-promoting"; `test_sole_candidate_remote_skipped_exits_none_with_reason`.
- ✅ **R6** (`openup-board.py resolve` inherits) — `_promote_next` calls `cmd_next` with a
  `SimpleNamespace` lacking the new attrs; `getattr` defaults the guard **on**. Verified
  functionally: `resolve` returns `path=noop` ("…delivered-but-unmerged… merge its PR")
  for a task with an origin branch, `path=promote` without. No edit to `openup-board.py`.
- ✅ **R7** (docs) — `/openup-next` SKILL §1c promote + noop bullets and
  `script-cli-reference.md` document the skip + `--no-remote-check`/`--remote`.

All 7 ✅ — no ❌.

## 1b. Success-measure instrumentation

Measure: "zero re-promotions of a delivered-but-unmerged task." Instrumentation is
twofold and **exists in the diff**: (a) the guard's own regression test
`test_sole_candidate_remote_skipped_exits_none_with_reason` replays the T-065/PR-#64
scenario and asserts a skip, not a promote; (b) `docs/agent-logs/runs/` (pre-existing)
records promote cycles, so a re-promotion of an open-PR task would be visibly absent.
✅ instrumentation present. Read-back: next unmerged-PR-across-a-cycle occurrence.

## Bonus test

`test_token_boundary_no_false_positive` — `feat/T-1010-…` must not match `T-101`
(delimited-token match via the reused T-044 regex).

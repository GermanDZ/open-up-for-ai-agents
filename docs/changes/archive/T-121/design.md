# T-121 — in-flight design + completion verification

## Scope decision (2026-07-16): B3 deferred

The review's B3 ("prose-safe Operations-box classification") was dropped from
this sweep after reading the existing tests. `test_backticked_git_command_is_script`
and `test_plain_python3_command_is_script` **deliberately assert** that a command
mid-prose (backticked or bare) *is* a script step — syntactically identical to
B3's example "use `git log` to understand history". No parser recovers author
intent; the `(judgment)` marker is the existing escape hatch. Making
classification prose-safe is a **contract change**, not a bug fix. Applied
fix-spec-first: spec + roadmap row narrowed to B1, B2, B4, B5, B6, B7 before any
code. (`extract_command`/`classify_box` behavior is unchanged; the B4 fix only
restricts extraction to the box's *first line*, which is identical for the
single-line boxes those tests use.)

## Completion verification (step 1a) — requirements graded against the diff

Graded against `git diff harness-optional...HEAD` and the passing tests (the
G/W/T **Then**-checks are the hermetic regression tests). All ✅.

1. ✅ **B1 — grep ignores VCS/vendor + skips oversized files** —
   `_GREP_IGNORE_DIRS` prune of the rglob walk + `_GREP_MAX_FILE_BYTES` size skip
   (`tools.py`). Then: `test_grep_default_ignores_git_and_vendor`,
   `test_grep_skips_oversized_file`, `test_grep_explicit_path_into_ignored_dir_still_works`.
2. ✅ **B2 — exec cwd-escape returns an error, never crashes** — `cwd` `_resolve`
   wrapped to return `ERROR:`; `dispatch` also catches `ToolError` (`tools.py`).
   Then: `test_exec_cwd_escape_returns_error_not_crash`,
   `test_dispatch_exec_cwd_escape_is_string`.
3. ✅ **B4 — wrapped judgment-box bodies preserved** — `parse_boxes` appends
   continuation lines to the current box body; `extract_command` reads the first
   line only (`cycle.py`). Then: `test_wrapped_box_retains_continuation_in_body`,
   `test_wrapped_continuation_does_not_flip_judgment_to_script`,
   `test_wrapped_box_first_line_command_still_scripts`.
4. ✅ **B5 — completion merge-fail does not strand the lane** — `complete()`
   aborts the merge, checks out the branch, records `pending_merge`, returns
   `EXIT_STEP`; `_retry_pending_merge` retries it in the recovery pre-pass
   (`cycle.py`). Then: `test_complete_merge_conflict_records_pending_and_leaves_base_clean`,
   `test_retry_pending_merge_merges_and_clears_marker`,
   `test_retry_pending_merge_conflict_keeps_marker_and_returns_to_branch`,
   `test_retry_pending_merge_noop_without_marker`.
5. ✅ **B6 — read_file marks truncation** — whole-file read over `_MAX_READ_BYTES`
   appends `… [truncated — full file at <path>]` (`tools.py`). Then:
   `test_read_file_truncation_marks_and_names_path`, `test_read_file_under_cap_unmarked`.
6. ✅ **B7 — exec output capped** — `_cap` on each stdout/stderr, `exit=` line
   preserved (`tools.py`). Then: `test_exec_output_capped_with_marker`.

Full suite: 649 passed (0 fail). Gates: check-docs OK · spec-scenarios 6/6
G/W/T · fence clean (base harness-optional, 8 files in lane).

## Success-measure instrumentation (step 1b)

n/a — argued in the spec. This is an internal correctness sweep; the falsifiable
check is the six hermetic regression tests (each reproduces the pre-fix failure).
No runtime metric or flag.

## Design decisions

- **B4 + retained match-anywhere is safe** because `extract_command` now reads
  only the first physical line: a continuation that mentions a command cannot
  flip a judgment box to a script step, and single-line boxes classify
  identically (the tested contract is untouched).
- **B5 recovery via `.openup/cycle.json`** — the cycle engine runs in-place (one
  checkout, not a worktree), so the `pending_merge` marker survives to the next
  cycle; `_retry_pending_merge` runs before `resolve_decision` (gated by
  `recover`, consistent with `reconcile_unclosed_lanes`).
- **Caps chosen conservative**: grep skips files > 1 MB; exec caps each stream at
  40 k chars; read_file marker fires at the existing 400 k cap — each only
  engages on the failure path, so the happy path is byte-identical.

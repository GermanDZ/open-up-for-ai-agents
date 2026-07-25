# T-131 — Implementation-vs-spec verification

## Requirements grading (against `git diff origin/main...HEAD`)

1. ✅ `used_seqs_in_repo()` scans `docs/agent-logs/runs/*.jsonl` `task_id`
   fields — `scripts/openup-claims.py` (new block after the `docs/changes`
   scan). Scenario proven by
   `test_next_id_scans_runlog_shard_task_ids` (`scripts/tests/test_openup_claims.py`).
2. ✅ `used_seqs_in_repo()` scans `docs/status-notes/YYYY-MM-DD-<id>.md`
   filenames — same function, `note_pat` block. Scenario proven by
   `test_next_id_scans_status_note_filenames`.
3. ✅ Malformed shard line / non-matching status-note filename degrades
   silently — `json.JSONDecodeError` caught per-line; `note_pat.match` returns
   `None` and is skipped. Scenario proven by
   `test_used_seqs_skips_malformed_shard_line_and_nonmatching_note`.
4. ✅ `openup-session.py begin` stamps `base_sha` into the claim file and
   `.openup/state.json` — `_current_head_sha()` computed once in `cmd_begin`,
   threaded into `claim_argv`/`init_argv`; `--base-sha` added to
   `openup-claims.py claim` and `openup-state.py init` (+ schema). Scenario
   proven by `test_begin_stamps_base_sha_into_claim_and_state`
   (`scripts/tests/test_openup_session.py`) — asserts both files carry the
   real `git rev-parse HEAD` value.
5. ✅ `resolve_base` prefers the stamped `base_sha` over `origin/main`/`main`
   when no explicit `--base`, and an explicit `--base` still wins —
   `scripts/openup-fence.py:resolve_base`. Both scenarios proven:
   `test_stamped_base_sha_excuses_a_prior_already_merged_lane` (zero
   violations for the prior lane's file) and
   `test_stamped_base_sha_still_catches_a_genuine_out_of_lane_file` (a
   genuinely out-of-lane file in the second lane's own commit is still
   caught) in `scripts/tests/test_openup_fence.py`; explicit-override proven
   by `ResolveBaseTests.test_explicit_wins_over_stamped` +
   `test_explicit_unresolvable_does_not_fall_back` (preserves the pre-existing
   contract exercised by `test_unresolvable_base_is_inapplicable_not_fatal`).
6. ✅ A pre-existing state file with no `base_sha` key degrades to the
   `origin/main`/`main` chain — proven by
   `test_no_base_sha_falls_back_to_origin_main_chain` and
   `ResolveBaseTests.test_falls_through_to_origin_main_then_main_when_no_stamped`.

**Result: 6/6 ✅. No requirement unmet.**

## Success Measures

`n/a — internal process-tooling correctness fix` (per the spec's own
`## Success Measures` section) — no instrumentation to verify; the
falsifiable expectation is read back at a future retrospective (recurrence of
the manual-workaround / false-fence-failure episodes), not from a metric
emitted by this diff.

## Rollout

`n/a — not user-facing` (per the spec's own `## Rollout` section) — no flag,
no removal follow-up required.

## Verification commands run

- `python3 -m unittest discover -s scripts/tests -p "test_*.py"` — 712+
  (pre-existing) plus this task's new tests, full suite green (background run
  confirmed exit 0 after the F3 commit).
- `python3 scripts/check-docs.py --changed-only` — clean.
- `python3 scripts/openup-fence.py check --task-id T-131` — clean (15 changed
  files, all within lane).

## Gotchas found during implementation

- The task-spec template (`docs-eng-process/templates/task-spec.md`) has no
  `touches:` frontmatter key, unlike every real spec in the repo — copying it
  literally left the claim empty and the fence flagged the iteration-plan file
  OUT OF LANE. Fixed by adding `touches:` by hand, matching real spec
  convention. Also missed `scripts/openup-state.schema.json` in the initial
  `touches:` list (the schema file touched by the F3 work) — caught by the
  fence at the final verification box, fixed and re-claimed.
- `resolve_base`'s naive `[explicit, stamped, "origin/main", "main"]`
  candidate-list rewrite broke `test_unresolvable_base_is_inapplicable_not_fatal`:
  the pre-existing contract is that an explicit-but-invalid `--base` does
  **not** fall back to `origin/main`/`main` — it must resolve to "inapplicable"
  (exit 0, no violations reported). Fixed by keeping `explicit` on an
  exclusive branch (`[explicit] if explicit else [stamped, origin/main, main]`).
- `reserve-id`/`next-id` reproduced the exact F2 bug this task fixes, live,
  while reserving T-131's own id (returned `T-129`, already used) — confirms
  the bug report from `docs/explorations/2026-07-25-measurement-tooling-and-lane-hygiene.md`
  a third time this session.

# T-146 — design notes

## Implementation verification against spec (complete-task step 1a)

Graded against `git diff 3da4e5f...HEAD` + the working tree, requirement by
requirement.

1. ✅ **`update_project_status()` skips `Iteration` when the lane's value is
   falsy** — `scripts/sync-status.py`: the unconditional
   `set_field(text, "Iteration", str(state.get("iteration", "")))` is now behind
   `if state.get("iteration"):`, and writes `str(state["iteration"])` inside the
   guard (so the fallback-to-empty-string branch that could blank the field no
   longer exists at all).
   - Scenario 1 (quick sentinel): green test
     `test_falsy_iteration_leaves_shared_header_untouched` — a `--iteration 0`
     quick state against a header reading `**Iteration**: 1` leaves it at `1`,
     and asserts `**Iteration**: 0` is absent.
   - Scenario 2 (absent key): green test
     `test_absent_iteration_key_leaves_header_untouched` — the key is deleted
     from the state file on disk and the header is still untouched, proving the
     check is falsiness rather than `== 0`.

2. ✅ **A real iteration number is still written** — green test
   `test_real_iteration_number_still_written` (`--iteration 96` → header reads
   96). Independently guarded by the pre-existing
   `test_t006_hooks.SyncStatusTests` assertion `**Iteration**: 3`, which was not
   modified by this lane and still passes.

3. ✅ **Every other header field still syncs on a falsy-iteration lane** — green
   test `test_falsy_iteration_still_syncs_every_other_field`: `Current Task`,
   `Phase`, `Status` and `Updated By` are all regenerated, `Last Updated` is no
   longer the fixture's `2026-01-01`, and the roadmap Status cell is still
   stamped `in-progress`.

4. ✅ **The `Status` question is carried, not dropped** — recorded in three
   places: (a) a comment adjacent to the guard in
   `scripts/sync-status.py`'s `update_project_status()`, stating that `Status`
   has the same root cause, is deliberately unfixed, and naming T-149; (b) this
   `design.md` (below); (c) roadmap entry **T-149**, added in this lane, so the
   question survives this change folder's archival.

**No ❌.** `gates.implementation_verified` set accordingly.

## Success-measure instrumentation (complete-task step 1b)

✅ **instrumentation pre-exists.** The measure ("zero occurrences of
`**Iteration**: 0` in `docs/project-status.md`") is read with
`git log -S'**Iteration**: 0' -- docs/project-status.md` — an exact query over
the file's own history, needing nothing in the diff. Read-back: the next
`/openup-retrospective`.

## Carried open question (unresolved by design)

**`**Status**` in `docs/project-status.md` means two things at once.**
`update_project_status()` writes it from `derive_status(state)` — the *active
lane's* status — while readers, and `/openup-retrospective` step 1, treat the
header as describing the *last completed iteration*. A quick lane in flight can
therefore rewrite a completed iteration's `completed` to `in-progress`, which is
the same failure shape as the `Iteration` clobber this task fixes.

It is **not** fixed here because, unlike `Iteration`, there is no sentinel to
test for: the value being written is a perfectly valid status, just an answer to
a different question. The two candidate resolutions are:

- **(a) Split the field** — `Iteration Status` (last completed iteration) and
  `Lane Status` (active lane). Honest, but it changes the document's shape, so
  `docs-eng-process/templates/project-status.md` and `/openup-init`'s generated
  header must move with it.
- **(b) Skip on `quick`** — mirror the `Iteration` treatment exactly: don't
  write `Status` when the lane is quick. Cheaper and consistent, but leaves the
  field's double meaning intact for standard/full lanes.

Carried as roadmap entry **T-149**, with the tie-break left to whoever takes it.

## Decisions

- **DD1 — Falsiness, not `== 0`.** A state with no `iteration` key (hand-written,
  or migrated from an older schema) should behave identically to the quick-track
  sentinel, and no valid iteration number is falsy — the counter starts at 1.
- **DD2 — Skip, never blank.** The guard wraps the write rather than substituting
  an empty value; `**Iteration**: ` (empty) would be a worse version of the same
  bug. This also removed the old `state.get("iteration", "")` default, which was
  the only path that could have produced it.
- **DD3 — `/openup-quick-task`'s `--iteration 0` stays.** The sentinel is fine;
  the bug was a consumer writing a lane-local sentinel into a project-wide view.
  Changing the producer would have needed a schema migration (a nullable
  `iteration`) for no gain.

## Gotchas

- The bug is **latent in this repo**: `/openup-quick-task`'s steps set gates
  directly and never invoke `sync-status.py`, so no quick lane here has
  triggered it. It reproduces downstream and would reproduce here the moment any
  skill revision or a manual `sync-status.py` run happened with a quick state
  live — which is why the fix is a guard in the consumer rather than a change to
  the quick-task flow.

# T-149 — design notes

## Implementation verification against spec (complete-task step 1a)

Graded requirement by requirement against the diff vs `origin/main` and the
working tree. Every requirement's `Then` clause is mechanically checkable here,
so each is backed by a green test rather than a reading of intent.

1. ✅ **Falsy `iteration` leaves `**Status**` untouched** —
   `scripts/sync-status.py`: `set_field(text, "Status", status)` moved inside the
   pre-existing `if state.get("iteration"):` guard. Green
   `test_quick_lane_cannot_rewrite_a_completed_iterations_status` (header stays
   `Iteration: 104` / `Status: completed`, and asserts `**Status**: in-progress`
   is absent) plus `test_absent_iteration_key_also_preserves_status`, which
   deletes the key from the state file on disk — proving falsiness, not `== 0`.
2. ✅ **A real iteration number still writes `**Status**`** — the true branch of
   the same guard. Green `test_real_iteration_still_writes_status` (105 →
   `in-progress`), and `test_iteration_and_status_always_move_together` asserts
   the DD2 invariant across *both* branches.
3. ✅ **`**Lane Status**` written on every sync** — the `upsert_field` call sits
   outside the guard. Green `test_lane_status_written_on_a_falsy_iteration_lane`
   (the one that matters: `Lane Status: in-progress` beside `Status: completed`),
   `..._on_a_real_iteration_lane_too`, and `test_lane_status_tracks_completion`.
4. ✅ **Inserted after `**Status**`, replaced when present, nothing else added** —
   `upsert_field()` in `scripts/sync-status.py`. Green
   `test_lane_status_is_inserted_directly_after_status` (asserts adjacency by
   line index), `test_second_sync_replaces_rather_than_duplicates` (exactly one
   occurrence; byte-identical second run), `test_upsert_does_not_add_other_missing_fields`
   (`Iteration Goal` / `Last Updated` stay absent), and
   `test_missing_anchor_is_a_no_op` (DD4).
5. ✅ **Hook decides from `**Lane Status**` when present** —
   `docs-eng-process/.claude-templates/scripts/hooks/on-task-request.py`:
   `(fields.get("Lane Status") or fields.get("Status", "")).lower()`. Green
   `test_lane_status_wins_over_a_completed_iteration_status` (exit 0, "Active
   iteration detected") and its inverse `test_lane_status_blocks_when_no_lane_is_live`
   (exit 2) — the pair proves the hook reads the new field rather than
   coincidentally agreeing with the old one.
6. ✅ **Falls back to `**Status**` when `**Lane Status**` is absent** — green
   `test_falls_back_to_status_when_lane_status_absent`, asserting **both**
   directions on un-migrated fixtures (`in-progress` → exit 0, `pending` →
   exit 2), plus `test_empty_lane_status_falls_back_rather_than_reading_blank`
   (DD5).

**No ❌.** Full suite: **863 passed, 1 skipped, 20 subtests passed**.
`gates.implementation_verified` set accordingly.

## Success-measure instrumentation (complete-task step 1b)

✅ **instrumentation pre-exists, in the named read-back environment (this repo).**
The primary measure reads `docs/project-status.md`'s own git history
(`git log -p --follow`) for the clobber signature — `**Iteration**` unchanged
while `**Status**` moves `completed` → `in-progress`. History-as-instrument needs
nothing in the diff, the same approach T-146 used. The secondary check
(`**Lane Status**` present in `docs/project-status.md`) is satisfied by this
completion's own `sync-status.py` run — and it exists precisely so a `0` on the
primary measure can be distinguished from "the upsert never fired".
Read-back: the next `/openup-retrospective`.

## The tie-break: (a) split, not (b) skip-on-quick

T-146 carried this question forward with two candidate resolutions and left the
choice to this lane. The deciding evidence was not in the T-146 note: **the field
has two live programmatic readers wanting opposite things.**

- `on-task-request.py` reads `Status == "in-progress"` as *"a lane is live"* and
  uses it to choose between blocking a task-request (`sys.exit(2)`) and the
  advisory reminder branch.
- `/openup-retrospective` steps 1–2 read the header as *"how did the iteration
  named in `**Iteration**` go"*.

Option **(b) skip-on-quick** would have made the header self-consistent — and it
is genuinely cheaper — but it removes the hook's only signal without replacing
it: during a quick lane the hook would read a stale `completed` and block a
legitimate task-request. That trades a visible bug (a wrong value in a document)
for an invisible one (a gate misfiring). Option **(a)** keeps both consumers
answerable.

## Decisions

- **DD1 — `**Status**` keeps the *iteration* meaning; `**Lane Status**` is the
  new field.** At rest every existing `project-status.md` already reads that way
  (`Iteration: 104` / `Status: completed`), so no downstream file's current value
  becomes a lie on upgrade, and the addition is purely additive. Naming the new
  field for the *lane* also matches how it is written (unconditionally, from
  `derive_status`).
- **DD2 — `**Status**` is written under the *same* guard as `**Iteration**`, not
  its own.** This is the load-bearing part: binding the pair to one condition
  makes "the recorded status describes the recorded iteration" an invariant
  rather than a convention. `test_iteration_and_status_always_move_together`
  asserts it across both branches.
- **DD3 — `set_field()` stays replace-only; insertion is a new
  `upsert_field()`.** Making `set_field` insert-when-missing would have been one
  word of diff and would have materialized every absent header field (`Iteration
  Goal`, `Retrospective`, …) in every un-migrated document — a much larger
  behavior change than the one being asked for, arriving silently.
  `test_upsert_does_not_add_other_missing_fields` pins this.
- **DD4 — a missing anchor is a no-op, not an append.** If a document has no
  `**Status**` line at all (hand-rolled, heavily edited), `upsert_field` declines
  to restructure it. The hook's fallback keeps such a document working, which is
  a better failure mode than a generator quietly rewriting a shape it does not
  recognize.
- **DD5 — the hook falls back on falsy, not on absent.**
  `fields.get("Lane Status") or fields.get("Status", "")` — an empty
  `**Lane Status**:` value falls back rather than being read as "no lane".
  A blank is not an answer.

## Changed another task's test (deliberate, not incidental)

`test_sync_status_notes.py::test_falsy_iteration_still_syncs_every_other_field`
is T-146's, and it asserted `**Status**: in-progress` on a falsy-iteration quick
lane — *exactly* the behavior requirement 1 changes. Re-pointing it at
`**Lane Status**` (and adding an assertion that `**Status**` keeps the fixture's
`planned`) preserves the test's actual subject: a quick lane still syncs
everything that is not iteration-scoped. Flagged here because silently editing
another lane's regression test is how a real regression gets laundered into a
green suite. `plan.md`'s Structure section carries the same note, and
`touches` was extended before the edit (fix-spec-first).

## Falsifiability check on the new tests

The suite was run against `git show HEAD:scripts/sync-status.py` (the
pre-change generator): **9 of 11 fail**, 11/11 pass after. The two that pass
both ways are deliberate no-regression guards —
`test_real_iteration_still_writes_status` (behavior that must *not* change) and
`test_missing_anchor_is_a_no_op` (the old code never wrote the field, so the
assertion is trivially true there).

## Gotchas

- **`**Lane Status**` lands between `**Status**` and `**Current Task**`.** The
  upsert anchors on `**Status**`, so the two status fields read adjacently —
  which is the point: a reader who sees one immediately sees the other and the
  distinction.
- **This repo's own `docs/project-status.md` gains the field at completion**,
  via the generator, not by hand — it is a derived view. If it is ever absent
  after a sync, the upsert did not fire and the success measure's `0` is
  meaningless (which is why the secondary measure checks for the field's
  presence).
- **`**Current Task**` has the same lane-scoped shape** and was left alone
  deliberately: naming the live lane is its whole job, so there is no clobber to
  fix. Not an oversight.

## Tooling bug hit during completion (not fixed here — out of lane)

**`openup-claims.py claim --force` deletes the existing claim *before* the
remote-check can refuse, stranding the lane unclaimed.** Reproduced exactly:
this lane extended its `touches` mid-work (the T-146 test, see above), so the
claim written at `begin` was stale and the fence correctly reported `OUT OF
LANE`. The documented fix — "add to the task's frontmatter `touches` and
re-claim" — was run as `claim --force`, which printed
`REFUSED: T-149 already claimed on remote by session <this same session>` **and
left no claim file at all**. Two distinct problems:

1. `--force` is not atomic: it removes the old claim, then the remote check
   refuses, and nothing is written back. The lane silently loses its lease.
2. The remote check refuses against the lane's **own** session id. A re-claim
   from the same session/branch is the documented recovery path for a stale
   `touches` list, so it should be an update, not a collision.

The tell is subtle and worth naming: after the failed `--force` the fence went
**green** — not because the surface was claimed, but because with no claim file
the fence falls back to the plan's frontmatter. A disappearing lease reads as
success. Recovered with an explicit `release` → `claim` → `heartbeat`.

Not fixed in this lane (`scripts/openup-claims.py` is not in `touches`, and the
fix needs a decision about same-session re-claim semantics). Surfaced for
roadmap triage rather than filed unilaterally.

# T-145 — design notes

## Implementation verification against spec (complete-task step 1a)

Graded against `git diff 5261aee...HEAD` + the working tree, requirement by
requirement.

1. ✅ **Schema declares `implementation_verified` under `gates`, not in
   `gates.required`** — `scripts/openup-state.schema.json`: the new property sits
   in `gates.properties` alongside `retro_due`; the `gates.required` array is
   byte-unchanged (`team_deployed`, `plan_persisted`, `log_written`,
   `roadmap_synced`, `retro_due`).
   - Scenario 1 (legacy state validates): green test
     `test_state_without_verified_gate_still_validates`
     (`scripts/tests/test_openup_state.py`) — `init` writes a `gates` object with
     no such key, and `validate` exits 0.
   - Scenario 2 (absent key reads unset, not a crash): same test —
     `get gates.implementation_verified` returns the defined *key missing* exit
     5 with a `Key not found:` message, never a traceback. Every consumer
     (`cmd_check_gates`, `derive_status`) reads via `gates.get(name)`, so the
     absent key is falsy = not verified.

2. ✅ **`TRACK_REQUIRED` requires the gate on every track** —
   `scripts/sync-status.py:60-77`, all three entries.
   - quick/standard bookkeeping-only → `in-progress`: green tests
     `test_bookkeeping_only_state_does_not_complete` and
     `test_quick_track_also_requires_delivery_evidence`
     (`scripts/tests/test_sync_status_notes.py`), which assert both the roadmap
     cell and the `project-status.md` header.
   - all three tracks, gate absent then present:
     `test_every_track_requires_delivery_evidence` (subTest per track).
   - gate present → `completed (YYYY-MM-DD)`:
     `test_single_run_completes_when_gates_met`,
     `test_completed_cell_is_date_stamped_and_stable`.

3. ✅ **`DEFAULT_REQUIRED_GATES` includes the gate** —
   `scripts/openup-state.py:62-70`. Green test
   `test_check_gates_default_requires_delivery_evidence`: with the three
   bookkeeping gates true and this one unset, `check-gates` (no `--require`)
   exits 6 and names `implementation_verified` on stderr; setting it flips the
   same call to exit 0.

4. ✅ **`/openup-complete-task` step 1a sets the gate, step 7 requires it** —
   `docs-eng-process/procedures/openup-complete-task.md`: step 1a gains point 6
   with the `set-gate implementation_verified true` call, stated as conditional
   on every requirement reading ✅ and explicitly refusing a "provisional" set;
   step 7's two `check-gates --require` invocations both list the gate, prefixed
   by a line saying it is required on every track. The Success Criteria bullet
   at the top of the skill names it too.

5. ✅ **`/openup-quick-task` sets the gate at its verification step** —
   `docs-eng-process/procedures/openup-quick-task.md`: step 3 gains the
   `set-gate` call gated on having actually confirmed the change works; step 2's
   preamble and step 6's `check-gates --require` line both list it, and step 6
   carries an explicit note that the gate is *not* set there alongside the
   bookkeeping gates. Success Criteria updated.

6. ✅ **Documented where the gate set is documented** —
   `docs-eng-process/state-file.md`: field table row, the
   "All fields are required" paragraph (now naming the one optional key), the
   `check-gates` CLI row's default set, the gate-lifecycle table row, and the
   Track-dependent-gates paragraph (with the bookkeeping-vs-evidence rationale).
   `docs-eng-process/tracks.md`: the `check-gates` wiring row.

**No ❌.** `gates.implementation_verified` set accordingly.

## Success-measure instrumentation (complete-task step 1b)

✅ **instrumentation pre-exists.** The measure ("zero roadmap rows stamped
`completed` whose task produced no implementation diff") is read from
`sync-status.py --reconcile --dry-run` (already shipped: `run_reconcile`,
`scripts/sync-status.py:366-395`, prints machine-readable `DRIFT <id> <status>`
lines) joined with `git log --stat` per stamped task. Nothing new needed in the
diff. Read-back: the next `/openup-retrospective` — which, with T-141 landing in
this same PR, now verifies and retires carried action items, so the read-back has
a place to be recorded and retired rather than accumulating.

## Decisions

- **DD1 — The gate is set by the completion skills, not computed by a script.**
  The verification is a judgment step (grading requirements against a diff); only
  its verdict is mechanical. A script that tried to re-derive the verdict would
  either duplicate the judgment badly or degrade to "the diff is non-empty" —
  weak evidence of exactly the kind this task rejects. Recorded as an Assumption
  in the spec, unchallenged at review.
- **DD2 — `DEFAULT_REQUIRED_GATES` changes too.** `sync-status.py`'s
  `TRACK_REQUIRED` and `openup-state.py`'s default must agree, or a lane could
  pass `check-gates` while the derived roadmap still read `in-progress` — a
  split-brain that would read as a `sync-status.py` bug.
- **DD3 — Not seeded by `init`.** The key is never written at iteration start;
  it appears only when a completion skill sets it. That keeps the schema's
  optional-key contract honest (a state file genuinely may not have it) and
  means the gate can only ever be present because someone verified.

## Gotchas

- **`openup-claims.py claim --force` refuses a re-claim by its own session.**
  Adding `docs-eng-process/skills-guide.md` to `touches` mid-lane required a
  re-claim; `claim --force` ran the T-044 remote-duplicate check, which compares
  only *existence* of `refs/openup/claims/<id>` on origin, not the session id —
  so the lane's own pushed ref refused its own re-claim (`REFUSED: T-145 already
  claimed on remote by session <same session>`), **and the local claim file was
  left deleted** by that path. Worked around with `--force --no-push` (the remote
  ref was already ours). Surfaced to the roadmap as a separate finding, not fixed
  here.
- `docs-eng-process/skills-guide.md` is generated from the skill files
  (`check-skills-guide.py --write`) and has its own live-repo test
  (`test_check_skills_guide.LiveRepoTests`) — any procedure-pack edit must
  regenerate it or the full suite fails.

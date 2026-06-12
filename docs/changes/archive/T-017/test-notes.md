# T-017 — Test notes

## Automated

- `python3 scripts/tests/test_openup_board.py` — **15 tests, OK.** Covers: the exact
  10-field lane set; `ready` vs `blocked` (unmet dep) vs `colliding` (foreign lease
  overlap) vs `in-progress` (own lease); `done`/archived lanes excluded; checkbox parsing
  incl. `(role)` hat tag, `developer` default, all-ticked → `null`, and legacy numbered →
  `null` (still queueable); `top` priority ordering, clean exit-3 when none pickable, and
  empty-board stop; deterministic byte-identical output; board-file write; default
  subcommand = `refresh`.
- `python3 -m unittest scripts.tests.test_openup_board scripts.tests.test_openup_claims
  scripts.tests.test_openup_state` — **47 tests, OK** (no regression in the shared claims/
  state machinery the board imports).

## Live (real repo)

- `python3 scripts/openup-board.py refresh` → writes `.openup/board.json` with one lane
  (T-017), `state: in-progress` (this session holds the lease), `hat: developer`,
  `next_action` = the first unchecked Operations box, `depends_ok: true`,
  `collides_with: null`. Field set exactly as specified.
- `python3 scripts/openup-board.py top` → exit **3**, stderr `no pickable lane (1
  in-progress)`. This is the `/openup-next` no-op path: from a cold session it would print
  the reason and stop cleanly. ✔
- Agreement-by-construction: board imports the same `openup-claims.py` module
  (`dep_satisfied` / `touches_overlap`) used by `preflight`, verified at import.

## `/openup-next` dry-run (narrative)

Cold session → `openup-board.py top`:
- **Pick path** (proven by `test_top_picks_pickable_lane`): exit 0 emits the lane JSON →
  skill delegates to `/openup-start-iteration task_id track`, self-briefs under `hat`,
  works `next_action`, ticks boxes, exits via `/openup-complete-task` or
  `/openup-create-handoff` (the only two exits).
- **No-op path** (proven live above): exit 3 → print reason, stop. Successful no-op.

## Not covered (deliberate)

- A live end-to-end run of two parallel `/openup-next` loops over two real READY lanes —
  there is only one active change folder (T-017 itself) right now, so the two-disjoint-lane
  scenario is covered deterministically by the unit tests (`top` selection + collision
  classification) rather than live. Re-exercise once a second active lane exists.

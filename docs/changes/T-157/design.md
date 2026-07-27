# T-157 — design decisions

In-flight decisions for `sync-status.py --views-only`. The spec (`plan.md`) is the
contract; this file records what was decided while building and why.

## DD1 — Rejected: point `--state-dir` at the archived state

A workaround exists today and was rejected rather than documented. `state_dir(args)`
resolves `<dir>/state.json`, and `/openup-complete-task` archives to
`docs/changes/<id>/state.json` — so `--state-dir docs/changes/T-NNN` would technically
find a completed lane's state and let the normal path run.

Rejected because:

1. The change folder is archived to `docs/changes/archive/T-NNN/` shortly after, so the
   path a maintainer would have learned is correct for a narrow window and wrong after.
2. The run calls `set_gate_roadmap_synced()`, which would **write into an archived
   artifact** — mutating the audit record of a finished lane to satisfy a recovery.
3. It reconstructs header fields from a *stale* lane's state, stamping the views with
   values describing a lane that finished, which is exactly the class of bug T-146 and
   T-149 spent two lanes removing.

`--no-gate` suppresses (2) but not (1) or (3), and its help text says "used in isolated
tests" — repurposing it as a recovery path would make a test affordance load-bearing in
production recovery.

## DD2 — What `--views-only` regenerates, and what it deliberately does not

The dividing line is **whether the input is committed and lane-independent**:

| View region | Derived from | In scope? |
|---|---|---|
| `## Notes` in `project-status.md` | `docs/status-notes/*.md` shards | **yes** — committed, lane-independent |
| `## T-NNN:` section Status lines in `roadmap.md` | archived change folders | **yes** — committed, lane-independent (existing `--reconcile` pass) |
| Header fields (`Phase`, `Iteration`, `Status`, `Current Task`, `Lane Status`, `Iteration Goal`, `Last Updated`, `Updated By`) | `.openup/state.json` | **no** — needs a live lane |
| Roadmap **table-row** Status cells | a lane's `task_id` + `derive_status(state)` | **no** — needs a live lane |
| `gates.roadmap_synced` | — | **no** — no lane to gate |

The retrospective's own manual recovery (`assemble_notes` / `update_notes_section`
called directly) covered exactly the first row, which is confirmation the scope is the
observed need rather than a guess at it.

**Consequence, accepted knowingly:** a lane that recovers a conflict this way carries
trunk's header values rather than its own, and on merge those persist — so the
recovering lane's iteration is never reflected in `Iteration` / `Iteration Goal` /
`Current Task`. The alternative is DD1's guess-from-stale-state. Named in `plan.md`
§Analysis Context so a later reader sees a decision, not an oversight.

## DD3 — `Last Updated` / `Updated By` kept inside the no-go zone

Genuinely arguable: these two describe the *document*, and a `--views-only` run does
modify the document, so writing them would be defensible. They were left untouched so
requirement 4's assertion stays absolute — *nothing* above `## Notes` changes — which is
a far stronger invariant to test and to reason about than "nothing except these two".
A no-go zone with exceptions in it erodes; this one does not. The cost is a slightly
stale `Last Updated` after a recovery, which is visible and harmless.

Recorded as a vetoable Assumption in `plan.md` rather than settled silently.

## DD4 — Test placement deviates from the spec's original Structure

The spec initially split the new tests across `test_sync_status_notes.py` (reqs 1, 2, 4,
6) and `test_sync_status_sections.py` (reqs 3, 5), mirroring which module each exercised.
Built as a single `ViewsOnlyTests` class in the notes file instead: every case shares the
same "no state file present" fixture, which *is* the subject of the feature, and
splitting by implementation internals would leave neither file showing the feature's
coverage. `plan.md` §Structure was corrected to match (fix-spec-first) rather than left
to drift; `test_sync_status_sections.py` is unmodified and remains in `touches` as a
harmless superset.

## DD5 — Scope grew by one file, mid-lane

`docs-eng-process/.claude-templates/CLAUDE.md` was **not** in the original `touches`. It
carries the "If a PR conflicts in the views" rule — the copy loaded into every agent
session — and would have kept naming the broken command. Added to the spec (touches,
Structure, new requirement 9) *before* editing it.

The same search deliberately did **not** sweep `docs/status-notes/`,
`docs/explorations/`, `docs/iteration-retrospectives/`, or `docs/changes/archive/`,
several of which state the old recipe verbatim. Those are audit records of what was true
when written; rewriting them to match current behavior would destroy the evidence trail
this task was built from — including the iteration-103 finding that motivated it.

## DD6 — Verification notes

- **Bite check.** 9 of 11 new tests fail against `HEAD`'s script. The 2 that do not are
  `test_plain_sync_still_fails_without_state` (a deliberate no-regression guard — it
  *should* pass both ways) and `test_table_row_status_untouched`, which passes vacuously
  on the old script because the command errors out before touching anything. Recorded
  rather than reported as "11 failing", since a vacuous pass is not evidence.
- **Pure widening.** Full suite 884 passed / 1 skipped / 20 subtests = the 873 baseline
  (recorded in the T-155 status note) + 11 new, with no pre-existing assertion edited.
- **Live check.** Against a copy of the real repo docs with the state file absent and
  `## Notes` truncated to one stale line: plain run exits 3, `--views-only` exits 0 and
  restores 113/113 shards with the header diff empty.

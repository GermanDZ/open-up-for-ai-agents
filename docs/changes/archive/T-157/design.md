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

## Completion verification (complete-task steps 1a / 1b)

### Step 1a — every requirement graded against the actual diff

| # | Requirement | Verdict | Evidence in the diff |
|---|---|---|---|
| 1 | Runs with no state file, exit 0 not 3 | ✅ | `sync-status.py` `main()` returns `run_views_only(args)` *before* `read_state()`; `ViewsOnlyTests::test_runs_without_state_file` green, and `test_plain_sync_still_fails_without_state` proves the un-flagged path still exits 3 |
| 2 | Reassembles `## Notes` newest-first from the shards | ✅ | `run_views_only()` calls `assemble_notes()` / `update_notes_section()`; `test_reassembles_notes_newest_first` asserts T-003 < T-002 < T-001 ordering |
| 3 | Runs the state-free roadmap section reconcile | ✅ | `run_views_only()` calls `reconcile_sections()`; `test_reconciles_archived_section` asserts the `completed (YYYY-MM-DD)` stamp |
| 4 | Writes no lane-derived header field | ✅ | `run_views_only()` never calls `update_project_status()`/`set_field()`; `test_header_is_byte_identical` asserts the whole region above `## Notes`, and the live run's `diff` was empty |
| 5 | Sets no `gates.roadmap_synced` | ✅ | `set_gate_roadmap_synced()` is unreachable from this path; `test_does_not_write_gate_or_state` asserts a present state file is byte-unchanged |
| 6 | `--dry-run` reports and writes nothing | ✅ | early `return EXIT_OK` in the `args.dry_run` branch; `test_dry_run_writes_nothing` asserts both files byte-identical + `DRIFT T-042` on stdout |
| 7 | Every existing invocation unchanged | ✅ | Full suite **884 passed / 1 skipped / 20 subtests** = 873 baseline + 11 new; no pre-existing assertion edited (`git diff` on the test file is additive only) |
| 8 | `parallel-lanes.md` recipe names the working command | ✅ | Recipe now branches lane-live vs completed; the completed branch's `sync-status.py --views-only` is the exact command exercised in the live check (exit 0). *Scope note: the `git fetch`/`rebase`/`push --force-with-lease` lines are unchanged from the original recipe and were not re-executed here* |
| 9 | Live instructions updated, historical records left alone | ✅ | `docs-eng-process/.claude-templates/CLAUDE.md` updated (`check-claude-sync` green); `git diff --name-only main...HEAD` matches **no** file under `docs/status-notes/`, `docs/explorations/`, `docs/iteration-retrospectives/`, or `docs/changes/archive/` |

**Result: 9/9 ✅** — `gates.implementation_verified` set.

### Step 1b — success-measure instrumentation

`✅ instrumentation` — the measure names the **Measure Read-Back table of this repo's
iteration retrospectives**, cross-checked against `git log` on the two view paths.
**Read-back environment: this repo**, and the instrument demonstrably pre-exists *there*:
`## Measure Read-Back` tables are present in `iteration-77`, `iteration-86`,
`iteration-98`, and `iteration-103` retrospectives — the last of which recorded this very
incident in exactly the required form. No new instrumentation was needed.

**Read-back date: the second retrospective after landing** (absolute backstop
**2026-09-30**). Expectation: hand-repairs fall from 2-of-2 to **0 of the next 3**
view-conflicting PRs. The spec states that fewer than 3 such PRs must be reported as
*insufficient data*, not as the measure being met.

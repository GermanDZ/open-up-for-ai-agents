# T-142 — In-flight design decisions

## DD1 — The increment lives in `archive`, not in `/openup-quick-task`'s prose

The roadmap description sanctioned either "route quick-task completion through
the retro-increment call" **or** "a shared teardown step with
`/openup-complete-task`". We took the second.

The deciding argument: the defect *is* prose not being followed. The increment
was a documented step in exactly one skill, and the skill that did not document
it did not do it. Copying the same prose into `/openup-quick-task` fixes the two
completion paths that exist today and reintroduces the identical gap the moment
a third is added. Putting the increment in `openup-state.py archive` — which
`openup-session.py end` (and therefore `/openup-complete-task`) and
`/openup-quick-task` step 7 both already run — makes the cadence advance by
construction.

Consequence that had to be handled: `/openup-complete-task` §7a would then
double-count, so its `retro increment` command was removed and the step reduced
to a note explaining *why* there is nothing to run there. The note is load-bearing
— without it, a future editor "restores" the missing command.

## DD2 — Increment after the unlink, and only on success

`cmd_archive()` increments *after* `state_path(args).unlink()`, so:

- a validation failure (exit 7) or a missing state file (exit 3) never advances
  the count;
- a second `archive` for the same lane exits 3, so a repeated call cannot
  inflate the cadence.

Both are tested (`test_failed_archive_does_not_advance_cadence`).

## DD3 — Over-counting is the safe direction

`archive` increments unconditionally rather than trying to detect "was this
really a lane completion". A cadence gate that over-counts makes a retrospective
due *sooner*; one that under-counts silently disables itself — which is the bug
being fixed. `--no-retro` exists for the caller that genuinely knows an archive
is not a completion; nothing in the skill pack passes it today.

## DD4 — The existing test asserted the old contract

`scripts/tests/test_t011_retro.py::test_counter_survives_archive` asserted that
`archive` leaves the counter **untouched** — the exact behaviour T-142 inverts.
It was not caught by the targeted test run, only by the full suite. The test was
updated to assert "survives *and* increments" rather than deleted: the
carry-forward guarantee it was written to protect (the counter outliving the
state file `archive` deletes) is still real and still worth a test.

This also relocated the new cadence tests: `test_t011_retro.py` is the counter's
home, not `test_openup_state.py` where the spec originally put them. The spec's
Structure/`touches` lists were corrected to match (no requirement or scenario
changed — the file list was simply wrong).

## Completion verification (step 1a) — 2026-07-27

Graded against the diff vs `origin/main`, not against intent.

| # | Requirement | Verdict | Evidence |
|---|---|---|---|
| 1 | `archive` advances the counter by one | ✅ | `scripts/openup-state.py::cmd_archive` (increment after `unlink`); `test_archive_advances_cadence` asserts stdout `Retro cadence: 1` **and** the on-disk value |
| 2 | A failed archive does not advance it | ✅ | increment is unreachable on the exit-3 path; `test_failed_archive_does_not_advance_cadence` |
| 3 | `--no-retro` suppresses the increment | ✅ | `--no-retro` on the `archive` subparser; `test_archive_no_retro_suppresses_increment` (also asserts the archive itself still happened) |
| 4 | `/openup-complete-task` issues no `retro increment` | ✅ | `grep -c 'openup-state.py retro increment' docs-eng-process/procedures/openup-complete-task.md` → `0`; §7a is now a note explaining why |
| 5 | `/openup-quick-task` mirror mentions `retro` | ✅ | `grep -c retro …/skills/openup-quick-task/SKILL.md` → `6` |
| 6 | `state-file.md` documents archive-increment + `--no-retro` | ✅ | new "Where the increment lives, and why (T-142)" paragraph + `--no-retro` in the CLI and cadence tables (3 occurrences) |

**Result: all ✅.** Full suite 891 passed / 1 skipped (was 887/1 — net +4 tests
after consolidating the cadence tests into `test_t011_retro.py`).

## Success-measure instrumentation (step 1b)

✅ — the measure compares `openup-state.py retro get` against the count of
archived state files under `docs/agent-logs/<Y>/<M>/<D>/state-*.json`. Both
already exist and are produced by the process itself; no new telemetry was
needed. This change additionally makes the increment *observable* at the moment
it happens — `archive` now prints `Retro cadence: N`, which lands in every
completion's output. **Read-back: the next `/openup-retrospective`**, and it must
be taken *before* that retrospective's `retro reset`.

# T-060 Design — Parallel fan-out: stale-lease reaper + /openup-fan-out skill

## Requirement Grades (step 1a — completion gate)

1. ✅ **heartbeat subcommand** — `cmd_heartbeat` in `scripts/openup-claims.py` stamps
   `last_heartbeat` atomically via `write_claim_atomic`; exits `EXIT_BAD_INPUT` (7) when
   claim file absent. Tests: `test_stamps_last_heartbeat_on_existing_claim`,
   `test_exits_7_when_no_claim` both pass.

2. ✅ **reap subcommand** — `cmd_reap` in `scripts/openup-claims.py`: skips claims with
   no `last_heartbeat` (backward-compat invariant), skips fresh heartbeats, deletes stale
   ones. `--dry-run` prints without deleting. Always exits 0. Tests: all 8 `TestReap`
   scenarios pass.

3. ✅ **top-n subcommand** — `cmd_top_n` in `scripts/openup-board.py`: greedy
   collision-free selection in board priority order, stops at N, exits 3 when no READY
   lanes. Tests: all 9 `TestTopN` scenarios pass.

4. ✅ **start-iteration heartbeat stamp** — both copies of `openup-start-iteration/SKILL.md`
   now include `python3 scripts/openup-claims.py heartbeat --task-id {task_id}` after the
   claim write step.

5. ✅ **/openup-fan-out skill** — `docs-eng-process/.claude-templates/skills/openup-fan-out/SKILL.md`
   exists (synced to `.claude/skills/` at session start).

6. ✅ **fan-out collision-free partitioning** — `test_excludes_colliding_lane` and
   `test_returns_disjoint_lanes` verify that `top-n` returns a mutually collision-free
   partition. Full E2E fan-out with background agents requires a second READY lane; the
   mechanism is in place and the unit tests prove correctness.

7. ✅ **stale claim reap + re-pickable** — `test_reaps_stale_heartbeat` confirms stale
   claim deletion. Integration scenario (2026-06-21) confirmed stale claim reaped and
   lane re-pickable.

## Success Measure Instrumentation (step 1b)

**Spec:** wall-clock time for 2 disjoint READY lanes ≤ `max(cycle_time_A, cycle_time_B) + 10%`
vs serial `cycle_time_A + cycle_time_B`.

**Instrumentation:** `openup-log-run` emits `started` and `completed` timestamps per lane
(pre-existing). Read-back: on first real multi-lane `/openup-fan-out` run against this
repo's roadmap (within 2 iterations or by 2026-07-05).

✅ Instrumentation pre-exists (run-log system).

## Design Decisions

**D1: Frontmatter re-read in `cmd_top_n`** — chose to re-read plan.md frontmatter for
touches instead of threading `_touches` through `build_board`. Rationale: avoids changing
the board's public contract; the overhead is O(N) plan reads for the READY subset (typically
small). Alternative was storing `_touches` in build_lane and stripping it in build_board,
then accessing it before the strip in a new code path — more complex with no real gain.

**D2: Default stale-after = 1800s** — 30 minutes is the conservative safe floor for
full-track cycles. A tighter window (e.g. 5 min) would false-positive reap a live long-
running cycle. One-shot heartbeat (stamped at claim time, not polled) is the v1 approach;
polling heartbeat (every 60s) would allow a 5-min window but adds complexity (deferred to
v2 per spec Open Question 3).

**D3: reap always exits 0** — advisory design. Partial failures (e.g. a claim file that
can't be deleted due to permissions) are printed to stderr and skipped rather than aborting
the sweep. This preserves the "reap is never a blocker" invariant.

## Pre-Existing Doc Failures (not T-060's surface)

`python3 scripts/check-docs.py` exits 1 due to pre-existing failures on `origin/main`:
- `docs/changes/archive/T-056/plan.md` — status `done` not in allowed enum
- `docs/iteration-plans/t-059-loop-support-openup-next.md` — status `pending` not in enum

Both exist on `origin/main` before T-060's changes. Fixing them is out of T-060's `touches`
surface (write-fence would block). They are pre-existing debt.

T-060's iteration plan status was fixed: `status: implemented` (previously `pending`).

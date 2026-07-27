# T-148 — In-flight design decisions & completion evidence

## DD1 — Fix the tool, not only the prose

The roadmap entry scoped T-148 to the skill template's step 6. Its own acceptance
bullet, however, was behavioral: *"a fresh `begin` for a standard-track task with a
committed spec never needs a follow-up `set-gate plan_persisted` call."* A prose-only
fix cannot satisfy that — it only re-words an instruction the next agent may skip
again, which is the exact failure mode being fixed (five skips in five tasks). So the
resolution moved into `openup-session.py`, where it cannot be forgotten, and the pack
edit became documentation of what the tool already does. Belt *and* braces, with the
braces load-bearing.

## DD2 — Resolution sits outside the rollback boundary

`_resolve_plan_path` is called at the top of `cmd_begin`, next to `base_sha`, **before**
the claim is taken. The T-063 contract is that any failure *after* the claim releases it;
adding a new step between claim and state-init would widen that boundary. The helper is
pure and read-only (one `is_file()`), so placing it first keeps the boundary exactly where
T-063 put it.

## DD3 — Fail-open, and `quick` is skipped

Three branches, all deliberate: an explicit `--plan` wins verbatim (legacy lanes point at
`docs/plans/` and `docs/iteration-plans/`); a missing spec leaves the gate `false` rather
than refusing the begin (a lane whose plan lives elsewhere must stay startable); and the
`quick` track never auto-resolves, because `tracks.md` relaxes the gate there. Each is a
recorded spec Assumption and each has its own regression test.

## Requirement Grade (step 1a) — all ✅

Graded against `git diff origin/main...HEAD`, not against intent.

| # | Requirement | Grade | Evidence |
|---|---|---|---|
| 1 | standard/full auto-resolves the task spec | ✅ | `_resolve_plan_path` returns `docs/changes/<id>/plan.md`; consumed at `cmd_begin`'s `if plan_path:` (replacing `if args.plan:`). `test_standard_track_auto_resolves_task_spec` asserts the gate string. |
| 2 | explicit `--plan` wins | ✅ | `if plan_arg: return plan_arg, False` (first branch). `test_explicit_plan_wins_over_auto_resolution` asserts `docs/plans/legacy.md` survives. |
| 3 | missing spec is fail-open, exit 0 | ✅ | `if not (root / rel).is_file(): return None, False`. `test_missing_spec_is_fail_open` runs with `expect=0` and asserts the gate is `False`. |
| 4 | `quick` does not auto-resolve | ✅ | `if track not in PLAN_GATE_TRACKS`. `test_quick_track_does_not_auto_resolve` asserts the gate is `False`. |
| 5 | auto-resolution observable in the run log | ✅ | `cmd_begin` step 7 emits `log-event --event plan_gate_autoresolved`. The step-1 test reads the shard and asserts the event is present; the step-2 test asserts it is *absent* when `--plan` was explicit. |
| 6 | pack no longer advertises the wrong path | ✅ | `grep -c 'docs/plans/{plan}.md' docs-eng-process/procedures/openup-start-iteration.md` → **0**. The new paragraph states the auto-resolution, its `standard`/`full` scope, and forbids the manual `set-gate` follow-up. |
| 7 | mirror matches the pack | ✅ | `python3 scripts/render-skills-mirror.py --check` → exit 0 ("mirror in sync with the pack (37 skills)"); `--write` reported exactly 1 updated file. |

**Mutation check** (the tests are not vacuous): reverting only `if plan_path:` back to
`if args.plan:` makes `test_standard_track_auto_resolves_task_spec` fail with
`AssertionError: False != 'docs/changes/TEST-P1/plan.md'`; restoring it passes. Run
before and after, in-place.

**Suites:** `scripts/tests` 844 passed / 1 skipped; `tests/` 106 passed;
`scripts/check-docs.py` OK (8 instances). `tests/test-scripts.sh` reports 16/17 — its
Test 16 (`After a sync, on-stop allows a clean stop`) fails **identically on `main` at
b2810c0**, so it is pre-existing and out of this lane's scope. Not fixed here; it belongs
to whichever lane owns the sync/on-stop surface.

## Success-Measure Instrumentation (step 1b) — ✅

- **Instrument:** the `plan_gate_autoresolved` record appended to
  `docs/agent-logs/runs/<date>-<task>.jsonl` — created **in this diff**
  (`scripts/openup-session.py` `cmd_begin` step 7), not assumed to exist.
- **Read-back environment:** *this repo*. Verified present and git-tracked:
  `git ls-files docs/agent-logs/runs/` returns shards, and 2026-07-27 files exist for
  T-146, T-150, T-151, T-152, T-153. The measure is about lanes started **here**, so the
  T-152 failure mode (an instrument named in a downstream repo that lacks it) does not
  apply.
- **Read-back date:** the next retrospective, or **2026-08-10**, whichever comes first.
- **Expectation:** manual `set-gate plan_persisted` recoveries go from 5-of-5 to 0 across
  the next 5 `standard`/`full` lanes.

**Honest caveat:** *this lane's own* shard has no `plan_gate_autoresolved` record. T-148
was started through the pre-fix path, where `--plan docs/changes/T-148/plan.md` had to be
passed by hand — which is precisely the manual step being removed. The first true
end-to-end proof is the next lane started after this merges.

## Rollout (step 4a) — not flagged

`## Rollout` argues no flag (internal tooling default, no user-facing surface, backout is a
one-line revert). No flag ⇒ no flag-removal row to enqueue.

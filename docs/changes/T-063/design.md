# T-063 — In-flight design decisions

## DD1 — `end` is complete-task's teardown; `/openup-create-handoff` is NOT changed (spec correction)

**Discovered during implementation (Operations step 1).** The authored spec
(`plan.md` Change 3 / Operations step 5 / iteration-plan) assumed
`/openup-create-handoff` performs `release + archive + log` and would be slimmed to call
`openup-session.py end --status handoff`. **This is inaccurate.** The actual
`.claude/skills/openup-create-handoff/SKILL.md` does **no** claim release, **no** state
archive, and **no** teardown log-event — it only assembles and writes `handoff.md`. A
handoff deliberately **keeps** the lease + `.openup/state.json` so the next `/openup-next`
resumes the lane via the resume path (§1a). (Verified against this very T-063 handoff: the
lease stayed held and the board kept the lane `in-progress`.)

**Decision.** `openup-session.py end` implements the **completion teardown only** —
`release claim + archive state + log session_end` — which is `/openup-complete-task`'s §7b.
`/openup-create-handoff` is left unchanged (it never had a teardown to slim). Consequences:

- Requirement 3's AC (`end --status done`) is the real, tested contract. The `--status
  handoff` variant is dropped — it had no caller and would only add speculative dead code.
- Operations step 5 narrows to `/openup-complete-task` §7b only.
- Requirement 6 / touches: the `openup-create-handoff` skill dirs are dropped from the
  fenced surface (no edit needed there).
- `end` signature: `end --task-id T --archive-to PATH` → archives the live
  `.openup/state.json` to PATH (the change folder's `state.json`, matching complete-task's
  `openup-state.py archive "docs/changes/<id>/state.json"`), releases the claim, logs
  `session_end`. Rolls nothing back (teardown is terminal).

This is a scope **reduction**, not a behavior change to a shipped feature — recorded here
rather than re-running create-task-spec, since it removes an assumption the spec made about
another skill, not a change to T-063's own delivered behavior.

## DD2 — Composition mechanism: call the modules' `main(argv)` in-process

`openup-session.py` loads `openup-claims.py` and `openup-state.py` via `importlib`
(hyphenated filenames), then drives them through their existing `main(argv)` entry points
(`claims.main(["claim", ...])`, `state.main(["init", ...])`). `main()` returns the
subcommand's exit code and does **not** call `sys.exit` itself — but some `cmd_*` handlers
(`cmd_init` on an existing file, `cmd_get` on a missing key, `cmd_archive` on invalid state)
**do** `sys.exit(...)`. So every composed call is wrapped to capture both a returned code and
a raised `SystemExit`, normalizing to an int. This keeps `openup-session.py` a pure
composition (zero duplicated claim/state logic — safeguard held) while still detecting
partial failure for rollback.

## DD3 — `begin` rollback boundary

`begin` order: dry-run reap (warn) → remote-check (advisory; exit 9 aborts *before* any
claim, nothing to roll back) → **claim** → heartbeat → state-init → log `session_begin`.
The rollback boundary is **after the claim**: if heartbeat, state-init, or the log call
fails, `begin` calls `claims release --no-push` for the task and returns non-zero, leaving
no half-acquired session (Requirement 2). Failures *before* the claim need no rollback.

## DD4 — Board reap wiring stays inside `openup-board.py` (claims.py is Do-not-touch)

`openup-claims.py` is out of the fenced surface, so the board cannot refactor a
non-printing `reap_stale()` helper into it. Instead `cmd_refresh` calls the existing
`claims.cmd_reap` with `stdout` redirected (so the reap summary never pollutes the board
JSON on stdout); a one-line notice goes to stderr only when something was actually reaped.
A `--reap-stale-after SECONDS` (default 1800, matching the CLI) and `--no-reap` flag keep it
tunable. Heartbeat-less claims are still skipped by `cmd_reap` itself — the T-060 invariant
is inherited, not re-implemented.

## DD5 — Skill-adoption details (Operations steps 4-6, 2026-07-06)

Landing the three remaining boxes surfaced two small faithful-adoption decisions:

- **`session-id` now flows to state, not just the claim.** The old §6 `openup-state.py
  init` passed **no** `--session-id` (so `.openup/state.json.session_id` stayed `null`),
  while §6b's `claim` used the branch. `begin` passes one `--session-id` to *both* the
  composed claim and state-init, so the slimmed §6 passes `--session-id "$BRANCH"` — state
  and claim now agree (branch as the session id) instead of the prior latent `null`
  mismatch. Behaviour-neutral for the reaper (heartbeat-gated, not session-id-gated).
- **`iteration_start` log folds into `begin`'s `session_begin`.** The former §9 standalone
  `log-event --event iteration_start` is removed — `begin` already appends a `session_begin`
  record (same deterministic clock-stamped logger, carrying `--goal`/`--run-id`/`--branch`/
  `--phase`). `iteration_start` was only a free-form label with no control-flow consumer
  (grep: only an example in `openup-state.py --help` and a sample in `test_openup_state.py`);
  the fold is a cosmetic event rename, not a semantic change. §9 is kept as a one-line map
  from the old event to the folded one.
- **Box 121 narrowed to complete-task only**, per DD1 — `/openup-create-handoff` is left
  unchanged (no teardown existed to slim). Its skill dirs stay in the claim `touches` (a
  superset is fenced-legal) but received no edit.

**Verification:** full `scripts/tests/` suite 300 passed / 1 pre-existing failure
(`test_docs_index.py::…test_write_creates_index_file` — a macOS `/private/var` vs `/var`
tmpdir-symlink assertion, reproduces identically with these edits stashed, unrelated to
T-063). `scripts/check-docs.py` green (7 instances). Live⇄template copies byte-identical
for both edited skills.

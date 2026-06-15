# T-042 — design / evidence

Source: `es-invoices/docs/iteration-retrospectives/iteration-1-7-retrospective.md`
"What to Improve". That run reached iteration 7 (real worktree + quick-track use),
so it exercised paths the first audit (iterations 1–4) did not.

## Evidence per fix

- **G3 (sync-status:258 vs :287).** `status = derive_status(state)` runs on the
  in-memory state where `roadmap_synced` is still false; `set_gate_roadmap_synced`
  runs only after (line ~287). So the first run always stamps `in-progress`, a
  second stamps `completed`. Retro Process Gap #3 ("two-run dance"); I hit it in
  T-041's own completion. Fix: when the run will set the gate (not `--no-gate`),
  set `state["gates"]["roadmap_synced"]=True` in memory *before* deriving, so the
  derive reflects the reality the run is creating. One run → completed.

- **G2 (openup-fence build_allowlist).** `task_touches` returns `[]` for a
  quick-track task (no claim touches, no plan frontmatter), so its real edits are
  `OUT OF LANE`. Retro Process Gap #2 ("6 re-claims"). Fix: read `track` from
  `.openup/state.json`; if `quick` AND no declared surface (no claim/plan touches
  and no `--allow`), do not flag out-of-lane — quick is single-file/no-plan-gate
  by design, so it is unfenced unless it opts back in with `--touches`/`--allow`.
  The stale-view check is unchanged (view freshness is orthogonal to lane purity).

- **Fix-7b (auto-log-commit:182,185 + on-stop:182,197).** Both `state_get(cwd, …)`
  — the same cwd-pinning blindness T-041 fixed only in `gate-edits.py`. Under a
  worktree, cwd is the main repo (no state) → `auto-log-commit` logs `task_id:
  null`; `on-stop` reads absent gates. Retro Process Gap #1. Fix: a shared-shape
  `resolve_state_root(cwd)` — cwd if it has state, else the first linked worktree
  (`git worktree list --porcelain`) whose `.openup/state.json` exists, preferring
  a branch match; else cwd (fail-safe). Unlike gate-edits there is no edit-target,
  so resolution is worktree-enumeration, not path-walking.

## Completion verification (step 1a — graded against the diff)

- ✅ **R1 G3** — `sync-status.py:257` forces `roadmap_synced` true in-memory
  before `derive_status`; `test_single_run_completes_when_gates_met` proves one
  run → `completed`. `--no-gate` path unchanged (`DeriveStatusTests` still pass).
- ✅ **R2 G2** — `openup-fence.py` `resolve_track` + `quick_unfenced`;
  `FenceQuickTrackTests` (4): unfenced when undeclared, fences with `--allow`,
  stale-views still flagged, standard still blocks.
- ✅ **R3 Fix-7b** — `resolve_state_root` in both hooks;
  `test_resolves_task_from_worktree_when_cwd_has_no_state` (auto-log-commit:
  task_id resolved from worktree, not null). on-stop gate block reads `sroot`.
  Fail-safe to cwd verified by all existing hook tests (cwd == root) still green.
- ✅ **R4 G4** — complete-task SKILL (both copies) flips plan.md `status: done`
  before archive; T-041 retro-flipped → T-042 preflight READY (demonstrated live).
- ✅ **R5** — suite 242 pass / 1 pre-existing env failure; parity green (62).

**Step 1b — Success Measures**: `n/a`. Internal tooling/process correctness; the
falsifiable measure is the test suite (+6 tests encoding each fix's behavior) and
the eliminated frictions (two-run dance, quick re-claims, task_id-null logs,
dependency-blocks-on-done). No runtime metric to instrument.

## Decisions log

- **DD1**: Stack on T-041 (unmerged, shares sync-status.py) rather than branch
  from main and conflict.
- **DD2**: In-place — broader Fix-7 hooks are the bug; can't trust worktrees yet.
- **DD3**: Quick-track fence is *opt-out by default* (unfenced unless touches
  declared), mirroring quick's no-plan-gate philosophy — not a fence deletion.
- **DD4**: Worktree resolution is fail-safe (ambiguous/none → cwd) so a parallel
  multi-worktree setup can never make these hooks worse than today.

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

## Decisions log

- **DD1**: Stack on T-041 (unmerged, shares sync-status.py) rather than branch
  from main and conflict.
- **DD2**: In-place — broader Fix-7 hooks are the bug; can't trust worktrees yet.
- **DD3**: Quick-track fence is *opt-out by default* (unfenced unless touches
  declared), mirroring quick's no-plan-gate philosophy — not a fence deletion.
- **DD4**: Worktree resolution is fail-safe (ambiguous/none → cwd) so a parallel
  multi-worktree setup can never make these hooks worse than today.

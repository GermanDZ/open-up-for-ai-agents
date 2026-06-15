# T-041 — design / audit evidence

In-flight decisions and the evidence behind each fix. Sources: es-invoices
`docs/agent-logs/agent-runs.jsonl`, archived `state-T-00X.json`, and 12 session
transcripts under `~/.claude/projects/-…-es-invoices/`. NB: that directory was
**reused across several project restarts** (es-invoices ⇄ FacturaSimple, T-000 vs
T-001 numbering, opus-4-7), so cross-restart naming/model differences are noise,
not findings — discounted below.

## Evidence per fix

- **Fix 1/2 (timestamps).** `state.json.started_at` and `sync-status.py` dates are
  already script-stamped (`openup-state.py:294`, `sync-status.py:254`). But
  `agent-runs.jsonl` `ts` + run-log Start/End come from `[ts]` placeholders in the
  scribe briefs at `openup-start-iteration/SKILL.md:275-279`,
  `openup-complete-task/SKILL.md:107-112`, `openup-log-run/SKILL.md:26-27`.
  Observed corruption: T-003 `iteration_complete` logged `08:15:00Z` but its
  commits landed `08:32:18Z`/`08:32:52Z`; `state-T-003.json.started_at` is
  `08:30:35Z` — i.e. "started" after it "completed". Round invented times
  (`00:00:00Z`, `07:55:00Z`). The scribe contract says "never invent values", so
  handing it `[ts]` is the root cause. **Decision**: move the stamp into the
  script (`log-event`) so the model can't supply one.

- **Fix 3 (track).** `on-task-request.py:62-68` `QUICK_TRACK_RE` matches bare
  `docs?`/`readme`, so Vision + risk-list auto-selected `quick`, skipping plan +
  rubric gates (`state-T-00X.json`: `plan_persisted:false`, `track:quick`).
  **Decision**: add `SPINE_RE`, checked before the quick branch in
  `suggest_track()`; keep the function pure for the existing unit tests.

- **Fix 7 (worktree gate).** `gate-edits.py` reads state via `state_get(cwd, …)`
  (`gate-edits.py:58-67,151`) — always the harness cwd. With `worktree:true`,
  state lives in the worktree, so a legitimate in-worktree edit blocks. es-invoices
  session hit this and worked around it by collapsing the worktree to in-place.
  **Decision**: resolve the state root by walking up from the **edit target** to
  its git worktree root (`git -C <dir> rev-parse --show-toplevel`), fall back to
  cwd. This iteration runs in-place precisely because the bug isn't fixed yet.

- **Fix 8 (plan exemption).** Same hook blocked this remediation's own plan-mode
  plan file (`~/.claude/plans/…md`) — not in `EXEMPT_PREFIXES`
  (`gate-edits.py:42-48`). **Decision**: exempt the plan-mode plan path
  (process-state, like `docs/explorations/`).

- **Fix 2 (agents).** `setup-agent-teams.sh:252-268` copies teammates/teams/
  skills/rubrics/hooks but not `agents/`; template exists at
  `.claude-templates/agents/{openup-scribe,openup-explorer}.md`. es-invoices had no
  `.claude/agents/` → `Agent type 'openup-scribe' not found`, forcing CLI fallback.

- **Fix 4 (next guidance).** `openup-next/SKILL.md:50-53` treats exit 3 as a clean
  no-op (correct) but gives no path forward when pending rows lack a change folder.
  Board derives lanes from `docs/changes/*/plan.md` (`openup-board.py:73-86`).

- **Fix 5 (CLI ref).** Repeated `usage:`/`unrecognized arguments` on
  `check-docs.py`, `openup-state.py`, `openup-claims.py`; invocations scattered
  inline across skills, no central reference.

- **Fix 6 (bootstrap commit).** `bootstrap-project.sh:178` commits
  `"Initial commit: Bootstrap…"` — fails the canonical format
  `validate-commit.py` enforces (`^(feat|fix|…|chore|quick)(\(scope\))?!?: .{3,}`).

## Dropped candidate

`docs/status.md` vs `docs/project-status.md`: no stale references in the framework;
the es-invoices probe was an old-session typo, not a framework bug.

## Findings surfaced during implementation (beyond the original 8)

- **F9 — `/openup-next` end-of-phase is correct, not a bug.** The user saw the
  loop no-op when all roadmap rows were `completed`. That is the designed stop;
  the *template* openup-next already promotes pending tasks (step 1c) and stops
  only when truly empty. Action taken: the **live** openup-next was a stale
  pre-1c copy — synced it to the (newer) template, and added an explicit
  "run `/openup-phase-review`" line to the fully-delivered fall-through. Folded
  into Fix 4.
- **F10 — pre-existing `.claude ↔ .claude-templates` drift (34 files).** Baseline
  `check-claude-sync.sh` is already red, independent of this task (hooks aren't
  even covered by it; the skills I touched were drifted before I arrived). Out of
  scope for T-041 — flagged for its own cleanup task. I did not worsen it (every
  edit was applied to both copies identically) and net-reduced it by 1 by syncing
  openup-next.
- **F-immediate — es-invoices unblock.** es-invoices had no `.claude/agents/` and
  was hitting `Agent type 'openup-scribe' not found` every cycle. Installed the
  two agent definitions into its `.claude/agents/` directly (the framework Fix 2
  only reaches it on the next bootstrap/sync).

## Completion verification (step 1a — graded against the diff)

- ✅ **R1** log-event clock-stamps ts — `scripts/openup-state.py` `cmd_log_event`
  + parser; `LogEventTests` (3 tests) assert ISO-8601 ts + monotonicity.
- ✅ **R2** skills off `[ts]` — start-iteration §9 / complete-task §5 / log-run
  briefs now call `log-event`; `grep '\[ts\]'` returns nothing in those skills.
- ✅ **R3** agents installed — `setup-agent-teams.sh` agents block; verified
  end-to-end into a temp project (both agent files appear).
- ✅ **R4** spine off quick — `on-task-request.py` `SPINE_RE`; `SuggestTrackTests`
  spine cases pass (vision/risk/use-case → standard; architecture → full;
  "fix typo in readme" still quick).
- ✅ **R5** next guidance — `openup-next` SKILL exit-3 / fully-delivered branches
  name `/openup-create-task-spec` + `/openup-phase-review`.
- ✅ **R6** CLI reference — `script-cli-reference.md` exists; synopses taken from
  live `--help`; linked from README + both CLAUDE copies.
- ✅ **R7** worktree gate — `gate-edits.py` `resolve_state_root`;
  `test_worktree_state_resolved_from_target` (state in worktree, cwd in main → allow).
- ✅ **R8** plan-mode exempt — `gate-edits.py` `is_plan_mode_path`;
  `test_plan_mode_path_exempt_without_state`.
- ✅ **R9** no regressions — suite 233 pass / 1 pre-existing env failure
  (docs-index `/private` symlink, untouched); parity green post-reconcile.

**Step 1b — Success Measures**: `n/a`. This is internal tooling remediation, not a
user-facing feature; the falsifiable measure is the test suite (the +7 tests
encode each fix's observable behavior) and the eliminated failure class
(fabricated timestamps can no longer be authored — the model never supplies a ts).
No runtime metric/event to instrument.

## Decisions log

- **DD1**: Track standard (not full) — mechanical, no architecture/multi-role.
- **DD2**: In-place, not worktree — avoids Fix 7 until it lands.
- **DD3**: One task (T-041) with 8 Operations boxes, worked sequentially.
- **DD4**: Every live hook/skill edit mirrored to `.claude-templates/`.
- **DD5**: `check-claude-sync` left red — pre-existing drift (F10), not this
  lane's surface; fixing 34 unrelated files would violate stay-in-your-lane.

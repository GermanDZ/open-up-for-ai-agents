# T-065 — Design & Verification Notes

## In-flight decisions

- **In-process composition, not subprocess.** `resolve`/`status` import the sibling
  scripts (`openup-input`, `openup-roadmap`) via the same `importlib` pattern the board
  already uses for `openup-claims`, and read `.openup/state.json` directly for the active
  iteration (avoids openup-state.py's module-level `REPO_ROOT`, which would not track
  `--root`). One process, zero round-trips. (Assumption 1 held.)
- **Read-only proven, not asserted.** `build_board` is called without `write_board` and
  without the reap; a test snapshots state/roadmap/claims/board.json and asserts
  byte-identity after `resolve`.
- **Promote = roadmap next, by construction.** `_promote_next` invokes
  `openup-roadmap.py cmd_next` with stdout/stderr captured, so `resolve`'s promote pick is
  the *same* selector — a divergence=0 test asserts it.
- **Fence surface.** Two derived mirrors move with the skill edits and had to be declared
  in `touches`: `.claude/skills/openup-start-iteration/SKILL.md` (the sole tracked `.claude`
  mirror; `check-claude-sync` forces it to match the template) and
  `docs-eng-process/skills-guide.md` (derived index embedding skill success-criteria).

## Step 1a — Requirement verification against the diff (BLOCKING)

- ✅ **R1** one JSON, `path ∈ {resume,pick,promote,noop}` + lane/payload + reason —
  `cmd_resolve`/`resolve_decision`; scenario (active→resume) green in
  `test_resume_active_iteration`.
- ✅ **R2** precedence == §0–§1 — `resolve_decision` order; scenarios green:
  `test_resume_answered_input_outranks_active`, `test_pick_top_lane`,
  `test_promote_roadmap_task`, `test_noop_when_exhausted`.
- ✅ **R3** read-only — `test_resolve_is_read_only` (byte-identity); live smoke: `board.json`
  stayed absent after `resolve`.
- ✅ **R4** ≤~40 lines — `test_line_budget`; live `resolve` on this repo = 11 lines.
- ✅ **R5** `status` superset — `cmd_status`; `test_status_superset` (active + leases +
  pickable + promotable).
- ✅ **R6** §0–§1 single `resolve` call, sentinel + two exits unchanged — `openup-next/SKILL.md`
  312→247 lines; `OPENUP-NEXT: ADVANCED/DONE` ×4, `complete-task`/`create-handoff` ×7 still present.
- ✅ **R7** start-iteration skips re-read on pre-resolved lane — new `### 0.` guard (was-I-handed-a-task_id).
- ✅ **R8** `openup-loop.sh` no-op pre-check — `resolve`-based pre-check exits 0 without spawning
  a cycle on `path:"noop"`; `bash -n` clean, noop-grep verified.
- ✅ **R9** reference + manifest document `resolve`/`status` — `script-cli-reference.md` board
  section lists both; `process-manifest.txt` already ships `openup-board.py` (tests are
  not manifest-tracked, per existing convention).

**All requirements ✅ against the diff. No ❌.**

## Step 1b — Success-measure instrumentation (BLOCKING, standard)

Measure: input tokens on the state-discovery phase drop ≥40% within the first 10 cycles.
Instrumentation: before/after token counts read from `docs/agent-logs/runs/`.
- ✅ instrumentation **pre-exists** — the per-cycle run-log shards under
  `docs/agent-logs/runs/` are the read-back source; no new emitter needed. Read-back date:
  10 `/openup-next` cycles after this lands on trunk.

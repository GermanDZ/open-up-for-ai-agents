# Project Status

**Phase**: construction
**Iteration**: 14
**Iteration Goal**: T-022 — Fix template→.claude sync (flat skills + rubric/hook coverage) + auto-commit log tail at stop
**Status**: completed
**Current Task**: None
**Iteration Started**: 2026-06-12
**Last Updated**: 2026-06-12
**Updated By**: openup-complete-task

## Notes

- **Iteration 14** (2026-06-12): T-022 sync correctness — rewrote `scripts/sync-templates-to-claude.sh` to the flat skill layout (one level under `.claude/skills/`, the discovery requirement) and added rubric/hook/config/agent coverage it was missing (root cause of the nested-skill discovery break). Back-propagated two drifted hooks (`check-unfinished-tasks.py`, `gate-edits.py`) live→template. Added an `on-stop.py` step that auto-commits a lone dirty `agent-runs.jsonl` as a log-only `[openup-skip]` commit so sessions end on a clean tree (verified: lone-jsonl→commit, non-log→block exit 2, clean→noop). Solo, standard track, no team.
- **Iteration 12** (2026-06-12): T-017 `/openup-next` continue-loop — headline of the clarity/self-brief/loop path. Added `scripts/openup-board.py` (deterministic derived `.openup/board.json`: lanes with task/title/track/state/lease/hat/next_action/plan/collides_with/depends_ok; imports `openup-claims.py` so board `ready` == preflight-clear), the `/openup-next` skill (one cycle: top pickable lane → `/openup-start-iteration` claim+worktree → self-brief+hat → execute under track → tick Operations boxes → exit via complete-task OR create-handoff, the only two exits), checkbox `## Operations` convention (optional `(role)` hat tag; ticking is sanctioned progress state), and `CLAUDE.openup.md` no-conversation-only-state rule. board.py placed at repo-root `scripts/` (not the plan's `.claude/scripts/`) to sit beside its peers. 15 board tests + 47-test suite green. Solo, standard track, no team.
- **Iteration 11** (2026-06-12): T-016 self-briefing roles — second task under the solo-by-default model. Added a uniform `## On Start, Read` block (status · active change folder · role guidelines) to all 5 reasoning teammate files; scribe keeps its read-only-target-file rule as the deliberate exception; one-line pointers in all 6 compacts. Collapsed the PM Delegation Brief Format to pointer-only (`[ROLE]: T-NNN. Deltas: …`) and named "writing scope into a brief" a fix-spec-first signal; added the briefing-from-docs principle to `CLAUDE.openup.md`. Resolved plan Open Question #3 (compacts get a pointer, not a verbatim copy). `.claude/` → `.claude-templates/` parity green (61 files). Solo, standard track, no team. Unblocks T-017 (`/openup-next`).
- **Iteration 10** (2026-06-12): T-015 ambiguity gate — first task run under the new solo-by-default model (teams opt-in). Added an Ambiguity Gate step to `create-task-spec` and `plan-feature`, the `**Assumption:**` convention to the task-spec template, and rubric criterion 9. The T-015 spec itself exercised the gate (3 non-blocking assumptions recorded, no blocking questions). Solo, standard track, no team.
- **Iteration 9 closed** (2026-06-11): T-002 `/openup-sync-spec` completed. Process v2 program (T-001–T-011) all delivered. [Retrospective](iteration-retrospectives/iteration-9-retrospective.md). Retro counter reset to 0.
- Iteration tracking initialized with the Process v2 program (docs/plans/2026-06-10-process-v2-claude-code-harness.md). Prior framework work (PRs #1–#3) predates status tracking.
- **Process v2 complete** (2026-06-10 to 2026-06-11): All readiness gates, graded tracks, worktree-per-task, sync-spec skill, retro cadence operational. Next: promote OpenSpec ideas plan or backfill SPDD out-of-band work.

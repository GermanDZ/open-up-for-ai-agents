# T-046 Handoff — Shard `agent-runs.jsonl` into lane-owned files

**Status:** in-progress (2 of 8 Operations done) · **Branch:** `feature/T-046-shard-agent-runs-jsonl` · **For:** next dev session
**Last commit:** `98d6e32` — feat(state): shard run-log writer + runs-build consolidator [T-046]

## 1. Acceptance criteria
Full spec: `docs/changes/T-046/plan.md` (R1–R5, all with Given/When/Then).
- [x] **R1** — `log-event` writes `docs/agent-logs/runs/<UTC-date>-<key>.jsonl` (key = task_id else branch slug), not the shared file. *(done, `_shard_key` + `cmd_log_event` in `openup-state.py`)*
- [x] **R3-build** — `openup-state.py runs build` derives `agent-runs.jsonl` from the shard glob, sorted by `ts`. *(done, `cmd_runs_build`)*
- [ ] **R3-untrack** — `agent-runs.jsonl` gitignored, `git rm --cached`'d, and its `merge=union` line dropped from `.gitattributes:8`.
- [ ] **R4** — `auto-log-commit.py` + `on-stop.py` stage the lane **shard**, never `agent-runs.jsonl`. (Both have `.claude` ↔ `docs-eng-process/.claude-templates/` mirrors — edit the template, copy to `.claude`.)
- [ ] **R5** — `duplicate_start_blocked` counting points at the shard glob / `runs build` (doc-only — no code consumer in `openup-claims.py`).
- [ ] Tests + docs (see §2, §4).

## 2. How to exercise it (test cases)
Verified working today:
1. `python3 scripts/openup-state.py log-event --event x --task-id T-999 --branch feature/T-999-y --log-dir /tmp/t` → writes `/tmp/t/runs/<date>-T-999.jsonl`, **not** `agent-runs.jsonl`.
2. Same without `--task-id` → shards by branch slug (`<date>-feature-T-999-y.jsonl`).
3. `python3 scripts/openup-state.py runs build --log-dir /tmp/t` → rebuilds `/tmp/t/agent-runs.jsonl` from shards, ts-sorted.
4. `python3 -m unittest scripts.tests.test_t006_hooks scripts.tests.test_openup_claims` → 70 green (regression baseline before R4).

Still to add (tester step): two-lane-disjoint-files (R2), hook-commits-shard-not-shared (R4), counter-reads-shards (R5).

## 3. Troubleshooting
- **`re` was unimported in `openup-state.py`** → `_shard_key` uses `re.sub`; added `import re` (line 42). Watch for this if you add more regex.
- **The gate blocks `docs/changes/T-046/` edits without active state** → state is live now (`task_id=T-046`, `plan_persisted` set); if you re-clone the session, re-`init` + `set-gate plan_persisted` first (or it's covered once on the branch).
- **R4 is the delicate part** → `auto-log-commit.py` keeps idempotency by reading `agent-runs.jsonl`'s last-line SHA and has a `commit_only_touches_logs` tail-chasing guard (`LOG_REL` at line 47). Re-point these at the **shard** path (compute key from the resolved state's task_id/branch — `resolve_state_root` already finds the right worktree). `on-stop.py` has `EXEMPT_DIRTY_PATHS={agent-runs.jsonl}` (line 41) — once `agent-runs.jsonl` is gitignored it won't be tracked-dirty; make sure freshly-written **shards** are committed by auto-log-commit so they don't strand the stop-gate.

## 4. Open questions
- **Do we keep `agent-runs.jsonl` rebuilt-on-commit, or purely on-demand?** Current plan: gitignored, built by `runs build` when someone wants to query. Confirm no skill/hook silently depends on it being present post-commit.
- **Shard retention / rollup?** Per-task-per-day files will accumulate under `docs/agent-logs/runs/`. Out of scope here, but a future `runs gc`/monthly-rollup may be wanted (note, don't build now).
- **Docs to update (R4/R5 commit):** `docs-eng-process/parallel-work.md` (reclassify the run log from class-2 union → class-1 shard + derived view) and `script-cli-reference.md` (add `runs build`). `parallel-lanes.md` is in `touches` for the same reclassification.

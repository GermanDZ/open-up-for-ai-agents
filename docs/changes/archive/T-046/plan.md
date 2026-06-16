---
id: T-046
title: "Shard agent-runs.jsonl into lane-owned files; derive the consolidated view"
status: done
track: standard
priority: medium
estimate: 1 session
depends-on: [T-023]
blocks: []
touches: [scripts/openup-state.py, docs-eng-process/.claude-templates/scripts/hooks/auto-log-commit.py, docs-eng-process/.claude-templates/scripts/hooks/on-stop.py, scripts/openup-claims.py, .gitattributes, .gitignore, scripts/tests/test_t006_hooks.py, scripts/tests/test_openup_claims.py, docs-eng-process/parallel-lanes.md, docs-eng-process/parallel-work.md, docs-eng-process/script-cli-reference.md, scripts/tests/test_openup_state.py, docs/changes/T-046, docs/roadmap.md]
claimed-by: null
---

# T-046 — Shard `agent-runs.jsonl` into lane-owned files

## Story

> **As a** team running parallel lanes whose PRs go through GitHub
> **I want** the machine-readable agent run log to stop causing merge conflicts
> **So that** two branches that both logged runs merge cleanly without a manual
> rebase every time.

INVEST: ✅ Independent · ✅ Negotiable · ✅ Valuable · ✅ Estimable · ✅ Small · ✅ Testable

## Analysis Context

- **The defect.** `docs/agent-logs/agent-runs.jsonl` is a single append-only file
  with `merge=union` in `.gitattributes` (T-023). The union driver resolves
  divergent appends **locally**, but **GitHub does not run custom merge drivers
  server-side**, so any two branches that both appended (observed this session:
  T-043 vs T-044, then T-045) show `CONFLICTING` on their PRs and need a rebase.
- **The proven precedent.** T-024 solved the *identical* "shared insertion point"
  problem for `project-status.md`'s `## Notes`: shard to **lane-owned files**
  (`docs/status-notes/YYYY-MM-DD-<task>.md`, class-1, one writer by construction)
  and **derive** the assembled view. The human-readable `.md` run logs are
  *already* sharded this way (`docs/agent-logs/YYYY/MM/DD/<ts>-agent-<branch>.md`);
  only the machine-readable JSONL index is still a single shared file.
- **Decided approach (ambiguity gate).** Resolved with the product owner
  2026-06-16: **Option A (shard)**, not Option B (defer-commit-off-main). A is
  consistent with T-024 + the existing `.md` sharding and is *truly* conflict-free
  (lane-owned), where B leaves branch-side entries uncommitted/fragile.
- **Assumption (vetoable):** the shard key is `<date>-<task_id>` when a task id is
  present, else `<date>-<branch>` — one file per task-per-day, so a lane never
  shares a file with another lane. Sub-day multiplicity within one task is the
  same lane (no conflict).
- **Assumption (vetoable):** `agent-runs.jsonl` becomes a **derived, gitignored
  build artifact** rebuilt on demand from the shards (`openup-state.py runs
  build`). Memory `project_t006_autolog_onstop_loop` cautioned against gitignore
  *of the source log*; here the **shards are the committed source of truth** and
  the consolidated file is genuinely derived, so gitignoring the derived view is
  correct (it is no longer a source). Removing it from tracking is what
  eliminates the cross-branch conflict at the root.

## Requirements

1. **`log-event` writes to a lane-owned shard, not the shared file.**
   - **Given** `log-event --event X --task-id T-099` on branch `feature/T-099-y`,
     **When** it runs, **Then** the record is appended to
     `docs/agent-logs/runs/<UTC-date>-T-099.jsonl` and **not** to
     `docs/agent-logs/agent-runs.jsonl`.
   - **Given** an event with **no** `--task-id`, **When** it runs, **Then** it
     shards by branch: `docs/agent-logs/runs/<UTC-date>-<branch-slug>.jsonl`.

2. **Two lanes never write the same shard file (the conflict-free invariant).**
   - **Given** lane A (`T-043`) and lane B (`T-044`) both log on the same UTC day,
     **When** each logs, **Then** they write distinct files
     (`...-T-043.jsonl` vs `...-T-044.jsonl`) — a three-way merge of the two
     branches touches disjoint paths and cannot conflict.

3. **`agent-runs.jsonl` is derived and no longer tracked.**
   - **Given** the repo, **When** inspected, **Then** `docs/agent-logs/agent-runs.jsonl`
     is gitignored (absent from `git ls-files`), and `.gitattributes` no longer
     declares `merge=union` for it (the union hack is obsolete).
   - **Given** `openup-state.py runs build`, **When** run, **Then** it concatenates
     all `docs/agent-logs/runs/*.jsonl` records sorted by `ts` into
     `agent-runs.jsonl` for local querying (idempotent; a derived view).

4. **The auto-log-commit + on-stop hooks commit the shard, not the shared file.**
   - **Given** a commit on a task branch, **When** `auto-log-commit` runs,
     **Then** it stages/commits the lane's shard file under `docs/agent-logs/runs/`
     (lane-owned, fence-clean) and never the derived `agent-runs.jsonl`.

5. **Existing consumers keep working against the shards.**
   - **Given** the T-044 `duplicate_start_blocked` counter (which counted via
     `agent-runs.jsonl`), **When** counting, **Then** it reads the shard glob
     (`docs/agent-logs/runs/*.jsonl`) or the rebuilt consolidation and still
     returns the correct count.

## Behavior Delta

- **Modified:** the *storage location* of machine-readable run events
  (`docs-eng-process/parallel-work.md` class-2 "append-only union" entry → now a
  class-1 lane-owned shard + class-3 derived view). No change to the event schema
  or to any user-facing product behavior.
- **Removed:** `agent-runs.jsonl` as a tracked, `merge=union` file.
- **Added:** `docs/agent-logs/runs/<date>-<key>.jsonl` shards; `runs build` derived-view command.

## Success Measures

`n/a` — internal process tooling. The falsifiable check is mechanical and lives
in Requirement 2's scenario: after this lands, two branches that both log on the
same day produce a **clean** GitHub merge (no `agent-runs.jsonl` in the conflict
set). That is verified by the test suite, not a usage metric.

## Approach

Repoint the single writer (`openup-state.py log-event`) at a per-lane shard path;
add a `runs build` consolidator that derives `agent-runs.jsonl` from the shard
glob; gitignore the derived file and drop its `merge=union` line; update the two
log-committing hooks to stage the shard; update the T-044 counter to read shards.
Mirror the hook edits into `.claude-templates/`. The `.md` run logs are unchanged
(already sharded).

## Structure

- **Modify** `scripts/openup-state.py` — `cmd_log_event` shard path + new `runs build`.
- **Modify** `.claude-templates/scripts/hooks/auto-log-commit.py` + `on-stop.py` — stage shard.
- **Modify** `scripts/openup-claims.py` — `duplicate_start_blocked` counter reads shards (if it reads the file).
- **Modify** `.gitattributes` (drop union line) + `.gitignore` (add derived file).
- **Modify** tests `test_t006_hooks.py`, `test_openup_claims.py`; docs `parallel-lanes.md`, `script-cli-reference.md`.
- **Do not touch** the `.md` run-log sharding, the event schema, `sync-status.py`.

## Rollout

`n/a — internal tooling`. Not user-facing; takes effect for agents/humans on
update. Migration of the existing tracked `agent-runs.jsonl`: removed from
tracking in this task's commit; its history stays in git log. No flag (the change
is structural, a flag would add no safety).

## Safeguards

- The shards are lane-owned (write-fence: `docs/agent-logs/` is already an allowed
  audit surface) — do not reintroduce a shared append file.
- `runs build` is a derived view: never hand-edited, regenerated — same discipline
  as `roadmap.md`/`project-status.md`.
- Keep the event schema byte-identical so historical `.md` logs + queries still parse.

## Operations

- [x] R1: `cmd_log_event` writes `docs/agent-logs/runs/<date>-<key>.jsonl` (task_id else branch slug)
- [x] R3: add `openup-state.py runs build` consolidator (glob → sorted agent-runs.jsonl)
- [x] R3: gitignore `docs/agent-logs/agent-runs.jsonl`; drop its `merge=union` from `.gitattributes`; `git rm --cached` it
- [x] R4: auto-log-commit.py + on-stop.py stage the lane shard, not the derived file; mirror to `.claude-templates/`
- [x] R5: point the T-044 `duplicate_start_blocked` counter at the shard glob
- [x] (tester) Tests: shard-path, two-lane-disjoint-files, derived rebuild, hook-commits-shard, counter-reads-shards
- [x] Docs: `parallel-work.md`/`parallel-lanes.md` reclassify the run log; `script-cli-reference.md` `runs build`
- [x] Full hook + claims + state suites green; `.claude`↔template sync green

## Norms

- Write-fence + lane-owned audit surfaces: [parallel-lanes.md](../../../docs-eng-process/parallel-lanes.md).
- Derived-view discipline (regenerate, never hand-edit): same as `sync-status.py` views.
- Clock-stamped events only (no model-authored `ts`): `openup-state.py log-event` (T-041).

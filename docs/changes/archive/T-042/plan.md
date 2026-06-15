---
id: T-042
title: "Retro-surfaced framework fixes: sync-status single-pass, quick-track unfenced, worktree-aware audit hooks"
status: done
track: standard
priority: high
depends-on: [T-041]
blocks: []
touches: [scripts/sync-status.py, scripts/openup-fence.py, scripts/tests/test_sync_status_notes.py, scripts/tests/test_openup_fence.py, scripts/tests/test_t006_hooks.py, docs-eng-process/.claude-templates, docs/changes/T-042, docs/changes/archive/T-041/plan.md]
claimed-by: null
---

# T-042 — Retro-surfaced framework fixes

## Context

`es-invoices/docs/iteration-retrospectives/iteration-1-7-retrospective.md` (a real
project run through iteration 7) independently corroborated two T-041 fixes
(worktree/cwd = Fix 7; sync-status completion = F11) and surfaced three further
defects. T-041 fixed the *gates* of sync-status (F11) but not its *ordering*; it
fixed `gate-edits.py`'s worktree blindness but not the other state-reading hooks.
This task closes those gaps. Stacked on the unmerged T-041 branch (shares
`sync-status.py`). Runs in-place because the broader Fix-7 hooks are still
worktree-blind until this task lands. Evidence: [design.md](./design.md).

## Requirements

1. **sync-status completes in a single run (G3).** `sync-status.py` derives the
   roadmap Status cell from the *post-sync* gate set, so one run stamps
   `completed` when the other gates are met — no "two-run dance".
   - **Given** a standard task with `log_written=true` and `roadmap_synced=false`,
     **When** `sync-status.py` runs once (without `--no-gate`), **Then** the
     roadmap cell is stamped `completed (YYYY-MM-DD)` in that single run.
   - **Given** `--no-gate` (isolated tests), **When** sync runs, **Then** it does
     not force `roadmap_synced` and derives from the actual gates (unchanged).

2. **Quick-track lanes with no declared surface are unfenced (G2).** A quick-track
   task has no `plan.md`, so its claim `touches` is empty; the fence must not flag
   its real edits out-of-lane (the retro's "6 re-claims" friction).
   - **Given** a quick-track active iteration with empty `touches` and no
     `--allow`, **When** `openup-fence.py check` runs over its diff, **Then** no
     file is reported `OUT OF LANE` and it exits 0 with a note that quick lanes
     are unfenced.
   - **Given** a quick-track task that *did* declare `touches`/`--allow`, **When**
     the fence runs, **Then** it enforces normally (a declared surface opts back in).
   - **Given** a stale shared view in the diff, **When** the quick fence runs,
     **Then** the stale-view check still applies (quick relaxes lane purity, not
     view freshness).

3. **Audit hooks resolve state from the active worktree (broader Fix 7).**
   `auto-log-commit.py` and `on-stop.py` read iteration state from the worktree
   that holds it, not only the harness cwd.
   - **Given** an active iteration whose state lives in worktree `W` while the
     hook fires with cwd = the main repo (no state), **When** `auto-log-commit`
     logs a commit, **Then** the record carries `W`'s `task_id` (not null).
   - **Given** the same worktree/cwd split, **When** `on-stop` evaluates its
     unmet-gate block, **Then** it reads `W`'s gates (so it neither false-blocks
     nor false-passes).
   - **Given** no worktree has state and cwd has none, **When** either hook runs,
     **Then** it behaves exactly as today (fail-safe fallback to cwd).

4. **complete-task flips the change folder `plan.md` status to `done` (G4).**
   `/openup-complete-task` sets the archived spec's frontmatter `status: done`
   so dependency resolution (which reads frontmatter, not the derived roadmap)
   sees a completed dependency. Found when T-042's preflight blocked on
   "T-041 is in-progress" despite the roadmap showing it completed.
   - **Given** a task whose dependency's archived `plan.md` says `status: done`,
     **When** `openup-claims.py preflight` runs, **Then** the dependency is
     satisfied (no false "in-progress" block).
   - **Given** the complete-task skill, **When** its text is read, **Then** it
     includes a step setting the change folder `plan.md` `status: done` before
     archiving. (Retro-fix the already-merged T-041 spec to `done` as data.)

5. **No regressions.** Full suite green (1 pre-existing env failure excepted);
   `.claude ↔ template` parity green; new tests cover each fix.

## Behavior Delta

- **Modified**: `sync-status.py` derive order (force `roadmap_synced` in-memory
  before `derive_status` unless `--no-gate`); `openup-fence.py` (quick-track +
  undeclared surface → unfenced, views still checked); `auto-log-commit.py` &
  `on-stop.py` (resolve state root across linked worktrees). Each cites the retro
  finding it closes; no Ring-1 artifact changes.
- **Added**: `resolve_state_root` helper in the two audit hooks; tests.
- **Removed**: nothing.

## Operations

- [x] G3 — sync-status single-pass completion (+ integration test)
- [x] G2 — quick-track unfenced when no declared surface (+ 4 tests, incl. standard-still-blocks)
- [x] Fix-7b — auto-log-commit.py worktree-aware state (+ worktree test)
- [x] Fix-7b — on-stop.py worktree-aware state (gate block reads from state-bearing worktree)
- [x] G4 — complete-task sets plan.md `status: done`; T-041 retro-flipped (unblocked T-042 preflight)
- [x] Hooks (on-stop, auto-log-commit) + complete-task skill mirrored to `.claude-templates/`
- [x] Full suite 242 pass / 1 pre-existing env failure; parity green (62 files)

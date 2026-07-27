---
id: T-143
title: "Retro-cadence counter must live in a location genuinely shared across worktrees"
status: done
priority: high
estimate: 1 session
plan: ""
depends-on: []
blocks: []
last-synced: ""
touches:
  - scripts/openup-state.py
  - scripts/tests/test_t011_retro.py
  - docs-eng-process/state-file.md
  - docs-eng-process/procedures/openup-start-iteration.md
  - docs-eng-process/procedures/openup-retrospective.md
  - docs-eng-process/.claude-templates/skills/openup-start-iteration/SKILL.md
  - docs-eng-process/.claude-templates/skills/openup-retrospective/SKILL.md
  - docs/roadmap.md
---

# T-143 — Retro-cadence counter isn't safely durable across worktrees

## Story

> **As a** process owner whose lanes each run in their own git worktree
> **I want** the retro-cadence counter to be stored somewhere every worktree
> reads and writes the same value
> **So that** the count a lane advances is the count the next lane sees, instead
> of every fresh worktree starting over from zero.

INVEST check:
✅ Independent (no DAG dep; ships with T-142 for value, not for correctness) ·
✅ Negotiable (storage location and migration policy are stated as defaults) ·
✅ Valuable (without it, T-142's new increments still evaporate) ·
✅ Estimable (one path-resolution function + migration + tests) ·
✅ Small (single session) ·
✅ Testable (two worktrees sharing a git common dir must read one count)

## Analysis Context

- **Domain.** The durable retro-cadence counter's *storage*, resolved today by
  `retro_path()` in `scripts/openup-state.py` as `state_dir(args)/retro.json`,
  where `state_dir()` defaults to `REPO_ROOT/.openup` and `REPO_ROOT` is derived
  from `__file__` — i.e. the **current worktree's** checkout.
- **The defect, in this repo.** `.gitignore:43` ignores `/.openup/`, so
  `retro.json` is neither tracked nor shared. Each worktree gets its own
  `scripts/` checkout, so `REPO_ROOT` differs per worktree and the counter
  restarts at `0` in every new lane. Observed directly this session: a T-135
  worktree read `retro get` as `0` immediately after T-132 had advanced it to
  `1`.
- **The defect, downstream.** A sibling project that *does* track
  `.openup/retro.json` in git hits the mirror-image failure: two lanes branching
  from the same count each write a scalar, and the merge **overwrites rather
  than sums** — a lost update that worsens with parallelism.
- **The prior art this mirrors.** `scripts/openup-claims.py` already solves
  exactly this for claims: `claims_dir()` resolves
  `git rev-parse --git-common-dir` → `<common>/openup/claims`, a directory every
  linked worktree shares and git never merges. The counter belongs beside it.
- **Scope boundaries.** This task moves *where* the counter lives. It does NOT
  change *when* it advances (T-142, same PR), the threshold, the reset, or the
  `iterations_since_retro` mirror field inside `state.json`. It does not
  introduce an event-list or union-merge representation — those solve the
  tracked-file variant only, and are recorded below as the rejected alternative.
- **Definition of done.** Two sequential worktrees of the same clone read and
  advance one counter; an existing per-worktree count is carried forward rather
  than silently reset to zero; tests still isolate.

> **Assumption:** the counter moves to `<git-common-dir>/openup/retro.json`,
> matching `openup-claims.py`'s claims-dir resolution. The roadmap entry names
> this location; the alternative (keep it tracked, add an additive merge
> strategy) is rejected because it does not fix *this* repo's gitignored variant
> at all. *(Vetoable at review.)*

> **Assumption:** an explicit `--state-dir` continues to scope the retro path
> too (with a new `--retro-dir` taking precedence over both). `--state-dir` is
> passed only by tests and by callers that deliberately isolate state, so
> honoring it preserves test isolation and prevents a temp-dir test from
> mutating the developer's real counter. *(Vetoable at review.)*

> **Assumption:** migration is read-forward and non-destructive — if the shared
> path has no file and the legacy `<worktree>/.openup/retro.json` does, its
> count seeds the shared file on first write/read; the legacy file is left in
> place rather than deleted. Deleting during a migration is the riskier half of
> the operation and buys nothing (the legacy file is gitignored and no longer
> read once the shared file exists). *(Vetoable at review.)*

No blocking questions: the roadmap entry names the target location and both
acceptance criteria; the three choices above are non-blocking defaults.

## Requirements

1. `retro_path()` resolves to `<git-common-dir>/openup/retro.json` when no
   directory override is supplied.
   - **Given** a git repository with no `--state-dir` / `--retro-dir` override
     **When** `openup-state.py retro increment` runs
     **Then** the file written is `$(git rev-parse --git-common-dir)/openup/retro.json`.
2. Two worktrees of the same clone read and advance a single shared count.
   - **Given** a clone whose counter is `1`, and a linked worktree created from
     it **When** `openup-state.py retro get` runs inside the linked worktree
     **Then** it prints `1`, and a subsequent `increment` there makes the main
     worktree's `retro get` print `2`.
3. An explicit `--retro-dir` overrides the shared location; an explicit
   `--state-dir` scopes the retro path when `--retro-dir` is absent.
   - **Given** a temp directory `D` **When** `openup-state.py retro increment
     --retro-dir D` runs **Then** `D/retro.json` is written and the shared
     `<git-common-dir>/openup/retro.json` is unchanged.
4. An existing legacy counter is carried forward, not reset to zero.
   - **Given** a `<worktree>/.openup/retro.json` holding `3` and no file at the
     shared path **When** `openup-state.py retro get` runs with no override
     **Then** it prints `3` (not `0`).
5. The migration is non-destructive and idempotent.
   - **Given** the legacy file holding `3` and a first `retro increment`
     **When** the command completes **Then** the shared file holds `4`, the
     legacy file still exists holding `3`, and a second `retro get` prints `4`
     (the legacy value is not re-applied).
6. Resolution degrades safely outside a git repository.
   - **Given** a directory that is not inside a git work tree
     **When** `openup-state.py retro get` runs **Then** it exits 0 and falls
     back to the previous `<repo-root>/.openup/retro.json` behavior rather than
     raising.
7. `docs-eng-process/state-file.md` documents the new location, the override
   precedence, and the migration.
   - **Given** `docs-eng-process/state-file.md` **When** the retro-counter
     section is read **Then** it names `<git-common-dir>/openup/retro.json`, the
     `--retro-dir` > `--state-dir` > shared-default precedence, and the
     read-forward migration.

## Behavior Delta

**Modified:**
- The retro counter's on-disk location — from `<worktree>/.openup/retro.json`
  to `<git-common-dir>/openup/retro.json`. The governing artifact is
  `docs-eng-process/state-file.md` (the retro-counter section, which today
  states the `.openup/retro.json` path), updated here. No Ring-1
  `docs/product/` use case describes the counter's storage.
- `retro_path()`'s override contract — gains `--retro-dir` ahead of the existing
  `--state-dir`. Governing artifact: `docs-eng-process/state-file.md` and
  `scripts/openup-state.py`'s module docstring (the `retro` subcommand line,
  which names `.openup/retro.json`).

**Added:** the read-forward migration from the legacy per-worktree path.
**Removed:** none — the legacy path stays readable as a migration source and as
the non-git fallback.

## Success Measures

We expect the **count observed at the start of a fresh worktree lane** to be
**≥ the count observed at the end of the previous lane, on 100% of lanes** (it
is currently reset to `0` on effectively every worktree lane — a 1-of-1 failure
rate over this session's observed T-132→T-135 transition). Instrumentation:
`python3 scripts/openup-state.py retro get`, run at
`/openup-start-iteration` §3b (which already reads it) and recorded in the
lane's run-log entry — no new telemetry required, only reading the number the
gate already reads. Read-back: the next `/openup-retrospective`, comparing the
`retro get` values logged across the intervening lanes for any decrease.

## Rollout

**Flagged?** No. A path-resolution change in a deterministic, locally-run CLI
with no deployed surface and no in-flight users or data beyond one scalar file.
Reversible by revert; the read-forward migration leaves the legacy file intact,
so a revert restores the old behavior with the old value still present.
`--retro-dir` provides per-invocation escape without a flag framework.

## Entities

- **`retro_path()`** (modified) — `scripts/openup-state.py`
- **`read_retro_count()` / `write_retro_count()`** (modified) —
  `scripts/openup-state.py`; gain the migration fallback
- **`claims_dir()`** (read-only, pattern source) — `scripts/openup-claims.py:112`
- **`state_dir()`** (read-only, unchanged) — `scripts/openup-state.py`
- **retro-counter docs** (modified) — `docs-eng-process/state-file.md`

## Approach

Give the counter its own path resolver instead of borrowing `state_dir()`,
resolving `git rev-parse --git-common-dir` the way `openup-claims.py` already
does for claims — the one directory this framework already treats as
shared-across-worktrees and outside git's merge machinery. Overrides stay
explicit and ordered (`--retro-dir`, then `--state-dir`, then the shared
default) so tests and isolated callers keep working unchanged. Reads fall back
to the legacy per-worktree file when the shared one is absent, which makes the
move a silent carry-forward rather than a reset; the first write lands at the
shared path and the fallback stops applying.

## Structure

**Add:**
- `retro_dir()` resolver + `--retro-dir` argument on the `retro` subparser —
  `scripts/openup-state.py`
- Worktree/migration tests in `scripts/tests/test_t011_retro.py` (a new
  `RetroStorageLocationTests` class that plants the CLI in a throwaway git repo,
  so the real `git rev-parse` path is exercised without touching the developer's
  own shared counter)

**Modify:**
- `scripts/openup-state.py` — `retro_path()` uses the new resolver;
  `read_retro_count()` falls back to the legacy path; module docstring's `retro`
  line names the new location
- `docs-eng-process/state-file.md` — new location, override precedence,
  migration note
- `docs-eng-process/procedures/openup-start-iteration.md` and
  `openup-retrospective.md` — both name `.openup/retro.json` in prose; repointed
  at the shared path (plus their rendered mirrors, regenerated not hand-edited)
- `docs/roadmap.md` — status (regenerated by `sync-status.py`, not hand-edited)

**Do not touch:**
- `state_dir()` and `.openup/state.json` — per-worktree by design; the live
  iteration state *should* be lane-local, only the durable counter should not be
- `iterations_since_retro` inside `state.json` — an init-time mirror for audit;
  its meaning is unchanged
- `scripts/openup-claims.py` — reused as a pattern, not refactored into a shared
  helper; a shared git-dir utility is a worthwhile follow-up but would widen
  this task's blast radius across the claims machinery
- `.gitignore` — the fix is to stop storing the counter in an ignored, per-
  worktree directory, not to start tracking that directory
- The increment site — that is T-142, shipping in the same PR as its own change
  folder

## Operations

- [x] Add `retro_dir()` (git-common-dir resolution with a non-git fallback to
      `REPO_ROOT/.openup`) and the `--retro-dir` argument; repoint
      `retro_path()` at it (`scripts/openup-state.py`)
- [x] Add the read-forward legacy fallback in `read_retro_count()` so an
      existing `<worktree>/.openup/retro.json` seeds the shared value once
- [x] Update the module docstring's `retro` subcommand line to name the new
      location
- [x] Document location, override precedence, and migration in
      `docs-eng-process/state-file.md`, and repoint the `.openup/retro.json`
      prose in `/openup-start-iteration` and `/openup-retrospective`
- [x] (tester) Tests in `scripts/tests/test_t011_retro.py`: shared path is used
      by default; a linked worktree reads/advances the same count; `--retro-dir`
      and `--state-dir` overrides win in that order; legacy value is carried
      forward once and not re-applied; a non-git checkout falls back without
      raising
- [x] Run the full test suite and `python3 scripts/check-docs.py`

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, pre-commit housekeeping
- `scripts/openup-state.py`'s own design rules (deterministic, stdlib-only,
  skills write through the CLI, `--state-dir` override for tests)
- `scripts/openup-claims.py`'s `claims_dir()` — the git-common-dir resolution
  pattern this mirrors

## Safeguards

- **Reversibility.** Revert of a single commit. The legacy file is never
  deleted, so a revert finds the old value intact (it will be stale by the
  number of increments taken since the move — acceptable, and self-corrects at
  the next `retro reset`).
- **No-go zones.** No test may write to the developer's real
  `<git-common-dir>/openup/` — every test must pass `--retro-dir` or
  `--state-dir`, or run inside a temp clone. `git` must never be invoked with a
  mutating subcommand from `retro_dir()`; `rev-parse` only.
- **Fail-open.** A missing/failing `git` must degrade to the legacy path, never
  raise — the counter is an advisory cadence gate, not a correctness gate.
- **Token / size budget.** ≤ 40 net lines in `scripts/openup-state.py`; no new
  dependencies (stdlib + `subprocess` to `git`, as `openup-claims.py` already
  does).

## Verification

- `python3 -m pytest scripts/tests/test_openup_state.py -q` passes, including
  the new worktree/migration tests
- Full suite: `python3 -m pytest scripts/tests tests -q`
- Manual: in a linked worktree, `python3 scripts/openup-state.py retro get`
  prints the same value as in the main worktree
- `python3 scripts/check-docs.py` passes
- Grade against `.claude/rubrics/task-spec-rubric.md` — all criteria ✅

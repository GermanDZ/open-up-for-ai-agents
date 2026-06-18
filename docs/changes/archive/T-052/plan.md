---
id: T-052
title: Framework syncs must not leave uncommitted changes that trip on-stop
status: done
priority: medium
estimate: 1 session
plan: ""
touches:
  - scripts/sync-from-framework.sh
  - tests/test-scripts.sh
  - docs-eng-process/updating.md
depends-on: []
blocks: []
last-synced: ""
---

# T-052 — Framework syncs must not leave uncommitted changes that trip on-stop

## Story

> **As an** agent running `/openup-next` in a repo that consumes the OpenUP framework
> **I want** a framework sync's own tooling upgrades to land already-committed (or be invisible to the stop guard)
> **So that** my lane can reach a normal stop instead of `on-stop.py` looping on changes I never made

INVEST check:
✅ Independent (only touches sync + on-stop) · ✅ Negotiable (two viable approaches) ·
✅ Valuable (kills a hook-loop that burns a whole turn) · ✅ Estimable (1 session) ·
✅ Small (≤2 files of logic) · ✅ Testable (simulate a sync, assert clean stop)

## Analysis Context

State the *why* the spec needs but the code can't show:
- **Domain.** Framework distribution + the stop guard. `scripts/sync-from-framework.sh`
  (and its helper `scripts/lib/install-process-clis.sh`) overwrite tracked process CLIs
  in a consumer repo on upgrade. `.claude/scripts/hooks/on-stop.py` blocks turn-end while
  the working tree has uncommitted changes, exempting only `docs/agent-logs/runs/`.
- **Scope boundaries.** Does NOT change *what* the sync installs, the manifest, or the
  `.bak` behavior (T-051 already fixed the untracked-debris half). Does NOT touch the
  write-fence or gate-edits. Only addresses **modified tracked files left uncommitted by a
  sync** carrying into the next lane session.
- **Definition of done.** After a framework sync overwrites tracked CLIs in a consumer
  repo, a subsequent `/openup-next` lane reaches `on-stop.py` and is allowed to stop
  without the hook blocking on the sync-introduced changes — and no real abandoned lane
  work is silently let through.

> **Assumption:** The primary fix is approach (1) — `sync-from-framework.sh` stages and
> commits its own CLI/template upgrades as a `chore(process)` commit so the tree is clean
> when the sync returns. Approach (2) (an on-stop exemption for synced paths) is treated as
> a fallback only, because a static path-exemption set drifts and risks masking genuinely
> abandoned work. *(Vetoable at review — if maintainers prefer on-stop staying authoritative
> and the sync staying side-effect-free, swap the primary.)*

## Requirements

1. A framework sync that modifies tracked files leaves the working tree clean with respect
   to those files (they are committed by the sync, not left as `M`).
   - **Given** a consumer repo on a clean trunk whose `scripts/openup-board.py` differs from
     the framework's current version, **When** the framework sync runs to completion,
     **Then** `git status --porcelain` reports no `M`/`??` entry for any file the sync wrote.
2. The sync's self-commit is attributable and uses the canonical commit format so
   `validate-commit.py` accepts it.
   - **Given** the sync committed its upgrades, **When** the resulting commit subject is
     read, **Then** it matches `type(scope): description` and carries `[openup-skip]` (no
     lane task owns a framework sync) so the commit-format hook passes.
3. The sync only commits files it actually wrote — it never sweeps unrelated user changes
   into its commit.
   - **Given** a consumer repo with an unrelated uncommitted edit in `src/app.py`, **When**
     the sync runs and commits its CLI upgrade, **Then** `src/app.py` remains uncommitted
     and is not part of the sync commit.
4. A subsequent `/openup-next` lane is not blocked by sync-introduced changes at stop.
   - **Given** a sync has just upgraded tracked CLIs, **When** an agent finishes a lane and
     `on-stop.py` runs, **Then** the hook exits 0 (allows stop) rather than reporting the
     sync's files as uncommitted.
5. Genuinely abandoned lane work still blocks stop (no regression of the guard's purpose).
   - **Given** an agent left an uncommitted edit to `scripts/openup-board.py` that was NOT
     produced by a sync, **When** `on-stop.py` runs, **Then** the hook still blocks (exit 2)
     and names that file.

## Behavior Delta

Internal process-tooling change; the governing description lives in the process docs, not a
`docs/product/` use case.

**Added** — behavior that did not exist before:
- `sync-from-framework.sh` makes a self-contained `chore(process)` commit of the files it
  upgrades when run inside a git repo with a clean-enough tree.

**Modified** — behavior that changes; cite the doc + section:
- Framework sync end-state: tree is left clean instead of dirty —
  `docs-eng-process/updating.md` (sync workflow).
- (If approach 2 is also adopted) `on-stop.py` dirty-check exemptions —
  `docs-eng-process/parallel-lanes.md` (write-fence / stop-guard section).

**Removed** — none.

## Entities

- **sync-from-framework.sh** (modified) — `scripts/sync-from-framework.sh`
- **install-process-clis.sh** (read-only / reference) — `scripts/lib/install-process-clis.sh`
- **on-stop.py** (modified, fallback only) — `.claude/scripts/hooks/on-stop.py` +
  its tracked source `docs-eng-process/.claude-templates/scripts/hooks/on-stop.py`
- **validate-commit.py** (read-only) — `.claude/scripts/hooks/validate-commit.py`
  (constrains the sync commit's subject format)

## Approach

Make the sync own its blast radius: after the installer copies upgraded CLIs/templates,
collect exactly the paths the sync wrote, and if any are dirty, stage *only those* and make
one `chore(process): sync OpenUP framework [openup-skip]` commit. This keeps the tree clean
on return, so the existing `on-stop.py` guard never sees sync changes — no new exemption
surface to drift. Only if maintainers reject a committing side-effect in the sync do we fall
back to teaching `on-stop.py` a synced-paths exemption (more fragile). Mirror any on-stop
edit into its `.claude-templates/` source per the dual-source rule.

## Structure

**Add:**
- (none expected; logic lands in existing scripts)

**Modify:**
- `scripts/sync-from-framework.sh` — after install, stage the written paths and commit them
  with the canonical `[openup-skip]` subject; guard on "inside a git repo" and "those paths
  are dirty"; never `git add -A`.

**Do not touch:**
- `scripts/lib/install-process-clis.sh` — T-051 already handles its `.bak` half; the
  commit concern belongs to the orchestrating sync script, not the per-file installer.
- `.claude/scripts/hooks/gate-edits.py`, the write-fence — unrelated guards.
- The process manifest / what gets installed — scope is *when it's committed*, not *what*.

## Operations

- [x] In `sync-from-framework.sh`, capture the set of repo-relative paths the installer
      actually wrote (board/claims/other CLIs + any templates), not a blanket `git status`.
- [x] After install, if the repo is a git work tree and any captured path is dirty, `git add`
      exactly those paths and commit with
      `chore(process): sync OpenUP framework to <version/sha> [openup-skip]`.
- [x] Guard the commit: skip cleanly (with a printed note) when not in a git repo, when
      nothing the sync wrote is dirty, or when a rebase/merge is in progress.
- [x] (tester) Simulate a sync in a scratch git repo: dirty a tracked CLI + an unrelated
      `src/app.py`, run the sync, assert the CLI is committed, `src/app.py` is untouched,
      and `on-stop.py` exits 0. *(Split into Test 15 (CLI committed + app.py untouched, R1–R3)
      and Test 16 (on-stop exit 0); see design.md — on-stop is whole-tree, so the exit-0
      assertion is checked once the unrelated edit is restored.)*
- [x] (tester) Regression: leave a non-sync edit to a tracked CLI, run `on-stop.py`, assert
      it still blocks (exit 2) and names the file. *(Test 17.)*
- [x] Update `docs-eng-process/updating.md` to state the sync now self-commits its upgrades.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, `[openup-skip]` usage.
- `.claude/CLAUDE.openup.md` — dual-source rule for hook edits (`.claude/` is a synced copy;
  the tracked source is under `docs-eng-process/.claude-templates/`), enforced by
  `check-claude-sync.sh`.
- `docs-eng-process/parallel-lanes.md` — write-fence / stop-guard model.

## Safeguards

- **Token / size budget.** Net new logic ≤ ~40 lines of shell; no new files.
- **Reversibility.** The sync's commit is an ordinary commit on the current branch — revert
  with `git revert` / `git reset`; no history rewrite.
- **No-go zones.** Never `git add -A` / `git add .` in the sync — only the explicitly
  captured written paths, so unrelated user work is never swept in (Requirement 3). The
  on-stop guard must keep blocking on non-sync abandoned changes (Requirement 5).
- **Dual-source.** If `on-stop.py` is touched (fallback), edit the
  `.claude-templates/` source and keep `.claude/` in sync (`check-claude-sync.sh`).

## Success Measures

We expect **on-stop override-cap loops attributable to sync-introduced changes** to move to
**zero occurrences** within **30 days** of release across the maintained consumer repos.
Instrumentation: grep `.claude/memory/bypass-log.md` and session transcripts for the
"hook blocked the turn from ending N consecutive times" override on a tree whose only dirty
files are framework-written paths. Read-back: **30 days after release**.

## Rollout

`n/a — internal developer tooling.` Not user-facing; reaches maintainers/agents via the
next `git pull` of the framework + their next `sync-from-framework.sh` run. No feature flag:
the change is a behavioral fix to a script with no runtime toggle to gate, and is trivially
reverted via git.

## Verification

- `bash -n scripts/sync-from-framework.sh` passes.
- The two tester Operations steps pass (clean stop after sync; still-blocks on real
  abandoned work; unrelated edits never swept into the sync commit).
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-052/plan.md` exits 0.
- Grade against `.claude/rubrics/task-spec-rubric.md` — all 13 criteria ✅.

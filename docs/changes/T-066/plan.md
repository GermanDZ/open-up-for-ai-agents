---
id: T-066
title: Promote-selector remote delivered-but-unmerged guard
status: ready   # proposed → ready → in-progress → done → verified
priority: high   # critical | high | medium | low
estimate: 1 session
plan: docs/roadmap.md#t-066-promote-selector-remote-delivered-but-unmerged-guard
depends-on: [T-064, T-065]
blocks: []
last-synced: ""
touches:
  - scripts/openup-roadmap.py
  - scripts/tests/test_openup_roadmap.py
  - .claude/skills/openup-next/SKILL.md
  - docs-eng-process/script-cli-reference.md
  - docs/changes/T-066/
---

# T-066 — Promote-selector remote delivered-but-unmerged guard

## Story

> **As an** agent running `/openup-next` on `main`
> **I want** the promote selector to skip a task that is already delivered in an open, unmerged PR on `origin`
> **So that** the loop never re-implements finished work whose only sin is not being merged yet.

INVEST check:
✅ Independent (small guard on an existing selector) · ✅ Negotiable · ✅ Valuable (a wasted re-implementation cycle avoided) · ✅ Estimable · ✅ Small · ✅ Testable (bare-remote fixture)

## Analysis Context

- **Domain.** The `/openup-next` promote step (§1c) — `openup-roadmap.py cmd_next`, which `openup-board.py resolve` (T-065) calls for its `promote` branch. This is the last selection gate before a roadmap task becomes a re-authored lane.
- **The bug this fixes (observed).** T-065 was fully delivered in PR #64 but the PR sat unmerged. `complete-task` had archived the change folder *on the branch*, released the lease, and pushed the branch. From `main`'s view: no active folder, no archived folder (it's on the unmerged branch), no live lease, roadmap still `pending` → `cmd_next` returned T-065 as promotable and the next cycle began re-authoring its spec. Every existing guard is **local**; a delivered-but-unmerged PR is a purely **remote** signal.
- **Scope boundaries.** Does NOT add PR-state querying via `gh` (branch-on-origin is a sufficient, cheaper signal and matches the T-044 mechanism). Does NOT change the local guards, dep logic, `list`, or `get`. Does NOT touch `openup-board.py` (it inherits the fix through `cmd_next`). Does NOT auto-merge anything.
- **Definition of done.** `cmd_next` skips a candidate when `origin` has a branch encoding its id, reusing `claims.remote_task_branches`; fail-open on any remote error; one `ls-remote` per invocation; `--no-remote-check` opt-out; the skip reason names the remote branch; tests cover present/absent/offline; reference updated.

> **Assumption:** a matching **remote branch** (via the T-044 token matcher) is sufficient evidence of delivered-but-unmerged — I do not additionally query PR open/closed state through `gh`. A branch left on origin after a *merged* PR would also match; that is acceptable because a merged PR also lands the archived folder / `completed` status on main, so `_effectively_completed` already filters it out *before* this guard runs. *(Vetoable at review.)*
> **Assumption:** the check is **on by default** and fail-open; `--no-remote-check` disables it for hermetic/offline callers. *(Vetoable at review.)*
> **Assumption:** no automatic `git fetch` — `ls-remote` alone (do_fetch=False), to keep the per-cycle cost to one lightweight round-trip. *(Vetoable at review.)*

## Requirements

1. `cmd_next` skips a promote candidate when `origin` has a branch encoding the task id, treating it as in-flight-elsewhere (does not return it as promotable).
   - **Given** roadmap task T-101 is `pending`, deps satisfied, no local folder/lease, and `origin` has branch `feat/T-101-x` **When** `openup-roadmap.py next` runs **Then** it does not return T-101; it returns the next promotable task (or exits 3 with a reason naming the remote branch).
2. The guard is fail-open: any remote error (no remote, unreachable, not a git repo) must not block promotion.
   - **Given** the repo has no `origin` (or origin is unreachable) **When** `next` runs **Then** it behaves exactly as before the guard (promotes the local candidate) — the guard never converts a reachable-promotable into a false skip on error.
3. The guard reuses the T-044 `claims.remote_task_branches` / `task_branch_match` mechanism (no re-implemented matcher) and runs at most one `ls-remote` per invocation (cached across candidates).
   - **Given** two promote candidates both need the remote check **When** `next` runs **Then** `ls-remote` is invoked at most once (result cached).
4. A `--no-remote-check` flag disables the guard entirely (for hermetic/offline callers).
   - **Given** `--no-remote-check` **When** `next` runs against a repo whose candidate has a matching remote branch **Then** the candidate IS returned (guard bypassed).
5. The exhaustion/skip reason distinguishes a remote-skip so a human sees "delivered elsewhere — merge PR", not a generic block.
   - **Given** the only promotable task is skipped solely because of a matching remote branch **When** `next` exits 3 **Then** stderr names the remote branch / instructs merging its PR.
6. `openup-board.py resolve`'s promote branch inherits the guard unchanged (it calls `cmd_next`); no separate edit to `openup-board.py`.
   - **Given** a candidate with a matching remote branch **When** `openup-board.py resolve` runs **Then** its `path` is not `promote` for that task.
7. `/openup-next` §1c prose and `script-cli-reference.md` note the remote-skip and the `--no-remote-check` flag.
   - **Given** the updated docs **When** a reader looks up the promote step / `openup-roadmap.py next` **Then** both the remote delivered-but-unmerged skip and the `--no-remote-check` opt-out are documented.

## Behavior Delta

Process tooling (the promote selector), not a Ring-1 product use case.

**Added:**
- A remote-branch guard in `cmd_next` + `--no-remote-check` flag.

**Modified:**
- `openup-roadmap.py next` selection — a candidate with a matching `origin` branch is now skipped as in-flight — `scripts/openup-roadmap.py` (`cmd_next`). Documented in `.claude/skills/openup-next/SKILL.md §1c` and `docs-eng-process/script-cli-reference.md`.

**Removed:**
- Nothing.

## Entities

- **`cmd_next`** (modified) — `scripts/openup-roadmap.py`
- **`claims.remote_task_branches` / `claims.task_branch_match`** (read-only, reused) — `scripts/openup-claims.py` (T-044)
- **`--no-remote-check` flag** (new) — `openup-roadmap.py next` argparse
- **`openup-board.py resolve`** (read-only, inherits) — `scripts/openup-board.py`

## Approach

In `cmd_next`, after a candidate clears the local in-flight and dep checks but *before* returning it, consult a memoized set of `origin` branch task-tokens (one `ls-remote` via `claims.remote_task_branches`, cached module-side for the invocation). If a branch encodes the candidate's id and there was no remote error, skip it as in-flight-elsewhere (record it for a remote-specific stderr reason); on any remote error, fail-open and promote as today. A `--no-remote-check` flag short-circuits the whole check. The guard sits alongside the existing `_active_folder`/lease skip, so `resolve` inherits it for free.

## Structure

**Add:**
- Remote-branch guard + `--no-remote-check` in `scripts/openup-roadmap.py` (`cmd_next` + its argparse)
- Tests in `scripts/tests/test_openup_roadmap.py` (bare-remote fixture: present → skip, absent → promote, offline/no-remote → fail-open, `--no-remote-check` → bypass)

**Modify:**
- `.claude/skills/openup-next/SKILL.md` — §1c note: delivered-but-unmerged is skipped remotely (one or two sentences; keep exits + sentinel unchanged)
- `docs-eng-process/script-cli-reference.md` — document the guard + `--no-remote-check`

**Do not touch:**
- `scripts/openup-board.py` — inherits via `cmd_next`; no edit needed
- `scripts/openup-claims.py` `remote_task_branches` — reused as-is, not modified
- The local `_active_folder` / lease / dep logic — unchanged

## Operations

- [ ] Implement the remote-branch guard in `openup-roadmap.py cmd_next`: memoized `claims.remote_task_branches(id, "origin", root, do_fetch=False)` consulted after local checks; skip candidate on a match with no error; fail-open on error; record a remote-skip reason. Add the `--no-remote-check` flag to the `next` subparser (default off = guard on).
- [ ] Emit a remote-specific stderr reason on exit 3 when the sole blocker was a matching remote branch (name the branch / instruct merging its PR).
- [ ] Update `.claude/skills/openup-next/SKILL.md` §1c to note the remote delivered-but-unmerged skip and the `--no-remote-check` opt-out; keep the two-exit contract + sentinel byte-unchanged. Sync the template copy if one exists.
- [ ] Update `docs-eng-process/script-cli-reference.md` with the guard + flag.
- [ ] (tester) Add path-coverage tests in `test_openup_roadmap.py` using a real bare `origin`: (a) matching branch → candidate skipped/next returned, (b) no matching branch → promoted, (c) no remote / unreachable → fail-open promote, (d) `--no-remote-check` → bypass. Confirm existing non-git-repo tests still pass (fail-open). Run the full suite green.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.)
- `docs-eng-process/script-cli-reference.md` — script CLI signature conventions
- Design rules in `scripts/openup-roadmap.py` module docstring — stdlib only, no model, reuse claims helpers

> Reference, don't copy.

## Safeguards

- **Fail-open is load-bearing.** Offline, no `origin`, unreachable remote, or non-git dir must never block promotion — the guard can only ever *skip on a positive match with no error*. This is the T-044 philosophy; the existing non-git-repo roadmap tests are the regression witness.
- **One round-trip per invocation.** `ls-remote` result is cached module-side; N candidates do not mean N network calls.
- **Read-only.** No fetch, no ref writes, no lease mutation — `do_fetch=False`, `ls-remote` only.
- **Contract-preserving.** `/openup-next` two-legal-exits + `OPENUP-NEXT:` sentinel unchanged; only §1c prose gains a note.
- **Reversibility.** Additive guard + flag; revert the commit to back out. `--no-remote-check` is the runtime escape hatch.
- **No matcher duplication.** Reuse `claims.task_branch_match` — do not write a second token regex.

## Verification

- `openup-roadmap.py next` against a bare-remote fixture with a matching branch → candidate skipped; without → promoted; offline → promoted (fail-open); `--no-remote-check` → bypass.
- `python3 -m unittest scripts.tests.test_openup_roadmap` green; full suite green (no regression in the existing non-git-repo tests).
- `openup-board.py resolve` on the matching-branch fixture → `path != promote` for that task (inheritance check).
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

## Success Measures

We expect **zero re-promotions of a delivered-but-unmerged task** going forward: instrumentation is the absence of a `promote`→re-author cycle for any task id that has an open PR, observable in `docs/agent-logs/runs/`. Concretely, replaying the T-065/PR-#64 scenario (roadmap `pending`, no local folder/lease, matching `origin` branch) must yield a **skip, not a promote**. Read-back: the next time a PR sits unmerged across a loop cycle (and the guard's own test asserts it now).

## Rollout

**Flagged?** No — internal process tooling. The `--no-remote-check` flag is a per-invocation opt-out, not a rollout gate; the guard is on by default and reversible by reverting the commit. `n/a — internal tooling, additive + revert-to-back-out; --no-remote-check is the escape hatch.`

---
id: T-060
title: "Parallel fan-out — stale-lease reaper + /openup-fan-out skill"
status: done
priority: high
estimate: 1–2 sessions
plan: docs/iteration-plans/t-060-parallel-fan-out.md
depends-on: [T-059]
blocks: []
last-synced: ""
touches:
  - scripts/openup-claims.py
  - scripts/openup-board.py
  - .claude/skills/openup-fan-out/SKILL.md
  - docs-eng-process/.claude-templates/skills/openup-fan-out/SKILL.md
  - .claude/skills/openup-start-iteration/SKILL.md
  - docs-eng-process/.claude-templates/skills/openup-start-iteration/SKILL.md
  - docs-eng-process/model-tiers.md
  - docs-eng-process/skills-guide.md
  - tests/test_board_topn.py
  - tests/test_claims_heartbeat_reap.py
---

# T-060 — Parallel fan-out — stale-lease reaper + /openup-fan-out skill

## Story

> **As a** practitioner with multiple READY collision-free lanes on the board
> **I want** to dispatch all pickable lanes concurrently as background subagents with a single command
> **So that** wall-clock delivery time compresses to `max(cycle_time)` instead of `sum(cycle_times)`, while my interactive session remains free for planning

INVEST check:
✅ Independent — depends only on T-059 (already done) and adds additive behavior
✅ Negotiable — one-shot vs polling heartbeat is deferred to v2; cap of 4 is vetoable
✅ Valuable — first real parallelism in the continue-loop; unlocks wide-board scenarios
✅ Estimable — 4 bounded changes (claims CLI, board CLI, start-iteration skill, new skill)
✅ Small — 1–2 sessions; no architectural rewrites
✅ Testable — hermetic unit tests for reap + top-n; integration test for 2-lane fan-out

## Analysis Context

- **Domain.** OpenUP's claim coordination system (`scripts/openup-claims.py`) + board derived view (`scripts/openup-board.py`) + the `/openup-start-iteration` skill. The lease is a single-clone mechanism: claims live in `<git-common-dir>/openup/claims/`. Fan-out across worktrees of one clone is therefore coordinated; cross-machine fan-out is out of scope (T-044's domain).
- **Scope boundaries.** Single-clone only. No cross-machine fan-out. No GUI/TUI for watching parallel progress. No automatic merge/rebase of parallel PRs (the write-fence keeps them conflict-free by design; integration ordering remains manual). Do NOT pass `isolation: "worktree"` to Agent for fan-out subagents — OpenUP's `/openup-start-iteration` manages worktrees; a harness-level worktree would either nest worktrees or split the `git-common-dir`, destroying claim coordination.
- **Definition of done.** `openup-claims.py heartbeat/reap` work correctly. `openup-board.py top-n` returns a collision-free partition. `/openup-fan-out` skill exists and passes its rubric. `/openup-start-iteration` stamps a heartbeat at claim time. A 2-lane fan-out integration scenario completes without claim conflicts.

**Assumption:** `reap` stale-after default is **1800 seconds** (30 min). A heartbeat stamped once at claim time means heartbeat age = cycle elapsed time; a tighter window would false-positive a live long-running cycle. *(Vetoable at review — prerequisite for tighter window is polling heartbeat in v2.)*

**Assumption:** Max fan-out cap is **4 lanes** per invocation. Reasonable for a single machine without overwhelming resources. *(Vetoable at review.)*

**Assumption:** v1 uses **one-shot heartbeat** — `/openup-start-iteration` stamps `last_heartbeat` once at claim time; no polling during execution. The 30-min stale window is the v1 safety net. Polling heartbeat (stamp every 60s) is a v2 improvement that would allow a tighter reap window but adds implementation complexity. *(Explicit risk; vetoable at review.)*

## Requirements

1. `openup-claims.py heartbeat --task-id T-NNN` reads the existing claim for T-NNN and atomically rewrites it with `last_heartbeat` set to the current ISO-8601 timestamp; exits 7 if the claim file does not exist.
   - **Given** a live claim exists for T-042 **When** `python3 scripts/openup-claims.py heartbeat --task-id T-042` runs **Then** the claim file now contains a `last_heartbeat` field and the command exits 0
   - **Given** no claim exists for T-099 **When** `python3 scripts/openup-claims.py heartbeat --task-id T-099` runs **Then** command exits 7 and the claims directory is unchanged

2. `openup-claims.py reap [--stale-after N] [--dry-run]` sweeps all claims in the claims directory; for each claim: if `last_heartbeat` is absent, skip it (legacy/interactive, never managed by a background agent); if `last_heartbeat` is present and its age exceeds `stale-after` seconds, delete the claim file (or print and skip with `--dry-run`). Exits 0 always (reap is advisory).
   - **Given** three claims — one with no heartbeat, one with a fresh heartbeat, one with a heartbeat older than stale-after **When** `python3 scripts/openup-claims.py reap --stale-after 300` runs **Then** only the stale-heartbeat claim is deleted; the no-heartbeat and fresh-heartbeat claims remain
   - **Given** a stale claim **When** `python3 scripts/openup-claims.py reap --dry-run` runs **Then** the claim is printed as "would reap" but not deleted, and exit code is 0

3. `openup-board.py top-n <N>` returns up to N mutually collision-free READY lanes from the board as a JSON array (same per-lane schema as `top`), in board priority order (greedy selection: each candidate is included if its `touches` don't prefix-overlap any already-selected lane's `touches`). Exits 0 with the array (possibly empty `[]`); exits 3 if the board has no READY lanes at all.
   - **Given** a board with 3 READY lanes where lanes 1 and 3 share a touches prefix but lane 2 is disjoint from both **When** `python3 scripts/openup-board.py top-n 4` runs **Then** the output is a JSON array containing lanes 1 and 2 (lane 3 excluded for collision with lane 1), exit 0
   - **Given** a board with no READY lanes **When** `python3 scripts/openup-board.py top-n 4` runs **Then** exit 3 with a human-readable reason on stderr

4. `/openup-start-iteration` stamps `last_heartbeat` on the claim immediately after the claim is written (via `python3 scripts/openup-claims.py heartbeat --task-id <task_id>`), opting every start-iteration-initiated claim into the heartbeat model.
   - **Given** a lane is started via `/openup-start-iteration task_id: T-NNN` **When** the claim is written **Then** `openup-claims.py list` shows a `last_heartbeat` field on that claim

5. A `/openup-fan-out` skill file exists at `.claude/skills/openup-fan-out/SKILL.md` (and its template mirror) implementing the process: reap stale claims (dry-run + confirm) → `top-n` for collision-free lanes → dispatch one background Agent per lane with `/openup-next task_id: <lane>` → collect `OPENUP-NEXT: ADVANCED/DONE` sentinels → present compact summary.
   - **Given** a board with 2 READY disjoint lanes **When** `/openup-fan-out` is invoked **Then** it dispatches 2 background subagents, each with `task_id:` forced, and the parent session receives a ≤6-bullet summary per lane when they complete

6. Running `/openup-fan-out` against 2 READY lanes with disjoint `touches` surfaces produces no claim-conflict errors and both lanes complete (reach `/openup-complete-task` or `/openup-create-handoff`).
   - **Given** 2 READY lanes with disjoint touches and no stale claims **When** `/openup-fan-out` dispatches both **Then** both subagents complete without `CLAIM_CONFLICT` errors and each emits a `OPENUP-NEXT: ADVANCED` or `DONE` sentinel

7. A claim with a stale `last_heartbeat` (age > stale-after) is removed by `reap` and its lane becomes READY (pickable) again.
   - **Given** a claim for T-NNN with `last_heartbeat` set to epoch (effectively infinitely stale) **When** `python3 scripts/openup-claims.py reap --stale-after 300` runs **Then** the claim file is deleted and `python3 scripts/openup-board.py top` returns T-NNN's lane (previously blocked by the stale claim)

## Behavior Delta

**Added** — behavior that did not exist before:
- `openup-claims.py heartbeat` subcommand — stamps `last_heartbeat` on a live claim
- `openup-claims.py reap` subcommand — sweeps claims with stale heartbeats (never touches claims without heartbeat)
- `openup-board.py top-n <N>` subcommand — returns collision-free lane partition of up to N lanes
- `/openup-fan-out` skill — dispatches one background subagent per collision-free READY lane

**Modified** — behavior that changes:
- `/openup-start-iteration` claim-write step: stamps `last_heartbeat` immediately after writing the claim — `.claude/skills/openup-start-iteration/SKILL.md §claim-step` (and its template mirror)

**Removed** — none

## Entities

- **`scripts/openup-claims.py`** (modified) — add `heartbeat` and `reap` subcommands
- **`scripts/openup-board.py`** (modified) — add `top-n <N>` subcommand
- **`.claude/skills/openup-fan-out/SKILL.md`** (new) — fan-out skill
- **`docs-eng-process/.claude-templates/skills/openup-fan-out/SKILL.md`** (new) — canonical template copy
- **`.claude/skills/openup-start-iteration/SKILL.md`** (modified) — heartbeat stamp step
- **`docs-eng-process/.claude-templates/skills/openup-start-iteration/SKILL.md`** (modified) — keep in sync with `.claude/` copy

## Approach

Extend the two existing CLIs (claims, board) with additive subcommands: `heartbeat`/`reap` on claims, `top-n` on board. Both extensions are backward-compatible — no existing subcommand behavior changes. Wire the heartbeat stamp into `/openup-start-iteration` as a one-liner after the existing claim step. Author the `/openup-fan-out` skill in both the canonical template tree and the synced `.claude/` tree. The skill's implementation delegates all coordination to the existing CLIs — it does not bypass the claim or board machinery.

## Structure

**Add:**
- `.claude/skills/openup-fan-out/SKILL.md`
- `docs-eng-process/.claude-templates/skills/openup-fan-out/SKILL.md`

**Modify:**
- `scripts/openup-claims.py` — `heartbeat` subcommand (stamp last_heartbeat atomically) + `reap` subcommand (sweep stale-heartbeat claims)
- `scripts/openup-board.py` — `top-n <N>` subcommand (greedy collision-free partition)
- `.claude/skills/openup-start-iteration/SKILL.md` — one-liner heartbeat stamp after claim write
- `docs-eng-process/.claude-templates/skills/openup-start-iteration/SKILL.md` — mirror the same one-liner

**Do not touch:**
- `scripts/openup-fence.py` — write-fence is unaffected by fan-out; lane surfaces are already enforced per-lane
- `scripts/openup-board.py refresh` and `top` — only the new `top-n` subcommand is added; existing subcommands are unchanged
- `scripts/openup-claims.py claim`, `release`, `preflight`, `list` — existing subcommands unchanged; the `reap` invariant (no-heartbeat = skip) preserves backward compatibility
- `docs/project-status.md` and `docs/roadmap.md` — derived views; updated by sync-status.py, never by hand

## Operations

- [x] Add `heartbeat` and `reap` subcommands to `scripts/openup-claims.py`; write unit tests in `tests/` (synthetic claim files: no-heartbeat skipped, fresh-heartbeat kept, stale-heartbeat reaped, `--dry-run` prints but doesn't delete)
- [x] Add `top-n <N>` subcommand to `scripts/openup-board.py`; write unit tests (greedy collision-free selection, stops at N, returns `[]` with exit 0 when board has READY lanes but all selected, exits 3 when no READY lanes)
- [x] Wire heartbeat stamp into `.claude/skills/openup-start-iteration/SKILL.md` (step after claim write: `python3 scripts/openup-claims.py heartbeat --task-id <task_id>`) and mirror to `docs-eng-process/.claude-templates/skills/openup-start-iteration/SKILL.md`
- [x] Create `/openup-fan-out` skill at `.claude/skills/openup-fan-out/SKILL.md` and `docs-eng-process/.claude-templates/skills/openup-fan-out/SKILL.md` per the design in the iteration plan
- [x] (tester) Run integration verification: 2-lane fan-out scenario (disjoint touches), assert no claim conflicts, both sentinels received; synthetic stale-claim scenario, assert `reap` clears it and lane is re-pickable; confirm `process-manifest.txt` is not missing entries for the new CLIs (they extend existing scripts, no new entries needed)

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, branch naming, etc.)
- `docs-eng-process/parallel-lanes.md` — the write-fence, claim coordination, and `git-common-dir` lease model that all claim-touching code must respect

## Safeguards

- **Backward compatibility invariant.** Claims with no `last_heartbeat` must never be touched by `reap` — this is the literal interlock that keeps interactive and legacy sessions safe when `reap` is run. Any implementation that reaps a claim without a heartbeat field breaks this invariant.
- **Claim atomicity.** `heartbeat` must rewrite the claim file atomically (same `write_claim_atomic` pattern as the existing `claim` subcommand). A partial write could corrupt the claim and wedge the lane.
- **No nested worktrees.** The `/openup-fan-out` skill must never pass `isolation: "worktree"` to the Agent tool. OpenUP's `/openup-start-iteration` is the sole worktree manager. See Analysis Context above.
- **Reap is advisory.** `reap` always exits 0 — it must not block or error on partial failures (e.g., a claim file that can't be deleted due to permissions). Print the error and move on.
- **Token budget.** The fan-out skill's parent-session duty (reap + top-n + dispatch + collect summaries) should stay under 10k tokens in the orchestrating session. Subagent transcripts are isolated; the parent receives only ≤6-bullet summaries per lane.
- **Reversibility.** All changes are additive to existing CLIs. Roll-back: remove the new subcommands and the heartbeat line in start-iteration. No data migration needed — existing claims without heartbeats are unaffected.

## Success Measures

We expect **fan-out wall-clock time for 2 disjoint READY lanes** to be ≤ `max(cycle_time_A, cycle_time_B) + 10% overhead`, demonstrating ≥30% reduction vs serial `cycle_time_A + cycle_time_B`. Instrumentation: run-log `started` and `completed` timestamps for each lane (already emitted by `openup-log-run`). Read-back: on the first real multi-lane run of `/openup-fan-out` against this repo's roadmap (within 2 iterations of release, or by 2026-07-05 at the latest).

## Rollout

n/a — internal tooling. All deliverables are additive CLI subcommands and a new skill; they are not user-facing in the product sense and carry no feature-flag surface. The skill is only invoked explicitly by the practitioner. `reap` is advisory (exit 0 always); `heartbeat` is a no-op if not called. No kill-switch is needed because the additions don't replace existing behavior — they layer on top of it.

## Verification

- `python3 scripts/openup-claims.py heartbeat --task-id <live-claim>` exits 0 and the claim file gains `last_heartbeat`
- `python3 scripts/openup-claims.py reap --dry-run` on a synthetic stale claim prints the claim and exits 0 without deleting
- `python3 scripts/openup-board.py top-n 4` on a 3-lane board with one collision returns 2 lanes as a JSON array
- `cat .claude/skills/openup-fan-out/SKILL.md` exists; same content at `docs-eng-process/.claude-templates/skills/openup-fan-out/SKILL.md`
- `grep "heartbeat" .claude/skills/openup-start-iteration/SKILL.md` shows the stamp step
- Integration trace: 2-lane fan-out completes both lanes, no `CLAIM_CONFLICT` in output, each subagent emits `OPENUP-NEXT: ADVANCED` or `DONE` sentinel
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-060/plan.md` exits 0

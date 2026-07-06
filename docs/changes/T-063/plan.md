---
id: T-063
title: "openup-session.py begin|end atomic claim lifecycle + reap wiring in the sequential loop"
status: ready
priority: high
estimate: 1–2 sessions
plan: docs/iteration-plans/t-063-openup-session-begin-end-reap.md
depends-on: []
blocks: []
last-synced: ""
touches:
  - scripts/openup-session.py
  - scripts/openup-board.py
  - scripts/tests/test_openup_session.py
  - .claude/skills/openup-start-iteration/
  - .claude/skills/openup-complete-task/
  - .claude/skills/openup-create-handoff/
  - docs-eng-process/.claude-templates/skills/openup-start-iteration/
  - docs-eng-process/.claude-templates/skills/openup-complete-task/
  - docs-eng-process/.claude-templates/skills/openup-create-handoff/
  - docs-eng-process/script-cli-reference.md
  - docs-eng-process/parallel-lanes.md
  - scripts/process-manifest.txt
  - docs/changes/T-063/
---

# T-063 — openup-session.py begin|end + reap wiring in the sequential loop

## Story

> **As a** practitioner running `/openup-next` from a shell loop or cron (unattended)
> **I want** the claim lifecycle to be atomic and stale leases to self-heal
> **So that** a crashed cycle recovers on its own instead of wedging its lane until I manually `release` — the difference between "autonomous" and "babysat".

INVEST check:
✅ Independent (composes over existing claims/state modules) · ✅ Negotiable (reap default is tunable) · ✅ Valuable (unattended loop survives crashes) · ✅ Estimable (one new script + one wiring point + skill slims) · ✅ Small (state+claim+log surface only; git stays in skills) · ✅ Testable (rollback + reap invariants are unit-checkable)

## Analysis Context

- **Domain.** The `/openup-next` sequential continue-loop's claim lifecycle — `scripts/openup-claims.py` (lease), `scripts/openup-state.py` (iteration state + log-event), and the skills that orchestrate them (`start-iteration`, `complete-task`, `create-handoff`).
- **Scope boundaries.** State + claim + log only. Git branch/worktree create/remove **stay in the skills**. No cross-machine/cross-clone coordination (T-044 remote-check already guards that; the lease is single-clone). No structured roadmap source (Option B, deferred). Not touching the T-064/T-065 scripts.
- **Definition of done.** `scripts/openup-session.py begin|end` exist and are composition-only over the existing modules; a partial `begin` failure leaves no half-acquired session; `openup-board.py refresh` reaps stale (heartbeat-gated) leases so a crashed lane returns to `ready` within one cycle; the three skills call the new verbs; reference + manifest updated; tests pass.

> **Assumption:** Reap-on-`begin` defaults to **dry-run + warn** (`--reap` opts into live deletion); the live reap that self-heals the loop lives in `openup-board.py refresh`. *(Vetoable at review.)*
> **Assumption:** `begin` does **not** create the git worktree — the skill creates branch+worktree first, then calls `begin` with their paths. *(Vetoable at review.)*
> **Assumption:** `openup-session.py` **imports** `openup_claims`/`openup_state` as modules (composition) rather than shelling out to them, to keep the lifecycle in one process for atomic rollback. *(Vetoable at review.)*

## Requirements

1. `scripts/openup-session.py begin` acquires claim + iteration state + a `session_begin` log record in a single invocation, composing the existing claim/state functions (no re-implemented claim/state logic).
   - **Given** a created worktree/branch and a `docs/changes/T-NNN/plan.md` with `touches`, **When** `openup-session.py begin --task-id T-NNN --session-id S --branch B --worktree W` runs on a collision-free lane, **Then** a claim file, a `.openup/state.json`, and a `session_begin` event all exist and the command prints compact JSON `{task, branch, worktree, claimed:true}`.

2. `begin` is atomic: any failure **after** the claim is written rolls the claim back, so no half-acquired session remains.
   - **Given** a lane where `state init` is forced to fail (injected), **When** `begin` runs, **Then** the exit code is non-zero AND no claim file remains for that task (the claim taken mid-`begin` is released).

3. `scripts/openup-session.py end` releases claim + archives iteration state + writes a `session_end` log record in one invocation; git worktree removal is **not** its responsibility.
   - **Given** an active session for T-NNN, **When** `end --task-id T-NNN --status done` runs, **Then** the claim file is gone, state is archived, a `session_end` event is recorded, and no worktree removal is attempted by the script.

4. `openup-board.py refresh` runs a live stale-lease reap before deriving lanes, so a crashed session's heartbeat-stale claim self-heals within one `/openup-next` cycle.
   - **Given** a claim whose `last_heartbeat` is older than the stale threshold, **When** `openup-board.py refresh` runs, **Then** that claim is reaped and its lane is reported `ready` (not `in-progress`).

5. The T-060 heartbeat-gated invariant is preserved: a claim with **no** `last_heartbeat` field is never reaped by either wiring point.
   - **Given** a claim with no heartbeat field, **When** `board.py refresh` (or `session begin`'s dry-run reap) runs, **Then** the claim is left untouched.

6. `/openup-start-iteration`, `/openup-complete-task`, and `/openup-create-handoff` call the new verbs instead of the multi-call acquire/release chains, in **both** the live `.claude/skills/` and the `docs-eng-process/.claude-templates/skills/` copies (sync parity).
   - **Given** the updated skills, **When** `scripts/tests/test_claude_sync` (or the sync check) runs, **Then** live and template skill copies are byte-identical and reference `openup-session.py`.

## Behavior Delta

This task changes **process tooling** (the `/openup-next` loop), not Ring-1 product behavior — the product here *is* the framework, but `docs/product/` carries no use-case for the claim lifecycle; the authority is the iteration plan.

**Added** — behavior that did not exist before:
- `openup-session.py begin|end` — an atomic claim lifecycle command.
- Self-healing stale leases in the *sequential* loop (previously only `/openup-fan-out` reaped).

**Modified** — behavior that changes:
- `/openup-start-iteration` acquire sequence — was remote-check + preflight + claim + heartbeat + state-init + log (6 calls); becomes one `begin`. Artifact: `.claude/skills/openup-start-iteration/SKILL.md` §6/§6b.
- `/openup-complete-task` release — was release + state-archive + log spread across §7b; becomes one `end`. Artifact: `.claude/skills/openup-complete-task/SKILL.md` §7b.
- `openup-board.py refresh` — now reaps before deriving (previously never reaped). Artifact: `scripts/openup-board.py`.

**Removed** — none (the separate preflight/heartbeat calls are folded into `begin`, not deleted from `openup-claims.py`; that CLI keeps its subcommands for direct use).

## Entities

- **openup-session.py** (new) — `scripts/openup-session.py`
- **openup-claims** (read-only import) — `scripts/openup-claims.py` (claim/release/preflight/remote-check/heartbeat/reap)
- **openup-state** (read-only import) — `scripts/openup-state.py` (init/archive/log-event)
- **openup-board** (modified) — `scripts/openup-board.py` (refresh reap wiring)
- **start-iteration / complete-task / create-handoff skills** (modified) — live + template copies

## Approach

Add a thin `scripts/openup-session.py` that **imports** the existing `openup_claims` and `openup_state` modules and sequences their functions inside one process, with a single try/rollback around the acquire path so a partial `begin` releases what it took. It owns only state+claim+log; git worktree ops stay in the skills. Wire the already-shipped T-060 `reap` (heartbeat-gated) into `openup-board.py refresh` as a live sweep, and into `session begin` as a dry-run warning. Then slim the three skills to call `begin`/`end`, keeping their git operations. The whole change is composition + wiring — no new claim/state semantics.

## Structure

**Add:**
- `scripts/openup-session.py` — `begin`/`end` subcommands (composition + rollback)
- `scripts/tests/test_openup_session.py` — rollback + reap-invariant + integration tests

**Modify:**
- `scripts/openup-board.py` — `refresh` runs live `reap` before deriving lanes
- `.claude/skills/openup-start-iteration/SKILL.md` (+ template copy) — acquire chain → one `begin`
- `.claude/skills/openup-complete-task/SKILL.md` (+ template copy) — §7b release → one `end`
- `.claude/skills/openup-create-handoff/SKILL.md` (+ template copy) — release via `end --status handoff`
- `docs-eng-process/script-cli-reference.md` — `openup-session.py` signatures
- `docs-eng-process/parallel-lanes.md` — board-refresh reap note
- `process-manifest.txt` — ship `scripts/openup-session.py`

**Do not touch:**
- `scripts/openup-claims.py` claim/state semantics — reused as-is; changing them re-scopes the task.
- `scripts/openup-roadmap.py` / `openup-board.py resolve` — those are T-064/T-065.
- Git worktree creation/removal in the skills — stays in the skills by design.

## Operations

- [x] Write `scripts/openup-session.py` with `begin` (reap-dry-run → remote-check → claim → heartbeat → state-init → log, with rollback-release on any post-claim failure) and `end` (release → state-archive → log); composition over imported `openup_claims`/`openup_state`, compact JSON output.
- [x] Wire live `reap` into `scripts/openup-board.py refresh` (heartbeat-gated) so stale leases self-heal; add the dry-run warn to `session begin`.
- [x] (tester) Write `scripts/tests/test_openup_session.py`: clean begin/end, injected post-claim failure → rollback (Req 2), stale-heartbeat reaped + no-heartbeat untouched (Req 4/5), board refresh flips `in-progress→ready`.
- [x] Slim `/openup-start-iteration` §6/§6b to a single `begin` call (live + template copies); keep git worktree creation.
- [x] Slim `/openup-complete-task` §7b to `end` (live + template copies); keep worktree removal in complete-task. (`/openup-create-handoff` is **not** changed — it has no teardown to slim; see design.md DD1.)
- [x] Update `docs-eng-process/script-cli-reference.md`, `docs-eng-process/parallel-lanes.md`, and `process-manifest.txt`; run the full test suite + `scripts/check-docs.py` green.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, process conventions
- `docs-eng-process/script-cli-reference.md` — CLI signature style for the new verbs
- `.claude/CLAUDE.openup.md` — sync-parity rule (live `.claude/` ↔ `.claude-templates/`), two-legal-exits, derived-views fence

## Safeguards

- **Composition-only.** `openup-session.py` must not duplicate claim/state write logic — it imports and calls the existing functions. Reviewer checks for zero copied write-claim code.
- **T-060 invariant.** Heartbeat-less claims are never reaped (regression test in the suite).
- **Reversibility.** New script + additive wiring; back out by reverting the branch. The skills' git operations are unchanged, so a revert leaves the loop working via the old chain.
- **No-go zones.** No change to claim/state *semantics*; no git worktree ops moved into the script; no cross-clone coordination.
- **Token/size budget.** `openup-session.py` ≤ ~200 lines (thin composition); if it grows past that it is re-implementing, not composing — stop.

## Rollout

`n/a — internal process tooling`. Not user-facing; `openup-session.py` is read at loop time by the skills. No feature flag: the skills either call the new verb or they don't (a flag adds no safety over a branch revert). Kill-switch = revert the branch; the pre-existing `openup-claims.py`/`openup-state.py` calls still work.

## Success Measures

We expect **tool-calls in the acquire phase of a promote cycle** to drop from ~6 to ~1, and **human `openup-claims.py release` interventions to unwedge the loop** to reach **0** over a two-week unattended window. Instrumentation: count acquire-phase `log-event` records per cycle in `docs/agent-logs/runs/`; count manual `release` invocations. Read-back: 2 weeks after release.

## Verification

- `python3 -m pytest scripts/tests/test_openup_session.py` — all green (rollback + reap invariants + integration).
- Full suite (`scripts/tests/`) stays green; `python3 scripts/check-docs.py` exits 0.
- Manual: seed a stale-heartbeat claim, run `openup-board.py refresh`, confirm the lane flips to `ready`; run a clean `begin`/`end` round-trip and confirm claim+state+log lifecycle.
- Grade the final spec against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅ or a clear gap call-out.

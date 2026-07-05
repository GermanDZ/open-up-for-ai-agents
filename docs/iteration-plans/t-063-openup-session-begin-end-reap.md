---
type: iteration-plan
id: T-063
status: draft
title: "Atomic claim lifecycle (openup-session.py begin|end) + reap wiring in the sequential loop"
traces-from: []
verified-by: []
---

# T-063: openup-session.py begin|end + reap wiring in the sequential loop

**Phase**: construction
**Status**: pending
**Goal**: Give the sequential `/openup-next` loop an atomic claim lifecycle (one process acquires state+claim+log, one releases them) and make it self-heal from a crashed session's stale lease within one cycle — the difference between "autonomous" and "babysat".
**Priority**: high

---

## Context

Seed: [explorations/2026-07-05-next-loop-efficiency.md](../explorations/2026-07-05-next-loop-efficiency.md) — complaint #3 (round-trips) and #4 (lock/release). The product-manager challenge pass in that exploration ranked this item **first to ship** (Complement 1): a stale lease silently halts the whole autonomous loop, which is the loop's entire promise.

Two concrete problems today:

1. **No atomic claim lifecycle.** Acquiring a lane is four separate Bash calls — `openup-claims.py remote-check` → `preflight` → `claim` → `heartbeat` — plus `openup-state.py init` and a `log-event`. A crash between `claim` and `state init` leaves a half-acquired session: a lease exists with no iteration state, so the board reports the lane `in-progress` but no session is working it. Release is spread across `complete-task` §7b. There is no single command that means "this session now owns this lane" or "this session is done with it".

2. **Stale leases never self-heal in the sequential loop.** T-060 added `openup-claims.py heartbeat` + `reap` (heartbeat-gated: only claims that ever stamped a heartbeat and then went stale are reaped; heartbeat-less claims are never reaped, preserving the T-009 D1 invariant for interactive sessions). But `reap` is wired **only** into `/openup-fan-out`. In the sequential loop a crashed `/openup-next` cycle leaks its claim permanently — the board reports `in-progress` forever and the lane's whole `touches` surface is blocked until a human runs `openup-claims.py release`.

### Scope boundary (from the challenge pass)

`openup-session.py` is **composition-only**: it imports and calls the existing `openup-claims.py` / `openup-state.py` functions in one process. It is **not** a second implementation of the start-iteration/complete-task lifecycle and must never drift into one. Git operations (branch + worktree create/remove) **stay in the skills** (`/openup-start-iteration`, `/openup-complete-task`); the script owns only **state + claim + log** — the smallest surface that removes the round-trips and gives crash-atomicity. This boundary is load-bearing: widening it re-creates the drift risk Option A called out.

---

## Current State

### Claim acquisition is a 4-call chain (`.claude/skills/openup-start-iteration/SKILL.md`)

`/openup-start-iteration` runs, in sequence: `remote-check` (T-044 cross-machine early-warning) → `preflight` (collision/dependency check) → `claim` (writes the lease) → `heartbeat` (stamps `last_heartbeat`), then `openup-state.py init`, then a `log-event`. Each is its own Bash round-trip; `claim` already runs `preflight` internally, yet the skill calls `preflight` separately, and a board-`ready` lane is guaranteed to pass preflight by construction (agreement-by-construction) — so preflight is effectively computed three times for one claim.

### `reap` exists but is unwired for the sequential loop (`scripts/openup-claims.py`)

```
$ python3 scripts/openup-claims.py reap -h
usage: openup-claims.py reap [-h] [--stale-after SECONDS] [--dry-run] [--claims-dir CLAIMS_DIR]
  --stale-after SECONDS   Reap claims whose last_heartbeat age exceeds this many seconds (default: 1800 = 30 min).
  --dry-run               Print what would be reaped without deleting anything.
```

`reap` is invoked by `/openup-fan-out` before it dispatches subagents. `/openup-next` and `scripts/openup-board.py` never call it. `heartbeat` (`--task-id`) exists but nothing in the sequential loop stamps it after the initial claim.

### Release is spread across complete-task (`.claude/skills/openup-complete-task/SKILL.md` §7b)

`openup-claims.py release --task-id` + `openup-state.py` archive + a `log-event` are separate steps late in complete-task. There is no `session end` verb pairing them atomically with the acquire side.

---

## Proposed Design

### Change 1: `scripts/openup-session.py` — atomic begin/end

**New file**: `scripts/openup-session.py`. Two subcommands, both pure composition of existing modules (import `openup_claims` / `openup_state` functions; do **not** shell out and do **not** re-implement their logic).

- `begin --task-id T --session-id S --branch B --worktree W [--touches …] [--reap|--no-reap]`
  Runs, in one process, with a single rollback path: (a) optional stale-lease reap (see Change 2), (b) `remote-check` (advisory, fail-open — never blocks offline), (c) `claim` (which itself runs preflight — the separate preflight call is dropped), (d) `heartbeat` stamp, (e) `state init`, (f) one `session_begin` `log-event`. If any step after the claim fails, it releases the claim it just took so no half-acquired session is left behind. Prints the same compact JSON the skill needs (`{task, branch, worktree, track, claimed}`) so `start-iteration` consumes one call instead of six.

- `end --task-id T [--status done|handoff]`
  Runs `release` + `state` archive + one `session_end` `log-event` atomically. Git worktree removal stays in `/openup-complete-task`.

**Git stays in the skill.** `begin` never creates the branch/worktree; the skill creates them first, then calls `begin` with their paths. This keeps the script's surface at state+claim+log.

### Change 2: wire `reap` into the sequential loop

Two wiring points, both preserving the T-060 heartbeat-gated invariant (heartbeat-less claims are never reaped):

- **`openup-session.py begin`** runs `reap --dry-run` by default and **warns** (prints reaped candidates to stderr) rather than auto-deleting — auto-reap inside `begin` would change its blast radius (Open Question in the exploration; default resolved to dry-run+warn for safety, `--reap` opts into live reaping).
- **`scripts/openup-board.py refresh`** runs a live `reap` before deriving lane state, so a stale `in-progress` lane self-heals to `ready` within one board refresh — i.e. within one `/openup-next` cycle — without a human `release`. This is the "self-heals within one cycle" acceptance criterion.

### Change 3: slim the skills to call the new verbs

- `/openup-start-iteration`: replace the remote-check/preflight/claim/heartbeat/state-init/log-event sequence (after it creates the branch+worktree) with a single `openup-session.py begin` call.
- `/openup-complete-task` §7b and `/openup-create-handoff`: replace release+archive+log with a single `openup-session.py end --status …` call (worktree removal stays in the skill).
- Update `docs-eng-process/script-cli-reference.md` with the new `openup-session.py` signatures (avoid `--help` round-trips) and note the board-refresh reap wiring in `docs-eng-process/parallel-lanes.md`.

---

## Acceptance Criteria

- [ ] `scripts/openup-session.py begin` acquires claim+state+log in one invocation and, on any post-claim failure, releases the claim (no half-acquired session remains — verified by an injected-failure test).
- [ ] `scripts/openup-session.py end` releases claim+state+log in one invocation.
- [ ] `openup-session.py` is composition-only: it imports `openup_claims`/`openup_state` and adds **no** new claim/state logic (verified by review + no duplicated write-claim code).
- [ ] A crashed session's stale lease (heartbeat older than `--stale-after`) is reaped by `openup-board.py refresh`, so the lane returns to `ready` within one `/openup-next` cycle with no human `release`.
- [ ] Heartbeat-less claims are **never** reaped (T-060 invariant held — regression test).
- [ ] `/openup-start-iteration` and `/openup-complete-task` call the new verbs; the removed round-trips no longer appear in the skills.
- [ ] `docs-eng-process/script-cli-reference.md` documents the new signatures.

---

## Success Measure

We expect **tool-calls-per-promote-cycle** in the claim/acquire phase to drop from ~6 to ~1, and **stale-lease human interventions** (`openup-claims.py release` run by a human to unwedge the loop) to reach **0** over a two-week unattended-loop window. Instrumentation: count acquire-phase `log-event` records per cycle in `docs/agent-logs/runs/`; count manual `release` invocations in shell history / run logs. Read-back: 2 weeks after release.

---

## Testing Strategy

- **Unit (composition)**: `begin` calls the real claims/state functions; assert the claim file, state file, and log record all exist after a clean `begin`, and that an injected failure after `claim` leaves **none** of them (rollback).
- **Reap invariant**: a claim with a stale `last_heartbeat` is reaped; a claim with **no** heartbeat field is left untouched.
- **Board self-heal**: seed a stale claim, run `openup-board.py refresh`, assert the lane flips `in-progress → ready`.
- **Skill integration**: `/openup-start-iteration` end-to-end still produces a working lease+state+worktree via the single `begin` call.

---

## Dependencies

- T-060 (`openup-claims.py heartbeat` + `reap`) — completed. This task wires the existing reaper into the sequential loop and adds the atomic lifecycle on top.

---

## Key Files

| File | Change |
|------|--------|
| `scripts/openup-session.py` | **New** — `begin`/`end` atomic lifecycle, composition of claims+state+log |
| `scripts/openup-board.py` | `refresh` runs live `reap` before deriving lanes |
| `.claude/skills/openup-start-iteration/SKILL.md` | Collapse acquire chain into one `begin` call |
| `.claude/skills/openup-complete-task/SKILL.md` | Collapse §7b release into one `end` call |
| `.claude/skills/openup-create-handoff/SKILL.md` | Release via `end --status handoff` |
| `docs-eng-process/script-cli-reference.md` | Document `openup-session.py` |
| `docs-eng-process/parallel-lanes.md` | Note board-refresh reap wiring |
| `process-manifest.txt` | Ship `scripts/openup-session.py` |

---

## Out of Scope

- Cross-machine / cross-clone claim coordination (T-044 remote-check already guards that; the lease is single-clone).
- Structured roadmap source (Option B — deferred; belongs to no task yet).
- Merging git worktree operations into the script (explicitly kept in the skills).

---

## Open Questions

1. Reap-on-begin default — resolved to **dry-run + warn** (`--reap` opts into live reaping) to avoid changing `begin`'s blast radius; the live reap lives in `board.py refresh`. Vetoable at review.
2. Does `begin` subsume `start-iteration`'s worktree creation? **Assumed: no** — skill keeps git, script owns state+claim+log (smallest surface). Vetoable at review.

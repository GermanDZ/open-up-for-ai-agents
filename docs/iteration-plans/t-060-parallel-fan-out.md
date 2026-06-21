---
type: iteration-plan
id: T-060
status: implemented
title: "Parallel fan-out — stale-lease reaper + /openup-fan-out skill"
traces-from: []
verified-by: []
---

# T-060: Parallel Fan-Out (/openup-fan-out)

**Phase**: construction
**Status**: pending
**Goal**: Let multiple collision-free OpenUP lanes run concurrently as background subagents — one per READY lane — while the user's interactive session remains free for planning, with a stale-lease reaper preventing crashed subagents from wedging lanes permanently.
**Priority**: high

---

## Context

`/openup-next` runs one cycle per invocation. The board often has multiple READY, collision-free lanes simultaneously — tasks touching disjoint surfaces. Today they run serially even though the lease machinery already coordinates them: the `git-common-dir` claim files prevent two lanes from overlapping, the write-fence enforces surface boundaries, and sharded status-notes (class 1) mean completions never conflict in the shared views.

The missing pieces are:
1. **A stale-lease reaper.** Claims never expire by design (T-009 D1 — "every present claim counts regardless of age"). This is correct for interactive sessions where a human notices a crash. For background subagents it means a crashed cycle leaks its claim permanently, wedging that lane with no recovery path until manual `openup-claims.py release`. A heartbeat + reaper closes this: a live subagent stamps a heartbeat; a reaper sweeps claims whose heartbeat has gone stale.
2. **A fan-out dispatcher.** The parent session reads the board, partitions collision-free READY lanes, and dispatches one background subagent per lane — each forced to its `task_id:` so they never race the board themselves. The parent's context stays at ≤6-bullet summaries; subagent transcripts are isolated.

**Dependency:** T-059 (sentinel output) must land first — the fan-out driver uses `OPENUP-NEXT: ADVANCED/DONE` to identify what each subagent completed.

### Key architectural constraint (from parallel-lanes.md)

The lease is a **single-clone mechanism**. Claims live in `<git-common-dir>/openup/claims/` — the same directory for every linked worktree of one clone. Fan-out across worktrees of one clone is therefore coordinated; fan-out across separate clones on separate machines is not (T-044's remote-check guards that). This task covers the single-clone case.

**Critical: do NOT pass `isolation: "worktree"` to the Agent tool for fan-out subagents.** OpenUP's `/openup-start-iteration` creates the branch + worktree + lease. A harness-level worktree would either nest worktrees or split the `git-common-dir` — in either case, the leases stop coordinating and collision is only caught at PR time (the cross-machine failure mode). Fan-out subagents run in the main clone and let `start-iteration` manage their worktrees.

---

## Current State

### Claims — no heartbeat, no reaper (`scripts/openup-claims.py`)

The claim file payload (written at `claim` time):

```python
# scripts/openup-claims.py:write_claim_atomic (~line 405)
payload = {
    "task_id": task_id,
    "session_id": session_id,
    "touches": touches,
    "claimed_at": claimed_at,
    # No heartbeat field. No PID.
}
write_claim_atomic(fp, payload)
```

There is no `last_heartbeat`, no `pid`, and no `reap` subcommand.

### Claims — no expiry by design (`scripts/openup-claims.py:11`)

```python
# Claims NEVER expire (T-009 design D1): every present claim counts in the
# live collision set regardless of age and blocks an overlapping claim until
# manually released or completed via legal exit.
```

This is the correct invariant for interactive sessions; it must be extended, not replaced, for background agents.

### Board — top pickable lane (`scripts/openup-board.py`)

`python3 scripts/openup-board.py top` prints the single top READY lane as JSON. There is no `top-n` or collision-partitioned multi-lane output.

### `/openup-next` — forced task_id

The skill already supports `task_id:` to force a specific lane:
```
/openup-next task_id: T-NNN
```
This is the correct injection point for fan-out subagents.

### No `/openup-fan-out` skill

No such skill exists.

---

## Proposed Design

### Change 1: Heartbeat + reaper in `openup-claims.py`

**File**: `scripts/openup-claims.py`

Add a `heartbeat` subcommand (stamps `last_heartbeat` in the claim file) and a `reap` subcommand (sweeps claims whose heartbeat is stale):

```python
# New: heartbeat subcommand
# Usage: python3 scripts/openup-claims.py heartbeat --task-id T-NNN
# Reads the existing claim, updates last_heartbeat to now (ISO-8601), rewrites atomically.
# Exit 0 on success, exit 7 if claim not found (already released).

# New: reap subcommand
# Usage: python3 scripts/openup-claims.py reap [--stale-after 300] [--dry-run]
# Sweeps all claims in the claims dir. For each:
#   - If last_heartbeat is absent → skip (legacy claim, never managed by a background agent).
#   - If last_heartbeat is present and age > stale-after seconds → print the claim + reason,
#     delete the claim file (equivalent to release).
# Exit 0 always (reap is advisory, never blocks).
# --dry-run: print what would be reaped, delete nothing.
# Default stale-after: 1800 seconds (30 minutes — safe floor for full-track cycles;
# see Open Question 1 for the rationale).
```

**Invariant preserved:** claims with no `last_heartbeat` are legacy/interactive claims and are never reaped. The new invariant is: a claim written by a background agent MUST have a `last_heartbeat` stamped at least once before the heartbeat timeout; `reap` only touches claims that opted in to the heartbeat model.

### Change 2: `openup-board.py top-n` subcommand

**File**: `scripts/openup-board.py`

Add a `top-n <N>` subcommand that returns up to N collision-free READY lanes from the board — no two of which have overlapping `touches`:

```python
# Usage: python3 scripts/openup-board.py top-n 4
# Output: JSON array of lane objects (same schema as `top`), mutually collision-free.
# Each lane is the next pickable after excluding all lanes whose touches overlap any
# already-selected lane. Selection is greedy in board order (product-manager's priority order).
# Exit 0 with array (possibly empty); exit 3 if board has no READY lanes.
```

Collision-freeness check: two lanes collide if any element of `lane_a.touches` is a
prefix-match for any element of `lane_b.touches` (same logic as `openup-claims.py preflight`).

### Change 3: `/openup-fan-out` skill

**New file**: `.claude/skills/openup-fan-out/SKILL.md`

```markdown
---
name: openup-fan-out
description: Dispatch one background subagent per collision-free READY lane, then collect
  their ≤6-bullet summaries. The caller's session stays free. Requires T-059 sentinel and
  T-060 reaper.
model: inherit
---

# Fan-Out

Runs multiple `/openup-next` cycles concurrently — one background subagent per collision-free
READY lane — while your session remains free to plan or ask questions.

## When to Use

- The board has ≥2 READY lanes with disjoint surfaces and you want them to run in parallel.
- You want background progress without tying up your interactive session.

## When NOT to Use

- Only one READY lane exists (use `/openup-next` directly).
- Lanes share surfaces — fan-out would just serialize them anyway (the board handles this).
- You want to watch step-by-step progress in your session (use `/openup-next` interactively).

## Process

### 1. Reap stale claims (prerequisite safety check)

```bash
python3 scripts/openup-claims.py reap --dry-run
```

Print what would be reaped and confirm with the user before proceeding if any stale claims
are found. Run without `--dry-run` after confirmation.

### 2. Refresh the board and select collision-free lanes

```bash
python3 scripts/openup-board.py top-n 4
```

Take at most 4 lanes (or the `max_lanes:` argument if provided). Record the list — this is
the partition; subagents are assigned their lane before any of them start, so no board-race
is possible.

If the board returns empty (exit 3), stop and report: "No READY lanes — nothing to fan out."

### 3. Dispatch one background subagent per lane

For each lane in the partition:

- Start a background Agent (run_in_background: true) with prompt:
  `/openup-next task_id: <lane.task>`
- The subagent works its full cycle (start-iteration if needed, execute, complete-task or
  create-handoff) and exits.
- Do NOT pass `isolation: "worktree"` — OpenUP manages worktrees; harness worktrees would
  break claim coordination.

### 4. Heartbeat (while subagents run)

Each subagent's `/openup-start-iteration` stamps `last_heartbeat` at claim time (Change 1).
If a subagent crashes mid-run, `reap` will clear its claim after the stale window.

### 5. Collect summaries

As each background subagent completes, collect its returned text. Each should end with a
`OPENUP-NEXT: ADVANCED — <task>` or `OPENUP-NEXT: DONE — <reason>` sentinel.

### 6. Present compact summary

Output:
- How many lanes were dispatched, which task IDs.
- Per-lane: sentinel received (ADVANCED/DONE), legal exit taken, top-level result.
- Any lanes that returned no sentinel (crash — remind user to run `openup-claims.py reap`).
```

### Change 4: Wire heartbeat into `/openup-start-iteration`

**File**: `.claude/skills/openup-start-iteration/SKILL.md`

After the claim is written (step 6), add:

```bash
python3 scripts/openup-claims.py heartbeat --task-id <task_id>
```

This opts the claim into the heartbeat model. Absent this stamp, `reap` ignores the claim (legacy/interactive safe).

---

## Acceptance Criteria

- [ ] `openup-claims.py heartbeat --task-id T-NNN` updates `last_heartbeat` on an existing claim atomically; exits 7 if the claim doesn't exist.
- [ ] `openup-claims.py reap --dry-run` prints stale claims (heartbeat age > stale-after) without deleting; `reap` (no flag) deletes them; claims with no `last_heartbeat` are never touched.
- [ ] `openup-board.py top-n N` returns up to N mutually collision-free READY lanes in board order as a JSON array; exits 3 with empty board.
- [ ] `/openup-fan-out` SKILL.md exists, passes the iteration-plan rubric on completeness.
- [ ] `/openup-start-iteration` stamps `last_heartbeat` at claim time (opts into heartbeat model).
- [ ] A fan-out of 2 lanes with disjoint surfaces completes without claim conflicts (integration test or trace).
- [ ] A simulated crash (manual `kill` of a subagent mid-run) leaves a stale claim that `reap` clears after the stale window; the lane is re-pickable afterward.
- [ ] `.claude-templates/` synced to `.claude/` (fan-out skill lands in templates).

---

## Success Measure

Two disjoint READY lanes dispatched in parallel complete in approximately `max(cycle_time_A, cycle_time_B)` wall-clock time instead of `cycle_time_A + cycle_time_B`. The fan-out demonstrates ≥30% wall-clock reduction on a 2-lane scenario vs serial execution.

Instrumentation: run-log timestamps on start and complete-task for each lane. Read-back: on the first real use of `/openup-fan-out` against this repo's roadmap.

---

## Testing Strategy

- **Unit (hermetic):** `reap` subcommand — test with synthetic claim files: no heartbeat (ignored), fresh heartbeat (kept), stale heartbeat (reaped), `--dry-run` (no deletion).
- **Unit (hermetic):** `top-n` — test with synthetic board: picks collision-free subset in priority order, stops at N, returns empty array on exit-3 board.
- **Integration:** 2-lane fan-out against a test roadmap; assert both complete, no claim conflicts, each sentinel received.
- **Crash recovery:** synthetic stale claim (heartbeat set to epoch); assert `reap` removes it and the lane becomes pickable.

---

## Dependencies

- **T-059** (sentinel output for `/openup-next`) — required. The fan-out driver uses `OPENUP-NEXT: ADVANCED/DONE` to classify each subagent's exit. T-059 must be merged before T-060 is started.

---

## Key Files

| File | Change |
|------|--------|
| `scripts/openup-claims.py` | Add `heartbeat` and `reap` subcommands |
| `scripts/openup-board.py` | Add `top-n <N>` subcommand |
| `.claude/skills/openup-fan-out/SKILL.md` | New skill |
| `.claude-templates/skills/openup-fan-out/SKILL.md` | New skill (templates canonical) |
| `.claude/skills/openup-start-iteration/SKILL.md` | Stamp heartbeat after claim |
| `.claude-templates/skills/openup-start-iteration/SKILL.md` | Keep in sync |
| `scripts/process-manifest.txt` | No new scripts; existing CLIs extended |

---

## Out of Scope

- Cross-machine fan-out (T-044 handles remote coordination; this task is single-clone only).
- Automatic merge/rebase of parallel PRs (human step; conflict-free by design via write-fence but integration ordering remains manual).
- A GUI or TUI for watching parallel progress (out of scope for this iteration).

---

## Open Questions

1. **Assumed: stale-after default is 1800 seconds (30 min).** ⚠️ Self-critique catch: a heartbeat stamped once at claim time (Open Question 3) means the heartbeat age equals the cycle's elapsed time. A 5-min stale window would reap a *live* 8-minute full-track cycle — a false positive that causes a live claim to be deleted mid-run, making the lane re-pickable and triggering a collision. 30 min is the conservative safe floor for full-track cycles. Standard/quick cycles finish well within this window. Vetoable at review; if a tighter window is wanted, polling heartbeat (Open Question 3, option b) is the prerequisite.
2. **Assumed: max fan-out cap is 4 lanes** (passed to `top-n`). Reasonable for a laptop without overwhelming CPU/memory. Vetoable at review.
3. **[Risk: one-shot heartbeat vs. polling.] `/openup-start-iteration` stamps the heartbeat once at claim time.** This is simple but has a real failure mode: `reap` can only distinguish "crashed before claiming" from "crashed after claiming" — it cannot distinguish "crashed after claiming" from "running a long cycle." The 30-min stale-after (Open Question 1) is the v1 mitigation. A polling heartbeat (subagent stamps every 60s during execution) eliminates the false-positive entirely but adds implementation complexity. This is an explicit risk to carry into implementation; the architect review should decide v1 vs. v2 approach before coding starts.

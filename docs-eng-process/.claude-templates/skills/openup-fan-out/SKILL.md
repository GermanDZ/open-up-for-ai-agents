---
name: openup-fan-out
description: Dispatch one background subagent per collision-free READY lane, then collect their ≤6-bullet summaries. The caller's interactive session remains free. Requires T-060 heartbeat+reaper and T-059 sentinel output.
model: inherit
fit: use when the board has ≥2 READY lanes with disjoint surfaces and you want them to run concurrently. Do NOT use for a single READY lane (use /openup-next) or for lanes that share surfaces (fan-out would serialize them anyway).
---

# Fan-Out (`/openup-fan-out`)

Runs multiple `/openup-next` cycles concurrently — one background subagent per
collision-free READY lane — while your interactive session stays free to plan or
answer questions. Each subagent works its full cycle (start-iteration → execute
→ complete-task or create-handoff) and emits a sentinel when done.

**Prerequisite:** T-059 sentinel output must be merged (the fan-out driver
relies on `OPENUP-NEXT: ADVANCED — <task>` / `OPENUP-NEXT: DONE — <reason>`
to classify each subagent's exit). T-060 heartbeat+reaper must also be merged
(claims need `last_heartbeat` for crash recovery).

## When to Use

- Board has ≥2 READY lanes with disjoint `touches` surfaces.
- You want background parallelism without tying up your interactive session.
- You want wall-clock time ≈ `max(cycle_time)` rather than `sum(cycle_times)`.

## When NOT to Use

- Only one READY lane exists → use `/openup-next` directly.
- Lanes share surfaces → the board already serializes them; fan-out cannot help.
- You want step-by-step visibility in your session → use `/openup-next` interactively.
- You need to watch each step for a correctness review → fan-out transcripts are isolated.

## Arguments (optional)

- `max_lanes: N` — cap the fan-out at N lanes per invocation (default: 4).

## Process

### 1. Reap stale claims (prerequisite safety check)

Run the reaper in dry-run mode first to see what would be cleared:

```bash
python3 scripts/openup-claims.py reap --dry-run
```

- **Nothing to reap** → proceed to step 2.
- **Stale claims found** → show the output to the user and confirm before proceeding.
  After confirmation, run without `--dry-run`:
  ```bash
  python3 scripts/openup-claims.py reap
  ```
  This frees any lane that was wedged by a crashed prior subagent. Reap is advisory
  (always exits 0) — a reap failure prints a warning but does not block fan-out.

### 2. Refresh the board and select collision-free lanes

```bash
python3 scripts/openup-board.py top-n <max_lanes>
```

- **Exit 0** → you receive a JSON array of up to `max_lanes` mutually
  collision-free READY lanes. Record the list — this is the **partition**; lanes
  are assigned before any subagent starts so no board-race is possible.
- **Exit 3** → board has no READY lanes at all. Stop and report:
  "No READY lanes — nothing to fan out. Run `/openup-next` to promote the next
  roadmap task, or wait for blocked lanes to unblock."
- **Empty array (`[]`)** with exit 0 → all READY lanes are collision-excluded
  (this cannot happen with a well-formed board; if it does, run `openup-board.py
  refresh` to diagnose).

### 3. Dispatch one background subagent per lane

For each lane in the partition, start a background Agent:

- **Prompt:** `/openup-next task_id: <lane.task>`
- **run_in_background:** `true`
- **DO NOT pass `isolation: "worktree"`** — OpenUP's `/openup-start-iteration`
  manages worktrees; harness-level worktrees would either nest worktrees or split
  the `git-common-dir`, destroying claim coordination. This is a hard constraint
  (T-060 design safeguard, not a style preference).

The subagent runs its full cycle autonomously: it starts an iteration (or resumes
one), executes the Operations steps, and exits via `/openup-complete-task` or
`/openup-create-handoff`.

### 4. Heartbeat while subagents run

Each subagent's `/openup-start-iteration` stamps `last_heartbeat` on its claim
immediately after writing it (T-060 Change 4). If a subagent crashes before
completing, the stale `last_heartbeat` allows `reap` (step 1 of the next fan-out
invocation) to free the wedged claim automatically.

### 5. Collect summaries as subagents complete

As each background subagent returns, collect its output text. Each should end
with one of:
- `OPENUP-NEXT: ADVANCED — <task>` — the cycle advanced and exited normally.
- `OPENUP-NEXT: DONE — <reason>` — no more work for this task.

**If a subagent returns no sentinel** (crash or forced stop), log it as:
`CRASH — no sentinel received for <task>. Run: python3 scripts/openup-claims.py reap`

### 6. Present compact summary (≤6 bullets per lane)

Output one section per dispatched lane:

```
## Fan-Out Summary

Dispatched: <N> lanes — T-NNN, T-MMM, ...

**T-NNN** — ADVANCED (legal exit: complete-task)
  - Implemented X, added tests for Y, committed Z
  - Worktree removed, claim released

**T-MMM** — ADVANCED (legal exit: create-handoff)
  - Completed steps 1–3; paused at step 4 (see handoff doc)
  - Claim held; resume with /openup-next task_id: T-MMM

**Summary:** <N> dispatched, <N1> advanced, <N2> crashed (run reap)
```

## Success Criteria

- [ ] `reap --dry-run` was run and any stale claims were confirmed and reaped.
- [ ] `top-n` was called to get the collision-free partition; exit 3 was handled as a
      clean stop.
- [ ] One background Agent was dispatched per lane with `task_id:` forced and
      NO `isolation: "worktree"`.
- [ ] Summaries were collected from all subagents; crashed lanes were flagged.
- [ ] The parent session received a ≤6-bullet summary per lane.
- [ ] Total tokens consumed by the parent session (reap + top-n + dispatch +
      collect) stayed under 10k (subagent transcripts are isolated).

## See Also

- [openup-next](../openup-next/SKILL.md) — the sequential continue-loop; use this
  for single-lane work or when you want interactive step visibility.
- `scripts/openup-claims.py reap` — stale-lease reaper.
- `scripts/openup-board.py top-n` — collision-free lane partition.
- `scripts/openup-claims.py heartbeat` — stamps `last_heartbeat` on a live claim.
- [parallel-lanes.md](../../../../docs-eng-process/parallel-lanes.md) — the
  write-fence, claim coordination, and `git-common-dir` lease model.

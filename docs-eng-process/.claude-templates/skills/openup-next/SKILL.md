---
name: openup-next
description: Run ONE OpenUP delivery cycle — read the derived board, claim the top READY lane, execute it, tick its progress, and exit through a legal exit. The sequential continue-loop.
model: inherit
fit:
  great: [driving delivery one session at a time, an outer /loop or cron repeatedly advancing the roadmap, "just do the next thing"]
  ok: [resuming a mid-cycle task whose progress is already persisted in its Operations checkboxes]
  poor: [authoring a brand-new spec (use /openup-create-task-spec first), exploratory work (use /openup-explore), picking a SPECIFIC task by id (use /openup-start-iteration directly)]
arguments:
  - name: task_id
    description: "Optional. Force a specific lane instead of the board's top pick (must still be pickable). Omit to take the top READY collision-free lane."
    required: false
---

# Next (sequential continue-loop)

**One invocation = one cycle of "read the next task and execute."** The queue is
derived deterministically by `scripts/openup-board.py` (never authored by the
model — "if a step is deterministic, the harness does it"). This skill reads the
board, claims the top pickable lane, works it under its track ceremony, ticks
its Operations checkboxes, and exits through one of **two legal exits**. Then the
session ends; an outer loop (`/loop`, cron, or a human) runs it again.

> **No continuation state may live only in this conversation.** Everything the
> next cycle needs — what is done, what is next, which role hat — is read back
> from the repo: the board, the lease, and the Operations checkboxes. If you
> find yourself needing to "remember" something across the exit, persist it
> (`design.md`, the run log, a ticked box), don't hold it in context.

## Success Criteria

After this skill completes, ALL of these must be true:
- [ ] Exactly one lane was claimed (lease written) and worked, OR the skill
      stopped cleanly because no lane was pickable.
- [ ] The Operations checkboxes for completed steps are ticked in the lane's
      `plan.md`.
- [ ] The cycle exited through `/openup-complete-task` **or**
      `/openup-create-handoff` — never a raw commit, never a third path.
- [ ] No information required to resume lives only in the conversation.

## Process

### 1. Refresh the board and take the top pickable lane

```bash
python3 scripts/openup-board.py top    # prints the top pickable lane as JSON; exit 3 = none
```

- **Exit 0** → you get the lane JSON: `{task, title, track, state, lease, hat, next_action, plan, collides_with, depends_ok}`. Continue with this lane.
- **Exit 3** → nothing is pickable. **Stop cleanly.** Print the reason from
  stderr (e.g. "1 in-progress, 2 blocked (unmet dep)") and do nothing else —
  this is a successful no-op, not a failure. (Run `python3 scripts/openup-board.py refresh`
  to show the full board if the user wants to see why.)

If `task_id` was passed, run `refresh` instead and select that lane from
`lanes[]`; refuse if it is not pickable (`state != "ready"`, or leased, or
`collides_with` set, or `depends_ok` false) and explain which condition failed.

A lane the board calls `ready` is one `scripts/openup-claims.py preflight` will
also clear — they share the same dependency/collision logic, so the claim in
step 2 will not surprise you.

### 2. Claim it + create the worktree (delegate to start-iteration)

Hand the lane's `task` and `track` to the existing machinery — do **not**
re-implement pre-flight / worktree / lease / state here:

```
/openup-start-iteration task_id: <lane.task> track: <lane.track or auto>
```

That skill runs the collision pre-flight, creates the branch + worktree, writes
the lease, and initializes `.openup/state.json`. Teams stay opt-in: a `standard`
lane is solo; only a `full` lane (or an explicit request) deploys one.

### 3. Self-brief and assume the lane's hat

Do **not** ask for a briefing — self-brief from the repo (T-016). Read the
`## On Start, Read` block of the role file named by `lane.hat` (default
`developer`) and load exactly its ring-scoped docs: status, the one change
folder `docs/changes/<task>/`, and that role's guideline docs. The spec
(`plan.md`) is authoritative; if it does not answer a question, **fix the spec**
(`/openup-create-task-spec` re-run), don't work around it.

`lane.next_action` is the first unchecked Operations box — your entry point.

### 4. Execute one cycle under the track's ceremony

Work the lane's Operations steps in order, under the track recorded in state
(`quick` / `standard` / `full` — see `tracks.md`). Assume role hats as the
`(role)` tags dictate (developer → tester → …), sequentially, one agent. Batch
implementation and its tests before reporting (token-efficiency protocol).

### 5. Persist progress — tick the boxes

As each Operations step lands, tick it in `plan.md`: `- [ ]` → `- [x]`. This is
the one sanctioned direct edit to a persisted spec (it is progress state, not a
behavior change). Record in-flight decisions in `docs/changes/<task>/design.md`
and append run-log records. The board re-derives `next_action`/`hat` from these
boxes next cycle — that is how resume works after the session ends.

### 6. Exit through a legal exit — and ONLY these two

- **Work for this task is complete** → `/openup-complete-task task_id: <task>`
  (commits, updates roadmap + status, releases the lease, removes the worktree,
  runs the rubric on `full`).
- **Pausing mid-task for the next owner/session** → `/openup-create-handoff task_id: <task>`
  (writes the receiver-facing brief; the lease and ticked boxes carry the rest).

There is no third exit. Never offer "just commit" or any process bypass. End the
session after the exit; the outer loop repeats from step 1.

## Output

A compact summary (≤6 bullets): the lane taken (or the clean no-op reason), the
hat assumed, what landed, which boxes are now ticked, and which legal exit was
taken.

## See Also

- [openup-start-iteration](../start-iteration/SKILL.md) — the claim/worktree/state machinery step 2 delegates to.
- [openup-complete-task](../complete-task/SKILL.md) — legal exit #1.
- [openup-create-handoff](../create-handoff/SKILL.md) — legal exit #2.
- [openup-readiness](../readiness/SKILL.md) — the human-readable DAG report; `openup-board.py` is its machine-readable superset.
- `scripts/openup-board.py` — the deterministic board generator (`refresh` / `top`).

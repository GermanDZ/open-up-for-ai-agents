---
name: openup-next
description: Run ONE OpenUP delivery cycle — resume the active iteration if one stopped mid-work, else claim the top READY lane, else promote the next pending roadmap task and start it. Always advances; only no-ops when nothing is left to do. The sequential continue-loop.
tier: reasoning
capabilities: {required: [read_write_files, exec], optional: []}
fit:
  great: [driving delivery one session at a time, an outer /loop or cron repeatedly advancing the roadmap, "just do the next thing", resuming a mid-cycle task, promoting the next roadmap line into a workable lane]
  ok: [starting the very next iteration from a roadmap that has no change folders yet]
  poor: [picking a SPECIFIC task out of PM order (use /openup-start-iteration directly), open-ended exploration with no roadmap line (use /openup-explore)]
arguments:
  - name: task_id
    description: "Optional. Force a specific lane instead of the board's top pick (must still be pickable). Omit to take the top READY collision-free lane."
    required: false
---

# Next (sequential continue-loop)

**One invocation = one cycle of "do the next thing."** Each cycle resolves the
next unit of work in a fixed precedence and advances it — it does **not** stop
and ask "want me to create the spec?" while pending work remains:

1. **Resume** — an iteration already started but stopped mid-work → continue it
   from its next unchecked Operations box.
2. **Pick** — no active iteration, but a change folder is a READY lane → claim
   and work it.
3. **Promote + start** — no lanes exist yet but the roadmap has a pending task →
   turn that next task into a workable lane (author its spec) and start it.
4. **No-op** — only when nothing is left: every lane is done/blocked/suspended
   and the roadmap has no pickable pending task.

The board queue is derived deterministically by `scripts/openup-board.py` (never
authored by the model — "if a step is deterministic, the harness does it"). The
cycle works the chosen lane under its track ceremony, ticks its Operations
checkboxes, and exits through one of **two legal exits**. Then the session ends;
an outer loop (`/loop`, cron, or a human) runs it again.

> **No continuation state may live only in this conversation.** Everything the
> next cycle needs — what is done, what is next, which role hat — is read back
> from the repo: the board, the lease, and the Operations checkboxes. If you
> find yourself needing to "remember" something across the exit, persist it
> (`design.md`, the run log, a ticked box), don't hold it in context.

## Success Criteria

After this skill completes, ALL of these must be true:
- [ ] `openup-board.py resolve` was called once to decide the cycle; on a
      `resume` with `resumable_input`, the answered lane was resumed (answers
      folded into the spec, lane un-suspended, request archived) before a new
      lane was claimed.
- [ ] Exactly one lane was advanced this cycle — by **resuming** the active
      iteration, **claiming** a READY lane, or **promoting** the next pending
      roadmap task into a new lane and starting it — OR the skill stopped cleanly
      because there was genuinely nothing to do (no lane pickable AND no pending
      roadmap task to promote).
- [ ] The Operations checkboxes for completed steps are ticked in the lane's
      `plan.md`.
- [ ] The cycle exited through `/openup-complete-task` **or**
      `/openup-create-handoff` — never a raw commit, never a third path.
- [ ] No information required to resume lives only in the conversation.

## Process

### 0–1. Resolve this cycle's lane — one call, branch on `.path` (T-065)

The whole §0–§1 precedence — resumable-input → active-iteration → top-pickable
lane → promotable roadmap task → no-op — is computed **as data** by one
read-only call. Do not chain `openup-input.py` / `openup-state.py` /
`openup-board.py top` / `openup-roadmap.py next` by hand, and do not read the
roadmap into context — `resolve` folds all four in:

```bash
python3 scripts/openup-board.py resolve   # one JSON decision; always exit 0
```

It returns `{path, lane, resumable_input, active_iteration, reason}` where
`path ∈ {resume, pick, promote, noop}`. Branch on `.path`:

- **`resume`** — the lane is already claimed and must continue *before* any new
  claim. Two sub-cases, distinguished by which field is set:
  - `resumable_input` is set → a human answered a question that suspended this
    lane. **Fold the answers into the spec, not into code** (fix-spec-first):
    read the named request, re-run `/openup-create-task-spec task_id: <task>` so
    the answers land in `docs/changes/<task>/plan.md` through the rubric, remove
    the `awaiting-input:` line from that plan's frontmatter, and archive the
    request (`status: processed` → `docs/input-requests/archive/`). Then work
    that lane (step 3).
  - `active_iteration` is set → an iteration is started and unfinished. **Do NOT
    re-run `/openup-start-iteration`** — the worktree, lease, and state already
    exist. Skip step 2; go to step 3 and continue from the **next unchecked
    Operations box**. If every box is ticked, jump to the legal exit
    (`/openup-complete-task`).
- **`pick`** — `lane` is the top pickable change-folder lane (`{task, title,
  track, hat, next_action, plan, …}`). A lane `resolve` calls pickable is one
  `openup-claims.py preflight` will also clear, so step 2's claim won't surprise
  you. Continue to step 2.
- **`promote`** — `lane.task` is the deterministically-selected next roadmap task
  (identical to `openup-roadmap.py next`: first `pending`/`planned` entry in
  document order with satisfied deps, no active/archived change folder, no live
  lease, and **no branch encoding its id on `origin`** — the T-066
  delivered-but-unmerged guard: a task finished in an open, unmerged PR is
  invisible to the local folder/lease checks, so without this it would be
  re-promoted and re-implemented. When that guard fires you get `noop` with a
  "merge its PR" reason, not `promote` — **merge the PR, don't redo the work**.
  The guard is fail-open (offline / no remote → promotion behaves as before) and
  disablable with `openup-roadmap.py next --no-remote-check`). **Track selection
  stays a model judgment** — `resolve` names *which* task; you choose *which
  ceremony track*. Promote **by task shape**:
  - **Implementation / change task** → `/openup-create-task-spec task_id: <id>`
    (writes the REASONS-Canvas `plan.md` that becomes the lane), then step 2.
  - **Inception artifact / requirements task** (Vision, use cases, risk list —
    content is questions, not code) → not loop-shaped; author it through its own
    skill inside a started iteration: `/openup-start-iteration task_id: <id>`
    then `/openup-create-vision` / `/openup-create-use-case` (or
    `/openup-plan-feature` at the idea stage). Drive human questions through
    `/openup-request-input` so the lane suspends cleanly.
- **`noop`** — nothing pickable and nothing promotable. **Stop cleanly** and
  print `reason`. Make it actionable: if the `reason` names a
  **delivered-but-unmerged** task (an `origin` branch / open PR exists), the move
  is to **merge that PR** — the work is done, not pending. If every roadmap row is
  `completed` and the phase's exit criteria look met, name the next move — run
  `/openup-phase-review` to advance the phase (a **product-manager decision** the
  loop surfaces, never performs). If the roadmap is simply empty, say so.

If `task_id` was passed, skip the precedence and select that lane directly from
`python3 scripts/openup-board.py top` / `refresh` `lanes[]`; refuse only if it is
not pickable (`state != "ready"`, leased elsewhere, `collides_with` set, or
`depends_ok` false) and say which condition failed.

For a human diagnostic superset (active iteration + all live leases + pickable
lanes + promotable next), use `python3 scripts/openup-board.py status` — also
read-only.

### 2. Claim it + create the worktree (delegate to start-iteration)

Applies to a lane from **1b (pick)** or the **implementation path of 1c
(promote)**. **Skip this step** when **1a (resume)** chose the lane — its
iteration already exists — and when **1c's inception path** already ran
`/openup-start-iteration` itself.

Hand the lane's `task` and `track` to the existing machinery — do **not**
re-implement pre-flight / worktree / lease / state here:

```
/openup-start-iteration task_id: <lane.task> track: <lane.track or auto>
```

That skill runs the collision pre-flight, creates the branch + worktree, writes
the lease, and initializes `.openup/state.json`. Teams stay opt-in: a `standard`
lane is solo; only a `full` lane (or an explicit request) deploys one.

It also runs the **cross-machine remote-check** (T-044) before claiming: the
local lease only sees this clone, so start-iteration asks `origin` whether
another teammate already pushed a branch for this task and refuses (recording a
`duplicate_start_blocked` event) if so. It is advisory/fail-open — offline or
remote-less runs are never blocked. This is the parallel-`openup-next`-across-
machines guardrail; the local lease guards parallel sessions on one clone.

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

A compact summary (≤6 bullets): which path ran (**resumed** / **picked** /
**promoted+started**, or the **clean no-op** reason), the lane and hat, what
landed, which boxes are now ticked, and which legal exit was taken. If you
promoted a roadmap task, name the spec/lane you created.

### Sentinel line (machine-readable, always last)

Every exit — ADVANCED or DONE — must end with exactly one of these lines as the
very last line of output, with nothing after it:

```
OPENUP-NEXT: ADVANCED — <task-id>
OPENUP-NEXT: DONE — <reason>
```

`ADVANCED` means a lane was worked this cycle (resumed, picked, or promoted+started).
`DONE` means a clean no-op: either every lane is blocked/suspended/elsewhere, or the
roadmap has no pickable pending task. The `<reason>` on DONE names the specific
condition (e.g. "board empty — all lanes done", "roadmap exhausted — phase review
needed", "all lanes blocked or suspended"). An outer loop MUST stop on `DONE` and
continue on `ADVANCED`. Any exit that is neither is a crash; treat it as `DONE`
(fail-safe stop).

## See Also

- [openup-start-iteration](../start-iteration/SKILL.md) — the claim/worktree/state machinery step 2 delegates to.
- [openup-complete-task](../complete-task/SKILL.md) — legal exit #1.
- [openup-create-handoff](../create-handoff/SKILL.md) — legal exit #2.
- [openup-readiness](../readiness/SKILL.md) — the human-readable DAG report; `openup-board.py` is its machine-readable superset.
- [openup-request-input](../request-input/SKILL.md) — how a cycle suspends on a question (creates the input-request + sets `awaiting-input`).
- `scripts/openup-board.py` — the deterministic board generator + precedence
  resolver (`refresh` / `top` / `top-n` / `resolve` / `status`).
- `scripts/openup-input.py` — maps answered input-requests back to resumable lanes (`resumable` / `list`).
- `scripts/openup-loop.sh` — the recommended shell-loop driver (`--max-cycles`, `--stall-limit`, `--task-id`).

## When Driven by an Outer Loop

`/openup-next` is designed to be re-invoked repeatedly by an outer driver — a
shell script (`openup-loop.sh`), `/loop`, or a cron job. The repo carries all
continuation state; each invocation starts cold.

**Stop rule (mandatory):** after every exit, check the last output line:
- `OPENUP-NEXT: ADVANCED — …` → schedule another invocation immediately (or
  after a short yield — never sleep longer than the worktree's expected cycle
  time).
- `OPENUP-NEXT: DONE — …` → stop the outer loop. Do not reinvoke. Surface the
  reason to the user.
- Anything else → treat as `DONE` (fail-safe stop; investigate the exit).

**Context model:** each invocation reads the repo from scratch (the
no-continuation-state rule at the top of this skill) — context stays minimal
every cycle regardless of how many cycles have run.

**Under `/loop` (interactive):** `/loop /openup-next` works but accumulates
context across ticks (same conversation). For long runs, prefer `openup-loop.sh`
(fresh `claude -p` process per cycle, truly cold context). Use `/loop` when you
want to watch progress interactively and the run is short (≤ ~10 cycles).

**Stall detection:** if the same task produces `create-handoff` exits N cycles in
a row (the lane keeps suspending on the same question), the outer loop should
stop and surface the stall rather than spinning. `openup-loop.sh` implements this
with `--stall-limit N` (default 3).

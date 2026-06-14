---
name: openup-next
description: Run ONE OpenUP delivery cycle — resume the active iteration if one stopped mid-work, else claim the top READY lane, else promote the next pending roadmap task and start it. Always advances; only no-ops when nothing is left to do. The sequential continue-loop.
model: inherit
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
- [ ] `openup-input.py resumable` was checked **first**; any answered-input lane
      was resumed (answers folded into the spec, lane un-suspended, request
      archived) before a new lane was claimed.
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

### 0. Resume any answered-input lane first (before claiming anything new)

A prior cycle may have **suspended** a lane on a question it could not resolve,
recording it as an input-request. Before touching the board, check whether a
human has answered — this is [Start-of-Run SOP](docs-eng-process/sops/start-of-run.md)
Step 0, made first-class for the loop:

```bash
python3 scripts/openup-input.py resumable   # prints "<task>\t<request>" lines; nothing = none
```

- **Nothing printed** → no suspended lane is answered; continue to step 1.
- **One or more lines** → resume the **first** task *before claiming any new
  lane*:
  1. Read the answers in the named request file.
  2. **Fold the answers into the spec, not into code.** Re-run
     `/openup-create-task-spec task_id: <task>` so the answers land in
     `docs/changes/<task>/plan.md` through the rubric (fix-spec-first). An
     answered request never auto-merges a behavior change — it only un-suspends
     the lane and surfaces the answers.
  3. **Un-suspend the lane**: remove the `awaiting-input:` line from that
     plan.md's frontmatter (the board reports the lane `suspended` only while it
     points at a `pending` request).
  4. **Close the request**: set its frontmatter `status: processed` and move the
     file to `docs/input-requests/archive/`.
  5. That task is now this cycle's lane — skip the board's top pick and go
     straight to step 2 (claim + work it).

The board models a lane with a still-`pending` request as `suspended` (not
generic `blocked`) and never picks it, so a question you raised cannot be
silently re-selected before it is answered.

### 1. Resolve this cycle's lane — resume → pick → promote

Work the precedence in order. The first that yields a lane wins; only fall
through to a no-op when none does. This is what makes the cycle *advance* instead
of stopping to ask whether to create a spec.

If `task_id` was passed, skip the precedence: run `python3 scripts/openup-board.py refresh`
and select that lane from `lanes[]`; refuse only if it is not pickable
(`state != "ready"`, or leased by another session, or `collides_with` set, or
`depends_ok` false) and explain which condition failed.

#### 1a. Resume — is an iteration already active?

```bash
python3 scripts/openup-state.py get task_id 2>/dev/null   # exit 3 = no active iteration
```

- **A task id is returned** (an iteration is started and not yet completed) →
  that task is this cycle's lane. **Do NOT re-run `/openup-start-iteration`** —
  the worktree, lease, and state already exist. Skip step 2, go straight to
  step 3 and continue from its **next unchecked Operations box** (this is "carry
  on where it stopped"). If every box is already ticked, the work is done →
  jump to the legal exit in step 6 (`/openup-complete-task`).
- **Exit 3 / nothing** → no active iteration; continue to 1b.

#### 1b. Pick — take the top pickable change-folder lane

```bash
python3 scripts/openup-board.py top    # prints the top pickable lane as JSON; exit 3 = none
```

- **Exit 0** → you get the lane JSON: `{task, title, track, state, lease, hat, next_action, plan, collides_with, depends_ok}`. Continue with this lane (step 2). A lane the board calls `ready` is one `scripts/openup-claims.py preflight` will also clear — same dependency/collision logic — so the claim in step 2 will not surprise you.
- **Exit 3** → read the **reason on stderr** and branch:
  - **"no pickable lane (… `N blocked` / `in-progress` / `suspended` …)"** — lanes
    exist but every one is held up. This is a genuine no-op: **stop cleanly**,
    print the reason, do nothing else. (Run `openup-board.py refresh` to show the
    full board if the user wants to see why.)
  - **"no active lanes — every change folder is done/archived or absent."** — there
    are zero lanes. Do **not** stop yet: the roadmap may still have pending work
    that simply has not been promoted into a change folder. Go to 1c.

#### 1c. Promote — turn the next pending roadmap task into a lane, then start it

Read `docs/roadmap.md` and select the **next pending task** — the first
`pending`/`planned` entry in the product-manager's given order whose
`depends-on` are satisfied and that has **no `docs/changes/<id>/` folder yet**.
Consume the order as given; do not re-prioritize (that is the product-manager
role's call). Then promote it **by task shape**:

- **Implementation / change task** → `/openup-create-task-spec task_id: <id>`.
  This writes `docs/changes/<id>/plan.md` (REASONS Canvas + Operations boxes),
  which becomes the lane. Then go to step 2 and start it this same cycle.
- **Inception artifact / requirements task** (Vision, use cases, risk list — work
  whose content is questions, not code) → it is **not loop-shaped**; do not force
  the REASONS Canvas onto it. Author it through its own skill within a started
  iteration: `/openup-start-iteration task_id: <id>` then `/openup-create-vision`
  / `/openup-create-use-case` (or `/openup-plan-feature` if still at the idea
  stage). Drive any human questions through `/openup-request-input` so the lane
  suspends cleanly (step 0 resumes it once answered) rather than dead-ending.

If the roadmap has **no** pending task to promote either, then there is genuinely
nothing to do → **stop cleanly** and say so (the roadmap is empty or fully
delivered).

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

## See Also

- [openup-start-iteration](../start-iteration/SKILL.md) — the claim/worktree/state machinery step 2 delegates to.
- [openup-complete-task](../complete-task/SKILL.md) — legal exit #1.
- [openup-create-handoff](../create-handoff/SKILL.md) — legal exit #2.
- [openup-readiness](../readiness/SKILL.md) — the human-readable DAG report; `openup-board.py` is its machine-readable superset.
- [openup-request-input](../request-input/SKILL.md) — how a cycle suspends on a question (creates the input-request + sets `awaiting-input`).
- `scripts/openup-board.py` — the deterministic board generator (`refresh` / `top`).
- `scripts/openup-input.py` — maps answered input-requests back to resumable lanes (`resumable` / `list`).

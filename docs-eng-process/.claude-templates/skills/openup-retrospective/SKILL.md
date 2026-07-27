---
name: openup-retrospective
description: Generate iteration retrospective with feedback and action items
model: sonnet
fit:
  great: [end-of-iteration reflection, capturing patterns to feed forward]
  ok: [mid-iteration when blockers pile up and a reset is needed]
  poor: [single-task wrap-ups (use complete-task notes), trivial iterations]
arguments:
  - name: iteration_number
    description: Iteration to review (optional, defaults to current)
    required: false
  - name: include_metrics
    description: "Include git metrics (true/false, default: true)"
    required: false
---

# Retrospective

Generate an iteration retrospective capturing what went well, what to improve, and action items.

## Process

### 1. Determine Iteration

If `$ARGUMENTS[iteration_number]` is provided, use it. Otherwise read `docs/project-status.md` for the current iteration number.

### 2. Read Project Context

Read `docs/project-status.md` for: iteration goal, dates, team members, overall status.

> **Read `**Status**`, not `**Lane Status**` (T-149).** `**Status**` describes the
> iteration named in `**Iteration**` — the one this retrospective is about.
> `**Lane Status**` describes whichever lane happens to be live while you run,
> which is a different question and may well be an unrelated quick task. See
> [state-file.md](../state-file.md) § *How state reaches `docs/project-status.md`'s
> status fields*.

### 3. Analyze Completed Tasks

Read `docs/roadmap.md` to identify: tasks planned, completed, not completed, and added during iteration. Note complexity, challenges, and successes for each.

### 4. Gather Feedback

Review these sources for patterns and issues:
- `docs/agent-logs/` - Agent run logs
- `docs/risk-list.md` - Risks emerged or mitigated
- `docs/roadmap.md` - Velocity (completed vs planned), blocked items
- Git commit messages

### 4b. Measure Read-Back (success measures whose date has passed)

This is the step that closes the loop between per-feature success measures
(task-spec `## Success Measures`, rubric criterion 12) and value
prioritization — without it, measures are write-only and the roadmap ordering
stays opinion-based.

1. Scan archived change folders (`docs/changes/archive/T-NNN/design.md`) for
   recorded success-measure grades + read-back dates (written by
   `/openup-complete-task` step 1b). Skip `n/a` entries.
2. For each entry whose **read-back date has passed** and has no recorded
   outcome yet: read the instrumentation named in the expectation (the event /
   metric / query) and record **actual vs expected** — including "instrumentation
   exists but nobody can produce the number" (that is a finding, not a skip).
3. Write the results into the retrospective document's **Measure Read-Back**
   section (see step 6): expectation, actual, verdict (met / missed / can't
   tell), one-line interpretation.
4. **Hand the section to the product-manager role** (`.claude/teammates/product-manager.md`):
   it consumes these verdicts to re-rank pending roadmap entries, updating each
   moved entry's `Value` rationale to cite the evidence ("UC-12's measure
   missed by 80% — demoting the follow-on entries below the X work"). The
   re-rank is the product-manager's call; the retrospective only delivers the
   evidence.
5. Note read-backs that come due **before** the next expected retrospective as
   action items with owners, so they aren't silently skipped.

### 5. Collect Metrics (if `$ARGUMENTS[include_metrics] == "true"`)

```bash
# Commits in iteration period
git log --oneline --since="$start_date" --until="$end_date" | wc -l

# Lines changed
git diff --stat trunk...HEAD

# Active contributors
git shortlog -sn --since="$start_date" --until="$end_date"
```

Task metrics: tasks planned, tasks completed, completion rate (completed / planned * 100%).

### 5b. Verify and Retire Carried Action Items — BLOCKING, before any new item is authored

Every retrospective so far has *appended* action items and none has ever pruned
one. That makes the one section agents are pointed at for context degrade
monotonically: a blocker resolved days ago keeps reading as live and
high-priority, and real work gets deprioritized behind a phantom. This step runs
**here**, physically ahead of step 6, because a reminder inside the authoring
step is exactly the failure mode being fixed.

1. **Collect the carried items from the durable trail, not from memory.** Read
   every prior file in `docs/iteration-retrospectives/` (newest first) and take
   every row of its `## Action Items` table that is **not already struck
   through** — those are the open items. Add any carried list the project keeps
   in `docs/project-status.md`. If a project has no prior retrospective, say so
   in one line and go to step 6.

2. **For each open item, establish what would make it true, then check it.** The
   check is mechanical wherever it can be: `grep` for the artifact the item asks
   for, run the command it names and read the output, read the roadmap row's
   Status, `git log` the file it wanted changed, open the path it wanted created.
   You are allowed judgment about *whether the evidence answers the item*; you
   are not allowed to skip the check.

3. **Assign exactly one of three verdicts:**

   | Verdict | When | What you write |
   |---|---|---|
   | **satisfied** | The thing the item asked for now exists | Strike the row through **in the retrospective that authored it**, appending `**satisfied YYYY-MM-DD** — <evidence>` |
   | **obsolete** | It is no longer wanted — superseded, reversed, or the underlying problem is gone | Strike it through the same way with `**obsolete YYYY-MM-DD** — <what superseded it>` |
   | **still open** | Neither of the above, *including* "probably done but nothing to cite" | Leave it unstruck and carry it forward (point 6) |

   Worked example — a row in `iteration-77-retrospective.md` rewritten in place:

   ```
   | ~~Fix `test_init_creates_valid_file` to assert `schema == CURRENT_SCHEMA`~~ | next `/openup-quick-task` | ~~next iteration~~ | **satisfied 2026-07-27** — `scripts/tests/test_openup_state.py:61`, commit `a1b2c3d` (T-133) |
   ```

4. **Evidence is mandatory and must be citable.** One of: a **commit SHA**, an
   **artifact path** (that exists), a **task id** whose change folder is archived,
   or a **command plus the output you observed**. "I believe this was done", "this
   looks handled", and "the task it belongs to is completed, so presumably" are
   not evidence. **An item you cannot cite evidence for stays open** — that rule
   is what keeps this pass from becoming a rubber stamp, and a false "satisfied"
   is worse than a stale item because it removes the thing that would have caught
   it.

5. **Never delete an item.** Retirement is strike-through **with** the evidence
   inline, never a deletion. The struck row is the trail that makes a wrong
   verdict provable later; deleting it destroys precisely the record you would
   need. This is also why the strike lands in the authoring retrospective — a
   reader arriving there from an old link sees the resolution instead of a stale
   demand.

6. **Carry the still-open items forward with their original date.** They go into
   the new retrospective's carried table (step 6) with the date they were first
   authored, so age is visible — a three-retrospective-old item should look like
   one. **Do not author a new item in step 6 that duplicates a carried one**;
   extend or re-date the carried item instead, otherwise the duplicate resets its
   apparent age and the section grows a second copy of the same debt.

> **Where this pass lives — open question, not settled.** It is a step of this
> skill today, because this is the only skill that authors action items. If a
> second skill ever needs the same disposition pass over carried, hand-written
> items (a phase review, a handoff), extract it into a shared "carried items"
> helper both call rather than copying these rules — the copy is what would drift.
> Until that second caller exists, a shared helper would be abstraction ahead of
> demand.

### 5c. Verify New Action Items' Premises — BLOCKING, before any item is authored

Step 5b asks of a carried item: *is this still true?* This step asks of a **new**
one: *was it ever true?* Both run ahead of step 6 for the same reason — a
reminder inside the authoring step is the failure mode being fixed.

An action item is a promise that someone will spend a session on it. Filing one
whose premise was never checked spends that session discovering the premise was
wrong — and the wrong item still costs a full lane to disprove. Of the five items
iteration-98 filed and promoted, **four did not survive contact**:

| Failure mode | What it looks like | Observed |
|---|---|---|
| **Already fixed** | The item describes a defect a merged task had removed before the retrospective was written | `A2` — T-142 had already shipped the fix and its regression tests; the lane observing it was running a pre-merge skill mirror (iteration 100) |
| **Disproved on inspection** | The claim was inferred from indirect evidence and falls apart the moment the actual command is run | `A3` — inferred from two direct file reads, never from `get`; in an isolated fixture the behavior was correct. Retired **WRONG**, not "done" |
| **Shrunk on measurement** | Real, but far smaller than filed — most sub-items already covered | `T-153` (two of three sub-items already had real coverage; the genuine gap was none of the three); `T-147` (owner noted it did not reproduce locally) |

So, for **each new item you are about to author**:

1. **State what would make the problem real, then check it** — the same
   mechanical bias as 5b: run the command, `grep` for the artifact, read the
   roadmap Status, open the path. Prefer the check that could *falsify* the item.
2. **Check it where the problem lives.** If the item is about a downstream or
   consumer repo, "it reproduces here" is not evidence — and neither is "it does
   not reproduce here". T-147's premise was structurally invisible in this repo
   because it gitignores `/.claude/*`. Name the environment you checked.
3. **Record the evidence on the item.** Every row of the `## Action Items` table
   carries an **Evidence** element: one line stating what was checked, where, and
   what it showed. A citation (file:line, command + output, task id) beats a
   summary.
4. **If the check shows the problem is already fixed, do not file the item.**
   Say so in *What Went Well* instead — that is a closed loop, not an action.
5. **If the check shows it is smaller than it looked, file the smaller item.**
   Scope it to what you measured, not to what you first suspected.

**An item with no Evidence element is a gap and blocks the retrospective** — the
same BLOCKING idiom as 5b. This is deliberately a graded, prose check with **no
validator script**: *"is this premise real?"* is not mechanically parseable, and a
name-matcher would pass any phrasing while answering nothing (the reasoning T-152
recorded for its own criterion).

> **Scope: new items only.** This step grades the `## Action Items` (new-only)
> table. Carried items are step 5b's business — re-verifying them here would
> duplicate that pass and reset the age signal it depends on.

### 6. Create Retrospective Document

Create `docs/iteration-retrospectives/iteration-{n}-retrospective.md` with sections:
- **Iteration Overview**: number, date range, goal, participants
- **Summary**: overall assessment, key achievements, major challenges
- **What Went Well**: process, technical, collaboration successes
- **What to Improve**: process issues, technical challenges, gaps
- **Measure Read-Back**: for each success measure due (step 4b) — expectation, actual, verdict (met / missed / can't tell), interpretation; plus the product-manager's resulting re-rank decisions (entries moved + updated `Value` rationale), or "no re-rank — evidence supports current order"
- **Carried Action Items** (from step 5b): two tables — **retired this cycle** (each item, its verdict `satisfied`/`obsolete`, and the evidence cited) and **still open** (each item with its *original* authoring date, so age is visible). "None carried" is a legitimate entry for a project's first retrospective; silence is not
- **Action Items**: specific action, owner, due date, priority, **and Evidence** for each improvement — **new items only**; none may duplicate a still-open carried item (step 5b point 6), and none may be authored without the verified premise step 5c requires. The Evidence element states what was checked, **where**, and what it showed; an item without one is a gap that blocks the retrospective
- **Metrics** (if included): task completion stats, git stats
- **Next Iteration Considerations**: carry forward, changes, risks to monitor

### 7. Update Project Status

In `docs/project-status.md`: add link to retrospective, note ongoing action items, update iteration status.

**Ongoing means still open.** Mirror only the items step 5b left unretired —
anything struck through as `satisfied` or `obsolete` must not reappear here. The
retrospective documents are the system of record for the full trail (retired
items keep their evidence there); `project-status.md` carries the short live
list agents actually read for context, and its whole value is that everything on
it is still true.

> `docs/project-status.md`'s header fields and `## Notes` are a **derived view**
> regenerated by `scripts/sync-status.py` — never hand-edit those. The action-item
> list is separate, hand-maintained content and is the part this step writes.

### 8. Reset the Retro-Cadence Counter (T-011)

Running this retrospective satisfies the cadence, so reset the durable counter. This zeroes
`<git-common-dir>/openup/retro.json` (shared across worktrees) and clears
`gates.retro_due` in any live `.openup/state.json`:

```bash
python3 scripts/openup-state.py retro reset
```

After this, `/openup-start-iteration` will permit `full`-track starts again until 5 more
tasks complete. See [state-file.md](../../../../docs-eng-process/state-file.md).

## Output

Returns: retrospective document path, counts of what went well / what to improve / action items, **carried-item disposition (retired satisfied / retired obsolete / still open, from step 5b)**, overall iteration rating, key metrics (if included).

## See Also

- [openup-start-iteration](../start-iteration/SKILL.md) - Start next iteration
- [openup-complete-task](../complete-task/SKILL.md) - Complete iteration tasks
- [openup-assess-completeness](../assess-completeness/SKILL.md) - Assess iteration completeness before retrospective
- [openup-create-iteration-plan](../openup-artifacts/create-iteration-plan/SKILL.md) - Plan next iteration based on retrospective

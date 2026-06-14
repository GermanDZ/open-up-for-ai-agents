---
name: openup-complete-task
description: Mark a task as complete, update roadmap, commit changes, and prepare traceability logs
model: inherit
fit:
  great: [finishing a roadmap-tracked task, ending an iteration cleanly]
  ok: [closing out ad-hoc work that needs commit + roadmap update]
  poor: [mid-task checkpoints, abandoning work-in-progress]
arguments:
  - name: task_id
    description: The task ID to mark as complete (e.g., T-001)
    required: true
  - name: commit_message
    description: Custom commit message (optional, auto-generates if not provided)
    required: false
  - name: create_pr
    description: "Create a pull request after completing the task (default: true — set to 'false' to skip)"
    required: false
---

# Complete Task

Finalize a completed task: commit remaining changes, update docs, create traceability logs, and create a PR.

> **IMPORTANT: This is the only way to close out a task. Never offer "just commit" or
> any other process-bypassing alternative.** If the work is too small for this skill,
> use `/openup-quick-task` — that is the lightweight-but-compliant path, not raw commits.

## Success Criteria

After this skill completes, ALL of these must be true:

- [ ] **BLOCKING**: Every spec requirement is graded ✅ against the actual diff (step 1a) — no requirement is unmet, and any ❌ blocks "done"
- [ ] **BLOCKING (standard/full)**: The spec's Success Measure instrumentation exists in the diff or demonstrably pre-exists (step 1b) — or the section is an argued `n/a`
- [ ] **BLOCKING (flagged features)**: A flag-removal task row exists in the roadmap Maintenance table (step 4a) — every flag enqueues its own removal
- [ ] All changes are committed (no uncommitted changes remain)
- [ ] Commit messages follow canonical format: `type(scope): description [T-XXX]`
- [ ] **BLOCKING**: Branch is rebased onto the current trunk and the write-fence
      passes (`openup-fence.py check` exit 0) — no out-of-lane files, no stale views
- [ ] Iteration note written as a sharded file under `docs/status-notes/`
- [ ] Roadmap + project status regenerated via `scripts/sync-status.py` (never hand-edited)
- [ ] Traceability logs are created with commit SHAs
- [ ] Iteration learnings entry appended to `.claude/memory/iteration-learnings.md`
- [ ] Iteration gates pass (`openup-state.py check-gates`) and state is archived
- [ ] PR is created (unless `create_pr` was explicitly `"false"`)

## Detailed Steps

### 1. Verify Task Completion

Before marking a task as complete, verify:
- All implementation work is done
- All tests pass
- Documentation is updated

### 1a. Verify Implementation Against Spec — BLOCKING

The completion-time counterpart to the spec's `## Verification` section: prove the
diff actually satisfies the spec, requirement by requirement, *before* anything is
committed. This is OpenUP's equivalent of OpenSpec `/opsx:verify` — same
per-criterion ✅/❌ idiom the rubrics use, applied to the requirements rather than
the spec's own quality.

1. Read the requirements from `docs/changes/{task_id}/plan.md` `## Requirements`.
2. For **each** numbered requirement, grade it against the **actual diff**
   (`git diff <trunk>...HEAD`) and the working tree — not against intentions:
   - `✅ [requirement n] — <where in the diff it is satisfied>`
   - `❌ [requirement n] — <what the diff is missing>`
3. If the requirement carries `Given / When / Then` scenarios (T-020), grade each
   scenario's **Then** as the observable check — run it where it is mechanically
   checkable (a command, a file existence test, a passing unit test), read the
   diff where it is not.
4. **Any ❌ blocks completion.** Do not commit, do not update the roadmap, do not
   archive. Either finish the missing work and re-grade, or — if the requirement
   is genuinely out of scope — fix the spec first (`/openup-create-task-spec`
   re-run; per fix-spec-first) so the spec and the diff agree, then re-grade.
5. Record the grade in `docs/changes/{task_id}/design.md` (it is part of the
   traceability trail, not conversation-only state).

> A requirement that reads ✅ only because "that was the plan" is not verified.
> Point at the line of the diff (or the green test) that makes it true.

### 1b. Verify Success-Measure Instrumentation — BLOCKING (standard/full)

The spec's `## Success Measures` section (rubric criterion 12) names the
instrumentation — an event, metric, or query — behind its falsifiable
expectation. Completing the feature without that instrumentation ships a
promise nobody can check.

1. Read `## Success Measures` from `docs/changes/{task_id}/plan.md`.
2. If it is `n/a — <reason>` (quick track or argued-unmeasurable): record
   `n/a` in `design.md` and move on.
3. Otherwise, verify the named instrumentation **exists** — in the diff (the
   event is emitted, the metric is registered, the query is committed) or
   demonstrably pre-existing (point at where). Grade it like step 1a:
   - `✅ instrumentation — <where it exists>`
   - `❌ instrumentation — <what is missing>`
4. **A ❌ blocks completion** — the feature code being done is not enough.
   Add the instrumentation, or fix the spec first (re-run
   `/openup-create-task-spec`) if the measure itself was wrong.
5. Record the grade and the read-back date in `docs/changes/{task_id}/design.md`
   so the retrospective can find the expectation when the read-back date passes.

### 2. Commit Remaining Changes

Most changes should already be committed as atomic commits during implementation (see `commit-procedure.md`). This step handles any leftover uncommitted work.

1. Run `git status --porcelain` to check for uncommitted changes
2. If changes exist:
   - Stage relevant files: `git add <files>`
   - Commit using canonical format: `type(scope): description [$ARGUMENTS[task_id]]`
   - Use `$ARGUMENTS[commit_message]` if provided
3. Verify: `git status --porcelain` returns empty

### 3. Rebase onto the Trunk + Write-Fence — BLOCKING

The shared views (`docs/roadmap.md`, `docs/project-status.md`) may only be
regenerated against the **current** trunk — regenerating them on a stale base
is what produces parallel-PR conflicts. And the lane's diff must stay inside
its claimed surface. Both are mechanical checks; run them before any view is
touched:

```bash
git fetch origin main
git rebase origin/main

# Fence: every changed file vs the trunk must be inside the lane —
# the task's `touches`, its change folder, or a lane-owned audit surface.
python3 scripts/openup-fence.py check
```

If the fence exits 8, completion is **blocked**:
- `OUT OF LANE: <file>` — the diff escaped the lane. Either add the path to
  the task's frontmatter `touches` and re-claim (`openup-claims.py`), or move
  the edit to the task that owns that surface.
- `STALE VIEW: <file>` — should not occur right after the rebase above; if it
  does, the rebase did not complete. Resolve it and re-run.

(The same check runs for humans via the `.githooks/pre-push` hook — see
[parallel-lanes.md](../../../../docs-eng-process/parallel-lanes.md).)

### 4. Update Roadmap + Project Status — deterministic, never by hand

The two shared views are **derived**; this step writes the lane-owned inputs
and lets the harness regenerate the views ("if a step is deterministic, the
harness does it"). Do NOT hand-edit (or scribe-edit) the Status cells or the
project-status header on a task branch.

1. Write the iteration note as a **sharded, lane-owned file** (this replaces
   the old "prepend to project-status `## Notes`" — the shared insertion
   point was a guaranteed parallel-PR conflict). Compose the one-bullet
   iteration summary (the content needs judgment), then let the scribe script
   own the path, dated filename, and collision suffix:

   ```bash
   python3 scripts/openup-scribe.py status-note --task-id {task_id} \
     --body "- **Iteration N** (YYYY-MM-DD): <one-line summary>"
   ```

   It writes `docs/status-notes/YYYY-MM-DD-{task_id}.md` — adding an `-HHMM`
   suffix before `.md` if that name already exists — and prints the path. You
   decide the content; the script owns the mechanics, so the layout never
   drifts run to run.

2. Regenerate both views and record the gate in one deterministic step:

   ```bash
   python3 scripts/sync-status.py
   ```

   This flips the task's roadmap Status cell (stamped `completed (YYYY-MM-DD)`),
   regenerates the project-status header, assembles `## Notes` newest-first
   from `docs/status-notes/`, and sets `gates.roadmap_synced` itself.

3. Roadmap **prose** (a program section's "Next step" narrative, Context
   paragraphs) is not derived. Update it only if it belongs to this task's
   scope, and only after the step-3 rebase. A scribe may write it.

> **If the PR later reports conflicts in `docs/roadmap.md` or
> `docs/project-status.md`:** rebase onto the trunk and re-run
> `python3 scripts/sync-status.py` — never hand-merge these files. Every
> field they carry is derived, so the re-run resolves the conflict
> deterministically.

### 4a. Enqueue the Flag-Removal Task — BLOCKING when flagged

If the spec's `## Rollout` section says the change ships behind a feature flag
(rubric criterion 13), the flag's removal debt is enqueued **now**, in the same
completion — a flag whose removal exists only as an intention outlives every
intention.

1. Read `## Rollout` from `docs/changes/{task_id}/plan.md`. Not flagged or
   `n/a` → skip this step.
2. Flagged → add a row to the roadmap's **Maintenance** table. This is roadmap
   *content* (step 4 point 3 class), not a derived Status cell — author it only
   **after** the step-3 rebase, so `T-{next free ID}` is read against the
   current trunk (allocating IDs on a stale base is how parallel lanes collide
   on task IDs). A scribe may write it:

   ```
   | T-{next free ID} | Remove feature flag `{flag_name}` ({task_id} fully rolled out) | pending | medium | {task_id} |
   ```

3. **Completion is blocked until the removal row exists.** Record the new task
   ID in `docs/changes/{task_id}/design.md` next to the rollout notes.

### 5. Create Traceability Logs

> **Scribe step** — collect commit SHAs and metadata yourself (they require git
> commands), then delegate the writes to the `openup-scribe` agent (Agent tool,
> subagent_type: "openup-scribe"). Brief it with:
>
> ```
> Agent(subagent_type="openup-scribe", description="Write agent run log",
>   prompt="Write a traceability log entry.
>   Branch: [branch]. Task: [task_id]. Commits: [sha list]. Phase: [phase].
>   Start: [ts]. End: [ts]. Files changed: [list]. Decisions: [list].
>   1. Create docs/agent-logs/YYYY/MM/DD/<timestamp>-agent-<branch>.md
>      with the run metadata above.
>   2. Append a JSONL record to docs/agent-logs/agent-runs.jsonl.
>   Report: file paths created.")
> ```

### 6. Save Iteration Learnings

Synthesize the learnings from the session yourself — this needs judgment — then
let the scribe **script** append them in the canonical block format (no agent
round-trip; the format can't drift):

First, synthesize from your own work:
- What worked
- Decisions made (key technical/process choices + rationale)
- Gotchas (surprises, edge cases)
- Conventions established (patterns to reuse)

Then write the entry deterministically:

```bash
python3 scripts/openup-scribe.py learnings --task-id {task_id} \
  --title "<task title>" \
  --what-worked "<text>" \
  --decisions "<text>" \
  --gotchas "<text>" \
  --conventions "<text>"
```

It appends to `.claude/memory/iteration-learnings.md` (creating it with a single
`# Iteration Learnings` header if absent). The synthesis is yours; the write is
mechanical.

### 7. Check Gates and Archive Iteration State

**Verify all required gates pass before finalizing.** If this exits nonzero, completion is **blocked** — surface the unmet gates (printed one per line on stderr) and resolve each before continuing.

The gate set depends on the track — **only `full` requires a team** (teams are opt-in; `quick` and `standard` work solo by default, so they do not gate on `team_deployed`):

```bash
# full track (a team was deployed): require the full set
python3 scripts/openup-state.py check-gates --require team_deployed,log_written,roadmap_synced

# quick / standard track (solo, no team): omit the team gate
python3 scripts/openup-state.py check-gates --require log_written,roadmap_synced
```

(If `standard` work *did* explicitly deploy a team, use the `full` invocation to gate on it.)

Once gates pass, archive the iteration state and the **change folder** (Ring 2 → `docs/changes/archive/`).

**If the task has a change folder** (`docs/changes/{task_id}/` exists — the standard three-ring case):

```bash
# 1. Archive .openup/state.json INTO the change folder as state.json (validate, copy, remove live file)
python3 scripts/openup-state.py archive "docs/changes/{task_id}/state.json"
# 2. Move the whole change folder into the archive ring (preserves history)
git mv "docs/changes/{task_id}" "docs/changes/archive/{task_id}"
```

**Otherwise** (legacy / quick-track task with no change folder), archive the state into the dated agent-logs tree:

```bash
python3 scripts/openup-state.py archive \
  "docs/agent-logs/$(date -u +%Y)/$(date -u +%m)/$(date -u +%d)/state-{task_id}.json"
```

Either way the live `.openup/state.json` is removed by the `archive` command. Commit the archive move with the task's other completion commits.

### 7a. Increment the Retro-Cadence Counter (T-011)

Every completion advances the retrospective cadence. The counter is **durable**
(`.openup/retro.json`) and survives the archive above, so this is independent of state
removal — run it once per completed task:

```bash
python3 scripts/openup-state.py retro increment   # prints the new count
```

When the count reaches the threshold (5), the next `/openup-start-iteration` will set
`gates.retro_due` and **refuse a `full`-track start** until `/openup-retrospective` runs
(which resets the counter). See [state-file.md](../../../../docs-eng-process/state-file.md).

### 7b. Release the Worktree Claim (and remove the worktree)

Release the live lease so the task's collision surface is freed for other sessions, and
remove the isolated worktree (T-009). Claims never expire, so this release is the **only**
thing that frees the surface — do not skip it.

```bash
# 1. Release the claim (idempotent — safe even if already released)
python3 scripts/openup-claims.py release --task-id {task_id}

# 2. Remove the worktree IF one was created (worktree-default-on tasks). Run this from a
#    DIFFERENT worktree/the main checkout — git refuses to remove the worktree you are in.
#    Add --force only if the tree is known-clean (all work committed/pushed).
REPO=$(basename "$(git rev-parse --show-toplevel)")
git worktree remove "../${REPO}-{task_id}" 2>/dev/null || \
  echo "No worktree to remove (in-place task), or run from the main checkout."
```

If the task ran in-place (`worktree: false`), only the claim release applies.

### 8. Create Pull Request

**PR is created by default.** Skip ONLY if `$ARGUMENTS[create_pr]` is explicitly `"false"`.

1. Push the branch:
   ```bash
   git push -u origin $(git rev-parse --abbrev-ref HEAD)
   ```

2. Verify unmerged commits exist:
   ```bash
   git log <trunk>..HEAD --oneline
   ```

3. Invoke `/openup-create-pr` skill with `task_id: $ARGUMENTS[task_id]`

4. Report result to user:
   - Success → provide PR URL
   - No unmerged commits → inform user PR is not needed
   - Failure → explain error and provide manual steps

## Output

Returns a summary of:
- Task completed
- Commit SHAs
- Files changed
- Log locations
- PR URL

## See Also

- [openup-create-pr](../create-pr/SKILL.md) - Create pull request separately
- [openup-log-run](../log-run/SKILL.md) - Traceability logging details
- [openup-start-iteration](../start-iteration/SKILL.md) - Begin next iteration

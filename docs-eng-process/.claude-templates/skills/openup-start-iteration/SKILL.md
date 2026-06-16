---
name: openup-start-iteration
description: Begin a new OpenUP iteration with proper phase context and task selection
model: haiku
fit:
  great: [feature work, multi-step tasks, anything needing a deployed team]
  ok: [single-component changes that benefit from explicit iteration framing]
  poor: [typo fixes, hotfixes, exploratory spikes, throwaway scripts]
arguments:
  - name: iteration_number
    description: The iteration number (optional, auto-increments if not provided)
    required: false
  - name: goal
    description: The iteration goal (optional, reads from project-status if not provided)
    required: false
  - name: task_id
    description: The task ID from roadmap to work on (required for task-based branching)
    required: true
  - name: track
    description: "Ceremony track (quick|standard|full). Optional — auto-selected from scope when omitted. quick = docs/config/typo/≤~50 LOC single file (state + auto-log only, no plan gate, no team, no readiness); standard = single-feature (plan gate + scribe + /openup-readiness, solo by default — team opt-in); full = multi-role/architectural (standard + team default-on, opt-out + rubric at complete-task). See tracks.md."
    required: false
  - name: team
    description: Team type to automatically deploy after initialization (feature, investigation, construction, elaboration, inception, transition, planning, full, or none)
    required: false
  - name: deploy_team
    description: "Whether to deploy a team after iteration initialization (true/false/auto, default: auto — deploy only on the full track; skip on quick/standard. Pass 'true' to force a team, 'false' to force solo)"
    required: false
  - name: worktree
    description: "Whether to create an isolated git worktree for this task (true/false, default: true — pass 'false' for a legacy in-place checkout). See T-009 / parallel-work.md."
    required: false
---

# Start Iteration

Initialize a new OpenUP iteration: read project state, create a task branch, and begin work.

## Success Criteria

After this skill completes, ALL of these must be true:

- [ ] **BLOCKING (full track only, when a team is requested)**: If the `full` track (or an explicit `team:` / `deploy_team: true`) calls for a team, it is deployed and coordinating before implementation begins. `quick` and `standard` default to solo sequential work — no team required.
- [ ] Project status is updated with new iteration
- [ ] **BLOCKING**: `git rev-parse --abbrev-ref HEAD` returns a non-trunk branch name. If it returns trunk, the skill has FAILED — do not proceed.
- [ ] Iteration goal is defined
- [ ] Answered input requests are processed
- [ ] Log entry is created
- [ ] `.openup/state.json` created

## Process

### 1. Read Project Status

Read `docs/project-status.md` to establish context:
- Current phase (inception | elaboration | construction | transition)
- Current iteration number
- Previous iteration status

### 2. Read Roadmap and Identify Task

Read `docs/roadmap.md` to:
- Find the task specified by `$ARGUMENTS[task_id]`
- Extract task details: title, description, task type (feature, bugfix, refactor, etc.)
- Determine priority, dependencies, and the `Value` rationale (if present)
- **If task_id not found**: Ask user to specify which task from the roadmap

**The roadmap's pending order is product-manager input — consume it as given.**
If the requested task sits below other READY pending entries, that is fine (the
human chose it), but do not yourself substitute a "more valuable" task or
re-order entries here: an item may be passed over only for mechanical reasons
(unmet dependency, collision, lease, missing spec). If the ordering looks wrong,
surface that to the product-manager role (`.claude/teammates/product-manager.md`)
— never re-prioritize from inside an execution skill.

### 3. Select Track

Choose the ceremony track that matches the task's scope. Use `$ARGUMENTS[track]` if
provided; otherwise auto-select from the task description / `docs/changes/{task_id}/plan.md`
scope using this decision table:

| Track | When | Ceremony applied |
|---|---|---|
| `quick` | docs / config / typo / comment / ≤ ~50 LOC, single file | state file + auto-log only — **no plan gate, no team, no readiness** |
| `standard` | single-feature work | plan gate + scribe logging + `/openup-readiness` check; team optional |
| `full` | multi-role / architectural / cross-cutting | standard **+ team deployment + rubric assessment** at complete-task |

The intake hook (`on-task-request.py`) prints a `Suggested track: …` line — treat it as the
default unless the actual scope differs. The selected track drives two things below: the
**Deploy-Team** step (step 4) and the `--track` flag passed to `openup-state.py init`
(step 6). See [tracks.md](../../../../docs-eng-process/tracks.md) for the full wiring.

### 3b. Check Retro Cadence (T-011)

The retrospective cadence is enforced by a durable counter, not a convention. Read it:

```bash
python3 scripts/openup-state.py retro get   # N = completed tasks since the last retrospective
```

**If `N >= 5` AND the selected track is `full`: REFUSE to start.** Do not create a branch
or deploy a team. Print the redirect and stop:

> ⛔ Retrospective overdue — N iterations since the last one. Run `/openup-retrospective`
> before starting `full`-track work (it resets the cadence). Or, if this work is genuinely
> lighter, re-run with `track: standard`.

**If `N >= 5` and the track is `quick`/`standard`:** proceed, but surface a **non-blocking**
reminder in your summary: "Heads-up: retrospective overdue (N since last) — consider running
`/openup-retrospective` soon." The hard gate intentionally targets only the heavy track
(WS6b); see [design.md](../../../../docs/changes/T-011/design.md) DD2.

(`gates.retro_due` is set to `N >= 5` by `retro check` in step 6 below — this step is the
human-facing decision; step 6 records the gate.)

### 4. Deploy Team — OPT-IN (default-on for `full` only)

**The default is solo, sequential work — one agent assumes roles as needed (analyst →
developer → tester) and persists progress to the repo between steps.** A team is deployed
only when the track or an explicit argument calls for it; you do not need a team to start.

Track determines the team default:
- **`quick`** ⇒ **no team** (proceed straight to step 5).
- **`standard`** ⇒ **no team by default** — work solo and sequentially. Deploy a team only
  if `$ARGUMENTS[team]` is set or `$ARGUMENTS[deploy_team]` is `"true"` (e.g. you want
  parallel specialists or independent review).
- **`full`** ⇒ **team default-on** — deploy the phase default unless `$ARGUMENTS[deploy_team]`
  is `"false"` or `$ARGUMENTS[team]` is `none`.

The explicit `$ARGUMENTS[deploy_team]` / `$ARGUMENTS[team]` args override the track default.
When a team IS deployed:

1. **Auto-select team type** if `$ARGUMENTS[team]` is not specified:
   - Check task description for keywords:
     - "investigate", "research", "spike" → `openup-investigation-team`
     - "plan", "roadmap", "prioritize" → `openup-planning-team`
   - Otherwise fall back to phase default:
     - `inception` → `openup-inception-team` (analyst + project-manager)
     - `elaboration` → `openup-elaboration-team` (architect + developer)
     - `construction` → `openup-construction-team` (developer + tester) ← most common
     - `transition` → `openup-transition-team` (developer + tester + project-manager)

2. **Team type override**: if `$ARGUMENTS[team]` is provided, use it directly:
   - **feature**: analyst, architect, developer, tester
   - **investigation**: architect, developer, tester
   - **construction**: developer, tester
   - **elaboration**: architect, developer, tester
   - **inception**: analyst, project-manager
   - **transition**: tester, project-manager, developer
   - **planning**: project-manager, analyst
   - **full**: all roles
   - **none**: skip team deployment (same as `deploy_team: false`)

3. Deploy the team using the Agent tool — spawn each role with:
   - Iteration goal and task ID
   - Current phase and phase objectives
   - Relevant project docs (project-status.md, roadmap.md)
   - The PM's orchestrator role: decompose the task, brief each specialist, collect and synthesize outputs

4. **PM takes the lead**: after spawning, the project-manager agent coordinates all subsequent work for this iteration. Specialists (developer, architect, tester, analyst) receive focused subtasks from the PM.

5. **Record the team gate** — once the team is up, flip the gate in iteration state (created in step 6 below; if the branch/state does not exist yet, do this right after step 6):

   ```bash
   python3 scripts/openup-state.py set-gate team_deployed true
   ```

### 5. Create Task Branch (+ Worktree, default-on)

**Worktree-per-task is the default** (T-009 design D6): each iteration gets an isolated
sibling worktree so parallel sessions never share a working tree. Pass `worktree: false`
to use a legacy in-place checkout (e.g. when a sibling path is impractical, or for a task
— like T-009 itself — that bootstraps the worktree feature).

```bash
# 1. Detect trunk
TRUNK=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
[ -z "$TRUNK" ] && TRUNK="main"
git rev-parse --verify "$TRUNK" 2>/dev/null || TRUNK="master"
REPO=$(basename "$(git rev-parse --show-toplevel)")
BRANCH={type}/{task_id}-{short-description}

# 2. Refresh trunk
git checkout "$TRUNK" && git pull origin "$TRUNK" 2>/dev/null || true

# 3a. DEFAULT (worktree-on): isolated worktree on a new branch (worktree FIRST — D6)
git worktree add "../${REPO}-{task_id}" -b "$BRANCH" "$TRUNK"
#    → continue all subsequent work inside ../${REPO}-{task_id}

# 3b. OPT-OUT (worktree: false): in-place branch
git checkout -b "$BRANCH"

# 4. VERIFY — this must NOT return trunk
git rev-parse --abbrev-ref HEAD
```

**If the branch already exists**, check its status:
- No unmerged commits → delete and recreate from trunk
- Has unmerged commits → create PR or merge first, then create new branch

### 6. Initialize Iteration State

Write the machine-readable iteration state file. This is what hooks read to enforce process gates (see [state-file.md](../../../../docs-eng-process/state-file.md)). Fill in the iteration's actual values — pass the **track selected in step 3** to `--track`:

```bash
python3 scripts/openup-state.py init \
  --task-id "{task_id}" \
  --iteration {iteration_number} \
  --phase {inception|elaboration|construction|transition} \
  --track {selected track: quick|standard|full} \
  --branch "$(git rev-parse --abbrev-ref HEAD)" \
  --worktree "$(git rev-parse --show-toplevel)" \
  --iterations-since-retro "$(python3 scripts/openup-state.py retro get)" \
  [--plan docs/plans/{plan}.md]    # standard/full only; the quick track has no plan gate
```

The `--iterations-since-retro` flag **seeds the new state's mirror from the durable
counter** (`.openup/retro.json`), carrying the cadence forward across the iteration that
`/openup-complete-task` archived. Then record `gates.retro_due` from the threshold:

```bash
python3 scripts/openup-state.py retro check   # sets gates.retro_due = (count >= 5)
```

If the team was already deployed in step 4, also run `python3 scripts/openup-state.py set-gate team_deployed true` now.

### 6b. Pre-flight + write the worktree claim

Live lease claims coordinate parallel sessions (one file per claim under
`<git-common-dir>/openup/claims/`, never committed). See
[parallel-work.md](../../../../docs-eng-process/parallel-work.md). The claim's collision
surface (`touches`) and `depends-on` come from the task's `docs/changes/{task_id}/plan.md`
frontmatter, so persist the plan **before** claiming.

The local lease is single-clone (it lives under `.git/`, never pushed). Step 0
adds the **cross-machine** early-warning (T-044): it asks the *remote* whether
another clone already pushed a branch for this task. It is **advisory and
fail-open** — a missing/unreachable remote exits `0` so solo/offline work is
never blocked; the local pre-flight below remains the hard gate.

```bash
# 0. REMOTE-CHECK (T-044): refuse early if another clone already owns this task on
#    origin. Exit 9 = remote duplicate; exit 0 = clear OR remote not consulted.
python3 scripts/openup-claims.py remote-check --task-id {task_id} \
  --self-branch "$(git rev-parse --abbrev-ref HEAD)"
if [ $? -eq 9 ]; then
  # Record the duplicate-start (clock-stamped; this is the counter that decides
  # whether the heavier atomic ref-lock, exploration Option A, is ever justified).
  python3 scripts/openup-state.py log-event --event duplicate_start_blocked \
    --task-id {task_id} --branch "$(git rev-parse --abbrev-ref HEAD)"
  echo "Remote duplicate — another clone owns {task_id}. Do NOT proceed."
  echo "Roll back this lane: git checkout \"$TRUNK\"; git branch -D \"$BRANCH\";"
  echo "  git worktree remove \"../\${REPO}-{task_id}\" 2>/dev/null || true"
  exit 1
fi

# 1. PRE-FLIGHT (read-only): refuse early on an unmet dependency or a touches collision
#    with a live claim. Exit 3 = unmet dep; exit 4 = collision (owner named); 0 = clear.
python3 scripts/openup-claims.py preflight --task-id {task_id} || {
  echo "Pre-flight refused — do NOT proceed. Resolve the dependency/collision above."; exit 1; }

# 2. WRITE THE CLAIM (worktree already created in step 5 — worktree-first, claim-second; D6).
#    On failure AFTER the worktree exists, roll back: git worktree remove "../${REPO}-{task_id}"
python3 scripts/openup-claims.py claim \
  --task-id {task_id} \
  --session-id "$(python3 scripts/openup-state.py get session_id 2>/dev/null || echo "$BRANCH")" \
  --branch "$(git rev-parse --abbrev-ref HEAD)" \
  --worktree "$(git rev-parse --show-toplevel)"
```

Claims **never expire** — an abandoned claim blocks its surface until a human removes the
file (`rm <git-common-dir>/openup/claims/{task_id}.json`); there is no TTL and no `--steal`.
`/openup-complete-task` releases the claim and removes the worktree.

### 7. Check for Answered Input Requests

Check `docs/input-requests/` for files with `status: answered`. Process any answered requests before continuing.

### 8. Initialize Iteration

> **Scribe step** — delegate to the `openup-scribe` agent (Agent tool,
> subagent_type: "openup-scribe"). You determine the values (iteration number,
> goal, task_id); the scribe only writes. Brief it with:
>
> ```
> Agent(subagent_type="openup-scribe", description="Initialize project-status for new iteration",
>   prompt="In docs/project-status.md update these fields:
>   - **Iteration**: [new number]
>   - **Iteration Goal**: [goal text]
>   - **Status**: in-progress
>   - **Current Task**: [task_id]
>   - **Iteration Started**: [YYYY-MM-DD]
>   - **Last Updated**: [YYYY-MM-DD]
>   - **Updated By**: openup-start-iteration
>   Report: each field changed from → to.")
> ```

### 9. Log Initialization

Append the `iteration_start` record with the **deterministic logger** — it stamps
`ts` from the system clock, so the model never authors a timestamp (the cause of
the fabricated round-number times the audit found). This is a script call, not a
scribe brief:

```bash
python3 scripts/openup-state.py log-event \
  --event iteration_start \
  --task-id "{task_id}" \
  --run-id "{run_id}" \
  --goal "{goal}" \
  --branch "$(git rev-parse --abbrev-ref HEAD)" \
  --phase "{phase}"
```

## Output

Returns a summary of:
- Current phase and iteration number
- Task being worked on (task_id, title)
- Iteration goal
- Active branch name (must be a non-trunk task branch)

## See Also

- [openup-next](../next/SKILL.md) - The sequential continue-loop; picks the top board lane and delegates here to claim + init it
- [openup-complete-task](../complete-task/SKILL.md) - Complete iteration tasks
- [openup-create-iteration-plan](../../openup-artifacts/create-iteration-plan/SKILL.md) - Plan iteration before starting

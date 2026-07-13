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
- [ ] **BLOCKING**: `git rev-parse --abbrev-ref HEAD` returns a non-trunk branch name. If it returns trunk, stop and report — do not proceed.
- [ ] Iteration goal is defined
- [ ] Answered input requests are processed
- [ ] Log entry is created
- [ ] `.openup/state.json` created

## Process

### 0a. Two modes — single-lane start vs Plan Iteration (T-077)

This skill has **two entry modes**, chosen by whether a concrete `task_id` was
handed in:

- **Single-lane start** (a `task_id` is given — a human names a task, or
  `/openup-next` resolved one lane). This is the classic flow: steps 0–9 below
  create a branch/worktree for that one task and begin it. **Unchanged.**
- **Plan Iteration** (no `task_id` — the board's `plan-iteration` decision, or a
  human running `/openup-start-iteration` with no argument). Instead of starting
  one hand-named task, **plan a phase-appropriate iteration**: derive the phase,
  mint an iteration id, choose 1–5 objectives, and generate the iteration's
  work-item lanes *from the process map* — then start its first lane through the
  single-lane flow. Run **§0b**, then rejoin at step 3.

The guard is exactly step 0's guard (*was I handed a `task_id`?*), extended: no
`task_id` **and** no pre-resolved lane ⇒ Plan Iteration (§0b).

### 0b. Plan Iteration — generate phase-appropriate lanes from the map (T-077)

Real **Plan Iteration** (KB §3): commit a set of work items to a named iteration
instead of promoting one roadmap row. Everything deterministic is a script call;
the only generative step is choosing objectives (the PM/analyst judgment the KB
assigns to a human role).

1. **Derive the phase** (never guess it):
   ```bash
   PHASE=$(python3 scripts/openup-lifecycle.py status --json | python3 -c 'import sys,json;print(json.load(sys.stdin)["phase"])')
   ```

2. **Read the Development Case** (T-076 tailoring) from `docs/project-config.yaml`
   `process:` — the archetype sets iteration budget + ceremony. **If the archetype
   resolves to `quick`, or this phase is `skipped`/single-iteration: degenerate to
   one work item** — take the board's `lane.task` (the `plan-iteration` decision's
   single next roadmap task) and go straight to the single-lane flow (step 3).
   This is the efficiency guardrail: `quick` costs exactly today's promote path.

3. **Mint the iteration id** and record it:
   ```bash
   ITER=$(python3 scripts/openup-process-map.py mint-iteration-id "$PHASE")   # e.g. C3
   ```

4. **Choose 1–5 objectives** (the generative step) from, in order: the **risk
   list** (highest-exposure items first), the **PM value order** (roadmap pending
   order — consume as given, never re-rank), and the **phase's objectives**. Keep
   it to what one iteration can deliver.

5. **Read the phase's activity composition** from the process map:
   ```bash
   python3 scripts/openup-process-map.py activities-for "$PHASE" --json
   ```
   Each entry is `{name, role, skills}` — the ordered activities OpenUP runs in
   this phase (Inception → vision/use-case/risk with `analyst`; Elaboration →
   architecture/increment/test; Construction → dev/test; per KB §4).

6. **Sketch the candidate work items** — one per activity needed to meet the
   objectives — deciding each one's planned `touches` and `depends-on` (you must
   know these to author its spec anyway). Give each a neutral placeholder id for
   now (`wi-1`, `wi-2`, …); the real cluster-prefixed id is assigned in step 6b
   once the partition is known.

6a. **Partition the candidates into non-colliding clusters (T-079).** Feed the
   sketched items to the partitioner — it returns the **connected components** of
   the `touches`-overlap ∪ `depends-on` graph, so distinct clusters are disjoint
   in `touches` and dependency-free across clusters, hence safe to run as
   **concurrent iterations**:
   ```bash
   echo '[{"id":"wi-1","touches":["scripts/x.py"],"depends-on":[]}, …]' \
     | python3 scripts/openup-board.py partition --stdin
   # → [["wi-1","wi-2"],["wi-3"]]   (one inner list per cluster)
   ```
   A **single** returned cluster is the common case (the `quick` archetype's
   single work item is always one cluster) — it degenerates to exactly T-077's
   one-iteration behavior. Parallelism appears **only** when the work is genuinely
   disjoint; it is discovered from the structure of the work, never forced.

6b. **Mint one named iteration per cluster and author its lanes.** The base
   `mint-iteration-id` result (`$ITER`, e.g. `C3`) is the **first** cluster's id;
   derive each subsequent cluster's id by **offsetting the ordinal by the cluster
   index** (`C3`, `C4`, `C5`, …) — a deterministic rule that needs no lane
   persisted between mints. For each cluster, in the base checkout (so the board
   sees the lanes, like the promote path):
   - reserve each member's id **under that cluster's prefix**:
     `python3 scripts/openup-claims.py reserve-id --prefix "${CLUSTER_ITER}-" --pad 3 --session-id "$CLUSTER_ITER"` → `C3-001…`, `C4-001…`
   - author its change-folder spec through the activity's own skill
     (`/openup-create-task-spec` for change tasks; the activity `skills:` — e.g.
     `/openup-create-use-case`, `/openup-create-architecture-notebook` — for
     requirements/architecture work), with the activity `role` recorded as the
     lane's **hat** in `## Operations`.
   - add its roadmap row (on the base, committed with the spec folder — same
     rule as step 6c: spec folder only, never the derived views).

7. **Author one iteration-plan instance per cluster** —
   `/openup-create-iteration-plan` — each recording its **minted iteration id**,
   the objectives it serves, its committed work-item ids (`C3-001…` / `C4-001…`),
   and its **evaluation criteria**. Each instance is the loop contract (§3.5) for
   its iteration; the iteration id lives here (state carries only the *active*
   lane's `iteration_id`, schema 2 — T-078).

8. **Start the first lane of the first cluster** through the single-lane flow: set
   `task_id` to that cluster's first committed work item and continue at **step 3**
   (track select) → §5 (branch/worktree) → §6 (begin). Every other lane — in this
   cluster and the others — is a READY change folder the board picks next.
   - **Within** one active iteration the board's **iteration-scoped `pick`** works
     only that iteration's lanes.
   - **Across** clusters, the moment a second cluster's lane also holds a live
     lease the board **un-scopes** (`_active_iteration_prefix` → `None`) and picks
     the top collision-free lane across both — so disjoint clusters run
     **concurrently**, each lane in its **own worktree** (branch-per-lane =
     worktree-per-lane isolation, live-run F5; see
     [parallel-lanes.md](../parallel-lanes.md)). An outer `/loop` or a second
     agent begins the other cluster's first lane to actually parallelize.

> **Concurrency is opt-in-by-structure.** With one cluster this is exactly T-077
> (one iteration, one prefix, sequential). N iterations appear only when the
> committed work items partition into ≥2 non-colliding clusters — no human
> hand-wires the parallelism, and cross-iteration task ids never collide because
> each carries its own iteration prefix.

### 0. Pre-resolved lane? Skip the re-read (T-065)

When `/openup-next` calls this skill it has **already** resolved the lane in one
`openup-board.py resolve` call — the `task_id` and `track` you were handed *are*
the decision. In that case **skip steps 1–2's re-read**: do not re-open
`docs/project-status.md` to find the phase/iteration or `docs/roadmap.md` to
"find the task" — you already have both. Read the phase + iteration number once,
cheaply, from state (`python3 scripts/openup-state.py get phase` is unavailable
pre-init, so take them from the caller / the task's `docs/changes/<id>/plan.md`),
and go straight to step 3 (track is given) → step 5 (branch/worktree).

Only when invoked **standalone** (a human runs `/openup-start-iteration` with no
pre-resolved lane, or `task_id` is absent) do steps 1–2 below self-brief by
reading status + roadmap. The guard is simply: *was I handed a `task_id`?* If
yes, trust it; if no, read to discover it.

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

### 6. Acquire the Session — one atomic `begin` (T-063)

`openup-session.py begin` folds the entire acquire chain into **one** call:
stale-lease reap-warn → remote-check (T-044) → pre-flight + claim → heartbeat →
iteration-state init → `session_begin` log. If any step **after** the claim fails it
rolls the claim back (release), so a partial begin never strands a half-acquired lane
(Requirement 2). This replaces the former six-call §6/§6b sequence — the individual
`openup-claims.py`/`openup-state.py` verbs still exist for direct use, but the skill no
longer sequences them by hand.

The **git worktree was already created in step 5** (worktree-first, claim-second) and
worktree creation stays there — `begin` owns only claim + state + log. The claim's
collision surface (`touches`) and `depends-on` are read from
`docs/changes/{task_id}/plan.md` frontmatter, so persist the plan **before** `begin`. Pass
the **track selected in step 3** to `--track`. See
[parallel-work.md](../../../../docs-eng-process/parallel-work.md).

```bash
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
python3 scripts/openup-session.py begin \
  --task-id "{task_id}" \
  --iteration {iteration_number} \
  --phase {inception|elaboration|construction|transition} \
  --track {selected track: quick|standard|full} \
  --branch "$BRANCH" \
  --worktree "$(git rev-parse --show-toplevel)" \
  --session-id "$BRANCH" \
  --iterations-since-retro "$(python3 scripts/openup-state.py retro get)" \
  --goal "{goal}" \
  --run-id "{run_id}" \
  [--plan docs/plans/{plan}.md]    # standard/full only; the quick track has no plan gate
rc=$?
if [ "$rc" -eq 9 ]; then
  # Remote duplicate (T-044): another clone already owns this task on origin. Record the
  # counter event (clock-stamped — decides whether the heavier atomic ref-lock is ever
  # justified), then roll the local lane back. Do NOT proceed.
  python3 scripts/openup-state.py log-event --event duplicate_start_blocked \
    --task-id {task_id} --branch "$BRANCH"
  echo "Remote duplicate — another clone owns {task_id}. Do NOT proceed."
  echo "Roll back this lane: git checkout \"$TRUNK\"; git branch -D \"$BRANCH\";"
  echo "  git worktree remove \"../\${REPO}-{task_id}\" 2>/dev/null || true"
  exit 1
elif [ "$rc" -ne 0 ]; then
  # Pre-flight refused (exit 3 unmet dep / 4 collision) or a post-claim step failed
  # (begin already released the claim). Resolve the cause above, then roll back the
  # worktree: git worktree remove "../${REPO}-{task_id}"
  echo "begin refused (code $rc) — do NOT proceed. Resolve the dependency/collision above."
  exit 1
fi

# begin seeded the retro INPUT (--iterations-since-retro); stamp the gate itself:
python3 scripts/openup-state.py retro check   # sets gates.retro_due = (count >= 5)
```

The `--iterations-since-retro` flag **seeds the new state's mirror from the durable
counter** (`.openup/retro.json`), carrying the cadence forward across the iteration that
`/openup-complete-task` archived. If the team was already deployed in step 4, also run
`python3 scripts/openup-state.py set-gate team_deployed true` now.

Claims **never expire on their own**, but a heartbeat-stale claim now self-heals: it is
reaped by `openup-board.py refresh` (and warned about by the next `begin`). An abandoned
claim otherwise blocks its surface until a human removes
`<git-common-dir>/openup/claims/{task_id}.json`. `/openup-complete-task`'s `end` releases
the claim and removes the worktree.

### 6c. Commit the promoted spec — make the lane durable + board-visible (T-048)

**When this start promoted a task into a new lane** (the spec `docs/changes/{task_id}/`
was just authored — the `/openup-next` promote path, or any first-time start), commit it
now. `openup-board.py` reads the working tree, so a spec left only as **uncommitted
worktree files** is invisible from trunk and from every other worktree/machine — a
"botched promote" that strands the lane and costs a recovery session. Committing here is
what makes the lane survive in git.

```bash
# Stage ONLY the spec folder — never docs/roadmap.md or docs/project-status.md.
# Those are derived shared views regenerated by sync-status.py; committing them
# here (on main, before the worktree branch exists) would push a roadmap row
# directly to trunk and cause a merge conflict when the task branch PR lands.
# The roadmap row for this task is added on the task branch (in the worktree),
# not on main — it reaches trunk through the normal PR merge.
# (.openup/ is gitignored Ring-3 state — NOT committed.)
git add "docs/changes/{task_id}/" 2>/dev/null || true
if ! git diff --cached --quiet; then
  git commit -m "docs({task_id}): promote lane — author spec, board-visible [{task_id}]"
fi
# Verify: the spec is committed (not dangling) and the board sees the lane.
git status --porcelain "docs/changes/{task_id}/"   # expect empty for the spec
```

If the spec was **already committed** before this start (e.g. registered in a prior
session / PR), this step is a no-op — `git diff --cached --quiet` short-circuits.

### 7. Check for Answered Input Requests

Check `docs/input-requests/` for files with `status: answered`. Process any answered requests before continuing.

### 8. Initialize Iteration

> **`docs/project-status.md` is a derived shared view — do NOT scribe-edit it here.**
> `sync-status.py` is the sole writer; any edit made directly on main (or before the
> worktree branch exists) diverges from the PR copy and causes a merge conflict at push.
> (Root cause fixed in the local-main conflict after T-056 — see iteration learnings.)
>
> The iteration goal and task ID are already captured in `.openup/state.json` (step 6)
> and in the run log (step 9). No further write is needed at start time; the status
> header is regenerated by `sync-status.py` at `/openup-complete-task`.

### 9. Log Initialization

**Already done by `begin` (step 6).** The `session_begin` record — carrying the
`--goal`, `--run-id`, `--branch`, and `--phase` passed to `begin` — is appended by the
**deterministic logger** inside `openup-session.py begin`, which stamps `ts` from the
system clock (the model never authors a timestamp). No separate log call is needed here;
this step is retained only as the map from the former standalone `iteration_start` log to
the folded `session_begin` event.

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

# Process v2: Mechanize OpenUP for the Claude Code Harness

**Status**: `completed` (2026-06-11 — T-004…T-011 + T-002 delivered)
**Created**: 2026-06-10
**Priority**: high
**Goal**: Replace prose-based process enforcement with harness mechanisms (frontmatter, hooks, state files, worktrees) so adherence stops depending on the model remembering instructions.

---

## Context

OpenUP-for-AI-agents works: the Kaze webapp shipped 84 tasks across 53 iterations in 77 days with 85–97% test coverage and only 8 merge conflicts. But an empirical audit of that project (2026-06-10, full report summarized below) shows that **every part of the process that is structural held up, and every part that is prose-only decayed**:

| Evidence from Kaze (620 commits, 88 logged runs) | Root cause |
|---|---|
| 4.4% of commits carry the prescribed `[T-XXX]` tag; 18.5% strict format compliance | `validate-commit.py` exists but format/tag rules are not enforced end-to-end |
| ~39% of runs have no markdown log; iterations 43–52 entirely unlogged | Log writing is a prose instruction ("Haiku/Scribe step"), not a mechanism |
| Roadmap said `pending` for T-015 while iteration 53 was actively building it | Status transitions are manual edits to two markdown files that drift |
| 1 Haiku run vs 64 Opus/Sonnet runs — zero model tiering despite the mandatory protocol | "Use lightweight models for coordination" is a bullet in CLAUDE.openup.md, not a `model:` field |
| 25/27 iteration plans never updated after creation; decisions landed in commit messages | No gate ties plan updates to behavior changes |
| All 8 merge conflicts were in shared process docs (`agent-runs.jsonl`, `roadmap.md`) | Append-to-one-shared-file design collides under parallel work |
| Retro cadence "every 3–5 iterations" → one 26-iteration gap | Cadence is a convention with no trigger |

The 2026 AI-agent SDLC landscape (AWS AI-DLC, GitHub Spec Kit, OpenSpec, BMAD, Kiro) converged on the same three principles this plan adopts:

1. **If a step is deterministic, the harness does it** — scripts paired with prompts (Spec Kit), not requests to the model.
2. **If a step needs the model, a gate verifies it** — blocking hooks reading machine-readable state, not "⛔ STOP" prose.
3. **Context is scoped per unit of work** — product truth vs. change folders vs. session debris (OpenSpec `specs/`–`changes/` split, Kiro per-feature folders).

Claude Code now natively supports the mechanisms this needs: `model:` in SKILL.md and subagent frontmatter, `context: fork` + `agent:` skill delegation, blocking hook exit codes on `PreToolUse`/`Stop`, and first-class worktrees.

This plan supersedes nothing; it absorbs items #1–#4 of [2026-05-13-openspec-ideas-for-openup.md](2026-05-13-openspec-ideas-for-openup.md) into a larger program and un-defers the precondition for T-002 (`/openup-sync-spec`).

---

## Current State

### Model routing is prose (`.claude/skills/openup-workflow/log-run/SKILL.md`)

```markdown
> **Haiku/Scribe step** — this entire skill is mechanical. Spawn a Haiku sub-agent with
> the scribe role to execute it. Brief template:
>
>   Agent(model="haiku", description="Write agent run log", ...)
```

No skill in `.claude/skills/` declares `model:` in frontmatter. There is no `.claude/agents/` directory — the scribe exists only as an inline prompt template the orchestrator may or may not follow. Kaze data: it followed it once in 88 runs.

### Enforcement is advisory (`.claude/scripts/hooks/check-iteration.py`)

```python
Intercepts `git commit` commands and verifies the agent is working inside
an active OpenUP iteration. Emits a strong warning if not, but does NOT
block — the commit proceeds.
...
sys.exit(0)  # Warn but do not block
```

Of the 7 hooks wired in `.claude/settings.json`, only `validate-commit.py` can block (exit 2). Nothing gates `Edit`/`Write` — an agent can modify code with no iteration, no branch, and no plan, receiving at most a stderr warning it is free to ignore.

### State is parsed from prose (`check-iteration.py`)

```python
def parse_project_status(path: Path) -> dict[str, str]:
    ...
    m = re.match(r"\*\*(.+?)\*\*:\s*(.*)", line)
```

Hooks regex-parse `docs/project-status.md` markdown to discover iteration state. There is no machine-readable record of what the current iteration has and hasn't done (branch created? plan persisted? log written? roadmap synced?).

### Logging requires the model to remember

`openup-log-run` must be invoked explicitly after commits. The JSONL append and markdown log are model-executed writes. Nothing detects "commits exist but no log was written" — which is exactly the 39% gap Kaze shows.

### Docs have two scopes where three are needed

`docs/` mixes product truth (vision, use cases), planning inputs (`docs/plans/`, flat), and per-task artifacts (`docs/tasks/T-NNN-*.md`, flat files). Iteration-scoped debris lands wherever the session puts it. The OpenSpec analysis already identified per-change folders (#3) and archive-on-complete (#4) as the fix; both are still `proposed`.

### Parallelism is unsupported

`/openup-start-iteration` does `git checkout -b` in place — one task per checkout. No claims, no ownership field anywhere in task frontmatter (`claimed_by` does not exist), no collision pre-check. Kaze's only merge conflicts were two sessions appending to the same `agent-runs.jsonl` and `roadmap.md`.

---

## Proposed Design

Six workstreams, ordered so each builds on the previous.

### WS1 — Model tiering via frontmatter (T-004)

**1a. Stamp `model:` into every SKILL.md** according to a tier map committed at `docs-eng-process/model-tiers.md`:

| Tier | Model | Skills |
|---|---|---|
| Scribe (mechanical writes) | `haiku` | `openup-log-run`, `openup-request-input`, roadmap/status update steps |
| Coordination (read, route, summarize) | `haiku` | `openup-start-iteration`, `openup-phase-review`, `openup-assess-completeness`, `openup-retrospective` |
| Authoring (artifact generation against rubric) | `inherit` | `openup-create-use-case`, `openup-create-test-plan`, `openup-create-vision`, `openup-plan-feature` |
| Reasoning (architecture, decomposition, code) | `inherit` | `openup-create-architecture-notebook`, `openup-orchestrate`, `openup-tdd-workflow` |

Example (`openup-log-run`):

```yaml
---
name: openup-log-run
description: Create traceability logs (markdown + JSONL) for the current agent run
model: haiku
---
```

**1b. Create real subagent definitions** in `.claude/agents/`, replacing inline prompt templates:

```yaml
# .claude/agents/openup-scribe.md
---
name: openup-scribe
description: Mechanical writer for logs, status updates, and roadmap entries. Never makes decisions.
model: haiku
tools: Read, Write, Edit, Bash
---
You are the OpenUP Scribe. You receive fully-specified write instructions
(paths, content, schemas) and execute them exactly. If any required field
is missing, report the gap — do not invent values.
```

Plus `openup-explorer.md` (`model: haiku`, read-only tools) for context-gathering steps. Skills then say "delegate to the `openup-scribe` agent" — a definition the harness resolves, not a convention.

**1c. Team configs gain explicit per-role models** — `model: haiku` for project-manager coordination lanes, `inherit` for developer/architect — replacing the "model tiering" prose bullet.

### WS2 — Machine-readable iteration state (T-005)

A single state file written by skills and read by hooks. Lives in the worktree, gitignored:

```json
// .openup/state.json
{
  "schema": 1,
  "task_id": "T-015",
  "iteration": 53,
  "phase": "construction",
  "track": "standard",            // quick | standard | full  (see WS6)
  "branch": "feature/T-015-external-agent-api",
  "worktree": "/abs/path",
  "session_id": "<claude session id>",
  "started_at": "2026-06-10T09:00:00Z",
  "gates": {
    "team_deployed": true,
    "plan_persisted": "docs/changes/T-015/plan.md",
    "log_written": false,
    "roadmap_synced": false,
    "retro_due": false
  },
  "iterations_since_retro": 3
}
```

`/openup-start-iteration` creates it; every workflow skill updates its own gate; `/openup-complete-task` requires all gates true and archives the file into the change folder. Hooks stop regex-parsing `project-status.md` (it becomes a generated view, see WS3).

### WS3 — Blocking gates + mechanical steps (T-006)

The adherence core. Three changes to `.claude/scripts/hooks/` + `settings.json`:

**3a. Gate edits.** New `PreToolUse` hook on `Edit|Write|NotebookEdit` (`gate-edits.py`): if the target is product/source code (not `docs/explorations/`, not `.openup/`) and `.openup/state.json` is absent or `gates.plan_persisted` is false → **exit 2** with the same redirect message `check-iteration.py` prints today. `[openup-skip]` escape hatch remains, audited in `bypass-log.md`. Quick-track tasks (WS6) get a relaxed gate (state file required, plan not).

**3b. Make logging deterministic.** New `PostToolUse` Bash hook (`auto-log-commit.py`): on a successful `git commit`, append the JSONL record to the run log **itself** — schema-validated, with `session_id`, model, branch, SHA, task_id from state. The model never writes JSONL again; `openup-log-run` shrinks to the markdown narrative (decisions, surprises) that genuinely needs a model. This single hook erases Kaze's 39% gap and its 13.6% malformed-`agent`-field problem.

**3c. Give Stop teeth.** `on-stop.py` upgrades from informational to blocking: if state shows commits this session but `gates.log_written` is false, or `gates.roadmap_synced` is false after a `task completed` event → return the hook decision that blocks stop with the specific unmet gate. Same for `validate-commit.py`: `[T-XXX]` tag becomes mandatory (exit 2) when `.openup/state.json` has a `task_id`, auto-suggesting the correct tag in the error.

**3d. Sync, don't remind.** `roadmap_synced` is set by a script (`scripts/sync-status.py`, callable by hook or scribe) that flips the task's status field in its frontmatter and regenerates `docs/project-status.md` from state + roadmap — one source of truth, two views. The Kaze "pending vs in-progress" contradiction becomes unrepresentable.

### WS4 — Three-ring docs scoping (T-007, absorbs OpenSpec #3 + #4)

```
docs/
├── product/            # Ring 1: what IS true now (vision, architecture, use-cases, product docs)
├── roadmap.md          # live board (status frontmatter per task, see WS5) — STAYS in place
├── project-status.md   # generated view of state + roadmap (WS3) — STAYS in place
├── plans/              # program-level / multi-task plans that SEED changes — STAYS in place
├── changes/            # Ring 2: one folder per change — inputs, not truth
│   └── T-015/
│       ├── plan.md         # the REASONS spec / iteration plan for THIS change
│       ├── design.md       # decisions made during execution (living)
│       ├── inputs/         # examples, ideas, references seeding the work
│       ├── test-notes.md
│       └── state.json      # archived .openup/state.json on completion
├── changes/archive/    # completed change folders, moved by /openup-complete-task
├── agent-logs/         # durable, committed audit trail (JSONL + markdown) — STAYS in place
└── explorations/       # pre-iteration notes (existing)
# Ring 3 (ephemeral session state, never committed to docs/): .openup/state.json + .claude/memory/
```

**Decided during T-007 (2026-06-11) — refinements to the sketch above:**
- **`docs/agent-logs/` is durable traceability, not Ring 3.** It is the committed audit trail that `auto-log-commit.py` appends to and `on-stop.py` exempts (WS3). Ring 3 ("session debris, never in `docs/`") means only the *ephemeral* `.openup/state.json` and `.claude/memory/` — not the audit log. Moving the audit log would re-open the 39% logging-gap that WS3 closed.
- **`docs/plans/` stays in place.** The 5 program-level plans span multiple tasks (the Process v2 program seeds T-004…T-011); they are planning *inputs* that seed change folders, not a single change. `on-plan-exit.py` saves new plans here. Per-change planning lives in `changes/T-NNN/plan.md`; program plans remain in `docs/plans/`.
- **`docs/project-status.md` and `docs/roadmap.md` stay in place** (Open Question #3: keep project-status as a generated view). Because they don't move, the apparent 150+/50+ reference blast radius is inert — the real migration surface is `docs/tasks/` (~10 refs) plus skill context-loading guidance.

Migration is mechanical (`git mv` + link rewrite). What actually moves in T-007: create `product/`, `changes/`, `changes/archive/`; migrate `docs/tasks/T-NNN-*.md` → `changes/[archive/]T-NNN/plan.md` (done/verified tasks straight to `archive/`). Skills that load context get the corresponding update: brief a specialist with **Ring 1 + one change folder**, not "scan all of `docs/`". On completion, durable outcomes merge into Ring 1 (the "fix-spec-first" rule already mandates this direction); the change folder archives. Plans stop going stale because `design.md` is the sanctioned place for mid-execution decisions — fixing Kaze's 25/27 frozen plans.

### WS5 — Readiness DAG + claims + worktrees (T-008, T-009; absorbs OpenSpec #1)

**5a. Task frontmatter** (in `docs/changes/T-NNN/plan.md`) gains coordination fields:

```yaml
---
id: T-016
status: ready          # proposed | ready | blocked | in-progress | done | verified
depends_on: [T-005]
touches: [".claude/scripts/hooks/", ".claude/settings.json"]   # declared collision surface
claimed_by: null       # session id, set on claim
claimed_at: null       # lease timestamp; stale after 24h
worktree: null
---
```

**5b. `/openup-readiness`** (new skill, `model: haiku`): computes the DAG, prints READY/BLOCKED per task, flags `touches` overlaps between READY tasks and active claims. PM intake becomes a query. This is the precondition that un-defers T-002 (`/openup-sync-spec`).

**5c. Worktree-per-task.** `/openup-start-iteration` gains `worktree: true` (default once stable): creates `../<repo>-T-NNN` via `git worktree add`, writes the claim. Claims are **leases, one file per claim**, stored in `.git/openup/claims/T-NNN.json` — the git common dir is shared across all worktrees but never committed, so parallel sessions coordinate without touching a shared markdown file. (Kaze evidence: shared-file appends were the *only* source of merge conflicts.) Pre-flight: refuse to claim if `depends_on` unmet or `touches` overlaps a live claim; print which session owns the conflict. `/openup-complete-task` releases the claim and removes the worktree.

### WS6 — Graded tracks + cadence triggers (T-010, T-011)

**6a. Three tracks instead of the quick/full binary** (BMAD's planning-track idea, AI-DLC's adaptive ceremony). Declared in `state.json.track`, selected by `/openup-start-iteration` from declared scope:

| Track | When | Ceremony |
|---|---|---|
| `quick` | docs/config/typo, ≤ ~50 LOC | state file + auto-log only; no plan gate, no team |
| `standard` | single-feature work | plan gate + scribe logging + readiness check |
| `full` | multi-role / architectural | standard + team deployment + rubric assessment |

Kaze data (4 quick-task uses in 77 days; 18% of commits bypassing process entirely) says the lightweight path must be the *default* for small work, not an opt-in — `on-task-request.py` suggests the track in its intake message.

**6b. Retro trigger.** `iterations_since_retro` increments in state on each completion; at ≥ 5, `start-iteration` sets `gates.retro_due` and refuses `full`-track starts until `/openup-retrospective` runs (scribe-assisted, `model: haiku` for collection). Kills the 26-iteration retro gap class.

**6c. `/openup-create-handoff`** (new skill): codifies the handoff-brief pattern that emerged organically in Kaze T-015 (acceptance criteria, test cases, troubleshooting, open questions) — promoted because it proved itself unprompted.

---

## Task Decomposition

| ID | Title | Workstream | Priority | Depends on | Est. |
|---|---|---|---|---|---|
| T-004 | Model tier map + `model:` frontmatter sweep + `.claude/agents/` scribe & explorer | WS1 | high | — | 1 session |
| T-005 | `.openup/state.json` schema + skill read/write integration | WS2 | high | — | 1–2 sessions |
| T-006 | Blocking gates: `gate-edits.py`, `auto-log-commit.py`, blocking `on-stop`, `[T-XXX]` enforcement, `sync-status.py` | WS3 | high | T-005 | 2 sessions |
| T-007 | Three-ring docs migration + archive-on-complete + context-loading updates in skills | WS4 | medium | — | 1–2 sessions |
| T-008 | Coordination frontmatter + `/openup-readiness` DAG skill | WS5 | medium | T-007 | 1 session |
| T-009 | Worktree-per-task + lease claims in `.git/openup/claims/` + pre-flight collision check | WS5 | medium | T-005, T-008 | 2 sessions |
| T-010 | Graded tracks (quick/standard/full) in state + intake routing | WS6 | medium | T-005, T-006 | 1 session |
| T-011 | Retro cadence trigger + `/openup-create-handoff` | WS6 | low | T-005 | 1 session |

**Wave sequencing** (waves are internally parallelizable once T-009 lands; until then, sequential):

1. **Wave 1**: T-004 (immediate cost win, zero risk) → T-005 (foundation)
2. **Wave 2**: T-006 (the adherence payoff) ∥ T-007 (independent)
3. **Wave 3**: T-008 → T-009 (parallel work unlocked here)
4. **Wave 4**: T-010 ∥ T-011; then revisit deferred T-002 (`/openup-sync-spec`), now unblocked by T-008

---

## Acceptance Criteria (program level)

- [ ] Every SKILL.md declares `model:`; `openup-log-run` and scribe-delegated steps run on Haiku without prose reminders (verify: spawn logs show model per skill)
- [ ] An `Edit` to source code with no active iteration state is **blocked** (exit 2), with `[openup-skip]` bypass audited
- [ ] A `git commit` in an active iteration auto-appends a schema-valid JSONL record — zero model involvement (verify: delete the instruction from the skill, record still appears)
- [ ] `git commit` without `[T-XXX]` while state has a task_id is rejected with the correct tag suggested
- [ ] Session cannot Stop with commits made and `log_written: false`
- [ ] Roadmap task status and `project-status.md` cannot disagree (status generated from one source)
- [ ] Two simultaneous sessions on disjoint tasks run in separate worktrees with visible claims; claiming an overlapping task is refused with the owning session named
- [ ] `/openup-readiness` lists READY/BLOCKED with dependency reasons
- [ ] A 6th iteration without a retrospective refuses to start in `full` track
- [ ] Kaze-style re-audit after 4 weeks of dogfooding shows: task-tag compliance > 95%, unlogged-run gap < 5%, zero roadmap/status contradictions

## Key Files

| File | Change |
|---|---|
| `.claude/skills/**/SKILL.md` | `model:` frontmatter; scribe delegation rewritten to reference `.claude/agents/openup-scribe.md`; context-loading paths for three rings |
| `.claude/agents/openup-scribe.md`, `openup-explorer.md` | new subagent definitions |
| `.claude/scripts/hooks/gate-edits.py`, `auto-log-commit.py` | new blocking/mechanical hooks |
| `.claude/scripts/hooks/check-iteration.py`, `on-stop.py`, `validate-commit.py` | upgrade to state-file reads; blocking behavior |
| `.claude/settings.json` | wire new hooks (`Edit\|Write\|NotebookEdit` matcher, PostToolUse Bash) |
| `scripts/sync-status.py` | roadmap/status single-source generator |
| `docs/` tree | three-ring migration (`product/`, `changes/`, `changes/archive/`) |
| `.claude/skills/openup-readiness/`, `openup-create-handoff/` | new skills |
| `docs-eng-process/model-tiers.md`, `parallel-work.md` | new process docs |
| `docs-eng-process/.claude-templates/` | mirror all `.claude/` changes (template sync hook covers this) |

## Out of Scope

- `/openup-sync-spec` (T-002) itself — un-deferred by this program but executed separately after T-008
- Cross-machine parallel work (claims in `.git/openup/` are single-host; a committed claims dir is a future option)
- Retrofitting Kaze or other consumer projects (they adopt by re-syncing templates; a migration note ships with T-007)
- CI-side enforcement (server-side commit checks) — local hooks first

## Open Questions

1. **Quick-track gate strictness** — should `quick` track also skip the `[T-XXX]` commit requirement (auto-generating a `QT-NNN` id instead), or is a real task id always required? Kaze's 18% direct-to-main suggests friction must be near zero or the path gets bypassed.
2. **Claims TTL** — 24h lease expiry proposed; is a stale-claim override (`--steal` with audit) needed for crashed sessions, or is manual `rm` acceptable?
3. **`project-status.md` fate** — keep as generated view (for humans/old hooks) or delete once all hooks read `state.json`? Proposal: keep one release as deprecated view, then remove.
4. **Where rubric assessment runs in tracks** — `standard` track currently keeps rubric checks only for artifacts; should code-bearing standard tasks require `/openup-assess-completeness` before complete-task, or is that `full`-only?

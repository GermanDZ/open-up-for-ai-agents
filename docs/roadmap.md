# Roadmap


### Maintenance (standalone fixes)

| ID | Title | Status | Priority | Depends on |
|---|---|---|---|---|
| [T-046](changes/archive/T-046/plan.md) | Shard `agent-runs.jsonl` into lane-owned files; derive the consolidated view (kills GitHub-side PR conflicts merge=union can't) | completed (2026-06-16) | medium | T-023 |
| [T-044](changes/archive/T-044/plan.md) | Remote-aware claim preflight for `openup-next` (Option B: branch-as-claim) — cross-machine duplicate-start early-warning + counter | completed (2026-06-16) | high | T-009 |
| [T-022](changes/archive/T-022/plan.md) | Fix template→.claude sync (flat skills + rubric/hook coverage) + auto-commit log tail at stop | completed (2026-06-12) | high | — |
| T-023 | `merge=union` gitattribute for `agent-runs.jsonl` (parallel-PR conflict quick fix) | completed (2026-06-12) | medium | — |
| [T-024](changes/archive/T-024/plan.md) | Write-fence + derived shared views (parallel-PR conflicts in roadmap/status) | completed (2026-06-12) | high | — |
| [T-031](changes/archive/T-031/plan.md) | Task-ID allocation race in parallel lanes: reserve IDs through the claims mechanism in `create-task-spec` / `plan-feature` | completed (2026-06-12) | medium | — |
| [T-032](changes/archive/T-032/plan.md) | Install scripts must ship the process CLIs (`scripts/openup-*.py`) so a bootstrapped project can actually run the workflow | completed (2026-06-14) | high | — |
| [T-033](changes/archive/T-033/plan.md) | Autonomous continue-loop: suspend a lane on a blocking input-request and auto-resume it when answered (board `suspended` state + `/openup-next` runs Step-0 answered-check first) | completed (2026-06-14) | high | — |
| [T-040](changes/archive/T-040/plan.md) | Fix hook-test `HOOKS_DIR` stale path (`.claude/scripts/hooks/` → `docs-eng-process/.claude-templates/scripts/hooks/` after T-022) | completed (2026-06-15) | medium | — |
| [T-041](changes/archive/T-041/plan.md) | OpenUP audit remediation: 8 fixes from the es-invoices session/log audit (clock-stamped `log-event`, agent install, spine track, worktree-aware gate, plan-mode exemption, CLI reference, next-loop guidance, canonical bootstrap commit) | completed (2026-06-15) | high | — |
| [T-042](changes/archive/T-042/plan.md) | Retro-surfaced fixes: sync-status single-pass completion, quick-track unfenced lanes, worktree-aware audit hooks (auto-log-commit + on-stop), complete-task status flip | completed (2026-06-15) | high | T-041 |

**Value (T-032, T-033)**: T-032 makes a bootstrapped/synced project runnable out of
the box — every install path ships the `scripts/openup-*.py` runtime from one
manifest, so `/openup-start-iteration`, `/openup-next`, and `/openup-complete-task`
work without hand-copying CLIs. T-033 makes the autonomous loop first-class: a lane
suspends on a blocking question (board `suspended` state) and `/openup-next` resumes
it deterministically once answered (`openup-input.py resumable` + Step-0 check),
instead of relying on the agent to grep and remember each cycle.

**Value (T-031)**: parallel planning sessions — human or agent — stop colliding on
task IDs, eliminating renumber-at-merge churn like the practice pack's T-024→T-025…T-030
shift; closes the one parallel-lane collision surface the T-024 write-fence does not
cover (IDs are allocated at planning time against possibly-stale local state, before
any claim or fence runs).

**Context**: Surfaced 2026-06-12 while fixing OpenUP skill discovery — the live `.claude/skills/` had drifted into nested grouping folders that broke slash-command discovery. Root cause: `scripts/sync-templates-to-claude.sh` expected a nested template layout (templates are flat), copied zero skills, and never synced rubrics/hooks — letting live hooks drift ahead of the shipped templates. T-022 makes the within-repo sync produce correct, complete, flat files and stops `agent-runs.jsonl` dangling uncommitted at session end. T-024 (seeded by [explorations/2026-06-12-multi-worktree-coordination.md](explorations/2026-06-12-multi-worktree-coordination.md)) finishes what T-023 started: the shared views (`roadmap.md` Status cells, `project-status.md` header + Notes) become script-derived (`sync-status.py`, fresh-trunk only), completion notes shard to `docs/status-notes/`, and `scripts/openup-fence.py` + `.githooks/pre-push` fence every lane's diff to its claimed surface — for agents and humans alike. Full model: [docs-eng-process/parallel-lanes.md](../docs-eng-process/parallel-lanes.md).


<!-- plan-hook: 2026-06-15 -->
### Completed: Project Docs Traceability & Validation Pack

- **Status**: `completed` (2026-06-15 — all of T-034…T-039 delivered)
- **Plan**: [plans/2026-06-15-project-docs-traceability-pack.md](plans/2026-06-15-project-docs-traceability-pack.md)
- **Created**: 2026-06-15
- **Priority**: medium
- **Goal**: Give every OpenUP project a `docs/` that stays linked, traceable, and validated — work-product instances carry typed traceability frontmatter (injected by the `openup-create-*` skills, graded by a rubric, never by editing OpenUP templates), a shipped validator checks schema + cross-links + OpenUP trace coverage, and a derived index/board surfaces the trace web — all distributed through `process-manifest.txt` and tailorable via `docs/project-config.yaml`'s new `trace_rules:` block.
- **Notes**: Hard guardrail respected: no edits to `openup-knowledge-base/**` or `docs-eng-process/templates/**`. Instance frontmatter lands on authored docs only; templates stay pristine. T-034..T-036 (Wave 1+2) landed in PR #29; T-037..T-039 (Wave 3+4) on this branch.

**Tasks**

| ID | Title | Status | Priority | Depends on |
|---|---|---|---|---|
| T-034 | Work-product taxonomy + instance-frontmatter spec + `docs-meta.schema.json` | completed (2026-06-15) | medium | — |
| T-035 | Derive `trace-model.json` from the vendored KB (`build-trace-model.py`) | completed (2026-06-15) | medium | T-034 |
| T-036 | `check-docs.py` validator core (schema + link/id resolution + bidirectional) | completed (2026-06-15) | high | T-034, T-035 |
| T-037 | Trace-coverage checks + derived trace index (`docs-index.py`, write-fence) | completed (2026-06-15) | medium | T-036 |
| T-038 | Author-time frontmatter via `create-*` skills + cross-cutting rubric + complete-task gate | completed (2026-06-15) | high | T-034, T-036 |
| T-039 | Distribution (`process-manifest`) + project-side hook + `trace_rules:` tailoring + adoption docs | completed (2026-06-15) | medium | T-036, T-037, T-038 |


<!-- plan-hook: 2026-06-12 -->
### Completed: Modern Product Practice Pack

- **Status**: `completed` (2026-06-12 — all of T-025…T-030 delivered)
- **Plan**: [plans/2026-06-12-modern-product-practice-pack.md](plans/2026-06-12-modern-product-practice-pack.md)
- **Exploration**: [explorations/2026-06-12-modern-product-practices-on-openup.md](explorations/2026-06-12-modern-product-practices-on-openup.md)
- **Created**: 2026-06-12
- **Priority**: high
- **Goal**: Layer modern product practices on top of OpenUP — product-manager role influencing the mechanical project manager, one falsifiable success measure per feature, flag-controlled rollouts, multi-environment deployment config, and a product-manager challenge pass in `/openup-explore`.
- **Notes**: Hard guardrail: OpenUP artifacts (`openup-knowledge-base/`, `docs-eng-process/templates/`) are read-only; all deltas land in `docs-eng-process/.claude-templates/` (skills, teammates, teams, rubrics) per owner decision 2026-06-12. KB anchors: Product Owner pattern, metrics concept, Develop Backout Plan, Transition beta-test objective.

**Tasks**

| ID | Title | Status | Priority | Depends on |
|---|---|---|---|---|
| T-025 | `product-manager` teammate: value authority over a mechanical project manager (roadmap value rationale, board consumes order as input) | completed (2026-06-12) | high | — |
| T-026 | Per-feature success measure: one falsifiable expectation (impact/engagement/value prompts) via create-task-spec + rubric criterion 12 | completed (2026-06-12) | high | — |
| T-027 | Rollout & feature-flag strategy: `## Rollout` authoring step, rubric criterion 13, flag-removal task auto-enqueued at complete-task | completed (2026-06-12) | medium | — |
| T-028 | `environments:` ordered chain in project-config consumed by `/openup-transition` (per-hop promotion checklists; staging→beta→production as example) | completed (2026-06-12) | medium | T-027 |
| T-029 | Measure read-back → re-prioritization loop in `/openup-retrospective` + product-manager duty | completed (2026-06-12) | high | T-025, T-026 |
| T-030 | Product-manager challenge pass in `/openup-explore` (role hat, pushback/complement/refine, vetoable) | completed (2026-06-12) | medium | T-025 |

> **Task-ID renumber (2026-06-12)**: this block was planned as T-024…T-029, but the
> parallel lane (PR #21, write-fence) allocated T-024 first — IDs shifted +1 at merge.
> Commit trailers `[T-024]`…`[T-029]` on the pack's branch predate the renumber and
> map to T-025…T-030 here.


<!-- plan-hook: 2026-06-12 -->
### Completed: Clarity, Self-Briefing, and the Sequential Continue-Loop

- **Status**: `completed` (2026-06-12 — all of T-015…T-021 delivered)
- **Plan**: [plans/2026-06-12-clarity-self-briefing-continue-loop.md](plans/2026-06-12-clarity-self-briefing-continue-loop.md)
- **Exploration**: [explorations/2026-06-12-openspec-clarity-waste.md](explorations/2026-06-12-openspec-clarity-waste.md)
- **Created**: 2026-06-12
- **Priority**: high
- **Goal**: Reduce waste from unclear objectives and misunderstandings — unambiguous specs, roles that self-brief from the repo, and a mechanical "read the next task and execute" loop.
- **Notes**: Follow-up to the 2026-05-13 OpenSpec plan re-focused on intent-clarity waste; absorbs that plan's one un-implemented item (#2, `project-config.yaml`) as T-018. Headline deliverable is T-017 (`/openup-next` continue-loop + derived `.openup/board.json`). Parallelism reframed as per-lane (T-009 machinery re-scoped, not removed); teams demote to opt-in for `full` track.

**Tasks**

| ID | Title | Status | Priority | Depends on |
|---|---|---|---|---|
| T-015 | Mandatory ambiguity gate in spec authoring (assumptions made visible/vetoable) | completed (2026-06-12) | high | — |
| T-016 | Self-briefing roles: per-role cold-start reading lists + pointer-only PM delegation | completed (2026-06-12) | high | T-015 |
| T-017 | `/openup-next` sequential continue-loop + derived `.openup/board.json` + Operations checkboxes | completed (2026-06-12) | high | T-015, T-016 |
| [T-018](changes/archive/T-018/plan.md) | `docs/project-config.yaml` context/rules injection (from 2026-05-13 #2) | completed (2026-06-12) | medium | — |
| [T-019](changes/archive/T-019/plan.md) | Behavior Delta section in the task spec (Added/Modified/Removed vs Ring 1) | completed (2026-06-12) | high | T-007 |
| [T-020](changes/archive/T-020/plan.md) | Scenario-per-requirement (Given/When/Then) + deterministic validation | completed (2026-06-12) | high | T-019 |
| [T-021](changes/archive/T-021/plan.md) | Implementation-vs-spec verify step in `/openup-complete-task` | completed (2026-06-12) | medium | T-020 |

**Next step**: T-015 ✅, T-016 ✅, T-017 ✅, T-018 ✅, T-019 ✅, T-020 ✅, T-021 ✅ done — **the Clarity, Self-Briefing, and Continue-Loop plan is fully delivered.** T-018 added the project-config layer: a project-owned `docs/project-config.yaml` (`context:` + per-artifact `rules:`) injected as `<project-context>`/`<project-rules>` into every `/openup-create-*` prompt, precedence framework rubric → project rules → task-spec safeguards, mechanism in `docs-eng-process/project-config.md`. No open threads remain in this plan.


<!-- plan-hook: 2026-06-10 -->
### Completed: Process v2 — Mechanize OpenUP for the Claude Code Harness

- **Status**: `completed` (2026-06-11 — all of T-004…T-011 + T-002 delivered)
- **Plan**: [plans/2026-06-10-process-v2-claude-code-harness.md](plans/2026-06-10-process-v2-claude-code-harness.md)
- **Created**: 2026-06-10
- **Evidence base**: Kaze webapp empirical audit (2026-06-10) + 2026 AI-agent SDLC research (AI-DLC, Spec Kit, OpenSpec, BMAD, Kiro)
- **Notes**: Absorbs items #1–#4 of the 2026-05-13 OpenSpec plan (readiness DAG, project-config, per-change folders, archive flow) into workstreams WS4/WS5. T-008 un-defers T-002 (`/openup-sync-spec`). Wave 2 complete. Wave 3 started — T-008 ✅ (coordination frontmatter + /openup-readiness DAG). Next: T-009 (worktree-per-task + lease claims). Wave 3 complete — T-009 ✅ (worktree-per-task + lease claims + collision pre-flight). Wave 4 started — T-010 ✅ (graded quick/standard/full tracks + intake track suggestion). Wave 4 — T-011 ✅ (retro cadence trigger + /openup-create-handoff).

**Tasks**

| ID | Title | Status | Priority | Depends on |
|---|---|---|---|---|
| T-004 | Model tier map + `model:` frontmatter sweep + scribe/explorer agents | completed (2026-06-10) | high | — |
| T-005 | `.openup/state.json` iteration state file | completed (2026-06-10) | high | — |
| T-006 | Blocking gates + deterministic auto-logging + status sync | completed (2026-06-10) | high | T-005 |
| T-007 | Three-ring docs scoping (product / changes / archive) | completed (2026-06-11) | medium | — |
| T-008 | Coordination frontmatter + `/openup-readiness` DAG | completed (2026-06-11) | medium | T-007 |
| T-009 | Worktree-per-task + lease claims + collision pre-flight | completed (2026-06-11) | medium | T-005, T-008 |
| T-010 | Graded tracks (quick/standard/full) | completed (2026-06-11) | medium | T-005, T-006 |
| T-011 | Retro cadence trigger + `/openup-create-handoff` | completed (2026-06-11) | low | T-005 |

**Next step**: T-002 (`/openup-sync-spec`) completed 2026-06-11 (iter 9). Process v2 program tasks all delivered.


<!-- plan-hook: 2026-05-13 -->
### Completed: OpenSpec Ideas Worth Adopting in OpenUP

- **Status**: `completed` (2026-06-12 — all five items landed: #1/#3/#4 via Process v2, #5 via `/openup-explore`, #2 as T-018)
- **Plan**: [plans/2026-05-13-openspec-ideas-for-openup.md](plans/2026-05-13-openspec-ideas-for-openup.md)
- **Evaluation**: [plans/2026-05-13-openspec-evaluation.md](plans/2026-05-13-openspec-evaluation.md) (SPDD self-grading)
- **Created**: 2026-05-13
- **Notes**: Counterpart to the 2026-04-28 SPDD plan. Item #1 (readiness DAG) is a precondition for un-deferring T-002 (`/openup-sync-spec`); item #5 (explore mode) is complementary to the 2026-04-28 "fix-spec-first" rule.


<!-- plan-hook: 2026-04-28 -->
### Completed: SPDD Ideas Worth Adopting in OpenUP

- **Status**: `completed` (2026-06-12 — T-001/T-002/T-003 delivered; T-013/T-014 backfilled)
- **Plan**: [plans/2026-04-28-spdd-ideas-worth-adopting-in-openup.md](plans/2026-04-28-spdd-ideas-worth-adopting-in-openup.md)
- **Evaluation**: [plans/2026-04-28-spdd-evaluation.md](plans/2026-04-28-spdd-evaluation.md) (SPDD self-grading)
- **Created**: 2026-04-28

**Tasks**

| ID | Title | Status | Priority |
|---|---|---|---|
| [T-001](changes/archive/T-001/plan.md) | REASONS task spec — template, skill, rubric | done | high |
| [T-002](changes/archive/T-002/plan.md) | `/openup-sync-spec` — refactor back-propagation | completed (2026-06-11) | medium |
| [T-003](changes/archive/T-003/plan.md) | Suitability "fit" metadata in workflow skills | done | low |
| [T-013](changes/archive/T-013/plan.md) | Fix-spec-first rule for behavior changes (plan item #2) | done (backfilled 2026-06-12) | high |
| [T-014](changes/archive/T-014/plan.md) | Edit artifacts through their skill, not by hand (plan item #5) | done (backfilled 2026-06-12) | low |

**Next step**: program complete. T-001/T-003 delivered, T-013/T-014 backfilled, and
T-002 (`/openup-sync-spec`) completed 2026-06-11 once T-008's readiness DAG un-blocked it.

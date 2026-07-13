# Roadmap


### Maintenance (standalone fixes)

| ID | Title | Status | Priority | Depends on |
|---|---|---|---|---|
| T-062 | Fix pre-existing `check-docs.py` failures (archived T-056 plan + t-059/t-060 iteration-plan frontmatter: status enum + duplicate id) so the complete-task 3a gate is green again | completed (2026-07-05) | medium | — |
| [T-061](changes/T-061/plan.md) | Optimize template skills for Opus 4.8 / Sonnet 5 — stale model string, stack-agnostic plan-feature, report-then-rank self-critique, emphasis/dedup pass, retrospective re-tier | completed (2026-07-02) | medium | — |
| T-058 | Periodic framework version staleness check — 6-hour cooldown, wired into board + start-iteration | completed (2026-06-19) | medium | — |
| [T-057](changes/T-057/plan.md) | Solo UX Friction — Free Exploration, Gate-at-Commit, Auto-Merge | completed (2026-06-19) | high | — |
| [T-056](changes/T-056/plan.md) | Web session bootstrap — auto-regenerate `.claude/` on session start + framework version selector (vendored/latest/pinned) | completed (2026-06-19) | high | — |
| [T-055](changes/T-055/plan.md) | Supply-chain & adoption-trust hardening (pin/release tag · clone-verify-run install · hook disclosure · LICENSE/SECURITY.md) | completed (2026-06-18) | medium | — |
| T-054 | Bump OpenUP framework version to 2.0.0 (major — openup-doctor + parallel-lanes/write-fence/board/typed-traceability since 1.5.0) | completed (2026-06-18) | low | — |
| [T-053](changes/archive/T-053/plan.md) | Add `scripts/openup-doctor.py` — read-only project health diagnostic (framework/manifest drift + `.openup/state.json` integrity + aggregation of existing `--check` modes) + thin `/openup-doctor` skill | completed (2026-06-18) | medium | — |
| [T-052](changes/T-052/plan.md) | Framework syncs must not leave uncommitted changes that trip on-stop (sync self-commits its CLI upgrades) | completed (2026-06-18) | medium | T-051 |
| [T-048](changes/archive/T-048/plan.md) | Audit fixes: archived-plan status bump (false dep-block) + worktree-promote board-blindness | completed (2026-06-17) | high | — |
| [T-047](changes/archive/T-047/plan.md) | Carry T-046's untrack migration into `sync-from-framework.sh` (a project adopting T-046 auto-gitignores + `git rm --cached` the now-derived agent-runs.jsonl) | completed (2026-06-17) | medium | T-046 |
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


## T-059: Loop Support for /openup-next
**Status**: completed (2026-06-20)
**Priority**: high
**Value**: Practitioners driving the roadmap from a shell script or cron get a reliable stop signal and safe wrapper, eliminating manual loop management and enabling unattended backlog drain.
**Description**: Add a machine-readable sentinel (`OPENUP-NEXT: ADVANCED/DONE`) to every `/openup-next` exit, a loop-behavior section in the skill, and `scripts/openup-loop.sh` — a wrapper with cycle cap, stall detection, and sentinel-based stop. Prerequisite for T-060.
- Sentinel line on every exit (ADVANCED vs DONE with reason)
- "When driven by an outer loop" section in `openup-next/SKILL.md`
- `scripts/openup-loop.sh` (cycle cap, stall limit, sentinel check, fail-safe exit codes)
- Entry in `process-manifest.txt`

**Dependencies**: none

**See**: `docs/iteration-plans/t-059-loop-support-openup-next.md`

---

## T-060: Parallel Fan-Out (/openup-fan-out)
**Status**: completed (2026-06-22)
**Priority**: high
**Value**: Teams (and solo practitioners with a wide board) can run multiple lanes concurrently as background subagents, compressing wall-clock delivery time while the interactive session stays free for planning — no manual parallelism wiring required.
**Description**: Add a stale-lease reaper to `openup-claims.py` (heartbeat field + `reap` subcommand) so crashed background subagents don't wedge lanes permanently, a `top-n` subcommand to `openup-board.py` for collision-free multi-lane selection, and a new `/openup-fan-out` skill that dispatches one background subagent per READY lane.
- `openup-claims.py heartbeat` + `reap` subcommands (stale-claim recovery)
- `openup-board.py top-n N` (collision-free lane partition)
- `/openup-fan-out` skill (dispatch + collect summaries)
- Heartbeat stamp wired into `/openup-start-iteration`

**Dependencies**: T-059

**See**: `docs/iteration-plans/t-060-parallel-fan-out.md`

---

<!-- plan-hook: 2026-07-05 -->
### Planned: Efficient /openup-next loop — deterministic selection, single-call state, self-healing claims

- **Status**: `planned` (awaiting implementation)
- **Exploration**: [explorations/2026-07-05-next-loop-efficiency.md](explorations/2026-07-05-next-loop-efficiency.md)
- **Created**: 2026-07-05
- **Goal**: Make one `/openup-next` cycle cheap (tokens), deterministic (selection), and low-friction (round-trips) by extending the script layer — without duplicating the skill machinery. Three ordered deliverables (T-063 → T-064 → T-065), reap+atomicity first per the exploration's product-manager challenge pass.
- **Next step**: Run `/openup-start-iteration task_id: T-063`

---

## T-063: openup-session.py begin|end + reap wiring in the sequential loop
**Status**: completed (2026-07-06)
**Priority**: high
**Value**: An unattended `/openup-next` loop survives its own crashes — a stale lease self-heals within one cycle instead of wedging the lane until a human runs `release` — which is the difference between "autonomous" and "babysat".
**Description**: Add `scripts/openup-session.py` with atomic `begin` (reap + remote-check + claim + heartbeat + state-init + log in one process, with rollback on partial failure) and `end` (release + state-archive + log). Composition-only over existing `openup-claims.py`/`openup-state.py` — git worktree ops stay in the skills. Wire the T-060 reaper into `openup-board.py refresh` so a crashed session's stale lease self-heals within one cycle.
- `scripts/openup-session.py begin|end` (atomic claim lifecycle, state+claim+log only)
- Reap wired into `openup-board.py refresh` (heartbeat-gated; T-060 invariant preserved)
- `/openup-start-iteration` + `/openup-complete-task` + `/openup-create-handoff` slimmed to call the new verbs
- Entry in `process-manifest.txt` + `script-cli-reference.md`

**Dependencies**: T-060

**See**: `docs/iteration-plans/t-063-openup-session-begin-end-reap.md`

---

## T-064: openup-roadmap.py — deterministic roadmap interface
**Status**: completed (2026-07-10)
**Priority**: high
**Value**: Solo developers running `/openup-next` stop paying a re-read of the whole roadmap every cycle and stop getting divergent picks — promote-step selection becomes script-decided, so two sessions on identical inputs choose the same task.
**Description**: Add `scripts/openup-roadmap.py` with `next` (mechanically implements `/openup-next` §1c's selection rule: first pending entry with satisfied deps, no change folder, no live lease — skipping in-flight-elsewhere ids), `list`, and `get`. Parses both roadmap entry shapes (table rows + manual `## T-NNN:` sections). Read-only. `/openup-next` §1c calls it instead of reading the roadmap into context. Track selection stays a model judgment.
- `scripts/openup-roadmap.py next|list|get` (read-only parser + selector)
- `/openup-next` §1c consumes `next`
- Selection divergence = 0 on identical fixtures (falsifiable measure)
- Entry in `process-manifest.txt` + `script-cli-reference.md`

**Dependencies**: none (composes with T-063)

**See**: `docs/iteration-plans/t-064-openup-roadmap-interface.md`

---

## T-065: openup-board.py status/resolve verb + skill slimming
**Status**: completed (2026-07-10)
**Priority**: high
**Value**: State discovery collapses to one call returning ≤~40 lines of JSON, and the per-cycle skill text shrinks — so the loop stops spending tokens just to learn "where are we", every cycle, compounding.
**Description**: Add `openup-board.py resolve` (the §0–§1 precedence — resume/pick/promote/noop — computed once as data, folding in resumable-input + state + board-top + roadmap-next) and `status` (superset diagnostic). Read-only. Slim `/openup-next` §0–§1 to a single `resolve` call, cut `/openup-start-iteration`'s double status/roadmap re-read, and give `openup-loop.sh` a no-op pre-check that avoids spawning a cycle process.
- `openup-board.py resolve` + `status` (read-only, ≤~40-line JSON)
- `/openup-next` §0–§1 → single `resolve` call; `start-iteration` double-read removed
- `openup-loop.sh` no-op pre-check
- Entry in `process-manifest.txt` + `script-cli-reference.md`

**Dependencies**: T-064

**See**: `docs/iteration-plans/t-065-openup-board-resolve-skill-slimming.md`

---

## T-066: promote-selector remote delivered-but-unmerged guard
**Status**: completed (2026-07-10)
**Priority**: high
**Value**: `/openup-next` stops re-promoting — and re-implementing — a task that is already fully delivered in an open, unmerged PR. Today a completed-but-unmerged task is invisible to every local promote guard (no active folder, archived folder lives on the branch, lease released), so the loop wastes a whole cycle redoing finished work. This closes the last re-promote hole.
**Description**: Add a remote-branch guard to `openup-roadmap.py cmd_next` (inherited by `openup-board.py resolve`'s promote branch): before promoting a candidate that passed the local in-flight checks, consult `origin` for a branch encoding the task id (reuse the T-044 `claims.remote_task_branches` helper). If one exists → skip as in-flight-elsewhere and surface "merge the PR", never re-promote. Fail-open (offline / no remote / git error → do not block), one `ls-remote` per invocation (cached), opt-out via `--no-remote-check`.
- `openup-roadmap.py cmd_next` remote-branch guard (fail-open, cached, `--no-remote-check`)
- `/openup-next` §1c note: delivered-but-unmerged is skipped remotely
- Path-coverage tests: real bare-remote fixture (branch present → skip; absent → promote; offline → fail-open promote)
- Entry in `script-cli-reference.md`

**Dependencies**: T-064, T-065

**See**: `docs/changes/T-066/plan.md`

---

## T-067: sync-status.py stamps section-style roadmap Status lines
**Status**: completed (2026-07-10)
**Priority**: high
**Value**: Closes the silent roadmap status-rot: `sync-status.py` only stamps table-row Status cells, never the free-form `**Status**:` lines that `/openup-plan-feature` emits for `## T-NNN:` sections — so section entries show completed only when a human hand-edits them. T-063/T-064/T-066 rotted (pending/ready despite being merged). This makes complete-task auto-sync section entries, adds a self-healing `--reconcile` sweep, and surfaces the drift in `openup-doctor`.
**Description**: (1) Extend `update_roadmap()` to stamp a `## <id>:` section's `**Status**:` line when no table row matches (same idempotent `completed (date)` convention). (2) Add `sync-status.py --reconcile` sweep that stamps `completed (<archival-date>)` for every `## T-NNN:` section with an archived change folder. (3) Add a read-only `warning` check in `openup-doctor` for archived-but-not-completed sections, pointing at `--reconcile`. (4) Backfill T-063/T-064/T-066 by running reconcile. (5) Path-coverage test.
- `update_roadmap()` section-line fallback
- `--reconcile` sweep (git archival date, idempotent)
- `openup-doctor` section-status-drift warning (read-only)
- Test + `script-cli-reference.md` entry

**Dependencies**: —

**See**: `docs/changes/T-067/plan.md`

---

## T-068: auto-log-commit logs to the worktree that received the commit
**Status**: completed (2026-07-10)
**Priority**: high
**Value**: Kills a recurring, cross-cutting friction: the `auto-log-commit` PostToolUse hook derives its shard path + logged sha from the pinned harness cwd (the main checkout), so every worktree commit appends a bogus `commit` record into **main's** run-log shard — dirtying main and silently blocking the next `git pull`/merge. Fires on every worktree-based task (the default flow), so pulls break "all the time".
**Description**: Add `resolve_commit_root(cwd)` to `auto-log-commit.py` that routes the log to the worktree whose HEAD has the newest committer timestamp (the just-made commit) via `git worktree list`, with a strict fallback to today's cwd behavior on ≤1 worktree or failure. Rewire `main()` to use that root/sha. Sync `.claude/` from the template; extend the T-006 hook tests with worktree-routing + main-stays-clean cases. No schema/idempotency/fail-open change; shards stay tracked (no gitignore).
- `resolve_commit_root` (sha↔worktree by newest committer ts)
- `main()` rewire off `payload.cwd`
- worktree-routing hook tests (+ main-clean assertion)

**Dependencies**: —

**See**: `docs/changes/T-068/plan.md`

---

## T-069: on-stop skips the run-log sweep-commit on trunk
**Status**: completed (2026-07-10)
**Priority**: high
**Value**: Kills a recurring pull-breaking friction (sibling of T-068): `on-stop.py` sweeps leftover run-log shards into a `chore(process): sweep run-log shards [openup-skip]` commit on whatever branch is checked out — including `main`. A local commit on trunk diverges from origin the moment a PR merges, so the next `git pull` fails with "divergent branches". Observed this session after PR #68 merged.
**Description**: Guard the sweep in `on-stop.py`: when HEAD is trunk (`main`/`master`/detected default via `get_trunk`), skip the `git commit` and leave the exempt shards uncommitted (they never block stop). Feature-branch sweep behavior is unchanged. No schema/gitignore/dirty-block change. Sync `.claude/` from the template; extend the T-006 hook tests with trunk-skip + feature-branch-still-sweeps + non-exempt-still-blocks cases.
- on-stop trunk guard on the sweep-commit
- feature-branch sweep preserved
- trunk-skip hook tests

**Dependencies**: —

**See**: `docs/changes/T-069/plan.md`

---

## T-070: validate-commit accepts the active task_id as the required tag
**Status**: completed (2026-07-10)
**Priority**: high
**Value**: Closes a self-contradicting enforcement gate: `validate-commit.py`'s mandatory-tag check rejects the exact `[{task_id}]` tag its own error message tells you to append, whenever the active `task_id` is non-numeric (e.g. any `/openup-quick-task` id). The lane becomes uncommittable without an audited `[openup-skip]` bypass — observed live this session, forcing two bypasses on a trivial cleanup. Since the live hook is byte-identical to its shipped template, every consuming project inherits the trap.
**Description**: In the mandatory-tag branch, accept the subject when it carries the lane's real `[{task_id}]` tag (regex-escaped, case-insensitive) OR any `[T-NNN]` (numeric alternative preserved); only reject when neither is present, so the hook's printed remedy is satisfiable for any active id. Sync live + template; extend the T-006 hook tests (non-numeric id + `[{id}]` passes; non-numeric id + no tag fails; numeric `[T-NNN]` still passes; `[openup-skip]` still bypasses).
- mandatory-tag branch accepts literal `[{task_id}]` or any `[T-NNN]`
- live↔template parity preserved
- T-006 hook tests for the non-numeric-id cases

**Dependencies**: —

**See**: `docs/changes/T-070/plan.md`, `docs/explorations/2026-07-10-validate-commit-numeric-tag-gap.md`

---

<!-- plan-hook: 2026-07-12 -->
### Planned: Harness-optional OpenUP core (integration branch `harness-optional`)

- **Status**: `planned` (awaiting implementation)
- **Integration branch**: `harness-optional` — all program work merges here;
  lanes branch off `main`, PRs target `harness-optional`; `main` stays clean.
- **Exploration**: [explorations/2026-07-12-harness-agnostic-openup.md](explorations/2026-07-12-harness-agnostic-openup.md)
- **Created**: 2026-07-12
- **Goal**: Make OpenUP **harness-optional** — a core of files + Python + git
  usable with no harness, each harness an optional adapter over one neutral
  procedure pack. Claude Code stays **first-class** (its adapter reproduces
  today's `.claude/`); prove the loop runs on a bare, non-Anthropic LLM.
- **Owner decisions (2026-07-12)**: (1) integration branch `harness-optional`;
  (2) git-centric enforcement (pre-push fence + git hooks) is the accepted
  opinion; (3) reference driver targets an OpenAI-compatible endpoint via
  `LLM_API_URL` + `LLM_API_KEY` (owner runs LM Studio); (4) Claude Code
  first-class, Cursor/Codex deferred, de-"Claude-flavoring" allowed only where it
  doesn't degrade Claude Code; (5) frontmatter schema open to change;
  (6) model tiers are runtime-name-matched (tier *name* → concrete model resolved
  per harness at runtime — no Claude model strings in the pack).
- **Ordered deliverables**: T-071 (Layer 1 — neutral pack + Claude Code adapter
  parity) ✅ → T-072 (Layer 3 — reference OpenAI-compatible driver) ✅ → **T-074
  (human-in-the-loop input handling in the driver)** → T-073 (Layer 4 — FastAPI
  service). T-074 is ordered **ahead of** T-073 (PM decision 2026-07-12): it makes
  the driver usable for procedures that ask blocking questions, and is a
  precondition for a genuinely useful service. T-073 still starts only once a
  **named consumer** exists (exploration Pushback 1).
- **Program acceptance**: one full `/openup-next`-style cycle end-to-end on
  **(a)** Claude Code and **(b)** the reference driver on a non-Anthropic/local
  model, each producing fence-clean, validator-clean commits.
- **Next step**: T-071 ✅, T-072 ✅ **`verified` 2026-07-13** (live-model
  acceptance MET — the driver drove `openup-create-vision` end-to-end on a
  non-Anthropic local model, `qwen/qwen3.6-35b-a3b`, 3/3 fence+validator-clean,
  producing genuine vision docs; batch `.openup/bench/20260713-160244`, recorded by
  T-086. Scope: create-vision authoring cycle; the `next` continue-loop on a weak
  local model is heavier/inconsistent — a model+ceremony finding tracked via the
  benchmark harness T-080…T-085, not a driver gap). T-074 ✅. Only **T-073**
  (FastAPI service) remains, gated on a named consumer.

---

## T-071: Neutral procedure pack + runtime tier map + re-pointed Claude Code adapter
**Status**: completed (2026-07-12)
**Priority**: high
**Value**: The framework maintainer gets a single source of truth for every
procedure body and Claude Code keeps working unchanged — the same pack a
non-Claude driver (T-072) can read, which is the whole premise of a
harness-optional OpenUP. Removes the Claude-shaped canonical home and the
hardcoded Claude model strings without touching the Claude Code experience.
**Description**: Extract the 35 skill bodies from `.claude-templates/skills/` into
a harness-neutral pack (`docs-eng-process/procedures/openup-*.md`) with a neutral
frontmatter schema — tiers declared as runtime-resolved **names** (`tier:`) plus a
`capabilities:` required/optional split — and a `tier-map.yaml` resolving tier name
→ concrete model per target. Re-point `sync-templates-to-claude.sh` at the pack as
a translating adapter (via a `render-claude-adapter.py` helper) so `.claude/` is
reproduced with parity. Keep `check-model-tiers.py` and the sync/parity checks green.
- Neutral procedure pack (`docs-eng-process/procedures/`) — no Claude model strings
- `tier-map.yaml` runtime tier→model map (`claude-code` + `driver` columns)
- `sync-templates-to-claude.sh` re-pointed as translating adapter + `render-claude-adapter.py`
- Parity: generated `.claude/skills/` matches today's; `check-model-tiers.py --check` green
- Single source of truth: `.claude-templates/skills/` removed/stubbed

**Dependencies**: —

**See**: `docs/iteration-plans/t-071-neutral-procedure-pack.md`

---

## T-072: Reference OpenAI-compatible driver (`openup-agent run`)
**Status**: completed (2026-07-12)
**Priority**: high
**Value**: Proves OpenUP is genuinely harness-optional — a practitioner with no
Claude Code (or any harness) can drive a delivery cycle on a local/non-Anthropic
model, because the deterministic steps (board, fence, validators, sync) are code
and only judgment steps need the LLM. This is the falsifiable half of the program
acceptance test.
**Description**: A plain Python agentic loop — `openup-agent run --dir <path>
--procedure next` — over any OpenAI-compatible chat-completions endpoint
(`LLM_API_URL` + `LLM_API_KEY`; owner runs LM Studio). Minimal 6-tool surface
(`read_file`, `write_file`, `edit_file`, `list_dir`/`glob`, `grep`, `exec`); the
driver owns the loop so hooks become deterministic code it runs itself
(`check-docs.py`, the fence, state updates). Reads the T-071 neutral pack directly;
resolves tiers via the `tier-map.yaml` `driver` column against the models the
endpoint surfaces. Full iteration plan authored when promoted.
- `openup-agent run --dir --procedure` loop (OpenAI-compatible, env-configured)
- 6-tool surface (exec narrowed to a git + `scripts/*.py` allowlist for safety)
- Deterministic hook enforcement in the loop (fence + `check-docs.py` + state)
- Runtime tier resolution against endpoint-surfaced model names

**Dependencies**: T-071

**See**: `Planned: Harness-optional OpenUP core` block above + `docs/explorations/2026-07-12-harness-agnostic-openup.md` — full iteration plan authored on promote

---

## T-074: Human-in-the-loop input handling in the reference driver
**Status**: completed (2026-07-12)
**Priority**: high
**Value**: The reference driver (T-072) can only drive procedures that never need
a human — it auto-proceeds and has no way to ask a question. But many OpenUP
procedures hit **blocking questions** (`/openup-request-input`, plan-gate approval)
that are the whole point of the process staying safe. Without this, a practitioner
on a local model cannot run a realistic cycle end-to-end; with it, the driver
surfaces the question, suspends cleanly, and resumes on the answer — reusing the
async input-request machinery the harness already has. It is also the precondition
for a genuinely useful T-073 service (answering questions over HTTP), which is why
the PM orders it **ahead of** T-073.
**Description**: Add driver support for questions that must be answered by a human,
reusing OpenUP's existing async input-request flow (`/openup-request-input` →
`awaiting-input` frontmatter → `openup-input.py resumable` → `/openup-next` resume).
Two modes governed by one flag (`--interactive`, default off):
- *Interactive CLI*: prompt on the controlling TTY, block for the answer, feed it back into the loop.
- *Async / non-interactive (CI, service)*: create the input-request doc, set
  `awaiting-input`, and terminate with a distinct **suspend sentinel + exit code** so
  an outer loop suspends the lane; resume folds the answer back via the existing path.
Mechanism (decide at promote): a 7th tool `ask_user(question, options?)` vs a
driver-level gate that emits the request-input. Same flag governs plan-gate approval
(the exploration's open question). Full iteration plan authored when promoted.
- `ask_user` mechanism (interactive TTY + async suspend-and-persist) wired into the loop
- Reuses `/openup-request-input` + `openup-input.py` resume path (no new machinery)
- Distinct suspend sentinel + exit code for the non-interactive/service case
- Hermetic tests: interactive answer round-trip + async suspend/resume, mock endpoint

**Dependencies**: T-072

**See**: `Planned: Harness-optional OpenUP core` block above + `docs/changes/archive/T-072/design.md` §Follow-on (captured shape) + `docs/explorations/2026-07-12-harness-agnostic-openup.md`

---

## T-073: FastAPI service wrapper over the reference driver
**Status**: pending
**Priority**: medium
**Value**: Lets a named consumer (CI job, web UI, or a second machine) run an
OpenUP cycle against a directory over HTTP without a local harness — but only
once such a consumer actually exists, so we don't build a remote-code-execution
surface ahead of demand.
**Description**: A thin FastAPI wrapper over the T-072 driver: `POST /runs
{dir, procedure, args, llm:{base_url, model}}` → run id; `GET /runs/{id}` (status +
log stream); `GET /projects/board` / `/status` (thin wrappers over
`openup-board.py` / `sync-status.py`). OpenAPI schema comes for free. **Gated**:
does not start until a named consumer is identified (exploration Pushback 1);
sandboxing (local-only bind by default, exec allowlist, container-per-run) is a
design question resolved at promote, not built up front. Full iteration plan
authored when promoted.
- `POST /runs` + `GET /runs/{id}` + board/status read wrappers
- OpenAPI schema surfaced by FastAPI
- Sandboxing decision (local-bind default + exec allowlist) at promote
- **Precondition**: a named consumer exists before this task is promoted

**Dependencies**: T-072, T-074

**See**: `Planned: Harness-optional OpenUP core` block above + `docs/explorations/2026-07-12-harness-agnostic-openup.md` — full iteration plan authored on promote

---

<!-- plan-hook: 2026-07-13 -->
### Planned: Phase-aware OpenUP loop — make the automated cycle follow the lifecycle

- **Status**: `completed` (2026-07-13 — all of T-075…T-079 delivered on `harness-optional`)
- **Exploration**: [explorations/2026-07-13-phase-aware-loop-redesign.md](explorations/2026-07-13-phase-aware-loop-redesign.md) (gap analysis + redesign) + [explorations/2026-07-13-openup-kb-process-model.md](explorations/2026-07-13-openup-kb-process-model.md) (authoritative KB distillation)
- **Created**: 2026-07-13
- **Goal**: Make the automated loop *follow* OpenUP's three-layer state machine —
  start each cycle from the product's current phase, run real iterations composed
  of per-role activities, and pause for a human milestone go/no-go — instead of
  running a flat task queue the model re-invents each session. Adds the two missing
  outer layers (project lifecycle + iteration lifecycle) over the working
  micro-increment layer; lanes, leases, and the write-fence stay unchanged.
- **Design principles**: derive-don't-author (phase/iteration state from
  deterministic scripts reading repo facts, never model judgment mid-loop); humans
  own the go/no-go (the loop prepares evidence and pauses via the T-074
  input-request machinery — it never advances a phase itself); tailoring is data (a
  per-project Development Case in config); the micro-increment layer is untouched.
- **Ordered deliverables**: T-075 (lifecycle status — read-only, unblocks all) →
  T-076 (Development Case config) → T-077 (process-map + phase-aware plan-iteration
  — biggest slice) → T-078 (assess-iteration + milestone-review — the convergence
  step) → T-079 (parallel iterations). Full iteration plan authored per task on
  promote, as the harness-optional program does.
- **Program acceptance**: one `/openup-next`-driven cycle resolves the current
  phase mechanically, plans a phase-appropriate iteration, executes it, runs Assess
  Results, and — at a phase boundary — pauses for a human milestone decision rather
  than draining to an empty queue.
- **Next step**: Program complete — T-079 (parallel iterations) merged the final
  slice. The loop now resolves the phase, plans a phase-appropriate iteration
  (partitioned into concurrent non-colliding clusters where the work is disjoint),
  converges via Assess Results, and pauses at a phase boundary for a human go/no-go.

---

## T-075: openup-lifecycle.py status + milestone decision records
**Status**: completed (2026-07-13)
**Priority**: high
**Value**: Everyone driving the loop gets an honest, derived answer to "what phase are we in and what does this milestone still need" — read from repo facts, not a stale hand-set label — which is the foundation every later slice reads from, and the smallest safe first step (advisory only, no loop behavior change).
**Description**: New read-only `scripts/openup-lifecycle.py status` computing the current phase + per-milestone criteria state from work-product instances and their `status:` frontmatter (T-038 typed traceability), roadmap rows, archived change folders, and milestone decision records. Add `docs/product/milestones/<phase>-<cycle>.md` records (human go/no-go, written only via `/openup-phase-review`) as the source of truth for "phase advanced"; `phase` in `.openup/state.json` becomes a cache stamped from this status. Same never-hand-edit rule as the board. No loop behavior change yet.
- `scripts/openup-lifecycle.py status` (derived phase + milestone criteria, read-only)
- `docs/product/milestones/` decision records + `cycle` counter (supports return-to-Construction)
- `phase` in state becomes a derived cache (no longer hand-set via `project-status.md`)
- Entry in `process-manifest.txt` + `script-cli-reference.md`

**Dependencies**: —

**See**: `docs/explorations/2026-07-13-phase-aware-loop-redesign.md` §3.1, §5 — full iteration plan authored on promote

---

## T-076: Development Case config (`process:` section + archetypes)
**Status**: completed (2026-07-13)
**Priority**: high
**Value**: A project maintainer tailors the whole lifecycle from one config block — the same engine runs a quick script, an MVP, or a full product by data — so ceremony matches scope instead of being one-size-fits-all (the quick archetype must degenerate to today's `/openup-quick-task` token cost, or the design fails its own efficiency bar).
**Description**: Extend `docs/project-config.yaml` with a `process:` section — OpenUP's Development Case made machine-readable: an `archetype` (quick | mvp | product) setting per-phase defaults (iteration budgets, required artifact set per milestone, exit criteria, milestone-review formality: human | auto-assess). Validate the section in `check-docs.py` / `openup-doctor`. Precedence extends the existing framework-rubric → project-rules chain documented in `docs-eng-process/project-config.md`.
- `process:` section + archetype defaults (quick/mvp/product) in `project-config.yaml`
- Schema + validation in `check-docs.py`; read-only drift warning in `openup-doctor`
- Development Case mapping + precedence documented in `docs-eng-process/project-config.md`
- Commented starter block emitted by `/openup-init`

**Dependencies**: —

**See**: `docs/explorations/2026-07-13-phase-aware-loop-redesign.md` §3.2, §5 — full iteration plan authored on promote

---

## T-077: process-map.yaml + phase-aware plan-iteration
**Status**: completed (2026-07-13)
**Priority**: high
**Value**: The loop stops re-inventing a process each run — `/openup-start-iteration` becomes real Plan Iteration, generating phase-appropriate lanes (vision/use-case/risk in Inception; architecture/skeleton/test in Elaboration; dev/test in Construction) from a data-encoded process map, so a human no longer hand-writes each roadmap row and the four phase skills stop being parallel manual guidance. Biggest slice.
**Description**: New framework-owned `docs-eng-process/process-map.yaml` encoding phase → activity → role → skill (KB §3/§4 as data). `/openup-start-iteration` becomes Plan Iteration proper: 1–5 objectives from risk list + PM value order + phase objectives, commits work items, and generates non-hand-written lanes from the map. Each planned iteration is minted with a stable id/name (e.g. `C3` = Construction iteration 3), and its committed work-item / lane ids are allocated **under that prefix** (`C3-NNN`) via the existing `openup-claims.py reserve-id --prefix` machinery — so every task is traceable to its iteration by id. `openup-board.py` / `openup-roadmap.py` resolve becomes lifecycle-aware and iteration-scoped; the one-row-at-a-time promote path dissolves into plan-iteration (quick archetype degenerates to ~today's single-work-item behavior). Phase skills become thin fronts over the map.
- `docs-eng-process/process-map.yaml` (phase→activity→role→skill)
- `/openup-start-iteration` = Plan Iteration (objective-driven; generates phase-appropriate lanes)
- Iteration minted with a stable id/name; work-item / lane ids allocated under that prefix (`<iter-id>-NNN`, reusing `openup-claims.py --prefix`)
- lifecycle-aware, iteration-scoped resolve in `openup-board.py` / `openup-roadmap.py`; promote → plan-iteration
- Phase skills refactored to thin fronts over the map

**Dependencies**: T-075, T-076

**See**: `docs/explorations/2026-07-13-phase-aware-loop-redesign.md` §3.3, §3.4, §5 — full iteration plan authored on promote

---

## T-078: assess-iteration + milestone-review wiring
**Status**: completed (2026-07-13)
**Priority**: high
**Value**: The loop *converges* instead of draining a queue — at iteration end it verifies evaluation criteria, demos only completed acceptance-tested work, feeds discovered work back, and at a phase boundary pauses for a human go/no-go rather than silently rolling on. This is the safety-critical human decision point the framework exists to provide.
**Description**: New `/openup-assess-iteration` (or an upgraded `/openup-retrospective`) running Assess Results: check evaluation criteria, demo completed acceptance-tested work only, feed new work/defects back into the roadmap, write the assessment into the iteration-plan instance, and trigger `/openup-phase-review` when the Development Case says the phase is done. Add resolve paths `plan-iteration` / `assess-iteration` / `milestone-review` to `openup-next` + `openup-agent.py` procedures; the milestone-review path pauses via the T-074 `/openup-request-input` machinery and records the human decision (never advances a phase itself). The DONE sentinel changes meaning from "roadmap empty" to "milestone-review pending human input / PR milestone accepted".
- `/openup-assess-iteration` (Assess Results incl. phase-end trigger)
- `openup-next` + `openup-agent.py` procedures gain plan-iteration / assess-iteration / milestone-review paths
- `/openup-phase-review` wired into the loop: pauses via T-074 input-request, writes the milestone record
- `.openup/state.json` schema 2 (`iteration_id`, `cycle`; `phase` = derived cache)

**Dependencies**: T-075, T-077

**See**: `docs/explorations/2026-07-13-phase-aware-loop-redesign.md` §3.4, §3.5, §5 — full iteration plan authored on promote

---

## T-079: Parallel Construction iterations (non-colliding clusters)
**Status**: completed (2026-07-13)
**Priority**: medium
**Value**: Low-dependency features deliver concurrently — the planner partitions committed work items into non-colliding iteration clusters (disjoint `touches` + use-case dependencies), lifting the existing lane-collision machinery one level to compress Construction wall-clock without a human wiring parallelism; and because each big Construction iteration is named/numbered with its tasks prefixed by that iteration id, work from concurrent iterations stays easy to track and never id-collides.
**Description**: Number/name each "big" Construction iteration and prefix its task ids with that iteration id (`<iter-id>-NNN`, built on T-077's minting), so tasks from different concurrent iterations are trivially attributable to their iteration and cannot collide on ids. Allow N concurrent iterations whose committed work items have disjoint `touches` and use-case dependencies; `openup-board.py` already computes collisions, and the planner partitions committed work items into non-colliding clusters. Depends on worktree-per-lane (live-run finding F5) for isolation.
- Named/numbered Construction iterations; task ids carry the iteration prefix (`<iter-id>-NNN`) for cross-iteration tracking + collision-free ids
- Planner partitions committed work items into non-colliding iteration clusters
- N concurrent iterations over disjoint `touches` / use-case deps (reuses board collision machinery)
- Worktree-per-lane isolation (live-run F5)

**Dependencies**: T-077

**See**: `docs/explorations/2026-07-13-phase-aware-loop-redesign.md` §3.6, §5 — full iteration plan authored on promote

---

## T-080: Reference-driver acceptance/benchmark harness
**Status**: completed (2026-07-13)
**Priority**: high
**Value**: Turns the T-072 **AC-program** live acceptance run (the owner step that was attempted, errored, and never recorded) into a repeatable, isolated, instrumented harness — so the reference driver can be run on a local/non-Anthropic model on demand to (a) record the AC-program pass/fail, (b) benchmark different models across many runs, and (c) regression-test changes to skills / the procedure pack / the driver tools by comparing runs before and after.
**Description**: A stdlib-only `scripts/openup-agent-bench.py` that, per run, `git clone --local`s the repo under test into a throwaway fixture, seeds a deterministic micro-task (one READY change-folder lane so `resolve` picks it, not the gated backlog), runs `openup-agent.py run --procedure next` as a subprocess (timeout + usage log), and recomputes outcome + gate-cleanliness + latency/iterations + work-delta + tokens on the fixture — aggregating N runs to `results.jsonl` + `summary.md`. Adds one env-gated (`OPENUP_AGENT_USAGE_LOG`) per-call usage capture to the loop (zero default behavior change). Hermetically validated against a mock endpoint; live runs are the owner's. + test plan `docs-eng-process/reference-driver-benchmark.md`.
- `scripts/openup-agent-bench.py` — clone-isolate + seed + run + measure + aggregate
- Env-gated `OPENUP_AGENT_USAGE_LOG` per-call token/latency capture in `loop.py`
- Built-in pluggable seed scenario (`scripts/bench-scenarios/quick-doc/`)
- Mock-endpoint hermetic harness test + `reference-driver-benchmark.md` test plan

**Dependencies**: T-072

**See**: `docs/changes/archive/T-080/plan.md` + `docs-eng-process/reference-driver.md`

---

## T-081: Benchmark harness surfaces the driver's failure reason
**Status**: completed (2026-07-13)
**Priority**: high
**Value**: The first live benchmark batch returned `endpoint-error` on every run but the harness swallowed the driver's stderr, hiding the reason (a transient endpoint-not-ready) and forcing a manual side-run to diagnose. This closes that observability gap so any non-pass run explains itself.
**Description**: Each run record gains `fatal` (the driver's `FATAL:` line) + `stderr_tail` + `stdout_tail`; the full driver stdout/stderr is written to `<out>/run-NN.driver.log`; on any non-`pass` outcome the reason is logged to the bench stderr and listed in a new `## Failures` section of `summary.md`. Additive, no behavior change to a passing run.

**Dependencies**: T-080

**See**: `docs/changes/archive/T-081/plan.md`

---

## T-082: Driver LLM client — handle slow-response timeout instead of crashing
**Status**: completed (2026-07-13)
**Priority**: high
**Value**: Found by the T-080 benchmark on a live local model: a slow LLM response fired the 120s per-call timeout as an uncaught `TimeoutError` and **crashed the whole run** (exit 1) instead of surfacing a clean, retryable error. On a local big model this recurs.
**Description**: `llm.chat_completion` now catches `(TimeoutError, OSError)` → `LLMError` (loop exits 3 `endpoint-error`, never an uncaught crash), the default per-call timeout rises 120→600s, and it's configurable via `OPENUP_AGENT_TIMEOUT`. +4 tests; env documented in `reference-driver.md`.

**Dependencies**: T-072 (found via T-080)

**See**: `docs/changes/archive/T-082/plan.md`

---

## T-083: Benchmark harness — realistic "stakeholder brief → Vision doc" scenario
**Status**: completed (2026-07-13)
**Priority**: high
**Value**: Makes the benchmark measure the framework's real first-iteration value — turning a stakeholder brief into a Vision document — instead of the `quick-doc` toy edit.
**Description**: New `inception-vision` scenario seeds a fresh project + an invented stakeholder brief and drives `openup-create-vision` directly, scoring on a valid `docs/vision.md`. Enablers: driver `--instruction` (hand a procedure its input); self-describing scenarios (`procedure`/`instruction`/`required_markers`, optional `expect_pick`); and a fix so a non-lane procedure run treats the write-fence's "no task" (exit 3) as inapplicable/skip, not a failure. +5 tests.

**Dependencies**: T-080, T-072

**See**: `docs/changes/archive/T-083/plan.md` + `docs-eng-process/reference-driver-benchmark.md`

---

## T-084: Benchmark harness archives each run's deliverable for inspection
**Status**: completed (2026-07-13)
**Priority**: medium
**Value**: A vision batch scored 5/5 clean but the produced `docs/vision.md` files died with the torn-down fixtures — quality was unreadable without `--keep`. Now every run's deliverable survives.
**Description**: Each run copies its `deliverable_file` into `<out>/run-NN.<basename>` (e.g. `run-01.vision.md`) before teardown, recording the path in `deliverable_archived` — so batches keep the artifacts they scored for reading + cross-model diffing. Additive; no scoring change.

**Dependencies**: T-080, T-083

**See**: `docs/changes/archive/T-084/plan.md`

---

## T-085: Benchmark fixture is a clean bootstrapped project, not a repo copy
**Status**: completed (2026-07-13)
**Priority**: high
**Value**: The first live vision run exposed it: `build_fixture` copied the whole repo, so a "new-project" fixture carried our developed `docs/` (project-status, roadmap, history) — the model read *our* iteration status instead of starting fresh.
**Description**: The fixture is now a genuinely bootstrapped project — only the framework trees (`docs-eng-process/`, `scripts/`, git config) + a fresh empty `docs/` + the scenario overlay, like `bootstrap-project.sh`. The repo's own `docs/` is never copied in. +2 tests.

**Dependencies**: T-080, T-083

**See**: `docs/changes/archive/T-085/plan.md`

---

## T-087: Getting-started doc — run your own project with the reference driver + your LLM
**Status**: completed (2026-07-13)
**Priority**: high
**Value**: A practitioner with only a local/OpenAI-compatible LLM (no Claude Code) had no task-oriented guide for running a real project with the reference driver. This provides one for the two common entry points.
**Description**: New `docs-eng-process/getting-started-reference-driver.md` — prerequisites (endpoint + env) + two end-to-end scenarios with copy-paste commands: (A) new project (bootstrap → stakeholder brief → drive create-vision → continue) and (B) existing project adopting OpenUP (install framework, then backfill missing docs from existing code via create-* procedures + `--instruction`). Flags the absence of an automated missing-docs detector and the `next`-loop weight on small local models. Cross-linked from getting-started.md + reference-driver.md.

**Dependencies**: T-072, T-083

**See**: `docs/changes/archive/T-087/plan.md`

---

## T-088: Ship the reference driver in the process-CLI manifest
**Status**: completed (2026-07-13)
**Priority**: high
**Value**: A user following the reference-driver getting-started hit `scripts/openup-agent.py: No such file or directory` after bootstrapping — the driver was never shipped to projects. Now every install path includes it.
**Description**: Added `openup-agent.py` + the `openup_agent/*.py` package to `process-manifest.txt` (the single source of truth every install path copies). The installer already handles nested paths, so no installer change; verified the driver + package install and import cleanly into a fresh scripts/. Stdlib-only → no new deps.

**Dependencies**: T-072, T-087

**See**: `docs/changes/archive/T-088/plan.md`

---

<!-- plan-hook: 2026-07-13 -->
### Planned: Deterministic cycle engine — stop paying the LLM to orchestrate

- **Status**: `planned` (awaiting implementation)
- **Exploration**: [explorations/2026-07-13-deterministic-cycle-engine.md](explorations/2026-07-13-deterministic-cycle-engine.md)
- **Created**: 2026-07-13
- **Goal**: Invert the reference driver's control: a new `openup-agent.py cycle`
  runs one delivery cycle as a **deterministic state machine** over the existing
  scripts (resolve → session → Operations-step executor → gates → completion;
  plan-iteration / assess / milestone paths), dropping to the LLM only at genuine
  judgment points — each as a **fresh, bounded, step-scoped sub-run**. Ceremony
  becomes code; the LLM only authors.
- **Why (measured)**: T-080 benchmark — same local model: `next` (LLM-orchestrated)
  = 37–50 iters / 1–2M tokens / inconsistent; a single authoring procedure = ~8
  iters / ~59k tokens / 3/3 clean. The ~20–30× gap is LLM-interpreted ceremony.
- **Ordered deliverables**: T-089 (cycle core: pick/resume + step executor) →
  T-092 (recovery bridge: degenerate plan-iteration) →
  T-094 (consent-gated replenishment when stuck) →
  T-090 (plan-iteration path) → T-091 (assess + milestone paths + pack
  ceremony/judgment split). Full iteration plan authored per task on promote.
- **Program acceptance (falsifiable)**: on the same local model/scenario, a
  `cycle`-driven ShareShed Inception delivery reaches **≥80% clean-pass at ≤1/10th
  the tokens** of the `next` baseline (T-080 benchmark); gates green; the Claude
  Code path untouched.

---

## T-089: Cycle engine core — deterministic pick/resume + Operations-step executor
**Status**: completed (2026-07-13)
**Priority**: high
**Value**: The heart of the inversion — a weak local model only ever authors one step at a time while code does the ceremony, collapsing token cost ~an order of magnitude and making the loop crash-safe (all inter-step state is already in the repo).
**Description**: New `openup-agent.py cycle --dir <project>`: `board.resolve()` → `openup-session.py begin` → for each unchecked `## Operations` box, dispatch script-steps as code and judgment-steps as bounded fresh `loop.run()` sub-runs (`--instruction` built from the box + role hat + Ring 1 + change folder), tick the box, run gates → deterministic completion (status flip, sync, archive, release). Bench scenario `cycle-quick-doc` proving ≥5× token reduction vs `next` on the same model.

**Dependencies**: T-072, T-080

**See**: `docs/explorations/2026-07-13-deterministic-cycle-engine.md` §3, §6 — full iteration plan authored on promote

---

## T-092: Cycle recovery mode — degenerate plan-iteration bridge (rebuild the missing spec, continue)
**Status**: completed (2026-07-13)
**Priority**: high
**Value**: A `cycle` loop on a real project stalls at exit 7 the moment the board says plan-iteration (my-product, 2026-07-13 live test) — yet the decision already names the next work item. One bounded spec-authoring sub-run turns "cannot proceed deterministically" into "rebuild the missing doc, then continue", keeping the loop end-to-end on local models without resurrecting the 1–2M-token `next` path. Cheap bridge, ordered before the full T-090 generalization.
**Description**: When `openup-board.py resolve` returns `plan-iteration`, `openup-agent.py cycle` runs the T-077 quick-archetype degenerate case in-engine: take the decision's `lane.task` (the next promotable roadmap item), author its `docs/changes/<id>/plan.md` via ONE bounded judgment sub-run carrying the create-task-spec content contract (typed frontmatter incl. `touches`, G/W/T scenarios, `## Operations` boxes authored to the engine's step conventions), gate it (`openup-spec-scenarios.py check` + `check-docs.py`), commit the spec, re-resolve → `pick` → continue the SAME cycle. `assess-iteration` / `milestone-review` keep their typed exit 7 (T-091 scope). Also reconcile the **done-but-unclosed lane** (my-product T-001, 2026-07-13: plan `status: done` with the folder never archived and the task branch never merged to trunk — invisible to `resolve`, so the loop plans NEW work atop an unfinished delivery): detect it before planning and finish its closure ceremony deterministically (archive → merge → sync) — zero LLM. Flag/default decided at promote (leaning: on by default; `--no-recover` opts out to preserve the bare exit-7 signal).

**Dependencies**: T-089

**See**: seeded from the my-product live test (cycle stalls at plan-iteration) — full iteration plan authored on promote

---

## T-094: Cycle recovery — consent-gated LLM replenishment when nothing is promotable
**Status**: completed (2026-07-13)
**Priority**: high
**Value**: Post-T-092 the loop still strands on the one gap recovery can't fix alone: a present-but-exhausted (or fully blocked) roadmap mid-phase. The missing ingredient is product judgment — what's next — which must not be invented silently by an unattended loop; asking the human first keeps the product-manager value-ordering authority intact while making the recovery complete.
**Description**: When `openup-agent.py cycle` (recovery on) hits a **stuck** decision — `noop` with `docs/roadmap.md` present but nothing promotable while the phase's exit criteria are unmet, or a non-advancing recovery round — it asks for consent to run an LLM planning pass: with `--interactive`, a TTY prompt; otherwise an input-request + suspend (exit 5, T-074 machinery), whose answered "yes" resumes the cycle. On consent, ONE bounded **product-manager-hat** sub-run reads vision + roadmap + project status + risk list and appends **1–5 pending roadmap rows, each with a Value rationale** (sanctioned planning-artifact edit), commits, re-resolves → `plan-iteration` → T-092 Case A authors the first spec and the same cycle continues. Proposed rows stay pending/human-editable (consent up front, veto after). An `--auto-replenish` flag may skip the ask for deliberately unattended loops (decided at promote). Deliberately shares its judgment step with T-090's choose-objectives (same PM call via the sad path) — T-090 reuses, not duplicates, it. Fresh-no-roadmap (Inception hint, T-092) and assess/milestone (T-091) are out of scope.

**Dependencies**: T-092

**See**: seeded from the T-092 review conversation (2026-07-13) — full iteration plan authored on promote

---

## T-095: `scripts/next-cycle` — one guided command from empty project to delivery loop
**Status**: completed (2026-07-13)
**Priority**: high
**Value**: A practitioner should need to remember exactly one command. Today the fresh-project path is four manual steps (env exports, brief authoring, a create-vision invocation with a composed --instruction, then cycle) and every typed exit code demands interpretation; the wrapper makes the tooling guide the human instead (asked for verbatim by the user on 2026-07-13: "I want to run a single command like ./scripts/next-cycle and the tooling must guide me").
**Description**: New executable `scripts/next-cycle` (stdlib-only, shipped via process-manifest): loads `.openup/agent.env` (KEY=VALUE) into the environment; if `LLM_API_URL` is missing, prompts for endpoint/model config on a TTY (offering to persist it) or prints a copy-paste setup block; on a fresh project (no vision, no roadmap) with no stakeholder brief, writes a template brief to `docs/inputs/stakeholder-brief.md` and asks the human to fill it; with a filled brief, runs the create-vision Inception step (vision + initial roadmap) via `openup-agent.py run`; otherwise runs ONE `openup-agent.py cycle`, passing `--interactive` when stdin is a TTY; translates every exit code into plain next-step guidance (5 → the request file to answer; 6/7/8 → what to fix; ADVANCED → re-run to continue). Composes the driver only — no new engine behavior.

**Dependencies**: T-094

**See**: full iteration plan authored on promote

---

## T-096: Process-agnostic `next-cycle` — LLM process navigator behind the driver
**Status**: completed (2026-07-13)
**Priority**: high
**Value**: T-095's wrapper hardcodes the pre-Inception state machine (brief → vision → cycle), duplicating process knowledge that lives in the pack — it rots as the process evolves and cannot classify unanticipated project states (partial Inception, an existing codebase adopting OpenUP — the T-087 backfill gap). Owner direction (2026-07-13): the entry point should know NOTHING about the process; navigation moves to an LLM evaluation of the OpenUP workflows against current project state — agnostic and resilient — while the deterministic layers (board resolve, the cycle engine) still answer first, preserving the measured T-080 token/reliability win.
**Description**: (1) Strip all process knowledge from `scripts/next-cycle` — it keeps only env guidance, one driver invocation, and exit translation. (2) New bounded **process-navigator** judgment in the driver: invoked only when the deterministic layers yield nothing actionable (fresh or unclassifiable project — e.g. cycle's no-roadmap noop), it reads `docs-eng-process/process-map.yaml` (T-077), `openup-lifecycle.py status --json`, a deterministic Ring-1 artifact survey (which vision/use-cases/roadmap/architecture files exist), and the procedures index, and returns — as structured file output, the T-072 pattern — the next procedure to run, its `--instruction`, and any **missing human inputs**; the driver then runs that procedure, or raises the missing input as a T-074 input-request (no more hardcoded template briefs). Consent boundary preserved: navigation that authors process artifacts runs directly; anything proposing product scope stays behind the T-094 consent gate. T-095's stage tests are superseded by navigator tests (fix-spec-first: T-095's archived spec notes the supersession).

**Dependencies**: T-095, T-077

**See**: seeded from the T-095 review (owner architecture direction) — full iteration plan authored on promote

---

## T-090: Cycle engine — plan-iteration path
**Status**: completed (2026-07-13)
**Priority**: high
**Value**: Inception/planning stops being the loop's most expensive, least reliable phase on local models — objectives and per-lane specs become small authoring sub-runs while minting, clustering (T-079), lane generation, and the iteration-plan skeleton are code.
**Description**: `cycle` handles `plan-iteration`: derive phase (lifecycle) + mint id + `activities-for` (code); one small LLM sub-run to choose 1–5 objectives; per generated lane, an authoring sub-run for its spec (create-task-spec content); partition + roadmap rows + iteration-plan instance deterministically. The ShareShed Inception flow runs end-to-end through `cycle` on a bootstrapped project.

**Dependencies**: T-089

**See**: `docs/explorations/2026-07-13-deterministic-cycle-engine.md` §3, §6 — full iteration plan authored on promote

---

## T-091: Cycle engine — assess + milestone paths; pack ceremony/judgment split
**Status**: completed (2026-07-13)
**Priority**: medium
**Value**: Cycle reaches full `/openup-next` parity (same sentinels, same human gates) and the prose–code drift risk is closed: ceremony authority moves to the engine, procedures slim to judgment content (what a good artifact looks like), Claude Code path unchanged.
**Description**: `cycle` handles `assess-iteration` (done-ness derived in code; a grading sub-run for non-derivable criteria; feed-back + `## Assessment` appended deterministically) and `milestone-review` (evidence + input-request pause, zero LLM); DONE-sentinel parity; slim the affected procedures' ceremony sections to describe the engine. Program acceptance measured here via the T-080 benchmark.

**Dependencies**: T-089, T-090

**See**: `docs/explorations/2026-07-13-deterministic-cycle-engine.md` §3, §5, §6 — full iteration plan authored on promote

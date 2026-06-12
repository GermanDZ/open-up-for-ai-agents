# Roadmap


<!-- plan-hook: 2026-06-12 -->
### Planned: Clarity, Self-Briefing, and the Sequential Continue-Loop

- **Status**: `planned`
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
| T-018 | `docs/project-config.yaml` context/rules injection (from 2026-05-13 #2) | proposed | medium | — |
| T-019 | Behavior Delta section in the task spec (Added/Modified/Removed vs Ring 1) | proposed | high | T-007 |
| T-020 | Scenario-per-requirement (Given/When/Then) + deterministic validation | proposed | high | T-019 |
| T-021 | Implementation-vs-spec verify step in `/openup-complete-task` | proposed | medium | T-020 |

**Next step**: T-015 ✅, T-016 ✅, T-017 ✅ done — the headline clarity → self-brief → continue-loop path is complete (`scripts/openup-board.py` + `/openup-next` + checkbox Operations). Remaining: **T-018** (D, `project-config.yaml`) is independent and startable anytime; the **T-019 → T-020 → T-021** spec-self-sufficiency + verify chain is the other open thread (T-019 unblocked via done T-007).


<!-- plan-hook: 2026-06-10 -->
### Planned: Process v2 — Mechanize OpenUP for the Claude Code Harness

- **Status**: `in-progress` (Wave 1 started 2026-06-10)
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
### Proposed: OpenSpec Ideas Worth Adopting in OpenUP

- **Status**: `proposed` (analysis only; no tasks created yet)
- **Plan**: [plans/2026-05-13-openspec-ideas-for-openup.md](plans/2026-05-13-openspec-ideas-for-openup.md)
- **Evaluation**: [plans/2026-05-13-openspec-evaluation.md](plans/2026-05-13-openspec-evaluation.md) (SPDD self-grading)
- **Created**: 2026-05-13
- **Notes**: Counterpart to the 2026-04-28 SPDD plan. Item #1 (readiness DAG) is a precondition for un-deferring T-002 (`/openup-sync-spec`); item #5 (explore mode) is complementary to the 2026-04-28 "fix-spec-first" rule.


<!-- plan-hook: 2026-04-28 -->
### In Progress: SPDD Ideas Worth Adopting in OpenUP

- **Status**: `in-progress` (decomposed into tasks; partial implementation)
- **Plan**: [plans/2026-04-28-spdd-ideas-worth-adopting-in-openup.md](plans/2026-04-28-spdd-ideas-worth-adopting-in-openup.md)
- **Evaluation**: [plans/2026-04-28-spdd-evaluation.md](plans/2026-04-28-spdd-evaluation.md) (SPDD self-grading)
- **Created**: 2026-04-28

**Tasks**

| ID | Title | Status | Priority |
|---|---|---|---|
| [T-001](changes/archive/T-001/plan.md) | REASONS task spec — template, skill, rubric | done | high |
| [T-002](changes/T-002/plan.md) | `/openup-sync-spec` — refactor back-propagation | completed (2026-06-11) | medium |
| [T-003](changes/archive/T-003/plan.md) | Suitability "fit" metadata in workflow skills | done | low |
| [T-013](changes/archive/T-013/plan.md) | Fix-spec-first rule for behavior changes (plan item #2) | done (backfilled 2026-06-12) | high |
| [T-014](changes/archive/T-014/plan.md) | Edit artifacts through their skill, not by hand (plan item #5) | done (backfilled 2026-06-12) | low |

**Next step**: pick T-003 (smallest, exercises the new format), then T-001.
T-002 (`/openup-sync-spec`) completed 2026-06-11 — implemented when T-008's readiness DAG un-blocked it.

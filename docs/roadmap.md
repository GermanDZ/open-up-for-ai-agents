# Roadmap


<!-- plan-hook: 2026-06-10 -->
### Planned: Process v2 — Mechanize OpenUP for the Claude Code Harness

- **Status**: `in-progress` (Wave 1 started 2026-06-10)
- **Plan**: [plans/2026-06-10-process-v2-claude-code-harness.md](plans/2026-06-10-process-v2-claude-code-harness.md)
- **Created**: 2026-06-10
- **Evidence base**: Kaze webapp empirical audit (2026-06-10) + 2026 AI-agent SDLC research (AI-DLC, Spec Kit, OpenSpec, BMAD, Kiro)
- **Notes**: Absorbs items #1–#4 of the 2026-05-13 OpenSpec plan (readiness DAG, project-config, per-change folders, archive flow) into workstreams WS4/WS5. T-008 un-defers T-002 (`/openup-sync-spec`).

**Tasks**

| ID | Title | Status | Priority | Depends on |
|---|---|---|---|---|
| T-004 | Model tier map + `model:` frontmatter sweep + scribe/explorer agents | completed (2026-06-10) | high | — |
| T-005 | `.openup/state.json` iteration state file | completed (2026-06-10) | high | — |
| T-006 | Blocking gates + deterministic auto-logging + status sync | planned | high | T-005 |
| T-007 | Three-ring docs scoping (product / changes / session) | planned | medium | — |
| T-008 | Coordination frontmatter + `/openup-readiness` DAG | planned | medium | T-007 |
| T-009 | Worktree-per-task + lease claims + collision pre-flight | planned | medium | T-005, T-008 |
| T-010 | Graded tracks (quick/standard/full) | planned | medium | T-005, T-006 |
| T-011 | Retro cadence trigger + `/openup-create-handoff` | planned | low | T-005 |

**Next step**: Wave 1 — `/openup-start-iteration task_id: T-004` (smallest, immediate cost win), then T-005 (foundation for all gates).


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
| [T-001](tasks/T-001-reasons-task-spec.md) | REASONS task spec — template, skill, rubric | done | high |
| [T-002](tasks/T-002-sync-spec-skill.md) | `/openup-sync-spec` — refactor back-propagation | deferred | medium |
| [T-003](tasks/T-003-suitability-stars.md) | Suitability "fit" metadata in workflow skills | done | low |

**Done (out-of-band, in `.claude/` — gitignored)**

- ✅ Plan item #2 — Fix-spec-first rule in `CLAUDE.openup.md` + dev/architect teammates
- ✅ Plan item #5 — "Edit artifacts through their skill" rule in `CLAUDE.openup.md`

**Next step**: pick T-003 (smallest, exercises the new format), then T-001.
T-002 stays deferred until drift is observed.

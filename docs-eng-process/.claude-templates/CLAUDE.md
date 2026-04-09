# OpenUP Agent Team Instructions (Short)

Goal: keep context small. This file is a quick index; details live in docs.

## Critical Rule
All work must be in an iteration.
- For normal work: `/openup-start-iteration` then `/openup-complete-task`
- For small changes: `/openup-quick-task`
- For complex multi-role work: `/openup-orchestrate`

## Quick Start
- New to OpenUP: `/openup-init`
- Teams are **active by default** — `/openup-start-iteration` auto-selects the right team for the current phase. No manual team setup needed.

## Roles (what they focus on)
- analyst: requirements, use cases
- architect: architecture decisions
- developer: implementation, unit tests
- project-manager: planning, risk list, **orchestration**
- tester: test planning and execution

## Where to Look Next (full docs)
- Skills and workflows: docs-eng-process/skills-guide.md
- Agent workflow: docs-eng-process/agent-workflow.md
- Team configs: docs-eng-process/teams-guide.md
- Quick start guide: docs-eng-process/QUICKSTART.md

## Common Commands (minimal list)
- Phase skills: `/openup-inception`, `/openup-elaboration`, `/openup-construction`, `/openup-transition`
- Artifacts: `/openup-create-vision`, `/openup-create-use-case`, `/openup-create-architecture-notebook`
- Workflow: `/openup-start-iteration`, `/openup-complete-task`, `/openup-quick-task`, `/openup-orchestrate`, `/openup-phase-review`
- Assessment: `/openup-assess-completeness` (rubric-based, per-criterion grading)

## Memory & Context Continuity
- At session start, read `.claude/memory/iteration-learnings.md` for decisions from past iterations
- Check `docs/plans/` for any plans with `planned` status — these are the authoritative spec
- Plans saved via plan mode are automatically captured to `docs/plans/` and tracked in `docs/roadmap.md`

## Quality: Rubric-Based Assessment
Work products are graded against explicit rubrics in `.claude/rubrics/`:
- `use-case-rubric.md`, `architecture-notebook-rubric.md`, `iteration-plan-rubric.md`
- `test-plan-rubric.md`, `vision-rubric.md`
Each criterion is graded ✅ satisfied / ❌ gap — [specific description]. Fix gaps before marking complete.

## Notes
- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set automatically via settings.json
- Project state docs: docs/project-status.md, docs/roadmap.md

# OpenUP Agent Team Instructions (Short)

Goal: keep context small. This file is a quick index; details live in docs.

## Critical Rule
All work must be in an iteration.
- For normal work: `/openup-start-iteration` then `/openup-complete-task`
- For small changes: `/openup-quick-task`

## Quick Start
- New to OpenUP: `/openup-init`
- Need a team: "Create an OpenUP agent team with [roles] to [task]"

## Roles (what they focus on)
- analyst: requirements, use cases
- architect: architecture decisions
- developer: implementation, unit tests
- project-manager: planning, risk list
- tester: test planning and execution

## Where to Look Next (full docs)
- Skills and workflows: docs-eng-process/skills-guide.md
- Agent workflow: docs-eng-process/agent-workflow.md
- Team configs: docs-eng-process/teams-guide.md
- Quick start guide: docs-eng-process/QUICKSTART.md

## Common Commands (minimal list)
- Phase skills: `/openup-inception`, `/openup-elaboration`, `/openup-construction`, `/openup-transition`
- Artifacts: `/openup-create-vision`, `/openup-create-use-case`, `/openup-create-architecture-notebook`
- Workflow: `/openup-start-iteration`, `/openup-complete-task`, `/openup-quick-task`, `/openup-phase-review`

## Notes
- Enable agent teams if needed: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- Project state docs: docs/project-status.md, docs/roadmap.md

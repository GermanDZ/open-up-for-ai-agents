# OpenUP Agent Team Instructions (Short)

Goal: keep context small. This file is a quick index; details live in docs.

## Critical Rules

**All delivery work must be in an iteration. No exceptions.**
- For normal work: `/openup-start-iteration` → work → `/openup-complete-task`
- For small changes: `/openup-quick-task`
- For complex multi-role work: `/openup-orchestrate`
- For **pre-delivery exploration** (is the problem real? what's the right shape?): `/openup-explore` — produces notes that may seed a proposal, not a deliverable.

**Never offer to skip or bypass the process.** "Just commit" is not a valid option.
If the work is small, use `/openup-quick-task` — that IS the lightweight path.
If the user is *thinking*, not *delivering*, use `/openup-explore` — that is the sanctioned home for pre-iteration notes.
If the user asks to skip, redirect: "Let me run `/openup-quick-task` instead — it's the fast path that keeps the project state consistent." (Or `/openup-explore` if the work is investigative rather than deliverable.)

**When the user asks to do a task, act as Project Manager first.**
- Read `docs/project-status.md` and `docs/roadmap.md`
- Run `/openup-start-iteration` — this deploys the team as step 3 (mandatory, before any code)
- The PM coordinates: decompose the task, brief each specialist, collect outputs, synthesize
- Never start coding or modifying files without a team deployed

**Fix the spec first when behavior changes.**
- **Behavior change** (logic, scope, acceptance criteria differ from artifact): update the use case / iteration plan / task description **first**, then change code.
- **Refactor only** (no behavior change): change code first, then back-propagate to artifacts via `/openup-sync-spec` (when available) or by re-running the originating `/openup-create-*` skill.
- This keeps specs and code from drifting silently. If you find yourself "just tweaking" code that contradicts the spec, stop and update the spec.

**Edit artifacts through their skill, not by hand.**
- Use cases, iteration plans, architecture notebook, vision, test plan: changes go through the relevant `/openup-create-*` or `/openup-detail-*` skill so the rubric in `.claude/rubrics/` is re-applied.
- Direct hand-edits silently bypass rubric criteria; only acceptable for typo-level fixes.

## Token-Efficiency Protocol (Mandatory)
- Run one subtask per session; start a fresh session when scope changes.
- Keep one active orchestrator (project-manager by default); spawn specialists only for bounded work.
- Allow status updates only at `started`, `blocked`, and `done`.
- Use compact handoffs (max 6 bullets): `decision`, `diff summary`, `risks`, `next action`.
- Do not resend full task lists after kickoff; reference task IDs and share only deltas.
- Use lightweight models for coordination; escalate only for complex architecture/debug/codegen.
- Batch implementation and tests before reporting back.
- Set a token budget per lane (PM/dev/test); checkpoint and restart with a fresh session if exceeded.

Default cycle:
`/openup-start-iteration` -> assign one subtask -> specialist completes and reports once -> PM routes next step -> new session on scope change.

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
- Workflow: `/openup-start-iteration`, `/openup-complete-task`, `/openup-quick-task`, `/openup-orchestrate`, `/openup-phase-review`, `/openup-explore`
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

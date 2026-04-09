⚠️ **CRITICAL: READ THIS BEFORE SPAWNING TEAMMATES** ⚠️

## STOP! DO NOT SPAWN TEAMMATES FIRST!

**The correct OpenUP workflow is:**

1. ✅ **FIRST**: Initialize the iteration with `/openup-start-iteration`
2. ✅ **SECOND**: Spawn teammates
3. ✅ **THIRD**: Coordinate work

**❌ WRONG:**
```
"Create an OpenUP team..." → Spawns teammates immediately → NO ITERATION
```

**✅ RIGHT:**
```
"Create an OpenUP team..." → /openup-start-iteration → Spawns teammates
```

**Even when the user says "create a team", you MUST initialize the iteration FIRST.**

The team lead's first action should always be calling `/openup-start-iteration`, not spawning teammates.

---

## Token-Efficient Team Protocol (Mandatory)

To reduce token usage while preserving quality, the team lead and all teammates MUST follow these rules:

1. **One subtask per session**: open a fresh session for each roadmap/task item. Do not keep long-running multi-task sessions.
2. **Single orchestrator**: keep one active coordinator (usually project-manager). Spawn specialist agents only for bounded work, then stop them.
3. **Milestone-only updates**: status messages are allowed only at `started`, `blocked`, and `done`. Do not send heartbeat or idle notifications.
4. **Compact handoffs**: every handoff must be max 6 bullets with only: `decision`, `diff summary`, `risks`, `next action`.
5. **No repeated large context**: do not resend full task lists/specs after kickoff. Refer by task ID and send only deltas.
6. **Model tiering**: use lightweight models for coordination/planning; escalate to stronger models only for complex design/debug/codegen.
7. **Batch before reporting**: complete a meaningful chunk (code + tests for the subtask) before reporting back.
8. **Budget gate**: define a token budget per iteration lane (PM/dev/test). If exceeded, checkpoint and restart with a fresh session.

Default execution cycle:
`/openup-start-iteration` -> assign one subtask -> specialist completes and reports once -> PM decides next subtask -> new session when scope changes.

---

# OpenUP Full Team Configuration

This is an agent team configuration for OpenUP (Open Unified Process) methodology.

⚠️ **MANDATORY FIRST STEP FOR TEAM LEAD** ⚠️

Before spawning any teammates, the team lead MUST initialize an iteration with `/openup-start-iteration`.
All work must be tracked in an iteration, even exploratory work.

---


## Team Overview

The OpenUP full team consists of all core roles working together to deliver software iteratively.

## Team Members

### analyst
- **Focus**: Requirements gathering, stakeholder communication, understanding problems
- **Key Work Products**: Vision, Use Cases, System-Wide Requirements, Glossary
- **Collaborates With**: Architect (technical feasibility), Developer (implementation input), Tester (acceptance criteria)
- **Reference**: `.claude/teammates/analyst.md`

### architect
- **Focus**: Architecture design, technical decisions, architecture documentation
- **Key Work Products**: Architecture Notebook
- **Collaborates With**: Analyst (requirements understanding), Developer (implementation feedback), Project Manager (planning)
- **Reference**: `.claude/teammates/architect.md`

### developer
- **Focus**: Implementation, unit testing, design, integration
- **Key Work Products**: Design, Implementation (code), Developer Tests
- **Collaborates With**: Architect (architecture constraints), Analyst (requirements input), Tester (test coverage)
- **Reference**: `.claude/teammates/developer.md`

### project-manager
- **Focus**: Planning, coordination, risk management, stakeholder communication
- **Key Work Products**: Project Plan, Iteration Plan, Risk List, Work Items List
- **Collaborates With**: All roles for planning and status tracking
- **Reference**: `.claude/teammates/project-manager.md`

### tester
- **Focus**: Test planning, test implementation, test execution, results analysis
- **Key Work Products**: Test Cases, Test Scripts, Test Logs
- **Collaborates With**: Analyst (acceptance criteria), Developer (test implementation), Architect (system understanding)
- **Reference**: `.claude/teammates/tester.md`

## Team Workflow

**CRITICAL FIRST STEP**: Before any work begins, the team lead MUST use `/openup-start-iteration` to initialize the iteration. All work must be tracked as part of an iteration.

The team works iteratively through these phases:

1. **Inception**: Define scope, vision, feasibility (led by Analyst + Project Manager)
2. **Elaboration**: Establish architecture baseline (led by Architect + Developer)
3. **Construction**: Build system incrementally (led by Developer + Tester)
4. **Transition**: Deploy to users (led by Developer + Project Manager)

## Creating This Team

To create an OpenUP full team, use this prompt:

```
Create an OpenUP agent team with all roles: analyst, architect, developer, project-manager, and tester.

Each teammate should follow their role instructions in .claude/teammates/{role}.md.

Spawn teammates for:
- analyst: to gather requirements and represent stakeholder concerns
- architect: to define software architecture and make technical decisions
- developer: to implement the solution
- project-manager: to lead planning and coordinate work
- tester: to design and execute tests

The team should work collaboratively through the OpenUP iterative workflow.
```

## Task Assignment Guidelines

When assigning tasks to teammates:

- **Requirements tasks** → analyst
- **Architecture tasks** → architect
- **Implementation tasks** → developer
- **Planning/tracking tasks** → project-manager
- **Testing tasks** → tester
- **Cross-cutting tasks** → Assign to primary role, involve others as needed

## Collaboration Patterns

- **Analyst ↔ Architect**: Requirements feasibility, architectural implications
- **Architect ↔ Developer**: Architecture constraints, implementation feedback
- **Developer ↔ Tester**: Test coverage, bug fixing, TDD
- **All ↔ Project Manager**: Status updates, planning, blockers
- **Tester ↔ Analyst**: Acceptance criteria, requirements validation

## Pull Request Workflow

After task completion, the team lead (typically project-manager or phase lead) ensures:
1. PR is created with proper task context linking to roadmap
2. Use `/complete-task task_id: T-XXX create_pr: true` to complete task and create PR
3. Or use `/create-pr task_id: T-XXX` to create PR manually
4. Verify PR description includes task context, changes summary, and testing checklist
5. All teammates review PR before merge

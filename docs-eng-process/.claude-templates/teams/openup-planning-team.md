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

# OpenUP Planning Team Configuration

This is a task-specific team configuration for iteration planning and roadmap management.

⚠️ **RECOMMENDED: Start with an Iteration** ⚠️

For proper tracking and traceability, the team lead should start an iteration before spawning teammates:

```
/openup-start-iteration goal: "Implement feature"
# Or with a task ID if you have a roadmap:
/openup-start-iteration task_id: T-005
# Then spawn teammates...
```

**If you don't have a roadmap yet**, you can spawn teammates directly and track work informally.

---


## Team Purpose

Plan iterations, update the roadmap, assess priorities, and coordinate project planning activities.

## Team Members

### project-manager (Lead)
- **Focus**: Lead planning session, coordinate roadmap updates
- **Key Activities**: Iteration planning, task prioritization, risk assessment
- **Collaborates With**: Analyst (requirements scope), Architect (technical feasibility), Developer (estimates)
- **Reference**: `.claude/teammates/project-manager.md`

### analyst
- **Focus**: Review and prioritize requirements
- **Key Activities**: Requirements analysis, stakeholder input, value assessment
- **Collaborates With**: Project Manager (prioritization), Architect (feasibility)
- **Reference**: `.claude/teammates/analyst.md`

### architect (As needed)
- **Focus**: Assess technical feasibility and dependencies
- **Key Activities**: Technical analysis, dependency identification, effort assessment
- **Collaborates With**: Analyst (requirements feasibility), Project Manager (planning)
- **Reference**: `.claude/teammates/architect.md`

### developer (As needed)
- **Focus**: Provide effort estimates for development tasks
- **Key Activities**: Task estimation, technical assessment
- **Collaborates With**: Project Manager (estimates), Architect (technical details)
- **Reference**: `.claude/teammates/developer.md`

## Planning Process

**CRITICAL FIRST STEP**: Before starting planning work, the team lead (project-manager) MUST use `/openup-start-iteration` to initialize the iteration. All work must be tracked as part of an iteration.

1. **Review Current State**
   - Review `docs/project-status.md` for current phase and iteration
   - Review `docs/roadmap.md` for pending tasks
   - Assess what was accomplished in the previous iteration

2. **Identify Candidates**
   - Analyst identifies high-value requirements
   - Architect identifies technical debt and architectural work
   - Project Manager reviews risks and dependencies

3. **Assess Feasibility**
   - Architect assesses technical feasibility
   - Developer provides effort estimates
   - Project Manager assesses resource availability

4. **Prioritize Tasks**
   - Prioritize by value, risk, and dependencies
   - Balance feature work with technical debt
   - Ensure iteration goals are achievable

5. **Create Iteration Plan**
   - Define iteration goal
   - Select tasks for the iteration
   - Assign tasks to roles
   - Define success criteria

6. **Update Documentation**
   - Update `docs/roadmap.md` with task status
   - Create iteration plan document
   - Update `docs/project-status.md`

## Creating This Team

To create an OpenUP Planning team, use this prompt:

```
Create an OpenUP agent team for iteration planning.

Spawn teammates for:
- project-manager: to lead the planning session
- analyst: to review and prioritize requirements
- architect: to assess technical feasibility

The project-manager should lead the planning session and update the roadmap.
The analyst should review requirements and help prioritize based on value.
The architect should assess technical feasibility and identify dependencies.
```

## Task Assignment Guidelines

- **Planning coordination** → project-manager
- **Requirements analysis** → analyst
- **Technical feasibility** → architect
- **Effort estimation** → developer
- **Prioritization** → project-manager + analyst
- **Risk assessment** → project-manager

## Collaboration Patterns

- **Project Manager ↔ Analyst**: Value vs. effort trade-offs
- **Project Manager ↔ Architect**: Technical feasibility assessment
- **Analyst ↔ Architect**: Requirements vs. technical constraints
- **All**: Task prioritization and iteration goal definition

## Example Usage

```
Create an OpenUP planning team for iteration planning.

The team should:
1. Review the current iteration status
2. Identify candidate tasks for the next iteration
3. Assess technical feasibility and effort
4. Prioritize tasks based on value and dependencies
5. Create the iteration plan
6. Update the roadmap and project status
```

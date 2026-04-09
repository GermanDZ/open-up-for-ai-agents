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

# OpenUP Feature Team Configuration

This is a task-specific team configuration for implementing new features end-to-end.

## Team Purpose

Implement a new feature from requirements through design, implementation, and testing.

## Team Members

### analyst
- **Focus**: Gather requirements, define acceptance criteria
- **Key Activities**: Requirements elicitation, use case creation, stakeholder communication
- **Collaborates With**: Architect (feasibility), Tester (acceptance criteria)
- **Reference**: `.claude/teammates/analyst.md`

### architect
- **Focus**: Design feature architecture, make technical decisions
- **Key Activities**: Architecture design, technical specifications, impact assessment
- **Collaborates With**: Analyst (requirements understanding), Developer (implementation guidance)
- **Reference**: `.claude/teammates/architect.md`

### developer (Lead)
- **Focus**: Implement the feature with tests
- **Key Activities**: Implementation, unit testing, integration
- **Collaborates With**: Architect (design constraints), Tester (test coverage)
- **Reference**: `.claude/teammates/developer.md`

### tester
- **Focus**: Create tests, validate feature meets requirements
- **Key Activities**: Test planning, test creation, test execution
- **Collaborates With**: Analyst (acceptance criteria), Developer (test coverage)
- **Reference**: `.claude/teammates/tester.md`

## Feature Implementation Process

**CRITICAL FIRST STEP**: Before starting feature work, the team lead (developer) MUST use `/openup-start-iteration` to initialize the iteration. All work must be tracked as part of an iteration.

1. **Requirements**
   - Analyst gathers requirements for the feature
   - Defines use cases and acceptance criteria
   - Creates input request for stakeholder questions if needed

2. **Design**
   - Architect designs the feature architecture
   - Identifies technical decisions and constraints
   - Creates design specifications

3. **Implementation**
   - Developer implements the feature following the design
   - Writes unit tests for the implementation
   - Integrates with existing code

4. **Testing**
   - Tester creates test cases based on acceptance criteria
   - Executes tests and validates the feature
   - Reports bugs to developer

5. **Refinement**
   - Developer fixes bugs found by tester
   - Tester validates fixes
   - Analyst confirms feature meets requirements

6. **Documentation**
   - Update relevant documentation
   - Create user documentation if needed
   - Update architecture and design docs

7. **Pull Request**
   - Team Lead (developer) ensures PR is created with proper task context
   - Use `/complete-task task_id: T-XXX create_pr: true` to complete task and create PR
   - Or use `/create-pr task_id: T-XXX` to create PR manually
   - Verify PR description links to roadmap task and includes context

## Creating This Team

To create an OpenUP Feature team, use this prompt:

```
Create an OpenUP agent team for feature implementation.

Spawn teammates for:
- analyst: to gather requirements and define acceptance criteria
- architect: to design the feature architecture
- developer: to implement the feature
- tester: to create and execute tests

The analyst should first create use cases for this feature.
Then the architect should design it.
Then the developer should implement it with tests.
Finally, the tester should validate the feature meets requirements.
```

## Task Assignment Guidelines

- **Requirements** → analyst
- **Architecture/design** → architect
- **Implementation** → developer
- **Testing** → tester
- **Documentation** → All (based on artifact type)
- **PR creation and coordination** → Team Lead (developer)

## Collaboration Patterns

- **Analyst → Architect**: Requirements → architecture design
- **Architect → Developer**: Design → implementation
- **Developer → Tester**: Implementation → test validation
- **Tester → Analyst**: Validation → requirements confirmation
- **All**: Documentation updates

## Example Usage

```
Create an OpenUP feature team to implement the user profile feature.

The team should:
1. Analyst: Gather requirements and define what the user profile should include
2. Architect: Design how the user profile feature integrates with the system
3. Developer: Implement the user profile with CRUD operations
4. Tester: Create tests to validate the feature works correctly
```

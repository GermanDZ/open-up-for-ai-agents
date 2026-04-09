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

# OpenUP Transition Team Configuration

This is an agent team configuration for the Transition phase of OpenUP.

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


## Phase Overview

**Transition** - Deploy to users. Deploy the system to users and ensure user satisfaction.

## Team Members

### tester (Lead)
- **Focus**: Final testing, validation, quality assurance for release
- **Key Work Products**: Test Cases, Test Logs, Test Reports
- **Collaborates With**: Developer (bug fixes), Analyst (user acceptance)
- **Reference**: `.claude/teammates/tester.md`

### developer
- **Focus**: Bug fixes, deployment support, final integration
- **Key Work Products**: Bug fixes, Deployment scripts
- **Collaborates With**: Tester (fixing bugs), Project Manager (deployment coordination)
- **Reference**: `.claude/teammates/developer.md`

### project-manager (Lead)
- **Focus**: Deployment coordination, user communication, release management
- **Key Work Products**: Deployment Plan, Release Notes
- **Collaborates With**: All roles for coordination
- **Reference**: `.claude/teammates/project-manager.md`

### analyst (As needed)
- **Focus**: User feedback, acceptance, documentation
- **Key Work Products**: User documentation, Feedback analysis
- **Collaborates With**: Tester (acceptance criteria)
- **Reference**: `.claude/teammates/analyst.md`

## Phase Objectives

1. Deploy the system to users
2. Train users and support staff
3. Fix defects found during testing
4. Complete user documentation
5. Obtain user acceptance

## Completion Criteria

- [ ] Product is ready for release
- [ ] All acceptance tests pass
- [ ] Deployment documentation complete
- [ ] Support materials ready
- [ ] Stakeholder sign-off obtained

## Creating This Team

To create an OpenUP Transition team, use this prompt:

```
Create an OpenUP agent team for the Transition phase.

Spawn teammates for:
- tester: to lead final testing and validation
- developer: to fix bugs and support deployment
- project-manager: to coordinate deployment and release

The tester should conduct final testing and ensure quality.
The developer should fix any bugs found and support deployment.
The project-manager should coordinate the deployment and communication.
```

## Typical Workflow

**CRITICAL FIRST STEP**: Before starting transition work, the team lead (tester or project-manager) MUST use `/openup-start-iteration` to initialize the iteration. All work must be tracked as part of an iteration.

1. **Tester** conducts comprehensive testing (beta, performance, security)
2. **Developer** fixes bugs found during testing
3. **Tester** validates fixes and creates test reports
4. **Project Manager** prepares deployment plan and coordinates release
5. **Analyst** (if needed) completes user documentation and gathers feedback
6. **All** participate in final acceptance and sign-off

## Task Assignment Guidelines

- **Final testing** → tester
- **Bug fixes** → developer
- **Deployment coordination** → project-manager
- **User documentation** → analyst
- **Training and support** → project-manager + analyst

## Collaboration Patterns

- **Tester ↔ Developer**: Bug finding and fixing
- **Project Manager ↔ All**: Deployment coordination and communication
- **Analyst ↔ Users**: Feedback and acceptance
- **All ↔ Stakeholders**: Release approval and sign-off

## Deployment Activities

1. **Final Testing** - Beta testing, performance testing, security testing, UAT
2. **Deployment Preparation** - Deployment scripts, production environment, rollback procedures
3. **User Preparation** - User documentation, training materials, communication
4. **Release** - Execute deployment, monitor issues, provide support

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

# OpenUP Inception Team Configuration

This is an agent team configuration for the Inception phase of OpenUP.

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

**Inception** - Define scope, vision, and feasibility. Understand what to build and identify key risks.

## Team Members

### analyst (Lead)
- **Focus**: Requirements gathering, stakeholder communication, vision definition
- **Key Work Products**: Vision, Use Cases (20-30%), Risk List, Project Plan
- **Collaborates With**: Project Manager (planning), Architect (feasibility assessment)
- **Reference**: `.claude/teammates/analyst.md`

### project-manager (Lead)
- **Focus**: Planning, coordination, risk management, stakeholder communication
- **Key Work Products**: Project Plan, Work Items List, Risk List
- **Collaborates With**: Analyst (requirements scope), Stakeholders (communication)
- **Reference**: `.claude/teammates/project-manager.md`

### architect (As needed)
- **Focus**: Technical feasibility assessment, initial architectural considerations
- **Key Work Products**: Initial architecture assessment
- **Collaborates With**: Analyst (requirements feasibility)
- **Reference**: `.claude/teammates/architect.md`

## Phase Objectives

1. Define the project's vision
2. Understand the problem to be solved
3. Identify key stakeholders
4. Define initial scope
5. Identify major risks
6. Demonstrate viability with a business case

## Completion Criteria

- [ ] Vision document approved by stakeholders
- [ ] Key use cases identified (20-30% detailed)
- [ ] Major risks documented with mitigation strategies
- [ ] Initial project plan with cost/schedule estimates
- [ ] Business case demonstrates viability
- [ ] Stakeholder agreement to proceed

## Creating This Team

To create an OpenUP Inception team, use this prompt:

```
Create an OpenUP agent team for the Inception phase.

Spawn teammates for:
- analyst: to lead requirements gathering and vision definition
- project-manager: to lead planning and coordination

The analyst should create the vision document and identify key use cases.
The project-manager should create the initial project plan and risk list.
```

## Typical Workflow

**CRITICAL FIRST STEP**: Before starting inception work, the team lead (analyst or project-manager) MUST use `/openup-start-iteration` to initialize the iteration. All work must be tracked as part of an iteration.

1. **Analyst** gathers requirements and creates initial vision
2. **Project Manager** creates initial project plan and risk list
3. **Analyst** identifies key use cases (20-30% detail)
4. **Architect** (if needed) assesses technical feasibility
5. **Analyst** and **Project Manager** present to stakeholders for approval

## Task Assignment Guidelines

- **Vision and requirements** → analyst
- **Planning and risk management** → project-manager
- **Technical feasibility** → architect
- **Business case** → analyst + project-manager

## Collaboration Patterns

- **Analyst ↔ Project Manager**: Scope vs. schedule trade-offs
- **Analyst ↔ Architect**: Requirements feasibility assessment
- **All ↔ Stakeholders**: Communication and approval gathering

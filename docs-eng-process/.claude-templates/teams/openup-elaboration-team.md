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

# OpenUP Elaboration Team Configuration

This is an agent team configuration for the Elaboration phase of OpenUP.

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

**Elaboration** - Establish architecture baseline. Design and implement the architecture, resolve high-risk elements.

## Team Members

### architect (Lead)
- **Focus**: Architecture design, technical decisions, architecture documentation
- **Key Work Products**: Architecture Notebook, Design documents
- **Collaborates With**: Developer (implementation feedback), Analyst (requirements understanding)
- **Reference**: `.claude/teammates/architect.md`

### developer (Lead)
- **Focus**: Architectural baseline implementation, spike solutions, prototyping
- **Key Work Products**: Implementation (code), Developer Tests
- **Collaborates With**: Architect (architecture constraints), Tester (validation)
- **Reference**: `.claude/teammates/developer.md`

### tester
- **Focus**: Test planning, architecture validation through testing
- **Key Work Products**: Test Cases, Test Scripts
- **Collaborates With**: Architect (testability), Developer (test implementation)
- **Reference**: `.claude/teammates/tester.md`

### analyst (As needed)
- **Focus**: Detailed requirements for critical use cases
- **Key Work Products**: Detailed Use Cases (80%)
- **Collaborates With**: Architect (requirements for architecture)
- **Reference**: `.claude/teammates/analyst.md`

## Phase Objectives

1. Design and validate the architecture
2. Detail the critical use cases
3. Implement and test the architectural baseline
4. Refine the project plan with accurate estimates
5. Mitigate high-priority risks

## Completion Criteria

- [ ] Architecture notebook completed
- [ ] Critical use cases detailed (80%)
- [ ] Technical risks identified and mitigated
- [ ] Prototype(s) validated key architectural decisions
- [ ] Project plan refined with accurate estimates
- [ ] Stakeholder agreement on architecture

## Creating This Team

To create an OpenUP Elaboration team, use this prompt:

```
Create an OpenUP agent team for the Elaboration phase.

Spawn teammates for:
- architect: to lead architecture design
- developer: to implement the architectural baseline
- tester: to validate the architecture through testing

The architect should create the architecture notebook and design documents.
The developer should implement the architectural baseline and create spike solutions.
The tester should create test cases and validate architectural decisions.
```

## Typical Workflow

**CRITICAL FIRST STEP**: Before starting elaboration work, the team lead (architect) MUST use `/openup-start-iteration` to initialize the iteration. All work must be tracked as part of an iteration.

1. **Architect** designs architecture and creates architecture notebook
2. **Analyst** (if needed) details critical use cases
3. **Developer** implements architectural baseline
4. **Tester** creates and executes tests to validate architecture
5. **Architect** and **Developer** refine architecture based on findings
6. **Project Manager** (if needed) updates project plan with accurate estimates

## Task Assignment Guidelines

- **Architecture design** → architect
- **Implementation** → developer
- **Testing** → tester
- **Detailed requirements** → analyst
- **Risk mitigation** → architect + developer

## Collaboration Patterns

- **Architect ↔ Developer**: Architecture constraints vs. implementation reality
- **Developer ↔ Tester**: Implementation vs. test coverage
- **Architect ↔ Tester**: Architecture testability
- **Architect ↔ Analyst**: Requirements vs. architectural implications

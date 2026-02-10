# OpenUP Elaboration Team Configuration

This is an agent team configuration for the Elaboration phase of OpenUP.

⚠️ **MANDATORY FIRST STEP FOR TEAM LEAD** ⚠️

**BEFORE spawning any teammates, the team lead MUST:**

1. Use `/openup-start-iteration task_id: XXX` to initialize the iteration
2. Only AFTER the iteration is started, then spawn teammates
3. Do NOT skip this step - all work must be tracked in iterations

**Example correct flow:**
```
/openup-start-iteration task_id: T-005
# Then spawn teammates...
```

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

# OpenUP Full Team Configuration

This is an agent team configuration for OpenUP (Open Unified Process) methodology.

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

# OpenUP Construction Team Configuration

This is an agent team configuration for the Construction phase of OpenUP.

## Phase Overview

**Construction** - Build the system incrementally. Implement all remaining features iteratively until ready for deployment.

## Team Members

### developer (Lead)
- **Focus**: Feature implementation, unit testing, integration
- **Key Work Products**: Implementation (code), Developer Tests, Design
- **Collaborates With**: Tester (test coverage), Architect (technical guidance)
- **Reference**: `.claude/teammates/developer.md`

### tester (Lead)
- **Focus**: Test planning, test implementation, test execution, quality assurance
- **Key Work Products**: Test Cases, Test Scripts, Test Logs
- **Collaborates With**: Developer (test implementation), Analyst (acceptance criteria)
- **Reference**: `.claude/teammates/tester.md`

### architect (As needed)
- **Focus**: Technical guidance, architecture adherence, code reviews
- **Key Work Products**: Architecture updates, Design reviews
- **Collaborates With**: Developer (implementation guidance)
- **Reference**: `.claude/teammates/architect.md`

### analyst (As needed)
- **Focus**: Requirements clarification, acceptance criteria
- **Key Work Products**: Requirements updates, Use case clarifications
- **Collaborates With**: Tester (acceptance criteria), Developer (requirements understanding)
- **Reference**: `.claude/teammates/analyst.md`

## Phase Objectives

1. Implement all remaining features
2. Iteratively test and refine the system
3. Prepare for beta testing
4. Complete user documentation
5. Achieve acceptable quality levels

## Completion Criteria

- [ ] Product is stable enough for beta testing
- [ ] Alpha test results documented
- [ ] Critical issues resolved
- [ ] User documentation is adequate
- [ ] Stakeholder agreement to deploy to beta users

## Creating This Team

To create an OpenUP Construction team, use this prompt:

```
Create an OpenUP agent team for the Construction phase.

Spawn teammates for:
- developer: to lead implementation
- tester: to lead testing and quality assurance

The developer should implement features from the roadmap with tests.
The tester should create test cases, execute tests, and track quality metrics.
```

## Typical Workflow

**CRITICAL FIRST STEP**: Before starting construction work, the team lead (developer) MUST use `/openup-start-iteration` to initialize the iteration. All work must be tracked as part of an iteration.

Each iteration:

1. **Developer** implements features with tests
2. **Tester** creates and executes test cases
3. **Developer** fixes bugs found by tester
4. **Tester** validates fixes and updates test results
5. **Architect** (if needed) provides technical guidance
6. **Analyst** (if needed) clarifies requirements
7. **Team Lead** ensures PR is created after task completion:
   - Use `/complete-task task_id: T-XXX create_pr: true` to complete task and create PR
   - Or use `/create-pr task_id: T-XXX` to create PR manually
   - Verify PR description includes task context from roadmap

## Task Assignment Guidelines

- **Feature implementation** → developer
- **Testing and quality** → tester
- **Technical guidance** → architect
- **Requirements clarification** → analyst
- **PR creation and coordination** → Team Lead (developer)

## Collaboration Patterns

- **Developer ↔ Tester**: Implementation vs. test coverage, bug fixing
- **Developer ↔ Architect**: Implementation vs. architecture adherence
- **Tester ↔ Analyst**: Acceptance criteria validation
- **All ↔ Project Manager**: Status updates (if PM is on team)

## Iteration Focus

Each construction iteration should:
1. Select features from the roadmap
2. Implement with tests
3. Review and validate
4. Update documentation
5. Prepare for next iteration

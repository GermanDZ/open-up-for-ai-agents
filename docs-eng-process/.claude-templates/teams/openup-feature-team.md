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

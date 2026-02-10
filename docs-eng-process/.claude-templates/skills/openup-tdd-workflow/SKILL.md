---
name: openup-tdd-workflow
description: Guide Test-Driven Development cycle adapted for AI agents
arguments:
  - name: phase
    description: TDD phase (red, green, refactor, full)
    required: false
  - name: feature
    description: Feature or component to implement
    required: true
---

# TDD Workflow

This skill guides you through the Test-Driven Development (TDD) cycle, adapted for AI agent workflows. TDD follows a red-green-refactor cycle to ensure code is testable and tested from the start.

## When to Use

Use this skill when:
- Starting feature implementation
- Practicing test-driven development
- Need to ensure test coverage for new code
- Implementing complex logic that benefits from test-first approach
- Refactoring existing code with tests

## When NOT to Use

Do NOT use this skill when:
- Adding tests after implementation is complete (use test generation instead)
- Doing simple bug fixes or trivial changes
- Exploratory coding or prototyping
- Writing documentation or configuration

## Success Criteria

After using this skill, verify:
- [ ] Test is written first (RED phase)
- [ ] Implementation makes test pass (GREEN phase)
- [ ] Code is refactored while tests pass (REFACTOR phase)
- [ ] All tests still pass
- [ ] Code is clean and maintainable

## Process Summary

1. Choose TDD phase or run full cycle
2. Follow phase-specific steps
3. Verify results before proceeding
4. Document TDD log

## Detailed Steps

### 1. Determine Phase

Based on `$ARGUMENTS[phase]`:

| Phase | Description |
|-------|-------------|
| red | Write failing test first |
| green | Implement to make test pass |
| refactor | Clean up code while tests pass |
| full | Run complete red-green-refactor cycle |

### 2. Run Phase-Specific Process

See phase-specific documentation:
- [RED Phase](./red-phase.md) - Write failing test
- [GREEN Phase](./green-phase.md) - Implement feature
- [REFACTOR Phase](./refactor-phase.md) - Improve code quality

### 3. Verify Before Proceeding

After each phase:
- RED: Verify test fails for the right reason
- GREEN: Verify test passes and implementation is minimal
- REFACTOR: Verify tests still pass and code is improved

### 4. Create TDD Log

Document the TDD cycle in `docs/tdd-logs/<feature>-tdd.md`:
- Feature name
- Test cases written
- Implementation notes
- Refactoring performed
- Lessons learned

## TDD Cycle Overview

```
         ┌─────────┐
         │   RED   │ Write failing test
         └────┬────┘
              │
              ▼
      ┌─────────────┐
      │    GREEN    │ Make it pass
      └──────┬──────┘
             │
             ▼
        ┌─────────┐
        │ REFACTOR│ Clean it up
        └────┬────┘
             │
             ▼
        (back to RED for next test)
```

## TDD Principles

1. **Write the test first** - Before any implementation code
2. **Write only enough test to fail** - Minimal test for the requirement
3. **Write only enough code to pass** - Minimal implementation
4. **Refactor** - Improve code without changing behavior
5. **Repeat** - One test/feature at a time

## AI Agent TDD Adaptations

Since AI agents generate code differently:

**RED Phase:**
- Agent writes test specification first
- Test is created and verified to fail
- Test captures requirement in code

**GREEN Phase:**
- Agent generates minimal implementation
- Implementation is verified against test
- Only what's needed to pass is added

**REFACTOR Phase:**
- Agent reviews code for improvements
- Refactoring is applied
- Tests verify behavior unchanged

## Output

Returns a summary of:
- TDD phase completed
- Test file created/updated
- Implementation file created/updated
- Test results
- Refactoring notes

## Example Usage

```
/openup-tdd-workflow feature: user-authentication phase: red
```

```
/openup-tdd-workflow feature: payment-processing phase: full
```

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Test doesn't fail | Test passes before implementation | Test may be incomplete or already satisfied |
| Can't make test pass | Requirement unclear or impossible | Review test and requirement |
| Tests fail after refactor | Refactoring changed behavior | Revert refactor, try smaller changes |
| Too complex | Trying to do too much at once | Break into smaller tests |

## References

- Test-Driven Development: By Example (Kent Beck)
- TDD Patterns: `docs-eng-process/templates/test-case.md`
- Developer Role TDD tasks: `docs-eng-process/.claude-templates/teammates/developer.md`

## See Also

- [openup-create-test-plan](../openup-artifacts/create-test-plan/SKILL.md) - Create comprehensive test plan
- [openup-complete-task](../complete-task/SKILL.md) - Complete task after TDD cycle
- [openup-detail-use-case](../openup-artifacts/detail-use-case/SKILL.md) - Detail use cases before writing tests

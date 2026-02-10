---
name: openup-tdd-workflow
description: Guide Test-Driven Development cycle adapted for AI agents with a pragmatic approach
arguments:
  - name: phase
    description: TDD phase (red, green, refactor, full)
    required: false
  - name: feature
    description: Feature or component to implement
    required: true
---

# TDD Workflow

This skill guides you through the Test-Driven Development (TDD) cycle, adapted for AI agent workflows with a pragmatic approach.

**Important**: This is a guideline, not a strict process. The goal is quality software, not process purity. TDD follows a red-green-refactor cycle to ensure code is testable and tested from the start.

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
- Doing simple bug fixes or trivial changes (just add tests as needed)
- Exploratory coding or prototyping (tests come later)
- Writing documentation or configuration
- TDD would significantly slow down development without adding value

**Remember**: TDD is a tool, not a mandate. Use it when it helps, skip it when it doesn't.

## Success Criteria

After using this skill, verify:
- [ ] Tests are written (preferably before implementation)
- [ ] Implementation makes tests pass
- [ ] Code is reasonably clean and functional
- [ ] Tests pass before commit

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
| red | Write test first (preferably before implementation) |
| green | Implement to make test pass (commit point) |
| refactor | Clean up code while tests pass (optional for small changes) |
| full | Run complete red-green-refactor cycle |

### 2. Run Phase-Specific Process

See phase-specific documentation:
- [RED Phase](./red-phase.md) - Write failing test
- [GREEN Phase](./green-phase.md) - Implement feature
- [REFACTOR Phase](./refactor-phase.md) - Improve code quality

### 3. Verify Before Proceeding

After each phase:
- RED: Write test first when practical (not mandatory for every case)
- GREEN: Verify test passes before committing (commit when green)
- REFACTOR: Verify tests still pass, refactor is optional for small changes

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
         │   RED   │ Write test (preferably first)
         └────┬────┘
              │
              ▼
      ┌─────────────┐
      │    GREEN    │ Make it pass ⭐ COMMIT HERE
      └──────┬──────┘
             │
             ▼
        ┌─────────┐
        │ REFACTOR│ Clean it up (optional for small changes)
        └────┬────┘
             │
             ▼
        (back to RED for next test)
```

## TDD Principles (Pragmatic Approach)

1. **Write tests when practical** - Before implementation when beneficial, not as a dogma
2. **Focus on coverage and quality** - Tests should verify behavior effectively
3. **Commit when green** - Only commit when tests pass, never in red state
4. **Refactor reasonably** - Address obvious improvements, don't obsess over perfection
5. **Run CI once at the end** - Use local tests during development, CI for final validation

## AI Agent TDD Adaptations

Since AI agents generate code differently, take a pragmatic approach:

**RED Phase:**
- Write test first when practical and beneficial
- Don't obsess over making tests fail - the goal is coverage
- Focus on capturing requirements in code

**GREEN Phase:**
- Generate implementation that makes tests pass
- This is the commit point - only commit when tests pass
- Focus on functionality over perfection

**REFACTOR Phase:**
- Review code for obvious improvements
- Address reasonable refactor opportunities before committing
- Don't let perfect be the enemy of good - larger refactors can be separate tasks

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

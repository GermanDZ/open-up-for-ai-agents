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

Guide the red-green-refactor cycle with a pragmatic approach. TDD is a tool, not a mandate -- use it when it helps.

## Process

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
- REFACTOR: Verify tests still pass; refactor is optional for small changes

### 4. Create TDD Log

Document the TDD cycle in `docs/tdd-logs/<feature>-tdd.md`:
- Feature name, test cases written, implementation notes, refactoring performed, lessons learned

## Success Criteria

- [ ] Tests are written (preferably before implementation)
- [ ] Implementation makes tests pass
- [ ] Code is reasonably clean and functional
- [ ] Tests pass before commit

## Output

Returns a summary of:
- TDD phase completed
- Test file created/updated
- Implementation file created/updated
- Test results
- Refactoring notes

## See Also

- [openup-create-test-plan](../openup-artifacts/create-test-plan/SKILL.md) - Create comprehensive test plan
- [openup-complete-task](../complete-task/SKILL.md) - Complete task after TDD cycle
- [openup-detail-use-case](../openup-artifacts/detail-use-case/SKILL.md) - Detail use cases before writing tests

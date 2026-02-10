# Test-Driven Development (TDD)

This document explains the Test-Driven Development practice used in this project.

**Note**: We take a pragmatic approach to TDD. The goal is quality software with good test coverage, not process purity. Use TDD when it helps, skip it when it doesn't.

## What is TDD?

Test-Driven Development (TDD) is a software development practice where you write tests *before* writing the implementation code. It follows a simple, repetitive cycle that ensures code quality, correctness, and maintainability.

### The TDD Cycle: Red-Green-Refactor

```
RED → GREEN → REFACTOR → RED → GREEN → REFACTOR → ...
```

1. **RED**: Write a failing test
   - Write a test for the next bit of functionality you want to add
   - Run the test and watch it fail (it should fail because the functionality doesn't exist yet)
   - If the test passes immediately, it's not testing anything new

2. **GREEN**: Make the test pass
   - Write the *simplest* code that makes the test pass
   - Don't worry about perfection—just make it work
   - Use hard-coded values if necessary; you'll refactor next

3. **REFACTOR**: Improve the code
   - Clean up the code while keeping tests green
   - Remove duplication
   - Improve names
   - Simplify logic
   - Tests protect you—if they still pass, your refactor is safe

## Why TDD?

### Benefits

1. **Design feedback**: Writing tests first forces you to think about the API/interface before implementation
2. **Regression safety**: Every feature has tests from day one
3. **Documentation**: Tests show *how* code is meant to be used
4. **Confidence**: Refactoring is safe when tests exist
5. **Focus**: You only write code needed to pass tests (YAGNI enforced)
6. **Debugging**: When a test fails, you know exactly what broke

## TDD Rules

### The Three Laws of TDD (Bob Martin)

1. **Don't write production code** until you have a failing test
2. **Don't write more of a test** than is sufficient to fail
3. **Don't write more production code** than is sufficient to pass the test

### Practical Guidelines

1. **Start with the simplest case**
2. **One test at a time**
3. **Test behavior, not implementation**
4. **Keep tests fast**
5. **Keep tests isolated**

## TDD and the Commit Sequence

TDD fits naturally into our atomic commit workflow:

```
1. [refactor] Prepare code structure (tests still pass)
2. [test] Write tests for new functionality (preferably first)
3. [feat] Implement feature to make tests pass (GREEN → COMMIT HERE)
4. [refactor] Clean up implementation (optional for small changes)
5. [docs] Update documentation
```

**Important**: Commit when tests are green. Never commit in red state.

## Integration with Agent Workflow

When implementing features using TDD (pragmatic approach):

1. **Plan phase**: Identify test cases from use cases
2. **Implementation phase**: Write tests (preferably first), implement until green
3. **Commit phase**: Commit when tests pass (green state), never in red state
4. **CI phase**: Run CI/test suite once at the end, not repeatedly during development
5. **Review phase**: Tests serve as specification documentation

**Key Points**:
- Write tests first when practical and beneficial
- Don't obsess over strict red-green-refactor adherence
- Commit when tests pass, run CI once at the end
- Focus on quality and coverage, not process purity

For complete TDD guidance, see the [OpenUP knowledge base](openup-knowledge-base/practice-technical/test_driven_development/).

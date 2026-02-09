# RED Phase: Write Failing Test

The RED phase is the first step in TDD where you write a test that captures the requirement and verify it fails.

## Goal

Write a test that:
- Clearly expresses the requirement
- Fails because the feature doesn't exist yet
- Provides a clear error message when it fails

## Process

### 1. Understand the Requirement

Before writing the test, ensure you understand:
- What behavior is being specified
- What inputs are expected
- What outputs should be produced
- What edge cases exist

**Sources:**
- Use case scenarios
- Design documents
- Requirements specifications
- User stories

### 2. Choose the Test Framework

Identify the test framework for the project:
- JavaScript: Jest, Mocha, Vitest
- Python: pytest, unittest
- Java: JUnit, TestNG
- Go: testing package
- Other: Project-specific framework

### 3. Write the Test

Create a test that:
- Has a clear, descriptive name
- Sets up necessary preconditions
- Executes the feature being tested
- Asserts expected behavior

**Test Structure:**

```javascript
// Arrange (Setup)
const input = /* test data */;
const expected = /* expected result */;

// Act (Execute)
const result = featureToTest(input);

// Assert (Verify)
expect(result).toBe(expected);
```

**Example Test:**

```javascript
describe('User Authentication', () => {
  it('should authenticate user with valid credentials', async () => {
    // Arrange
    const credentials = {
      email: 'user@example.com',
      password: 'correct-password'
    };

    // Act
    const result = await authenticateUser(credentials);

    // Assert
    expect(result.success).toBe(true);
    expect(result.token).toBeDefined();
    expect(result.user.email).toBe('user@example.com');
  });
});
```

### 4. Verify the Test Fails

Run the test to confirm it fails:

```bash
npm test User Authentication
# or
pytest test_user_auth.py
```

**Expected Failure:**
- Test should fail with clear error
- Error should indicate missing feature/function
- Error should NOT be due to test issues

**Good Failure Example:**
```
ReferenceError: authenticateUser is not defined
```

**Bad Failure Example (test issue):**
```
SyntaxError: Unexpected token
```

### 5. Create Test File

Create the test file in the appropriate location:
- JavaScript: `tests/` or `__tests__/` or `spec/`
- Python: `tests/` directory
- Java: `src/test/java/`
- Go: `*_test.go` files next to source

**Naming Convention:**
- `.test.js` or `.spec.js` for JavaScript
- `test_*.py` for Python
- `*Test.java` for Java
- `*_test.go` for Go

## RED Phase Checklist

- [ ] Requirement is clearly understood
- [ ] Test has descriptive name
- [ ] Test follows Arrange-Act-Assert pattern
- [ ] Test is created in correct location
- [ ] Test fails for the right reason (feature doesn't exist)
- [ ] Error message is clear

## Common RED Phase Issues

| Issue | Solution |
|-------|----------|
| Test passes immediately | Test may not be testing the right thing |
| Test fails with syntax error | Test code has an error, fix before proceeding |
| Test is too complex | Break into multiple smaller tests |
| Unclear what's being tested | Rewrite test with clearer name and structure |

## Output

At end of RED phase:
- Test file created
- Test fails with clear error
- Ready for GREEN phase

## Next Phase

Once RED phase is complete and verified, proceed to [GREEN phase](./green-phase.md).

# GREEN Phase: Make the Test Pass

The GREEN phase is where you implement just enough code to make the failing test pass.

## Goal

Write implementation that:
- Makes the test pass
- Is minimal and focused
- Doesn't add unnecessary features
- May be "ugly" but works (refactoring comes next)

## Process

### 1. Review the Failing Test

Look at the test failure:
- What is the test expecting?
- What is the exact error message?
- What needs to be implemented?

### 2. Plan Minimal Implementation

Identify the absolute minimum needed:
- What function/class/module is needed?
- What parameters does it need?
- What should it return?

**TDD Mantra:** "Make it work, make it right, make it fast."

### 3. Implement the Feature

Write just enough code to pass the test:

**For a Simple Function:**

```javascript
// Before (test fails)
// authenticateUser doesn't exist

// After (test passes)
async function authenticateUser(credentials) {
  const user = await findUserByEmail(credentials.email);
  if (!user) {
    return { success: false, error: 'User not found' };
  }
  const isValid = await verifyPassword(credentials.password, user.passwordHash);
  if (!isValid) {
    return { success: false, error: 'Invalid password' };
  }
  const token = generateToken(user);
  return {
    success: true,
    token,
    user: { id: user.id, email: user.email }
  };
}
```

**Important:** Only implement what the test requires. Don't add:
- Additional features
- Error handling for untested cases
- Optimizations
- Extra validation

These will come in later tests or refactoring.

### 4. Run the Test

Run the test again:

```bash
npm test User Authentication
```

**Expected Result:**
- Test should pass
- No other tests should break (if they exist)

### 5. Verify the Implementation

After test passes:
- Review the implementation
- Ensure it matches the test requirement
- Check for any obvious issues (but don't refactor yet)

## GREEN Phase Principles

1. **Do the simplest thing that works** - No premature optimization
2. **Only what the test requires** - One test at a time
3. **Pass the test** - That's the only goal
4. **Defer elegance** - Refactoring comes next

## Implementation Patterns

### Placeholder Implementation

Sometimes a hard-coded return is enough:

```javascript
// First test: check return type
function add(a, b) {
  return 0; // Will pass basic existence test
}

// Second test: check basic operation
function add(a, b) {
  return a + b; // Now implement actual logic
}
```

### Stub Implementation

Use stubs for dependencies:

```javascript
// Instead of real database
async function findUserByEmail(email) {
  return { id: 1, email, passwordHash: 'hash' };
}
```

### Incremental Implementation

Build up functionality test by test:

```javascript
// Test 1: Valid credentials
// Implement: Basic happy path

// Test 2: Invalid credentials
// Implement: Add validation

// Test 3: User not found
// Implement: Add error handling
```

## GREEN Phase Checklist

- [ ] Failing test is understood
- [ ] Minimal implementation is planned
- [ ] Only what test requires is implemented
- [ ] Test now passes
- [ ] No unnecessary features added
- [ ] Ready for refactoring

## Common GREEN Phase Issues

| Issue | Solution |
|-------|----------|
| Test still fails | Read error message carefully, implement exactly what's needed |
| Implementation too complex | You're probably doing too much, simplify |
| Other tests broke | Run all tests, fix what broke |
| Over-engineering | Remind yourself: REFACTOR is next phase |

## Output

At end of GREEN phase:
- Implementation makes test pass
- Code may not be pretty but works
- Ready for REFACTOR phase

## Next Phase

Once GREEN phase is complete and test passes, proceed to [REFACTOR phase](./refactor-phase.md).

## Alternative: Back to RED

If more tests are needed for this feature:
- Go back to RED phase
- Write next test
- Continue cycle until feature complete
- Then do final REFACTOR

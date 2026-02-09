# REFACTOR Phase: Improve the Code

The REFACTOR phase is where you improve the code structure and quality while ensuring tests still pass. Behavior doesn't change, only implementation.

## Goal

Improve the code so that:
- It's cleaner and more readable
- It follows project conventions
- It's more maintainable
- Tests still pass (behavior unchanged)

## Process

### 1. Review Current Implementation

Look at the code with fresh eyes:
- Is it readable?
- Are there duplications?
- Are names meaningful?
- Does it follow project patterns?

### 2. Identify Improvements

Common refactoring opportunities:

**Naming:**
- Poor variable names → Meaningful names
- Magic numbers → Named constants
- Ambiguous terms → Clear language

**Structure:**
- Long functions → Smaller, focused functions
- Duplicated code → Extracted functions
- Nested conditionals → Early returns
- Large parameters → Parameter objects

**Patterns:**
- Hard-coded values → Configuration
- Multiple responsibilities → Single responsibility
- Tight coupling → Looser coupling

### 3. Apply Refactorings

Apply improvements one at a time, running tests after each change.

**Example Refactorings:**

**Extract Function:**

```javascript
// Before
function authenticateUser(credentials) {
  const user = db.findUserByEmail(credentials.email);
  if (!user) {
    return { success: false };
  }
  const hash = crypto.hash(credentials.password);
  if (user.passwordHash !== hash) {
    return { success: false };
  }
  return { success: true, user };
}

// After
function authenticateUser(credentials) {
  const user = findUser(credentials.email);
  if (!user) return authenticationFailed();
  if (!passwordMatches(credentials.password, user.passwordHash)) {
    return authenticationFailed();
  }
  return authenticationSuccess(user);
}
```

**Extract Constant:**

```javascript
// Before
if (token.length < 32) { ... }

// After
const MIN_TOKEN_LENGTH = 32;
if (token.length < MIN_TOKEN_LENGTH) { ... }
```

**Improve Names:**

```javascript
// Before
function proc(d) { return d * 1.08; }

// After
function calculateTotalWithTax(subtotal) {
  const TAX_RATE = 0.08;
  return subtotal * (1 + TAX_RATE);
}
```

### 4. Run Tests After Each Change

After each refactoring:

```bash
npm test
```

**Critical:** Tests must still pass!
- If tests fail, you changed behavior
- Revert the change and try a different approach
- Refactoring should never change observable behavior

### 5. Verify Improvements

After refactoring:
- Code is easier to understand
- No new functionality added
- No functionality removed
- All tests pass
- Code follows conventions

## Refactoring Catalog

Common refactorings to apply:

| Refactoring | When to Use |
|-------------|-------------|
| Extract Method | Method is too long or does multiple things |
| Extract Variable | Complex expression that could be clearer |
| Rename | Name doesn't clearly express intent |
| Introduce Parameter Object | Too many parameters |
| Replace Magic Number | Hard-coded numeric values |
| Consolidate Conditional | Repeated condition checks |
| Extract Interface | Tight coupling to concrete class |
| Separate Concerns | One function does too much |

## REFACTOR Phase Principles

1. **Small changes** - One refactoring at a time
2. **Run tests frequently** - After every change
3. **Behavior unchanged** - Tests enforce this
4. **Improve gradually** - Don't try to fix everything at once
5. **Know when to stop** - Perfect is the enemy of good

## Refactoring Checklist

For each potential refactoring:
- [ ] Will this improve clarity?
- [ ] Can I do this safely (with tests)?
- [ ] Is this the right time?
- [ ] Do I understand the code well enough?

## REFACTOR Phase Checklist

- [ ] Code is reviewed for improvements
- [ ] Refactorings are identified
- [ ] Changes are made incrementally
- [ ] Tests run after each change
- [ ] All tests still pass
- [ ] Code is improved
- [ ] No behavior changes

## Common REFACTOR Phase Issues

| Issue | Solution |
|-------|----------|
| Tests fail after refactor | You changed behavior, revert and try smaller change |
| Over-refactoring | Stop when code is good enough, move to next feature |
| Big refactorings | Break into smaller, safer changes |
| Unclear if improvement | If not clearly better, don't change |

## When to Skip Refactoring

Sometimes it's okay to defer refactoring:
- Time pressure (rare in TDD context)
- Unclear best approach
- Larger refactoring needs planning
- Just learned a better pattern (apply to next feature instead)

## Output

At end of REFACTOR phase:
- Code is cleaner and more maintainable
- All tests still pass
- Behavior unchanged
- Feature is complete

## Next Steps

After REFACTOR phase:
- If more tests needed for feature → Back to RED phase
- If feature complete → Run full test suite
- If all good → Consider task complete

## Full TDD Cycle Complete

After completing RED → GREEN → REFACTOR:
- Feature is tested
- Code is clean
- Ready to move to next feature
- Or use `/openup-complete-task` to finalize

# OpenUP Investigation Team Configuration

This is a task-specific team configuration for debugging and technical investigation.

## Team Purpose

Investigate and resolve bugs, technical issues, or performance problems through collaborative analysis.

## Team Members

### architect (Lead)
- **Focus**: Analyze architecture and system design implications
- **Key Activities**: Root cause analysis, architectural impact assessment
- **Collaborates With**: Developer (code analysis), Tester (reproduction)
- **Reference**: `.claude/teammates/architect.md`

### developer (Lead)
- **Focus**: Analyze code, find root cause, implement fix
- **Key Activities**: Code inspection, debugging, fix implementation
- **Collaborates With**: Architect (design understanding), Tester (reproduction and verification)
- **Reference**: `.claude/teammates/developer.md`

### tester (Lead)
- **Focus**: Reproduce issue, verify fix, prevent regression
- **Key Activities**: Issue reproduction, test creation, fix verification
- **Collaborates With**: Developer (reproduction steps), Architect (impact assessment)
- **Reference**: `.claude/teammates/tester.md`

## Investigation Process

1. **Understand the Issue**
   - Gather bug report or issue description
   - Identify reproduction steps
   - Understand expected vs. actual behavior

2. **Analyze the Problem**
   - Architect analyzes system design and potential causes
   - Developer inspects relevant code
   - Tester reproduces and documents the issue

3. **Identify Root Cause**
   - Collaborate to find the actual cause
   - Assess architectural impact
   - Consider potential side effects

4. **Design Solution**
   - Architect proposes fix approach
   - Developer assesses implementation complexity
   - Tester defines verification criteria

5. **Implement Fix**
   - Developer implements the fix
   - Tester verifies the fix resolves the issue
   - Architect ensures no architectural violations

6. **Prevent Regression**
   - Tester creates or updates test cases
   - Developer adds tests if needed
   - Document lessons learned

## Creating This Team

To create an OpenUP Investigation team, use this prompt:

```
Create an OpenUP investigation team to investigate [issue description].

Spawn teammates for:
- architect: to analyze the architecture and identify root causes
- developer: to analyze the code and implement the fix
- tester: to reproduce the issue and verify the fix

The architect should analyze the system architecture and potential causes.
The developer should find the root cause in the code and implement a fix.
The tester should reproduce the issue, verify the fix works, and add tests to prevent regression.
```

## Task Assignment Guidelines

- **Root cause analysis** → architect + developer
- **Code inspection** → developer
- **Issue reproduction** → tester
- **Fix implementation** → developer
- **Fix verification** → tester
- **Test creation** → tester
- **Architectural assessment** → architect

## Collaboration Patterns

- **Architect ↔ Developer**: Architecture understanding vs. code reality
- **Developer ↔ Tester**: Fix implementation vs. verification
- **All**: Root cause analysis and solution design

## Example Usage

```
Create an OpenUP investigation team to investigate the login timeout issue.

The team should:
1. Reproduce the timeout issue
2. Analyze the authentication flow code
3. Identify the root cause
4. Implement a fix
5. Verify the fix works
6. Add tests to prevent regression
```

# Developer (Compact)

**Role**: Implement features, write code, create unit tests

**Creates**: Design, code, unit tests

**Collaborates**: Architect (design review), Tester (integration), Analyst (requirements)

**On start**: self-brief per the `## On Start, Read` block in `.claude/teammates/developer.md` — status · the task spec's Operations/Structure/Norms · role guidelines.

## Quick Process

1. Read task spec at `docs/changes/T-XXX/plan.md` (authoritative); fall back to roadmap line if no spec
2. Review design (or create with Architect)
3. Implement with TDD approach when applicable
4. Write/update unit tests
5. Document changes

## TDD Workflow (Adaptive)

For AI agents, TDD is flexible:
1. **Understand requirements** from analyst/use-cases
2. **Write test first** when requirements are clear
3. **Implement** to pass tests
4. **Refactor** when needed
5. **Document** key decisions

*Can skip strict test-first for minor changes*

## Key Commands

- `/openup-tdd-workflow` - Guided TDD cycle
- `/openup-complete-task` - Finish and commit work

## Quality Standards

- Code must compile/run without errors
- Unit tests for new functionality
- Follow project coding conventions
- Update relevant documentation
- **Spec-first for behavior changes**: update use case / task description before code; refactors go code-first then `/openup-sync-spec`

## When to Involve Others

- **Architect**: Design decisions, architectural changes
- **Tester**: Integration testing, QA handoff
- **Analyst**: Clarify requirements

---

*Full instructions: `.claude/teammates/developer.md`*

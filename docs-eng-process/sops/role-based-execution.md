# Role-Based Execution SOP

> Extracted from `agent-workflow.md` so skills that need only the role-execution
> procedure load this file instead of the whole operating-procedures document.

Agents assume different OpenUP roles as needed to complete work. Roles may switch during a run.

## Role Selection

After selecting a task, explicitly choose the initial role(s) based on phase + task type:

- **ProductOwner/Analyst** - for scope, requirements, prioritization
- **Architect** - for architecture decisions and constraints
- **Developer** - for implementation
- **Tester** - for test strategy and validation
- **ProjectManager** - for planning/tracking updates

## Role Usage Types

Distinguish between:

- **Primary role**: Main role responsible for the current task's outputs (this defines the task boundary)
- **Consulting role**: Brief consultation of another role's guidance (no new task boundary)

## Task Boundary Rules

- A new **task** starts when the agent changes the **primary role** *and* intends to modify code or project artifacts (including `/docs`)
- Consulting-role switches do **not** require a new task or a new commit when no code/artifacts are modified; they must be noted in the task log as consultation

## Task Planning

Each task must be planned before execution:

- Define objective
- Define expected outputs (including `/docs` updates)
- Define completion criteria
- Ensure the task supports the current phase + iteration goals

## Commit Policy Per Task

**⚠️ CRITICAL**: Commit DURING implementation, not just at the end.

**Do NOT save all changes for one big commit at the end.** Instead:

1. **Commit after each meaningful unit of work** — a new function, a passing test, a config change, a doc update
2. **Use the canonical commit format** from `docs-eng-process/conventions.md`:
   ```
   type(scope): brief description [T-XXX]
   ```
3. **At task end**, commit any remaining uncommitted changes, then verify with `git status --porcelain` that nothing is left

**MANDATORY**: Uncommitted changes mean the task is NOT complete. Before declaring a task finished, `git status --porcelain` must return empty.

**See [End-of-Run SOP](../agent-workflow.md#end-of-run-sop) for the complete mandatory procedure that must be followed before stopping.**

## Role Switching

When switching roles, the agent must:

- State the active role to the user before executing work in that role
- Keep changes aligned with the phase + iteration goals

## OpenUP Role References

Role definitions are available in the vendored knowledge base:

- [Analyst](../openup-knowledge-base/core/role/roles/analyst-6.md)
- [Product Owner](../openup-knowledge-base/core/role/roles/product-owner-2.md)
- [Architect](../openup-knowledge-base/core/role/roles/architect-6.md)
- [Developer](../openup-knowledge-base/core/role/roles/developer-11.md)
- [Tester](../openup-knowledge-base/core/role/roles/tester-5.md)
- [Project Manager](../openup-knowledge-base/core/role/roles/project-manager-4.md)

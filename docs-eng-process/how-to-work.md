# How to Work

This document provides minimal orientation. For detailed procedures, see [agent-workflow.md](agent-workflow.md).

## Process Overview

This repository uses **OpenUP** (Open Unified Process), a lean, iterative methodology with four phases:

1. **Inception** - Define scope, vision, and feasibility
2. **Elaboration** - Establish architecture baseline
3. **Construction** - Build the system incrementally
4. **Transition** - Deploy to users

Each phase contains one or more iterations, and each iteration delivers incremental value.

## Key References

- **Project Lifecycle**: [openup-knowledge-base/practice-management/risk_value_lifecycle/guidances/concepts/project-lifecycle.md](openup-knowledge-base/practice-management/risk_value_lifecycle/guidances/concepts/project-lifecycle.md)
- **Phase Milestones**: [openup-knowledge-base/practice-management/risk_value_lifecycle/guidances/concepts/phase-milestones.md](openup-knowledge-base/practice-management/risk_value_lifecycle/guidances/concepts/phase-milestones.md)
- **Introduction**: [openup-knowledge-base/guides/base/guidances/supportingmaterials/introduction-to-openup.md](openup-knowledge-base/guides/base/guidances/supportingmaterials/introduction-to-openup.md)

## Disciplines

OpenUP organizes work into disciplines:

- **Requirements** - Elicit, analyze, specify, validate requirements
- **Architecture** - Create and evolve software architecture
- **Development** - Design and implement the solution
- **Test** - Provide feedback through testing
- **Deployment** - Plan and deploy the solution
- **Project Management** - Coach, facilitate, and support the team
- **Environment** - Customize process and tools

## Iteration Lifecycle

Each iteration follows a cycle:

1. **Plan** - Select work items, assign to team members
2. **Implement** - Design, code, test (micro-increments)
3. **Assess** - Review results, demonstrate to stakeholders
4. **Adapt** - Adjust plans based on feedback

## For AI Agents

See [agent-workflow.md](agent-workflow.md) for:
- Start-of-run procedures
- Role-based execution
- Branching and commit policies
- Traceability logging requirements

## Fast completion mode (token-efficient)

When speed is the priority, use the smallest valid workflow for the task.

| Task size | Preferred workflow | Why |
|-----------|--------------------|-----|
| Tiny fix (single file, low risk) | `/openup-quick-task` | Lowest process overhead |
| Normal task (code + docs updates) | `/openup-complete-task` | Full completion with one closure path |
| Iteration/phase milestone work | Standard SOP + phase skills | Requires full traceability and review |

## Minimal-output defaults

To reduce token usage in long sessions:

- Request summary-first responses (brief status + next action)
- Prefer targeted reads/search over full-file reads
- For noisy commands, return counts + last 20-50 lines only
- Avoid repeating unchanged plans or previously confirmed context
- Use one closure path at the end (see below)

## Closure path rule

Use exactly one closure path per finished task:

- If you used `/openup-complete-task`, do not run `/openup-log-run` again unless logs explicitly failed and need recovery
- Use `/openup-log-run` directly only when you are not using `/openup-complete-task`

## Prompt templates for low token usage

### Small fix

```
Use quick mode for this small change.
Keep output concise (decision + action + result).
Do targeted reads only; avoid full-file dumps.
```

### Standard task

```
Implement this task with minimal token overhead.
Use one execution plan, concise progress updates, and one closure path.
If using /openup-complete-task, do not run /openup-log-run unless recovery is needed.
```

### Noisy command guardrail

```
When running commands that can produce large output, summarize results and include only essential snippets.
Prefer counts, error summary, and tail output.
```

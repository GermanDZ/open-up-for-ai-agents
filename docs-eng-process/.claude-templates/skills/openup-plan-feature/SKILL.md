---
name: openup-plan-feature
description: Generate iteration plan and roadmap entry for a feature idea
model: sonnet
fit:
  great: [turning a fresh feature idea into a roadmap entry + plan]
  ok: [re-planning when scope shifts mid-flight]
  poor: [already-scoped tasks with a plan (skip to start-iteration), trivial fixes]
arguments:
  - name: topic
    description: The feature idea or requirements to plan (e.g., "Add PDF export for chat conversations")
    required: true
  - name: task_id
    description: Override the task ID (e.g., C3-004). Reserved via `openup-claims.py reserve-id` if not provided.
    required: false
  - name: priority
    description: Task priority — critical, high, or medium (default medium)
    required: false
  - name: validate
    description: Spawn analyst + architect team to review the plan before finalizing (default false)
    required: false
  - name: create_pr
    description: Create branch, commit, push, and open a PR (default true)
    required: false
---

# Plan Feature

This skill automates the full "plan a feature" workflow: explore the codebase, generate a detailed iteration plan, add a roadmap entry, and optionally create a PR — all from a single feature idea.

## When to Use

Use this skill when:
- You have a new feature idea and need a detailed implementation plan
- You want to add a feature to the roadmap with a plan document
- You need to explore the codebase to understand what a feature will touch before coding
- Planning an iteration task from a high-level description

## When NOT to Use

Do NOT use this skill when:
- The feature already has an iteration plan (edit it directly)
- You need to start implementing (use `/openup-start-iteration`)
- The task is a quick fix or bug fix (use `/openup-quick-task`)
- You only need to update the roadmap without a plan (edit `docs/roadmap.md` directly)

## Success Criteria

After using this skill, verify:
- [ ] Iteration plan file exists at `docs/iteration-plans/{task_id}-{slug}.md`
- [ ] Plan includes Current State with actual code excerpts from the codebase
- [ ] Plan includes Proposed Design with concrete code examples
- [ ] Plan includes Acceptance Criteria, Dependencies, and Key Files
- [ ] Roadmap entry exists in `docs/roadmap.md` with correct format
- [ ] PR is created (if `create_pr` is true)

## Process Summary

1. Read project context (status, roadmap, architecture)
2. Reserve task ID through the claims mechanism
3. Explore codebase for relevant code
4. Ambiguity gate — classify open questions (blocking → ask, non-blocking → record)
5. Generate iteration plan document
6. Update roadmap with new entry
7. Self-critique the plan (hostile review; assumptions surfaced, criteria failable)
8. Optionally validate with analyst + architect team
9. Optionally create branch, commit, push, and PR
10. Present summary

## Detailed Steps

### 1. Read Project Context

Read these files to understand the current state of the project:
- `docs/project-status.md` — current phase, iteration, completed tasks
- `docs/roadmap.md` — existing tasks, priorities, dependencies, format
- `docs/architecture-notebook.md` — architectural decisions and constraints

Record:
- Current phase (e.g., `construction`)
- Current iteration number
- Naming conventions for task IDs in the current phase

### 2. Reserve Task ID

If `$ARGUMENTS[task_id]` is provided, use it directly.

Otherwise, **reserve** the next ID through the claims mechanism — do not
scan-and-increment yourself (a local roadmap scan races with parallel planning
lanes and stale checkouts; T-031):

1. Identify the current phase prefix from `docs/project-status.md` (e.g., `C`
   for Construction, `E` for Elaboration, `T` for Inception) and the current
   iteration number — together they form the ID prefix (e.g., `C3-`).
2. Reserve atomically:

   ```bash
   python3 scripts/openup-claims.py reserve-id --session-id <session> \
       --prefix "C3-" --title "<topic>"
   ```

   The printed ID (e.g., `C3-004`) is allocated repo-wide: the reservation
   file in the shared claims dir blocks every other lane, and the allocator
   unions live reservations with IDs found in change folders,
   `docs/roadmap.md` (including the "Future / Backlog Features" section), and
   `origin/main`'s roadmap. If no tasks exist yet for the iteration, it
   starts at `001`.
3. If the plan is abandoned before this skill commits, free the ID with
   `python3 scripts/openup-claims.py release-id --task-id <id>`; once the
   roadmap entry lands, the reservation is redundant.

### 3. Explore Codebase

This is a critical step. The iteration plan must reference real files and code, not abstract descriptions.

Based on the feature topic (`$ARGUMENTS[topic]`), explore:
1. **Models** — Grep/Glob for relevant ActiveRecord models, their associations, validations, and scopes
2. **Controllers** — Find controllers that handle related functionality
3. **Services** — Look for service objects in `app/services/` related to the feature
4. **Views** — Find relevant views and partials
5. **Routes** — Check `config/routes.rb` for related route definitions
6. **Schema** — Read `db/schema.rb` for relevant table definitions
7. **Locales** — Check `config/locales/en.yml` and `config/locales/es.yml` for existing i18n keys in the area
8. **Tests** — Find existing test files for the affected code
9. **Config** — Check `config/app_settings.yml` or other config files if relevant

Extract actual code snippets (with file paths and line numbers) for the "Current State" section of the plan.

### 4. Ambiguity Gate — MANDATORY before generating the plan

Now that you understand the request and the code, list the open questions and
classify each before drafting the plan:

- **Blocking** — the answer would change the feature's scope, acceptance
  criteria, or design direction. **Stop.** Raise it via `/openup-request-input`
  (related_task = this task ID) and do not generate the plan for the affected
  area until it is answered.
- **Non-blocking** — a default is reasonable. Pick it and record it under the
  plan's **Open Questions** section as a resolved assumption (`Assumed: <choice>
  — vetoable at review`), so the requester can override it.

If the request is unambiguous, note that in one line and proceed. This gate is
why the generated plan reflects the requester's intent, not the author's guess.

### 5. Generate Iteration Plan

Write the iteration plan to `docs/iteration-plans/{task_id_lower}-{slug}.md` where:
- `{task_id_lower}` is the lowercase task ID (e.g., `c3-004`)
- `{slug}` is a short kebab-case slug derived from the feature topic (e.g., `pdf-export`)

Use this structure (matching the project's established format):

```markdown
# {Task ID}: {Title}

**Phase**: {phase}
**Status**: pending
**Goal**: {one-line goal}
**Priority**: {priority}

---

## Context

{Why this feature is needed. Background and motivation.}

---

## Current State

{For each relevant area, show the actual current code with file paths and line numbers.
Include model definitions, controller actions, service methods, view excerpts, routes, schema.}

### {Area 1} (`path/to/file.rb`)

```ruby
# Current implementation
```

### {Area 2} (`path/to/file.rb`)

```ruby
# Current implementation
```

---

## Proposed Design

{For each change, show the proposed code with clear before/after or new code.
Group by logical units of work (e.g., Migration, Model, Service, Controller, Views, i18n).}

### {Change 1}: {Description}

**File**: `path/to/file.rb`

```ruby
# Proposed implementation
```

### {Change 2}: {Description}

**New file**: `path/to/new_file.rb`

```ruby
# Proposed implementation
```

---

## i18n

New keys for `config/locales/en.yml`:

```yaml
en:
  # new keys
```

New keys for `config/locales/es.yml`:

```yaml
es:
  # new keys
```

---

## Acceptance Criteria

- [ ] {Criterion 1}
- [ ] {Criterion 2}
- [ ] ...

---

## Success Measure

We expect {measure X} to move by {direction + magnitude Y} within {window Z} of release.
Instrumentation: {event / metric / query}. Read-back: {date or "Z after release"}.

{One falsifiable expectation — use impact, engagement, and returned value as prompts
to find it, not as three required slots. Write "n/a — <reason>" only for genuinely
unmeasurable internal work; the task spec (rubric criterion 12) will hold this line.}

---

## Testing Strategy

- {Test category 1}: {what to test}
- {Test category 2}: {what to test}

---

## Dependencies

- {Task ID} ({description} — {status})

---

## Key Files

| File | Change |
|------|--------|
| `path/to/file` | {Description of change} |

---

## Out of Scope

- {Item 1}
- {Item 2}

---

## Open Questions

1. {Question 1}
2. {Question 2}
```

### 6. Update Roadmap

Insert a new entry in `docs/roadmap.md` under the correct phase section.

Match the existing format exactly:

```markdown
---

## {Task ID}: {Title}
**Status**: pending
**Priority**: {priority}
**Value**: {one sentence, product-manager voice: who benefits and what outcome improves}
**Description**: {1-3 sentence description of the feature}
- {Key deliverable 1}
- {Key deliverable 2}
- ...

**Dependencies**: {comma-separated task IDs}

**See**: `docs/iteration-plans/{filename}.md`
```

**Value rationale** (product-manager concern): every new entry carries a one-line
`**Value**:` rationale — *who* benefits and *what outcome* improves. "High value"
with no who/what is not a rationale; if you cannot write the sentence, that is a
fit signal for `/openup-explore`, not a reason to omit it. Where the entry lands
in the pending order is the **product-manager role's** call (assume that hat, or
flag the placement for its review) — execution skills consume the order as given.

**Placement rules**:
- Insert under the correct phase heading (e.g., "## Construction Phase")
- Place after the last entry in that phase section (before the next phase heading or "---" separator)
- Pending tasks should appear after completed tasks in the same phase
- Among pending entries, position reflects the product-manager's value ordering

### 7. Self-Critique

Apply the **Self-Critique SOP** (`docs-eng-process/agent-workflow.md`) before any
team validation: take a hostile-reviewer stance on the plan you just generated,
surface every load-bearing assumption into its **Open Questions / Dependencies**,
and confirm the Acceptance Criteria and Success Measure could actually fail — not
"review and approve". This is mandatory and runs whether or not the optional team
review below is used. Fix or explicitly flag each genuine weakness, then record
the weakest point and its resolution in one line.

### 8. Validate with Team (Optional)

Only if `$ARGUMENTS[validate]` is `"true"`:

1. **Create a team** using TeamCreate with name `plan-review-{task_id}`
2. **Create review tasks**:
   - Task for analyst: "Review requirements completeness for {task_id}"
   - Task for architect: "Review technical feasibility for {task_id}"
3. **Spawn teammates**:
   - Analyst (subagent_type: `general-purpose`, team_name, instructions from `.claude/teammates/analyst.md`):
     - Read the generated iteration plan
     - Review for: requirements completeness, missing acceptance criteria, unclear scope, stakeholder impact
     - Send findings back via message
   - Architect (subagent_type: `general-purpose`, team_name, instructions from `.claude/teammates/architect.md`):
     - Read the generated iteration plan and `docs/architecture-notebook.md`
     - Review for: technical feasibility, architectural alignment, performance concerns, security implications, dependency risks
     - Send findings back via message
4. **Wait for both reviews** to complete
5. **Incorporate feedback** — update the iteration plan with any valid suggestions
6. **Shut down team** — send shutdown requests to both teammates, then delete team

### 9. Create Branch and PR (Optional)

Only if `$ARGUMENTS[create_pr]` is not `"false"` (default is true):

1. **Create branch**: `docs/{task_id_lower}-{slug}` (uses `docs/` prefix since this is documentation-only)
   ```bash
   git checkout -b docs/{task_id_lower}-{slug}
   ```

2. **Stage and commit**:
   ```bash
   git add docs/iteration-plans/{filename}.md docs/roadmap.md
   git commit -m "docs: add iteration plan and roadmap entry for {task_id}"
   ```

3. **Push branch**:
   ```bash
   git push -u origin docs/{task_id_lower}-{slug}
   ```

4. **Create PR**:
   ```bash
   gh pr create \
     --title "docs: {Task ID} — {Title}" \
     --body "$(cat <<'EOF'
   ## Summary

   - Add iteration plan for {Task ID}: {Title}
   - Add roadmap entry under {Phase} phase

   ## Files

   - `docs/iteration-plans/{filename}.md` — detailed implementation plan
   - `docs/roadmap.md` — new roadmap entry

   ## Review Notes

   This is a planning PR (documentation only). Review the iteration plan for:
   - Completeness of proposed design
   - Accuracy of current state analysis
   - Feasibility of acceptance criteria

   🤖 Generated with [Claude Code](https://claude.com/claude-code)
   EOF
   )"
   ```

### 10. Present Summary

Output a summary to the user:

```
## Feature Plan Created

- **Task ID**: {task_id}
- **Title**: {title}
- **Priority**: {priority}
- **Iteration Plan**: `docs/iteration-plans/{filename}.md`
- **Roadmap**: Updated `docs/roadmap.md`
- **Branch**: `docs/{task_id_lower}-{slug}` (if created)
- **PR**: {PR URL} (if created)
- **Validated**: {yes/no}

### Next Steps
- Review the iteration plan
- When ready to implement: `/openup-start-iteration task_id: {task_id}`
```

## Output

Returns a summary of:
- Task ID (auto-detected or provided)
- Iteration plan file path
- Roadmap entry location
- Branch name (if created)
- PR URL (if created)
- Validation results (if validated)

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `reserve-id` exits 6 | Requested ID already used or reserved by another lane | Re-run `reserve-id` without `--task-id` to get a fresh one |
| Roadmap parse error | Unexpected roadmap format | Verify `docs/roadmap.md` follows standard format |
| No relevant code found | Feature is entirely new | Plan will have minimal "Current State" — focus on "Proposed Design" |
| Team spawn failed | Agent teams not enabled | Set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` for validation |
| PR creation failed | No remote or gh not installed | Use `create_pr: false` and create PR manually |

## References

- Iteration Plans: `docs/iteration-plans/`
- Roadmap: `docs/roadmap.md`
- Project Status: `docs/project-status.md`
- Architecture Notebook: `docs/architecture-notebook.md`

## See Also

- [openup-start-iteration](../openup-start-iteration/SKILL.md) — Begin implementing a planned task
- [openup-create-iteration-plan](../openup-create-iteration-plan/SKILL.md) — Generic iteration planning (phase-level)
- [openup-complete-task](../openup-complete-task/SKILL.md) — Mark task complete after implementation
- [openup-create-pr](../openup-create-pr/SKILL.md) — Create PR with roadmap context

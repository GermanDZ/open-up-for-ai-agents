---
name: openup-request-input
description: Create an input request document for asynchronous stakeholder communication
arguments:
  - name: title
    description: Descriptive title for the request
    required: true
  - name: questions
    description: JSON array of questions (type, question_text, options for multiple-choice)
    required: true
  - name: context
    description: Additional context about what the agent is doing
    required: true
  - name: related_task
    description: Optional roadmap task ID (e.g., T-001)
    required: false
---

# Request Input

Create an input request document for asynchronous stakeholder communication.

## Process

### 1. Generate Filename

Format: `docs/input-requests/YYYY-MM-DD-<short-topic>.md` (derive topic from `$ARGUMENTS[title]`).

### 2. Fill Frontmatter

```yaml
---
title: "$ARGUMENTS[title]"
created: "<current-timestamp-ISO8601>"
created_by: "agent-name"
status: pending
run_id: "<current-run-id>"
related_task: "$ARGUMENTS[related_task]"  # optional
---
```

### 3. Write Context Section

Use `$ARGUMENTS[context]` to explain current task/phase, what information is needed, and why.

### 4. Add Questions

For each question in `$ARGUMENTS[questions]`, use the appropriate format:

**multiple-choice**: `### Q[N]: [Title]` with `**Type**: multiple-choice`, checkbox options (`- [ ] \`option\` - Description`), and `**Answer**:` placeholder.

**text**: `### Q[N]: [Title]` with `**Type**: text`, optional `**Example**:`, and `**Answer**:` placeholder.

**reference**: `### Q[N]: [Title]` with `**Type**: reference`, `**Accepts**: Path or URL`, and `**Answer**:` placeholder.

### 5. Include Instructions

Add instructions for respondent:
1. Fill in Answer section for each question
2. Update status from `pending` to `answered`
3. Save the file
4. Tell the agent to continue

### 6. Notify User

Inform user of document location and how to proceed.

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Invalid questions format | JSON array malformed | Verify valid JSON array |
| Missing context | Context not provided | Provide context argument |
| Directory not found | docs/input-requests/ missing | Create directory first |

## References

- Asynchronous Input SOP: `docs-eng-process/agent-workflow.md`
- Input Request Template: `docs-eng-process/templates/input-request.md`

## See Also

- [openup-start-iteration](../start-iteration/SKILL.md) - Process answered requests when starting iteration
- [openup-complete-task](../complete-task/SKILL.md) - Check for answered input before completing

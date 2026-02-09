---
name: request-input
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

This skill creates an input request document for asynchronous stakeholder communication, enabling questions to be shared via email and answered offline.

## When to Use

Create an input request document when:
- The question requires stakeholder consultation (not just the current user)
- Multiple related questions need to be answered together
- The user explicitly requests async communication
- The input may take time to gather (e.g., business decisions, approvals)
- The question could benefit from being shared via email

## Process

### 1. Generate Filename

Create filename in format: `docs/input-requests/YYYY-MM-DD-<short-topic>.md`
- Use `$ARGUMENTS[title]` to generate short topic
- Use current date

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

Explain what the agent is doing and why input is needed:
- Current task/phase context
- What specific information is needed
- Why this input is important for progress

Use `$ARGUMENTS[context]` as the base.

### 4. Add Questions

For each question in `$ARGUMENTS[questions]`:

**Multiple-choice**:
```markdown
### Q[N]: [Question Title]

**Type**: multiple-choice

**Question**: [The actual question text]

- [ ] `option-a` - Option A description
- [ ] `option-b` - Option B description
- [ ] `other` - Other (specify below)

**Answer**:
<!-- Check one option above or specify here -->
```

**Text**:
```markdown
### Q[N]: [Question Title]

**Type**: text

**Question**: [The actual question text]

**Example**: "[Example answer]"

**Answer**:
<!-- Write your answer here -->
```

**Reference**:
```markdown
### Q[N]: [Question Title]

**Type**: reference

**Question**: [The actual question text]

**Accepts**: Path to a file (relative to repo root) or URL containing the answer

**Answer**:
<!-- Provide path or URL, or write "None" -->
```

### 5. Include Instructions

Add instructions explaining how to fill and resume:
1. Fill in the Answer section for each question
2. Update status from `pending` to `answered`
3. Save the file
4. Tell the agent to continue

### 6. Notify User

Inform the user that an input request document has been created and where to find it.

## Output

Returns:
- File path to the input request document
- Number of questions
- Instructions for the user

## References

- Asynchronous Input SOP: `docs-eng-process/agent-workflow.md`
- Input Request Template: `docs-eng-process/templates/input-request.md`

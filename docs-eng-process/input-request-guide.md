# Input Request Guide

This guide explains how to fill out **Input Request Documents** created by AI agents. These documents allow you to provide information asynchronously, share them via email with stakeholders, and resume agent work when ready.

## What Are Input Request Documents?

Input Request Documents are structured markdown files that agents create when they need information from you. Instead of asking questions in chat, the agent creates a document with:

- **Context**: What the agent is doing and why it needs your input
- **Questions**: Structured questions with clear formats
- **Instructions**: How to fill and resume

## When You Receive an Input Request

1. **Location**: Check `docs/input-requests/` for files with `status: pending`
2. **Read the Context**: Understand what the agent is working on and why it needs your input
3. **Fill the Questions**: Answer each question in the document
4. **Update Status**: Change `status: pending` to `status: answered` in the frontmatter
5. **Save**: Save the file
6. **Resume**: Tell the agent to continue (e.g., "Continue with input-requests" or "Process input-requests")

## Answering Different Question Types

### Multiple-Choice Questions

For questions with checkboxes:

1. Find the question (e.g., `### Q1: Primary Target Audience`)
2. Review all options
3. Check the appropriate option by changing `[ ]` to `[x]`
4. If you select `other`, specify your answer in the **Answer** section below

**Example**:
```markdown
- [x] `b2b` - Business customers (B2B)
- [ ] `b2c` - Individual consumers (B2C)
```

### Text Questions

For questions requiring written answers:

1. Read the question and example (if provided)
2. Write your answer in the **Answer** section
3. Use the example as a guide for format and detail level

**Example**:
```markdown
**Answer**: 
Small businesses struggle to track expenses across multiple accounts. 
They often miss tax deductions and spend hours on manual reconciliation each month.
```

### Reference Questions

For questions asking for file paths or URLs:

1. Provide a file path relative to the repository root, or
2. Provide a URL, or
3. Write "None" if not applicable

**Example**:
```markdown
**Answer**: 
docs/requirements/product-requirements.md
```

Or:
```markdown
**Answer**: 
https://example.com/product-spec
```

## Sharing via Email

Input Request Documents are designed to be shared:

1. **Copy the document**: The markdown format is readable in most email clients
2. **Send to stakeholders**: Include relevant team members or decision-makers
3. **Collect responses**: Recipients can fill their answers directly in the document
4. **Consolidate**: Save all responses to the original file
5. **Resume**: Once all answers are collected, update status and tell the agent to continue

## Status Field

The frontmatter includes a `status` field. Update it as follows:

- `pending`: Initial state when the agent creates the document
- `answered`: Change to this when you've filled all questions
- `processed`: Agent sets this after processing (you don't need to change this)

## Tips

- **Be specific**: Provide clear, actionable answers
- **Use examples**: If the question includes an example, use it as a guide for detail level
- **Check all questions**: Make sure you've answered every question before marking as `answered`
- **Ask for clarification**: If a question is unclear, you can ask the agent in chat for clarification
- **Time-sensitive requests**: Check the `expires` field in frontmatter if present

## Example Workflow

1. Agent creates `docs/input-requests/2026-01-13-vision-scope.md` with `status: pending`
2. You open the file and read the context
3. You fill in all answers:
   - Check boxes for multiple-choice questions
   - Write text for text questions
   - Provide paths/URLs for reference questions
4. You update frontmatter: `status: answered`
5. You save the file
6. You tell the agent: "Continue with input-requests"
7. Agent processes the answers, updates status to `processed`, and moves file to `archive/`

## Troubleshooting

**Q: What if I can't answer a question?**
A: Leave it blank or write "TBD" in the Answer section. The agent will handle incomplete answers appropriately.

**Q: Can I edit the document after marking it as answered?**
A: Yes, you can update answers before the agent processes it. Once processed, the file is archived.

**Q: What if I need to ask the agent a question about the request?**
A: Use interactive chat to ask clarifying questions. The agent can update the input request document if needed.

**Q: Can multiple people fill the same document?**
A: Yes, you can share it via email and consolidate responses. Make sure all answers are in the document before marking as `answered`.

---

For agent procedures, see [agent-workflow.md](agent-workflow.md#asynchronous-input-sop).

# Asynchronous Input SOP

> Extracted from `agent-workflow.md` so `/openup-request-input` loads only this
> SOP instead of the whole operating-procedures document.

When an agent needs user input, it may create an **Input Request Document** instead of asking questions interactively. This enables asynchronous communication and allows documents to be shared via email for stakeholder input.

## When to Create an Input Request Document

Agents should create an input request document when:

- The question requires stakeholder consultation (not just the current user)
- Multiple related questions need to be answered together
- The user explicitly requests async communication
- The input may take time to gather (e.g., business decisions, approvals)
- The question could benefit from being shared via email
- The input is needed to unblock work but the user may not be immediately available

## When to Use Interactive Chat Instead

Use interactive chat for:

- Quick clarifications (yes/no, simple choices)
- Urgent blockers that need immediate resolution
- Follow-up questions during active work
- Single, straightforward questions that don't require stakeholder input

## Creating an Input Request Document

1. **Copy the template**: Copy `docs-eng-process/templates/input-request.md` to `docs/input-requests/`
2. **Name the file**: Use format `<YYYY-MM-DD>-<short-topic>.md` (e.g., `2026-01-13-vision-scope.md`)
3. **Fill the frontmatter**:
   - `title`: Descriptive title for the request
   - `created`: Current timestamp in ISO 8601 format
   - `created_by`: Agent identifier (e.g., "claude")
   - `status`: Set to `pending`
   - `run_id`: Current run identifier
   - `related_task`: Optional roadmap task ID (e.g., "T-001")
   - `expires`: Optional expiration date for time-sensitive requests
4. **Write the Context section**: Explain what the agent is doing and why input is needed
5. **Add Questions**: Use the structured question format:
   - **Type**: `multiple-choice`, `text`, or `reference`
   - **Question**: The actual question text
   - For `multiple-choice`: Provide checkbox options with short identifiers
   - For `text`: Include an example answer
   - For `reference`: Specify that it accepts file paths or URLs
   - **Answer**: Empty section for user to fill
6. **Include Instructions**: Explain how to fill and resume
7. **Notify the user**: Inform them that an input request document has been created and where to find it

## Question Format Standards

**Multiple-choice questions**:
```markdown
### Q1: [Question Title]

**Type**: multiple-choice

**Question**: [The actual question text]

- [ ] `option-a` - Option A description
- [ ] `option-b` - Option B description
- [ ] `option-c` - Option C description
- [ ] `other` - Other (specify below)

**Answer**: 
<!-- Check one option above or specify here -->
```

**Text questions**:
```markdown
### Q2: [Question Title]

**Type**: text

**Question**: [The actual question text]

**Example**: "[Example answer to guide the user]"

**Answer**: 
<!-- Write your answer here -->
```

**Reference questions**:
```markdown
### Q3: [Question Title]

**Type**: reference

**Question**: [The actual question text]

**Accepts**: Path to a file (relative to repo root) or URL containing the answer

**Answer**: 
<!-- Provide path or URL, or write "None" -->
```

## Processing Completed Requests

When processing an answered input request:

1. **Read the document**: Parse the frontmatter and all question answers
2. **Validate answers**: Ensure all required questions have answers
3. **Use the information**: Apply the answers to continue the related task
4. **Update status**: Change `status` from `answered` to `processed` in frontmatter
5. **Archive**: Move the file to `docs/input-requests/archive/`
6. **Log**: Record the processing in the agent-run log, including which task was unblocked

## Document Location

- **Active requests**: `docs/input-requests/`
- **Processed requests**: `docs/input-requests/archive/`
- **Template**: `docs-eng-process/templates/input-request.md`

## Status Lifecycle

- `pending` → User fills out the document
- `answered` → User updates status and saves (agent processes this)
- `processed` → Agent has processed the answers and archived the document

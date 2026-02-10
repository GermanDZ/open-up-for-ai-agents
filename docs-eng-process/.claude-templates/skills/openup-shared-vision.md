---
name: openup-shared-vision
description: Create shared technical vision for team alignment
arguments:
  - name: technical_objectives
    description: Key technical objectives to address (comma-separated)
    required: false
  - name: scope_focus
    description: Focus area for IN/OUT scope definition
    required: false
---

# Shared Vision

This skill creates a shared technical vision document that ensures alignment between stakeholders and the development team on technical objectives, scope, and key decisions.

## When to Use

Use this skill when:
- Vision document exists but needs technical elaboration
- Need to define IN/OUT scope clearly
- Starting Elaboration phase and need technical alignment
- Team members have different understanding of technical direction
- Need to document key technical decisions and constraints

## When NOT to Use

Do NOT use this skill when:
- No vision document exists (use `/openup-create-vision` first)
- In late Construction or Transition phases (should already exist)
- Only need architecture details (use `/openup-create-architecture-notebook`)
- Vision is already well-defined and understood

## Success Criteria

After using this skill, verify:
- [ ] Technical objectives are clearly documented
- [ ] IN/OUT scope is well-defined
- [ ] Technical assumptions and constraints are listed
- [ ] Key technical decisions have rationale
- [ ] Open questions are tracked for elaboration
- [ ] Document is linked from main vision

## Process Summary

1. Read existing vision document
2. Extract technical context and objectives
3. Define IN/OUT scope
4. Document technical assumptions and constraints
5. Record key technical decisions
6. Identify open questions

## Detailed Steps

### 1. Read Existing Vision

Read `docs/vision.md` to understand:
- Project problem statement
- Stakeholder needs
- Business objectives
- Current project status

### 2. Extract Technical Context

From the vision and project status, identify:

**Technical Objectives:**
- What technical problems need to be solved?
- What are the key quality attributes (performance, security, scalability)?
- What technical success criteria exist?

**If `$ARGUMENTS[technical_objectives]` is provided:**
- Focus on those specific objectives
- Add related technical objectives

**Examples:**
- "Achieve sub-second response times"
- "Support 10,000 concurrent users"
- "Ensure data encryption at rest and in transit"

### 3. Define IN/OUT Scope

Create clear boundaries for what is included and excluded:

**IN Scope:**
What features and capabilities are definitely included?
- Use `$ARGUMENTS[scope_focus]` as a starting point if provided
- List specific features, capabilities, and technologies
- Be specific about what "in scope" means

**OUT Scope:**
What is explicitly excluded to manage expectations?
- Features that are explicitly NOT being built
- Technologies that won't be used
- Capabilities that are out of scope for this project

### 4. Document Technical Assumptions

Record assumptions about the technical environment:

| Assumption | Impact | Validated By |
|------------|--------|--------------|
| Example: PostgreSQL available | Low - affects data layer | DBA |
| Example: Users on modern browsers | Medium - affects frontend | UX research |

### 5. Document Technical Constraints

Record known constraints that limit options:

| Constraint | Description | Mitigation |
|------------|-------------|------------|
| Example: Budget for cloud services | Must use cost-effective solutions | Serverless architecture |
| Example: Legacy system integration | Must work with existing APIs | Adapter pattern |

### 6. Record Key Technical Decisions

Document significant technical decisions with rationale:

**Examples:**
- Choice of programming language
- Architectural style (microservices vs monolith)
- Database selection
- Deployment approach

For each decision:
- What was decided
- Why (rationale)
- Alternatives considered
- Trade-offs accepted

### 7. Identify Open Questions

List questions that need answers during elaboration:

| Question | Impact | Target Phase |
|----------|--------|--------------|
| Example: How to handle offline mode? | High - affects architecture | Elaboration |
| Example: Third-party API limits? | Medium - affects design | Elaboration |

### 8. Create Shared Vision Document

Create `docs/shared-vision.md` using the shared vision template with:
- Technical objectives table
- IN/OUT scope sections
- Assumptions and constraints tables
- Key technical decisions
- Open questions

### 9. Link from Main Vision

Add a reference in `docs/vision.md`:
```markdown
## Technical Vision

See [Shared Vision](shared-vision.md) for detailed technical objectives, scope, and decisions.
```

## Output

Returns a summary of:
- Shared vision document created at `docs/shared-vision.md`
- Technical objectives documented
- IN/OUT scope defined
- Key decisions recorded
- Open questions identified

## Example Usage

```
/openup-shared-vision technical_objectives: "scalability, security" scope_focus: "user authentication"
```

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Vision not found | docs/vision.md doesn't exist | Create vision first with /openup-create-vision |
| Too vague | Objectives not specific enough | Add measurable criteria |
| Missing OUT scope | Only IN scope defined | Always define both IN and OUT |
| No rationale | Decisions without justification | Add why and alternatives considered |

## References

- Shared Vision Template: `docs-eng-process/templates/shared-vision.md`
- Vision Template: `docs-eng-process/templates/vision.md`
- Architecture Notebook Template: `docs-eng-process/templates/architecture-notebook.md`

## See Also

- [openup-create-vision](../create-vision/SKILL.md) - Create project vision first
- [openup-create-architecture-notebook](../create-architecture-notebook/SKILL.md) - Create detailed architecture documentation
- [openup-elaboration](../../openup-phases/elaboration/SKILL.md) - Elaboration phase activities

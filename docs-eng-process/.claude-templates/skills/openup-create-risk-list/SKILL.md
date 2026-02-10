---
name: openup-create-risk-list
description: Create or update risk assessment document from template
arguments:
  - name: risks
    description: JSON array of risks to add (optional)
    required: false
---

# Create Risk List

This skill creates or updates a risk list document from the OpenUP template.

## When to Use

Use this skill when:
- Starting a new project and need to identify risks
- In Inception phase documenting major risks
- New risks emerge during project
- Need to update risk probability or impact
- Planning risk mitigation strategies

## When NOT to Use

Do NOT use this skill when:
- Risk list exists and only minor updates needed (edit directly)
- Looking for issue tracking (use issue tracker)
- Risks have been realized and are now issues (manage as issues)
- Need detailed risk analysis (use risk management process)

## Success Criteria

After using this skill, verify:
- [ ] Risk list exists at `docs/risk-list.md`
- [ ] Risks are documented with descriptions
- [ ] Probability and impact are assessed
- [ ] Mitigation strategies are defined
- [ ] Risk owners are assigned

## Process

### 1. Check for Existing Risk List

Check if `docs/risk-list.md` exists:
- If yes, update it
- If no, create from template

### 2. Copy Template (if new)

If creating new, copy `docs-eng-process/templates/risk-list.md` to `docs/risk-list.md`

### 3. Read Project Context

Read `docs/project-status.md`, `docs/vision.md` to identify potential risks.

### 4. Fill in Risk List

Update with:
- **Project name** and context
- **Risks**: From `$ARGUMENTS[risks]` or identify from project context
  For each risk, document:
  - Risk description
  - Probability (high/medium/low)
  - Impact (high/medium/low)
  - Mitigation strategy
  - Owner/responsible party

### 5. Validate Completeness

Ensure the risk list includes:
- Clear risk descriptions
- Probability and impact assessments
- Mitigation strategies
- Risk owners

## Output

Returns:
- Path to risk list
- Number of risks documented
- High-priority risks summary

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Template not found | Template path incorrect | Verify `docs-eng-process/templates/risk-list.md` exists |
| No risks identified | Project context insufficient | Review vision and requirements for potential risks |
| Missing mitigation | Risks documented without mitigation | Add mitigation strategy for each risk |

## References

- Risk List Template: `docs-eng-process/templates/risk-list.md`
- Risk Management: `docs-eng-process/openup-knowledge-base/practice-management/risk_val_lifecycle/`
- Project Manager Role: `docs-eng-process/openup-knowledge-base/core/role/roles/project-manager-4.md`

## See Also

- [openup-inception](../../openup-phases/inception/SKILL.md) - Inception phase risk identification
- [openup-create-vision](../create-vision/SKILL.md) - Vision reveals potential risks
- [openup-create-architecture-notebook](../create-architecture-notebook/SKILL.md) - Technical risk assessment

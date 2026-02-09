---
name: create-risk-list
description: Create or update risk assessment document from template
arguments:
  - name: risks
    description: JSON array of risks to add (optional)
    required: false
---

# Create Risk List

This skill creates or updates a risk list document from the OpenUP template.

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

## References

- Risk List Template: `docs-eng-process/templates/risk-list.md`
- Risk Management: `docs-eng-process/openup-knowledge-base/practice-management/risk_val_lifecycle/`
- Project Manager Role: `docs-eng-process/openup-knowledge-base/core/role/roles/project-manager-4.md`

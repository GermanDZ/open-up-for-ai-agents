---
title: "[Descriptive Title]"
created: "YYYY-MM-DDTHH:MM:SSZ"
created_by: "agent-name"
status: pending  # pending | answered | processed
run_id: "YYYY-MM-DDTHH:MM:SSZ-agent-branch"
related_task: "T-XXX"  # optional - roadmap task ID
expires: "YYYY-MM-DD"  # optional - for time-sensitive requests
---

# [Descriptive Title]

## Context

[Explain what the agent is doing and why input is needed. Include:
- Current task/phase context
- What specific information is needed
- Why this input is important for progress]

## Questions

### Q1: [Question Title]

**Type**: multiple-choice | text | reference

**Question**: [The actual question text]

[For multiple-choice questions:]
- [ ] `option-a` - Option A description
- [ ] `option-b` - Option B description
- [ ] `option-c` - Option C description
- [ ] `other` - Other (specify below)

[For text questions:]
**Example**: "[Example answer to guide the user]"

[For reference questions:]
**Accepts**: Path to a file (relative to repo root) or URL containing the answer

**Answer**: 
<!-- Fill your answer here -->


### Q2: [Question Title]

**Type**: [multiple-choice | text | reference]

**Question**: [The actual question text]

[Include appropriate format based on question type]

**Answer**: 
<!-- Fill your answer here -->


## Instructions

1. Fill in the **Answer** section for each question above
2. For multiple-choice questions, check the appropriate option with `[x]` (change `[ ]` to `[x]`)
3. For text questions, write your answer in the Answer section
4. For reference questions, provide a file path (relative to repo root) or URL, or write "None" if not applicable
5. Update the frontmatter `status` field from `pending` to `answered` when all questions are complete
6. Save this file
7. Tell the agent to continue (e.g., "Continue with input-requests" or "Process input-requests")

**This document can be shared via email.** Recipients can fill it and return it. Save their responses to this file before resuming the agent.

---

## Agent Processing Notes

<!-- This section is for agent use only. Do not modify. -->

[When the agent processes this request, it will:
1. Read all answers
2. Use the information to continue the task
3. Update status to `processed`
4. Move this file to `docs/input-requests/archive/`]

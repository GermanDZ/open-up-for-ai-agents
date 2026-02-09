---
title: "[T-XXX] Brief description of changes"
created: "YYYY-MM-DDTHH:MM:SSZ"
created_by: "agent-name"
task_id: "T-XXX"
pr_link: "https://github.com/org/repo/pull/XXX"
base_branch: "main"
head_branch: "feature/T-XXX-description"
status: open  # open | merged | closed
---

# [{{TASK_ID}}] {{PR_TITLE}}

## Summary

{{BRIEF_DESCRIPTION_OF_CHANGES}}

## Task Context

- **Task ID**: `{{TASK_ID}}`
- **Description**: {{TASK_DESCRIPTION_FROM_ROADMAP}}
- **Priority**: {{PRIORITY_FROM_ROADMAP}}
- **Status**: {{STATUS_FROM_ROADMAP}}

{{IF_RELATED_REQUIREMENTS}}
### Related Requirements
- {{REQUIREMENT_ID_1}}: {{Requirement description}}
- {{REQUIREMENT_ID_2}}: {{Requirement description}}
{{END_IF}}

{{IF_RELATED_RISKS}}
### Related Risks
- {{RISK_ID_1}}: {{Risk description}}
- {{RISK_ID_2}}: {{Risk description}}
{{END_IF}}

## Changes Made

### Files Changed
```
{{LIST_OF_CHANGED_FILES_FROM_GIT_DIFF}}
```

### Commits
```
{{GIT_LOG_OUTPUT_WITH_COMMIT_MESSAGES}}
```

### Implementation Notes

{{ADDITIONAL_CONTEXT_ABOUT_IMPLEMENTATION_DECISIONS}}

## Testing Performed

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Code review completed
- [ ] Documentation updated
- [ ] No regressions detected

### Test Details

{{SPECIFIC_TEST_CASES_EXECUTED_AND_RESULTS}}

## Review Checklist

### Code Quality
- [ ] Code follows project style guidelines
- [ ] No TODOs or FIXMEs left in production code
- [ ] Error handling is appropriate
- [ ] Logging is adequate for debugging

### Documentation
- [ ] Code comments are clear and accurate
- [ ] API documentation updated (if applicable)
- [ ] User-facing documentation updated (if applicable)
- [ ] Architecture notebook updated (if architectural change)

### Testing
- [ ] Unit tests cover new functionality
- [ ] Unit tests cover edge cases
- [ ] Integration tests included (if applicable)
- [ ] Test cases documented in test plan

### Merge Readiness
- [ ] No merge conflicts with base branch
- [ ] All CI/CD checks pass
- [ ] Dependencies updated (if applicable)
- [ ] Database migrations included (if applicable)

## Related Issues

- Closes #{{TASK_ID}} in roadmap
- Related to {{ISSUE_URLS_OR_REFS}}

## Breaking Changes

{{IF_BREAKING_CHANGES}}
### Breaking Change Details
- **What changed**: {{DESCRIPTION}}
- **Migration path**: {{MIGRATION_STEPS}}
- **Impact**: {{WHO_IS_AFFECTED}}
{{ELSE}}
No breaking changes.
{{END_IF}}

## Notes

{{ADDITIONAL_CONTEXT_FOR_REVIEWERS}}

## Checklist

- [ ] I have read the OpenUP contribution guidelines
- [ ] My code follows the project style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have tested my changes locally
- [ ] My changes do not introduce new dependencies

---

## Agent Processing Notes

<!-- This section is for agent use only. Do not modify. -->

[When the PR is merged, the agent will:
1. Update docs/roadmap.md task status to 'completed'
2. Update docs/project-status.md with completion date
3. Create traceability log entry
4. Delete the feature branch if appropriate]

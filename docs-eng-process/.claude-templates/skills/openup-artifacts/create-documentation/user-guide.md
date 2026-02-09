# User Guide Documentation

This file provides detailed instructions for generating user guides from use cases and code.

## When to Generate User Guides

Generate user guides when:
- A feature is complete and ready for users
- Need to document how end users interact with the system
- Preparing for release or handoff
- Onboarding new users

## Process

### 1. Read Use Cases

Find and read the relevant use case files:
- `docs/use-cases/<feature>*.md`

Extract:
- Actor profiles (who is using the feature)
- User goals (what they want to accomplish)
- Preconditions (what they need before starting)
- Basic flow (happy path usage)
- Alternative flows (different ways to use the feature)

### 2. Extract Test Cases

Read test cases for realistic scenarios:
- `docs/test-cases/<feature>*.md`

Test cases often contain:
- Step-by-step procedures
- Test data that can become examples
- Edge cases that become troubleshooting items

### 3. Review Code for UI Elements

For UI-based features, identify:
- Screen names and navigation paths
- Form fields and their validations
- Buttons and actions
- Error messages and their causes

### 4. Generate User Guide Structure

Using the user guide template, create:

**Feature Overview:**
- What the feature does
- Who should use it
- Key benefits

**Prerequisites:**
- What users need before starting
- Account requirements
- Permissions
- Setup steps

**Getting Started:**
- Initial setup/configuration
- First-time use instructions

**Using the Feature:**
- Basic usage (most common tasks)
- Step-by-step procedures with screenshots
- Examples with realistic data

**Common Use Cases:**
- Scenario-based instructions
- Real-world examples
- Workflows for different goals

**Troubleshooting:**
- Common issues and solutions
- Error messages and what they mean
- How to get help

**FAQ:**
- Questions from use case alternative flows
- Questions from test scenarios
- Questions from stakeholder feedback

### 5. Write Clear Instructions

**Guidelines:**
- Use active voice ("Click Save" not "The Save button should be clicked")
- Write for the user's level of expertise
- Include examples with realistic data
- Add screenshots or diagrams where helpful
- Number steps for procedures

**Example:**

Good:
```
1. Navigate to Settings > Account
2. Click "Change Password"
3. Enter your current password
4. Enter your new password twice
5. Click "Update Password"
```

Poor:
```
The user should navigate to the Settings menu and select Account.
Then they need to click on the Change Password button...
```

### 6. Add Visual Elements

Where appropriate, include:
- Screenshots (with annotations)
- Diagrams showing workflows
- Tables for options/settings
- Code blocks for examples
- Callout boxes for tips and warnings

### 7. Review and Test

- Follow your own instructions
- Verify all screenshots are current
- Check all links work
- Have someone unfamiliar test the guide

## Output Format

User guides are typically created as:
- Markdown files for web documentation
- PDF for downloadable guides
- Inline help text for the application

## Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| Too technical | Focus on user goals, not implementation |
| Out of date | Set up review process with each release |
| No examples | Add realistic examples for each procedure |
| Missing edge cases | Include troubleshooting section |

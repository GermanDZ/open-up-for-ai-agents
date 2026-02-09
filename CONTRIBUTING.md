# Contributing to OpenUP for AI Agents

Thank you for your interest in contributing to the OpenUP for AI Agents framework! This document provides guidelines for contributing.

## Overview

This framework provides OpenUP (Open Unified Process) methodology adapted for AI-agent-driven software development. It includes:

- **docs-eng-process/** - Engineering process documentation and agent workflows
- **Agent team templates** - Claude Code agent teammate instructions for OpenUP roles
- **Update scripts** - Tools for updating existing projects with template changes
- **Test suite** - Automated tests to verify all scripts work correctly

## Development Workflow

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/open-up-for-ai-agents.git
cd open-up-for-ai-agents

# Add upstream as a remote
git remote add upstream https://github.com/GermanDZ/open-up-for-ai-agents.git
```

### 2. Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or use the naming convention:
# feature/description
# fix/description
# docs/description
```

### 3. Make Changes

- Edit files following the project structure
- Follow existing code style and conventions
- Add/update tests as needed
- Update documentation

### 4. Test Your Changes

```bash
# Run the test suite
./tests/test-scripts.sh

# Test scripts manually
./scripts/bootstrap-project.sh /tmp/test-project
```

### 5. Commit Changes

Follow the commit message format from `docs-eng-process/conventions.md`:

```
type(scope): brief description

- Detail about what changed
- Why it changed (if not obvious)

Refs #issue-number
```

**Types**: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

Example:
```
scripts: Fix setup-agent-teams.sh to use current directory

- Use TEMPLATE_ROOT for template files
- Use PROJECT_ROOT (current dir) for target files
- Fixes issue where script installed files in wrong location
```

### 6. Sync and Push

```bash
# Sync with upstream
git fetch upstream
git rebase upstream/main

# Push to your fork
git push origin feature/your-feature-name
```

### 7. Create Pull Request

- Go to GitHub and create a pull request
- Reference any related issues
- Describe your changes clearly
- Ensure CI checks pass

## Project Structure

```
open-up-for-ai-agents/
├── docs-eng-process/           # Engineering process (DO NOT modify during project tasks)
│   ├── .claude-templates/      # Agent team templates
│   │   ├── teammates/          # Individual role instructions
│   │   ├── teams/              # Team configurations
│   │   └── CLAUDE.md           # Main CLAUDE.md template
│   ├── openup-knowledge-base/  # OpenUP documentation (vendored)
│   ├── templates/              # Document templates
│   ├── agent-workflow.md       # Agent operating procedures
│   ├── agent-teams-setup.md    # Agent teams setup guide
│   ├── updating.md             # Update guide
│   └── .template-version       # Version tracking
├── scripts/                    # Utility scripts
│   ├── bootstrap-project.sh    # Create new project
│   ├── setup-agent-teams.sh    # Install agent teams
│   ├── update-from-template.sh # Update from template
│   ├── update-openup.sh        # Update wrapper
│   └── update-openup-simple.sh # Simple update script
├── tests/                      # Test suite
│   └── test-scripts.sh         # Automated tests
├── converter/                  # OpenUP HTML to Markdown converter
└── README.md                   # Project overview
```

## Types of Contributions

### Bug Fixes

1. Create an issue describing the bug
2. Create a branch: `fix/bug-description`
3. Write a test that reproduces the bug
4. Fix the bug
5. Verify all tests pass
6. Submit PR

### New Features

1. Create an issue describing the feature
2. Get feedback on the approach
3. Create a branch: `feature/feature-name`
4. Implement the feature
5. Add/update tests
6. Update documentation
7. Submit PR

### Documentation

1. Create a branch: `docs/what-improving`
2. Update documentation
3. Verify clarity and accuracy
4. Submit PR

### Agent Team Roles

When adding or modifying agent team roles:

1. **Role Instructions** (`docs-eng-process/.claude-templates/teammates/*.md`):
   - Base content on OpenUP role definitions in `openup-knowledge-base/core/role/roles/`
   - Include: Role Definition, Key Responsibilities, Skills, Work Products, Tasks
   - Specify collaboration patterns with other roles
   - Add key references

2. **Team Configurations** (`docs-eng-process/.claude-templates/teams/*.md`):
   - Define role focus areas
   - Specify collaboration patterns
   - Provide example prompts

3. **Update Tests**:
   - Add tests for new roles in `tests/test-scripts.sh`

### Script Changes

When modifying scripts:

1. **Maintain backward compatibility** when possible
2. **Add error handling** for edge cases
3. **Use appropriate exit codes**
4. **Include helpful error messages**
5. **Update tests** to cover new functionality
6. **Update documentation** (scripts/README.md, docs-eng-process/updating.md)

## Testing

### Running Tests

```bash
# Run all tests
./tests/test-scripts.sh

# Test specific functionality
./scripts/bootstrap-project.sh /tmp/test-project
./scripts/setup-agent-teams.sh
./scripts/update-from-template.sh --dry-run
```

### Writing Tests

Add tests to `tests/test-scripts.sh` following the existing pattern:

```bash
test_start "Description of test"
# Setup
TEST_DIR="/tmp/openup-test-XXX"
mkdir -p "$TEST_DIR"

# Execute
if command; then
    # Verify
    if condition; then
        test_pass "Success message"
    else
        test_fail "Failure message" "Details"
    fi
else
    test_fail "Execution failed" "Details"
fi

# Cleanup happens automatically via trap
```

## Documentation Standards

### Markdown Style

- Use ATX-style headers (`#` `##` `###`)
- Use sentence case for headers
- Include blank line before headers
- Use `-` for unordered lists
- Use proper spacing around code blocks

### Code Blocks

```bash
# Shell/bash
```bash
command here
```

```python
# Python
```python
code here
```

### Links

- Use relative links for internal references
- Include descriptive link text
- Test links before committing

## Version Management

### Template Version

When making changes that should be propagated to projects using this template:

1. Update `docs-eng-process/.template-version`
2. Follow semantic versioning (MAJOR.MINOR.PATCH)
   - MAJOR: Breaking changes
   - MINOR: New features (backward compatible)
   - PATCH: Bug fixes

### Changelog

Maintain a changelog in the release notes or commit history:

```
## [1.5.0] - 2025-02-09
### Added
- Agent team templates for OpenUP roles
- Update scripts for template synchronization
- Automated test suite

### Changed
- Improved bootstrap script to create scripts directory
- Fixed setup-agent-teams.sh to use current directory

### Fixed
- Bootstrap script not creating .claude directory
```

## Code Style

### Shell Scripts

- Use `#!/bin/bash` shebang
- Use `set -e` for error handling
- Quote variables: `"$VAR"`
- Use functions for reusable code
- Include comments for complex logic
- Use meaningful variable names

### File Naming

- Scripts: `lowercase-with-dashes.sh`
- Docs: `lowercase-with-dashes.md`
- Templates: follow existing patterns

## Pull Request Guidelines

### Before Submitting

- [ ] Tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages follow conventions
- [ ] Branch is up to date with main

### PR Description

Include:

- **Summary**: Brief description of changes
- **Motivation**: Why this change is needed
- **Changes**: List of files modified
- **Testing**: How changes were tested
- **Screenshots**: If applicable (for UI changes)

### Review Process

1. Automated checks must pass
2. At least one maintainer approval required
3. Address review feedback
4. Squash commits if requested
5. Maintain clean commit history

## Getting Help

- **Issues**: Use GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: See `docs-eng-process/` for detailed guides

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## Acknowledgments

This framework is based on:
- OpenUP (Open Unified Process) from the Eclipse Foundation
- Claude Code agent teams from Anthropic

Thank you for contributing!

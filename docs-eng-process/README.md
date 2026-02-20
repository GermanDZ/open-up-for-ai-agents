# Engineering Process - AI Agent Entrypoint

**⚠️ STRICT PROCESS: This directory contains the authoritative engineering process. Agents must follow these procedures. Do not modify files in `docs-eng-process/` during project tasks.**

## Quick Start

### For New Users

**📘 Start here:** [USER-GUIDE.md](USER-GUIDE.md) - Complete guide for using OpenUP with Claude Code

- Getting started with new projects
- Core concepts and common workflows
- Skills and teams reference
- Configuration and troubleshooting

**📄 Quick reference:** [QUICK-REFERENCE.md](QUICK-REFERENCE.md) - One-page cheat sheet

**🔄 Updates:** [updating.md](updating.md) - Canonical update guide and decision tree

### For AI Agents

1. **Read this file first** - understand the process structure
2. **Read [agent-workflow.md](agent-workflow.md)** - detailed operating procedures
3. **Initialize a new project**:
   - **Agent-driven**: Use [init-prompts.md](init-prompts.md) for copy/paste prompts (recommended)
   - **Manual**: Follow [getting-started.md](getting-started.md) for step-by-step setup

## Process Structure

This repository follows the **OpenUP** (Open Unified Process) methodology, adapted for AI-agent-driven development.

### Core Concepts

- **[Project Lifecycle](openup-knowledge-base/practice-management/risk_value_lifecycle/guidances/concepts/project-lifecycle.md)** - Four phases: Inception, Elaboration, Construction, Transition
- **[Phase Milestones](openup-knowledge-base/practice-management/risk_value_lifecycle/guidances/concepts/phase-milestones.md)** - Decision points at the end of each phase
- **[Introduction to OpenUP](openup-knowledge-base/guides/base/guidances/supportingmaterials/introduction-to-openup.md)** - Overview of the methodology

### Process Documentation

- **[agent-workflow.md](agent-workflow.md)** - Complete agent SOP (start-of-run, role-based execution, branching, logging)
- **[how-to-work.md](how-to-work.md)** - Minimal orientation and references
- **[getting-started.md](getting-started.md)** - Project initialization guide

### Templates

All document templates are in [templates/](templates/). These are sourced from the OpenUP knowledge base and should be used when creating project artifacts.

## Key Rules

1. **Strict Process**: Agents must follow `docs-eng-process/` procedures. If blocked, log the issue in `docs/` and proceed only as allowed.
2. **Self-Contained**: All links in `docs-eng-process/` reference only `docs-eng-process/` or `docs/` (no repo-root links).
3. **Project Docs**: `docs/` contains only project-specific artifacts (no instructions). Process guidance lives here.

## OpenUP Knowledge Base

The complete OpenUP knowledge base is vendored under [openup-knowledge-base/](openup-knowledge-base/) for reference. All process documentation links to this vendored copy.

---

**Next Steps**: Read [agent-workflow.md](agent-workflow.md) for detailed operating procedures.

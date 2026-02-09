# OpenUP Quick Reference

**Essential commands and workflows for OpenUP with Claude Code.**

---

## Essential Skills

```
/inception activity: initiate        # Start Inception phase
/elaboration activity: initiate       # Start Elaboration phase
/construction activity: initiate      # Start Construction phase
/transition activity: initiate        # Start Transition phase

/start-iteration goal: "..."          # Begin new iteration
/complete-task task_id: T-001         # Finish task, commit, update
/create-pr task_id: T-001             # Create pull request
/request-input title: "..."           # Request stakeholder input
/phase-review                         # Check phase completion
/log-run                              # Create traceability logs

/create-vision project_name: "..." problem_statement: "..."
/create-use-case use_case_name: "..." primary_actor: "..." description: "..."
/create-architecture-notebook system_name: "..." architectural_concerns: "..."
/create-risk-list risks: '[...]'
/create-iteration-plan iteration_number: 1
/create-test-plan scope: "..."
```

---

## Agent Teams

### Create a Team

```
Create an OpenUP agent team with [roles] to [task description].

Spawn:
- [role]: to [focus]
- [role]: to [focus]
```

### Team Templates

| Team | Roles | Use For |
|------|-------|---------|
| **Inception** | analyst, project-manager (+ architect) | Define vision, scope |
| **Elaboration** | architect, developer, tester (+ analyst) | Architecture baseline |
| **Construction** | developer, tester (+ architect, analyst) | Build features |
| **Transition** | tester, project-manager, developer (+ analyst) | Deploy to users |
| **Feature** | analyst, architect, developer, tester | Implement feature |
| **Investigation** | architect, developer, tester | Debug issues |
| **Planning** | project-manager, analyst (+ architect) | Plan iteration |
| **Full** | All roles | Comprehensive work |

### Enable Agent Teams

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

---

## Quick Workflows

### Start New Project
```bash
./scripts/bootstrap-project.sh my-project --base-dir ~/projects
cd ~/projects/my-project
# Run Prompt A from docs-eng-process/init-prompts.md
# Run Prompt B from docs-eng-process/init-prompts.md
```

### Continue Roadmap Work
```
Continue with the next task from docs/roadmap.md.
```

### Implement Feature
```
Create an OpenUP feature team for [feature name].
Implement following OpenUP workflow.
/complete-task task_id: T-XXX create_pr: true
```

### Fix Bug
```
Create an OpenUP investigation team for [bug description].
Find root cause, implement fix, verify.
/complete-task task_id: T-XXX create_pr: true
```

### Add Feature to Roadmap
```
Add task T-XXX to docs/roadmap.md: [feature description].
Priority: high, Status: pending.
```

---

## Project State Documents

| Document | Location | Purpose |
|----------|----------|---------|
| **Project Status** | `docs/project-status.md` | Phase, iteration, goals, blockers |
| **Roadmap** | `docs/roadmap.md` | Task backlog with priorities |
| **Vision** | `docs/vision.md` | Project vision and scope |
| **Risk List** | `docs/risk-list.md` | Risk tracking |
| **Architecture** | `docs/architecture-notebook.md` | Architecture decisions |
| **Phase Notes** | `docs/phases/{phase}/notes.md` | Phase progress |

---

## OpenUP Phases

```
Inception → Elaboration → Construction → Transition
   ↓              ↓               ↓              ↓
Vision/Scope   Architecture     Build         Deploy
1-2 weeks      2-4 weeks      Multiple      Variable
```

| Phase | Focus | Key Artifacts |
|-------|-------|---------------|
| **Inception** | Define scope, vision | Vision, Risk List, Initial Roadmap |
| **Elaboration** | Architecture baseline | Architecture Notebook, Detailed Use Cases |
| **Construction** | Build incrementally | Code, Tests, Working Software |
| **Transition** | Deploy to users | Deployment, User Acceptance |

---

## Branching

```
trunk (main/master)
  ↑
  └── feature/T-001-description  (work here)
  └── fix/T-002-bug-description
```

**Rules:**
1. Never work on trunk
2. Create branch for each task
3. Merge or PR before next task
4. Use descriptive names with task IDs

---

## Task Status Flow

```
pending → in-progress → completed
         ↓
       blocked → in-progress
```

**Roadmap format:**
```markdown
| ID | Description | Priority | Status | Owner |
|----|-------------|----------|--------|-------|
| T-001 | Implement login | high | in-progress | developer |
| T-002 | Fix bug | medium | pending | - |
```

---

## End-of-Run Checklist

Before agent stops, verify:
- [ ] All changes committed
- [ ] No uncommitted changes (`git status --porcelain` empty)
- [ ] Traceability logs created
- [ ] docs/ updated (project-status, roadmap, phase notes)
- [ ] Task marked complete in roadmap

---

## Navigation (In-Process Team Mode)

| Key | Action |
|-----|--------|
| `Shift+Up/Down` | Cycle through teammates |
| `Shift+Left/Right` | Switch agent/user view |

---

## File Locations

| Type | Location | Edit? |
|------|----------|-------|
| **Your work** | `docs/` | YES |
| **Process** | `docs-eng-process/` | NO (template) |
| **Skills** | `.claude/skills/` | Installed only |
| **Teams** | `.claude/teams/` | Installed only |
| **Settings** | `.claude/settings.json` | YES |

---

## Common Commands

```bash
# Enable agent teams
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# Bootstrap new project
./scripts/bootstrap-project.sh my-project --base-dir ~/projects

# Setup agent teams
./scripts/setup-agent-teams.sh

# Update from template
./scripts/update-from-template.sh

# Check git status
git status

# Create branch
git checkout -b feature/T-001-description

# View logs
git log --oneline
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Teams not appearing | Check `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` |
| Can't find teammate | Press `Shift+Down` to cycle |
| Changes not committed | Run `git status`, then commit manually |
| Skill not found | Check `.claude/skills/` exists |
| Project status missing | Initialize with Prompt A from init-prompts.md |

---

## When to Use Each Skill

| Situation | Skill |
|-----------|-------|
| Starting phase | `/inception`, `/elaboration`, `/construction`, `/transition` |
| Need vision | `/create-vision` |
| Defining requirements | `/create-use-case` |
| Architecture work | `/create-architecture-notebook` |
| Identifying risks | `/create-risk-list` |
| Starting iteration | `/start-iteration` |
| Finishing work | `/complete-task` |
| Creating PR | `/create-pr` |
| Need input | `/request-input` |
| Phase review | `/phase-review` |
| Logging | `/log-run` |

---

## Related Documentation

- **Full User Guide:** [USER-GUIDE.md](USER-GUIDE.md)
- **Agent Workflow:** [agent-workflow.md](agent-workflow.md)
- **Skills Guide:** [skills-guide.md](skills-guide.md)
- **Teams Guide:** [teams-guide.md](teams-guide.md)
- **Getting Started:** [getting-started.md](getting-started.md)
- **Initialization Prompts:** [init-prompts.md](init-prompts.md)

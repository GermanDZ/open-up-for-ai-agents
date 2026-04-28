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
/quick-task task: "..."               # Fast path for tiny, low-risk changes
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

**Closure path rule**:
- If you ran `/complete-task`, do not run `/log-run` again unless recovering from a logging failure.

---

## Low-token Patterns

- Use `/quick-task` for tiny fixes and short docs changes
- Prefer targeted search and partial reads over full-file dumps
- For noisy commands, return summary + tail output only
- Avoid repeated state checks when no state changed
- Keep progress updates to concise delta-only notes

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

## Skill Fit Matrix

Each workflow skill declares what it's good and bad for in its own front-matter
(`fit:` block). This matrix is the consolidated view — pick the skill whose
"great" column matches your situation.

| Skill | Great for | OK for | Poor fit |
|-------|-----------|--------|----------|
| `/quick-task` | typo fixes, doc updates, single-file config tweaks, hotfixes | small bug fixes (<50 LOC), single-component refactors | new features, multi-role work, architectural changes |
| `/start-iteration` | feature work, multi-step tasks, anything needing a deployed team | single-component changes that benefit from explicit framing | typo fixes, hotfixes, exploratory spikes, throwaway scripts |
| `/orchestrate` | complex multi-role tasks, architecture+impl+test cycles | medium tasks where decomposition aids token-efficiency | trivial changes, single-role work, hotfixes |
| `/plan-feature` | turning a fresh feature idea into a plan + roadmap entry | re-planning when scope shifts mid-flight | already-scoped tasks (skip to `/start-iteration`) |
| `/complete-task` | finishing a roadmap-tracked task, ending an iteration | closing out ad-hoc work needing commit + roadmap update | mid-task checkpoints, abandoning WIP |
| `/create-pr` | shipping a finished task, opening a review-ready PR | WIP / draft PRs for early feedback | pre-merge to local-only branches, uncommitted work |
| `/assess-completeness` | pre-merge quality gate, phase transitions, artifact rubric grading | mid-iteration sanity checks on partial artifacts | pure code changes (no rubric), exploratory work |
| `/phase-review` | end-of-phase milestone evaluation, transition gates | mid-phase sanity check on completion criteria | within-iteration progress checks |
| `/retrospective` | end-of-iteration reflection, capturing patterns | mid-iteration reset when blockers pile up | single-task wrap-ups, trivial iterations |
| `/request-input` | blocked tasks needing human decision, ambiguous requirements | scope/priority clarifications mid-iteration | obvious answers, urgent same-session needs |
| `/tdd-workflow` | well-specified features with clear test surface, regression bug fixes | refactors with strong existing test coverage | exploratory spikes, prototyping, UI-only tweaks |
| `/log-run` | end-of-session wrap-up after commits, audit-required workflows | mid-session checkpoints when commits exist | pre-commit runs (no SHAs), trivial sessions handled by hooks |

**Rule of thumb.** If your situation appears in a "poor fit" column, pick a different skill — don't force-fit.

---

## Related Documentation

- **Full User Guide:** [USER-GUIDE.md](USER-GUIDE.md)
- **Agent Workflow:** [agent-workflow.md](agent-workflow.md)
- **Skills Guide:** [skills-guide.md](skills-guide.md)
- **Teams Guide:** [teams-guide.md](teams-guide.md)
- **Getting Started:** [getting-started.md](getting-started.md)
- **Initialization Prompts:** [init-prompts.md](init-prompts.md)

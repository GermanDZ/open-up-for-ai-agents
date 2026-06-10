# Model Tiers

Decision doc for model tiering across OpenUP skills, agents, and team roles.
Tiering is **declared, not advised**: every skill and agent carries a `model:`
frontmatter line, and team configs assign a model per role. Prose hints like
"use a lightweight model" are not used — they were ignored in practice (see
Rationale).

## The Four Tiers

| Tier | Model | What belongs here |
|------|-------|-------------------|
| **Scribe** | `haiku` | Fully-specified mechanical writes: log appends, status field updates, roadmap status flips, JSONL records. The caller decides every value; the scribe only writes. |
| **Coordination** | `haiku` | Process orchestration with low judgment per step: starting iterations, deploying teams, phase checklists, rubric-driven grading against explicit criteria, retrospective assembly. |
| **Authoring** | `inherit` | Producing artifacts that require synthesis and domain judgment: use cases, vision, architecture notebook, iteration plans, test plans, task specs, documentation, PR descriptions. |
| **Reasoning** | `inherit` | Open-ended problem solving: implementation, TDD, exploration, multi-role orchestration, task completion (which embeds judgment about quality gates). |

`inherit` means the skill/agent runs on whatever model the session is using —
judgment-bearing work always gets the session model. `haiku` pins the cheapest
model for work where a stronger model adds cost but no quality.

## Skill Assignments (29 skills)

| Skill | Location | Model | Tier |
|-------|----------|-------|------|
| openup-log-run | workflow | `haiku` | Scribe |
| openup-request-input | workflow | `haiku` | Scribe |
| openup-start-iteration | workflow | `haiku` | Coordination |
| openup-deploy-team | workflow | `haiku` | Coordination |
| openup-phase-review | workflow | `haiku` | Coordination |
| openup-assess-completeness | workflow | `haiku` | Coordination |
| openup-retrospective | workflow | `haiku` | Coordination |
| openup-inception | phases | `haiku` | Coordination |
| openup-elaboration | phases | `haiku` | Coordination |
| openup-construction | phases | `haiku` | Coordination |
| openup-transition | phases | `haiku` | Coordination |
| openup-create-architecture-notebook | artifacts | `inherit` | Authoring |
| openup-create-documentation | artifacts | `inherit` | Authoring |
| openup-create-iteration-plan | artifacts | `inherit` | Authoring |
| openup-create-risk-list | artifacts | `inherit` | Authoring |
| openup-create-task-spec | artifacts | `inherit` | Authoring |
| openup-create-test-plan | artifacts | `inherit` | Authoring |
| openup-create-use-case | artifacts | `inherit` | Authoring |
| openup-create-vision | artifacts | `inherit` | Authoring |
| openup-detail-use-case | artifacts | `inherit` | Authoring |
| openup-shared-vision | artifacts | `inherit` | Authoring |
| openup-complete-task | workflow | `inherit` | Reasoning |
| openup-create-pr | workflow | `inherit` | Authoring |
| openup-explore | workflow | `inherit` | Reasoning |
| openup-tdd-workflow | workflow | `inherit` | Reasoning |
| openup-init | top-level | `inherit` | Reasoning |
| openup-orchestrate | top-level | `inherit` | Reasoning |
| openup-plan-feature | top-level | `inherit` | Authoring |
| openup-quick-task | top-level | `inherit` | Reasoning |

Totals: 11 × `haiku`, 18 × `inherit`.

## Agents

| Agent | Model | Tier | Purpose |
|-------|-------|------|---------|
| openup-scribe (`.claude/agents/openup-scribe.md`) | `haiku` | Scribe | Mechanical writer for logs, status updates, roadmap entries. Receives fully-specified instructions; never decides. |
| openup-explorer (`.claude/agents/openup-explorer.md`) | `haiku` | Scribe/Coordination | Read-only context gatherer: file excerpts, git metadata, doc summaries. Never modifies anything. |

## Team Role Assignments

Declared per role in each `.claude/teams/openup-*-team.md` (`- **Model**:` bullet).

| Role | Model | Tier |
|------|-------|------|
| project-manager | `haiku` | Coordination |
| developer | `inherit` | Reasoning |
| architect | `inherit` | Reasoning |
| analyst | `inherit` | Authoring |
| tester | `inherit` | Authoring/Reasoning |

## Rationale

Deterministic and mechanical work (log writes, status flips, checklist
walking) gets the cheapest model because a stronger model produces the same
output at higher cost and latency; judgment-bearing work (authoring artifacts,
implementing code, exploring problems) inherits the session model because
quality degrades visibly on smaller models. The enforcement mechanism matters
as much as the assignment: when tiering lived only in prose ("use lightweight
models for coordination"), it was not followed — the Kaze audit showed 1 of 88
runs used Haiku despite the guidance. Declaring the tier in `model:`
frontmatter makes the harness enforce it instead of relying on the agent to
remember.

## How to Change a Tier

1. Edit the `model:` frontmatter in **both** copies: the live file under
   `.claude/` (skills/agents) or the `- **Model**:` bullet (team configs), and
   the mirrored copy under `docs-eng-process/.claude-templates/`.
   (`scripts/check-claude-sync.sh --fix-from-live` mirrors live → templates.)
2. Update the assignment table in this document.
3. Run `scripts/check-claude-sync.sh` to confirm the copies are in sync.

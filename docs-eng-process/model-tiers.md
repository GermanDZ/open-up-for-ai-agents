# Model Tiers

Decision doc for model tiering across OpenUP skills, agents, and team roles.
Tiering is **declared, not advised**: every skill and agent carries a `model:`
frontmatter line, and team configs assign a model per role. Prose hints like
"use a lightweight model" are not used — they were ignored in practice (see
Rationale).

> The per-skill table below is **generated** from the live `model:` frontmatter
> by `scripts/check-model-tiers.py`. Do not hand-edit it. Change a skill's tier
> by editing its `model:` frontmatter, then run `python3
> scripts/check-model-tiers.py --write`. CI (`--check`) fails if the table and
> the frontmatter disagree, or if any skill/agent is missing a `model:` field.

## The Five Tiers

| Tier | Model | What belongs here |
|------|-------|-------------------|
| **Scribe** | `haiku` | Fully-specified mechanical writes: log appends, status field updates, handoff/input-request docs, JSONL records. The caller decides every value; the scribe only writes. |
| **Coordination** | `haiku` | Process orchestration with low judgment per step: starting iterations, deploying teams, phase checklists, the readiness DAG (deterministic by construction). |
| **Authoring** | `sonnet` | Producing artifacts that require synthesis but follow a template + rubric: use cases, vision, architecture notebook, iteration plans, test plans, task specs, documentation, PR descriptions, feature plans, retrospectives (measure read-back and went-well/improve synthesis are analysis, not assembly). Sonnet gives near-Opus authoring quality at materially lower cost. |
| **Quality Gate** | `inherit` | Judgment gates that decide whether work or a phase is *done*: per-criterion rubric grading and milestone phase-review. The gate must never run on a weaker model than the work it judges, so it inherits the session model. |
| **Reasoning** | `inherit` | Open-ended problem solving: implementation, TDD, exploration, multi-role orchestration, task completion (which embeds judgment about quality gates), spec back-propagation. |

`inherit` means the skill/agent runs on whatever model the session is using.
`haiku` pins the cheapest model for work where a stronger model adds cost but no
quality. `sonnet` is the deliberate middle tier for template-and-rubric
authoring, where the session model (often Opus) is more than the task needs.

## Skill Assignments

<!-- BEGIN GENERATED: skill-model-table (scripts/check-model-tiers.py) -->
| Skill | Model |
|-------|-------|
| openup-construction | `haiku` |
| openup-create-handoff | `haiku` |
| openup-deploy-team | `haiku` |
| openup-doctor | `haiku` |
| openup-elaboration | `haiku` |
| openup-inception | `haiku` |
| openup-log-run | `haiku` |
| openup-readiness | `haiku` |
| openup-request-input | `haiku` |
| openup-start-iteration | `haiku` |
| openup-transition | `haiku` |
| openup-assess-iteration | `sonnet` |
| openup-create-architecture-notebook | `sonnet` |
| openup-create-documentation | `sonnet` |
| openup-create-iteration-plan | `sonnet` |
| openup-create-pr | `sonnet` |
| openup-create-risk-list | `sonnet` |
| openup-create-task-spec | `sonnet` |
| openup-create-test-plan | `sonnet` |
| openup-create-use-case | `sonnet` |
| openup-create-vision | `sonnet` |
| openup-detail-use-case | `sonnet` |
| openup-plan-feature | `sonnet` |
| openup-retrospective | `sonnet` |
| openup-shared-vision | `sonnet` |
| openup-assess-completeness | `inherit` |
| openup-complete-task | `inherit` |
| openup-cycle | `inherit` |
| openup-explore | `inherit` |
| openup-fan-out | `inherit` |
| openup-init | `inherit` |
| openup-next | `inherit` |
| openup-orchestrate | `inherit` |
| openup-phase-review | `inherit` |
| openup-quick-task | `inherit` |
| openup-sync-spec | `inherit` |
| openup-tdd-workflow | `inherit` |

**Totals:** 11 × `haiku`, 14 × `sonnet`, 12 × `inherit` (37 skills).
<!-- END GENERATED: skill-model-table -->

The tier each skill belongs to (the prose categories above) is editorial; the
**model** column is the machine-checked source of truth.

## Agents

<!-- BEGIN GENERATED: agent-model-table (scripts/check-model-tiers.py) -->
| Agent | Model |
|-------|-------|
| openup-explorer | `haiku` |
| openup-scribe | `haiku` |
<!-- END GENERATED: agent-model-table -->

- **openup-scribe** — Scribe. Mechanical writer for logs, status updates,
  roadmap entries. Receives fully-specified instructions; never decides.
- **openup-explorer** — Scribe/Coordination. Read-only context gatherer: file
  excerpts, git metadata, doc summaries. Never modifies anything.

## Team Role Assignments

Declared per role in each `.claude/teams/openup-*-team.md` (`- **Model**:` bullet).

| Role | Model | Tier |
|------|-------|------|
| project-manager | `haiku` | Coordination |
| analyst | `sonnet` | Authoring |
| tester | `inherit` | Authoring/Reasoning |
| developer | `inherit` | Reasoning |
| architect | `inherit` | Reasoning |

## Rationale

Deterministic and mechanical work (log writes, status flips, checklist
walking, the readiness DAG) gets the cheapest model because a stronger model
produces the same output at higher cost and latency. Template-and-rubric
authoring gets `sonnet` — near-Opus quality at a fraction of the cost, on the
most frequent class of artifact work. Judgment-bearing work (quality gates,
implementing code, exploring problems) inherits the session model because
quality degrades visibly on smaller models — and a gate must never be weaker
than the author it grades.

The enforcement mechanism matters as much as the assignment: when tiering lived
only in prose ("use lightweight models for coordination"), it was not followed
— the Kaze audit showed 1 of 88 runs used Haiku despite the guidance. Declaring
the tier in `model:` frontmatter makes the harness enforce it instead of
relying on the agent to remember, and `scripts/check-model-tiers.py` keeps this
document from drifting away from the frontmatter.

## How to Change a Tier

1. Edit the `model:` frontmatter in the skill/agent file under
   `docs-eng-process/.claude-templates/` (and the mirrored copy under `.claude/`
   if a live install exists — `scripts/check-claude-sync.sh --fix-from-live`
   mirrors live → templates).
2. Run `python3 scripts/check-model-tiers.py --write` to regenerate the tables
   above, and update the prose tier categories if the tier changed.
3. Run `python3 scripts/check-model-tiers.py --check` (and
   `scripts/check-claude-sync.sh`) to confirm everything is consistent.

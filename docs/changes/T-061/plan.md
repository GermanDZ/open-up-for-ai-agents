---
id: T-061
title: "Optimize template skills for Opus 4.8 / Sonnet 5 — literalism, tier fit, dedup"
status: in-progress
priority: medium
estimate: 1 session
track: standard
depends-on: []
blocks: []
last-synced: ""
touches:
  - docs-eng-process/.claude-templates/skills/
  - .claude/skills/
  - docs-eng-process/model-tiers.md
---

# T-061 — Optimize template skills for Opus 4.8 / Sonnet 5

## Story

> **As a** framework maintainer running OpenUP skills on current Claude models (Opus 4.8 sessions, Sonnet 5 authoring tier, Haiku 4.5 mechanical tier)
> **I want** the 35 template skills tuned to how these models actually follow instructions — literally, with report-then-rank assessment and no stale scaffolding
> **So that** skills produce correct output (no wrong co-author stamps, no Rails greps in Python projects), self-critique surfaces every weakness instead of one, and token bloat from repeated rationale is removed.

## Analysis Context

Seeded by a three-lane tier review (haiku / sonnet / inherit) of all 35 skills in
`docs-eng-process/.claude-templates/skills/` conducted 2026-07-02 against the
Opus 4.8 / Sonnet 5 migration guidance (literal instruction following, recall
depression under conservative filters, native progress narration, tool
under-triggering). Findings summary:

- One output-corrupting bug: `openup-quick-task` stamps commits `Co-Authored-By: Claude Opus 4.6`.
- `openup-plan-feature` hardcodes a Ruby/Rails stack (paths, i18n section, ```ruby fences) that Sonnet 5 follows literally in any project.
- The Self-Critique block shared by all 10 authoring skills says "fix each **genuine** weakness … record **the weakest point**" — on Sonnet 5, "genuine" suppresses recall and the singular caps output at one item.
- Disproportionate emphasis on non-destructive gates (MANDATORY headers on ambiguity gates; "silence is not an option") over-triggers on literal-following models. Real gates (write-fence, two-legal-exits, trunk guard, fan-out worktree constraint) keep their strength.
- Token bloat: the same rationale stated 3–4× (log-run timestamps, init Bash-rule, sync-spec cost asymmetry, next no-state-in-conversation); duplicated Success-Criteria/Validate checklists in the six create-* skills; Process Summary + Detailed Steps restating identical steps (plan-feature, detail-use-case, shared-vision); a dated 2026-06-11 repo snapshot as readiness's worked example; invented time metrics in quick-task; a nonexistent `--no-git` flag in init.
- Tier mismatch: `openup-retrospective` (measure read-back, pattern analysis, went-well/improve synthesis) is judgment work pinned to `model: haiku`.

## Requirements

### R1 — No stale model references in skill bodies
Remove the hardcoded `Claude Opus 4.6` co-author line from the quick-task commit template; no template skill body names a specific Claude model version.

**Scenario:** Given the template skills tree, When I grep skill bodies for `Claude Opus`/`Claude Sonnet`/`Claude Haiku` version strings, Then zero matches remain (frontmatter `model:` aliases excluded).

### R2 — plan-feature is stack-agnostic
The codebase-exploration step detects the project stack first (from manifest files) and maps stack-neutral categories (data models, request handlers, routing, schema/migrations, business logic, i18n-if-present, tests, config) onto it; the generated plan template emits `## i18n` only when the project has i18n resources; code fences carry no hardcoded language.

**Scenario:** Given a non-Rails project, When `/openup-plan-feature` runs its explore step, Then no Rails-specific path (`app/services/`, `config/routes.rb`, `db/schema.rb`, `en.yml`) is prescribed and the plan contains no unconditional `## i18n` YAML section.

### R3 — Self-Critique blocks use report-then-rank
All authoring skills carrying a Self-Critique block instruct: list every weakness found, fix or explicitly flag each, rank them, record the top one or two with resolution — replacing the "genuine weakness … the weakest point" filter-first wording.

**Scenario:** Given the 10 authoring skills with Self-Critique blocks, When I grep for `genuine` and `the weakest point` in those blocks, Then zero matches remain and each block asks for an exhaustive list before ranking.

### R4 — Emphasis proportionate to risk
`MANDATORY` caps on the plan-feature and create-task-spec ambiguity gates, explore's "silence is not an option", and start-iteration's "the skill has FAILED" framing are softened to plain imperative gate language; hard gates guarding destructive/irreversible actions (trunk guard, write-fence, two-legal-exits, fan-out worktree constraint, sync-spec refusal, complete-task BLOCKING steps) are left at full strength.

**Scenario:** Given the four flagged files, When I read the softened passages, Then each still states the gate as a requirement ("before drafting", "stop and report") without ALL-CAPS alarm framing, and every legitimate BLOCKING tag in complete-task/fan-out/next is unchanged.

### R5 — Repeated rationale stated once
Each of these is stated once and referenced elsewhere: log-run's timestamps-from-clock rule; init's Bash-not-Write rule; sync-spec's cost-asymmetry argument; next's no-state-in-conversation rule. The six create-* skills keep one canonical Success-Criteria checklist (the validate step points back to it). Process Summary sections duplicating Detailed Steps are removed in plan-feature, detail-use-case, and shared-vision. readiness's dated worked example is replaced by a small synthetic dateless one. quick-task's invented time metrics are deleted. init's `--no-git` reference is corrected.

**Scenario:** Given the edited files, When I read each named file, Then the named rule appears once in full with at most pointer-references elsewhere, and no dated repo snapshot or invented metric remains.

### R6 — retrospective re-tiered to sonnet
`openup-retrospective` frontmatter moves `model: haiku` → `model: sonnet`; the model-tiers doc's generated table is regenerated and its prose tier categories updated; `check-model-tiers.py --check` passes.

**Scenario:** Given the re-tiered skill, When I run `python3 scripts/check-model-tiers.py --check`, Then it exits 0 with retrospective listed under `sonnet`.

### R7 — Templates and live copies in sync
All edits land in `docs-eng-process/.claude-templates/` (canonical) and are mirrored to `.claude/` via `scripts/sync-templates-to-claude.sh`; `scripts/check-claude-sync.sh` passes.

**Scenario:** Given the completed edits, When I run `scripts/check-claude-sync.sh`, Then it reports no drift between templates and live copies.

## Out of Scope (follow-up candidates)

- Scripting readiness's DAG/collision computation (shell-out like `openup-doctor`) — structural change, own task.
- Splitting start-iteration / the four phase skills into mechanical (haiku) + judgment (higher-tier) halves — needs a tiering design pass.
- Re-tiering the four phase skills' `check-status`/`next-steps` activities.

## Success Measures

- **Measure:** `grep -rn "Claude Opus 4\.\|Claude Sonnet 4\.\|genuine weakness\|the weakest point" docs-eng-process/.claude-templates/skills/` match count.
  **Expectation:** drops from >10 to 0 at completion; read back at completion via the grep above (instrumentation: grep over the templates tree).
  **Window/read-back:** at `/openup-complete-task` for this lane (same session).

## Rollout

Not flagged — docs/template-only change with no runtime behavior; consuming projects pick it up on their next framework sync (`sync-from-framework.sh`), which is the existing, reversible distribution path. Backout = revert the PR.

## Operations

- [ ] R1 stale model string fixed (quick-task)
- [ ] R2 plan-feature stack-agnostic
- [ ] R3 Self-Critique blocks rewritten (10 skills)
- [ ] R4 emphasis softened (4 files)
- [ ] R5 dedup pass (log-run, init, sync-spec, next, 6× create-*, 3× process-summary, readiness example, quick-task metrics, --no-git)
- [ ] R6 retrospective re-tiered + model-tiers regenerated
- [ ] R7 sync to .claude + drift check green

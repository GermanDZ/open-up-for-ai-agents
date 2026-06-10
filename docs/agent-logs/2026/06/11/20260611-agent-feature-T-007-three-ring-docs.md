# Agent Run — T-007 Three-Ring Docs Scoping (Process v2 WS4)

- **Task**: T-007 — Three-ring docs scoping (product / changes / archive) + context-loading updates
- **Branch**: feature/T-007-three-ring-docs
- **Phase**: construction | **Iteration**: 4 | **Track**: standard
- **Started**: 2026-06-11 | **Completed**: 2026-06-11
- **Commits**:
  - `2067cfe` chore(process): start iteration 4 — T-007 three-ring docs scoping [T-007]
  - `8d0cf6d` chore(process): sync roadmap + project-status for T-007 in-progress [T-007]
  - `af5b3b4` docs(log): iteration-start run log for T-007 [T-007]
  - `04765d3` feat(docs): T-007 three-ring docs scoping — product/changes/archive [T-007]
  - (completion commit appended below on finalize)

## What happened (this run)
- Ran `/openup-start-iteration`: created branch, `.openup/state.json` (iter 4, standard track), set `team_deployed`, logged `iteration_start`, updated + synced project-status/roadmap.
- Deployed construction team (developer + tester), PM-coordinated. Developer lane ran a read-only impact-surface recon of every reference to moving `docs/` paths.

## Recon findings (blast radius)
- `docs/project-status.md` (150+ refs) and `docs/roadmap.md` (50+ refs) **do not move** — status is a generated view (WS3), roadmap stays. Most of the apparent blast radius is inert.
- Real surface: ~10 `docs/tasks/` refs + new-folder context-loading guidance in skills.
- Hooks hardcode `docs/` paths (`auto-log-commit.py` → agent-runs.jsonl; `on-plan-exit.py` → docs/plans/; `sync-status.py` → roadmap/project-status); template mirror under `docs-eng-process/.claude-templates/` duplicates all hooks.

## Decisions (deviate from WS4 sketch — confirmed with user 2026-06-11)
- `docs/agent-logs/` **stays in docs/** — durable audit trail, not Ring-3 debris. (WS4 prose to be corrected: fix-spec-first.)
- `docs/plans/` **stays as-is** — program-level (multi-task) plans seed changes but are not per-change folders; `on-plan-exit.py` keeps working unchanged.
- Scope = structure (`product/`, `changes/`, `changes/archive/`) + clear migrations (`docs/tasks/T-NNN` → `changes/[archive/]T-NNN/plan.md`) + consumer migration note; defer cosmetic prose churn.

## Outcome (completed)
- Rings created: `docs/product/`, `docs/changes/`, `docs/changes/archive/`. `docs/tasks/` migrated (T-001/T-003 → archive/, T-002 → changes/) and removed; history preserved.
- References rewired: create-task-spec skill, developer teammates, skills-guide, task-spec template, roadmap + spdd-evaluation links; three-ring context-loading guidance added to `CLAUDE.md`.
- `docs-eng-process/migration-three-ring-docs.md` shipped; templates re-synced (`check-claude-sync` 58/58).
- Archive-on-complete mechanized in `openup-complete-task` §7 (was under-scoped in plan.md; added per charter — see design.md D6); dogfooded by archiving `docs/changes/T-007/` → `docs/changes/archive/T-007/`.
- Deliberately unchanged: `docs/agent-logs/`, `docs/plans/`, `docs/roadmap.md`, `docs/project-status.md` (keeps T-006 hooks + WS3 logging intact).

## Verification
- No dangling `docs/tasks/` refs in functional paths; moved links resolve; `check-claude-sync` parity holds.
- T-007 marked `completed` via `sync-status.py` (single-source), all required gates green.

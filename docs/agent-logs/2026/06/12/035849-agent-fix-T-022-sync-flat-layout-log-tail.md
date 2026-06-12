# Agent Run — T-022 (iteration 14)

- **Task**: T-022 — Fix template→.claude sync + on-stop log-tail auto-commit
- **Phase**: construction
- **Track**: standard
- **Branch**: fix/T-022-sync-flat-layout-log-tail
- **Started**: 2026-06-12
- **Completed**: 2026-06-12
- **Commit**: f0015bda5d8880498a34e68fb0386dc875f828e1
- **Key files**: scripts/sync-templates-to-claude.sh, docs-eng-process/.claude-templates/scripts/hooks/{on-stop,check-unfinished-tasks,gate-edits}.py, docs/changes/T-022/plan.md, docs/roadmap.md, docs/project-status.md
- **Decisions**:
  - (D1) Flat skill layout is the only correct target; within-repo sync now mirrors sync-from-framework.sh full coverage (skills/rubrics/hooks/config/agents)
  - (D2) Hook drift reconciled live→template; on-stop auto-commits only the lone-jsonl case (agent-runs.jsonl); non-log dirt still blocks commit
  - (D3) sync-check bypassed for this commit due to unrelated unmerged T-019 content in shared .claude
- **Verification**: Sync script tested against flat layout; on-stop hook verified to auto-commit JSONL-only runs; hook drift corrections applied to templates

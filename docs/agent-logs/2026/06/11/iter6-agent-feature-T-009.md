# Agent Run — T-009 (iteration 6)

- **Task**: T-009 — Worktree-per-task + lease claims + collision pre-flight
- **Phase**: construction
- **Branch**: feature/T-009-worktree-claims
- **Started**: 2026-06-11
- **Completed**: 2026-06-11
- **Commits**:
  - 3651d42 docs(T-009): start iteration 6 — worktree/claims spec + test strategy
  - 202879a docs(T-009): reconcile spec to resolved decisions
  - 688144d docs(T-009): sync roadmap + project-status to in-progress
  - bfe9518 feat(parallel): worktree-per-task + lease claims + collision pre-flight
- **Key files**: scripts/openup-claims.py, scripts/tests/test_openup_claims.py, docs-eng-process/parallel-work.md, .claude/skills/openup-workflow/{start-iteration,complete-task}/SKILL.md (mirrored to templates), docs/changes/T-009/{plan,design,test-notes}.md
- **Decisions** (design.md D1–D8): claims never expire (D1); manual rm only, no --steal (D2); atomic temp+rename (D3); claims dir auto-create (D4); live claim files authoritative (D5); worktree default-on (D6); claim carries its own touches (D7); corrupt claim fail-closed (D8). Q2 empty-touches=no-collide foot-gun; Q4 deps checked before collision.
- **Tests**: 17 new hermetic unit tests; full suite 59 green. Real-worktree E2E verified (two disjoint sessions isolated; overlapping third refused naming owner).
- **Verification**: unit + E2E. Real-worktree integration tier (TC-WT-*/PAR-*) verified manually via E2E rather than committed scripts.

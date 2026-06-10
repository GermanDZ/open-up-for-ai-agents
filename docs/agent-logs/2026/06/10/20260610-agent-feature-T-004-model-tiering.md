# Agent Run Log — T-004: Model Tiering (Process v2 Wave 1)

**Branch**: feature/T-004-model-tiering
**Task**: T-004 (docs/plans/2026-06-10-process-v2-claude-code-harness.md, WS1)
**Phase**: construction — Iteration 1
**Agent**: claude-fable-5 (orchestrator) + general-purpose developer, Explore/haiku tester, haiku scribes
**Start**: 2026-06-10T12:00:00Z (approx, iteration start)
**End**: 2026-06-10T12:13:38Z
**Commits**: 7f0c7df feat(skills): model tiering frontmatter, scribe/explorer agents, tier map [T-004] (+ docs completion commit, SHA recorded in JSONL)

## What changed
- `model:` frontmatter added to all 29 SKILL.md (11 haiku, 18 inherit) — live `.claude/` and canonical `docs-eng-process/.claude-templates/`
- New subagents: openup-scribe (haiku, mechanical writes), openup-explorer (haiku, read-only context)
- 8 team configs: per-role model assignments (PM=haiku, specialists=inherit)
- New decision doc: docs-eng-process/model-tiers.md
- scripts/check-claude-sync.sh extended to cover teams/ and agents/ (48 → 58 files)
- Inline `Agent(model="haiku")` prose in 4 skills replaced with openup-scribe delegation

## Decisions
- Templates in docs-eng-process/.claude-templates/ are CANONICAL; .claude/ is the gitignored deployed copy (user-confirmed)
- Tier philosophy: deterministic/mechanical → haiku; judgment-bearing → inherit
- assess-completeness kept at haiku per plan (rubric grading is per-criterion mechanical)

## Surprises / gotchas
- `--fix-from-live` regressed shipped team preambles (live side was stale) — caught in PM diff review, rebuilt from template base
- perl in-place edits double-encoded UTF-8 in team files (mojibake) — reversed; byte-safe pattern used in fix
- Sync script previously ignored teams/ and agents/ entirely — silent drift surface, now closed

## Verification
Tester (haiku, read-only): 9/9 acceptance checks PASS — frontmatter coverage, tier map match, agent files, sync at 58, no inline-Haiku leftovers, teams diff clean, no mojibake, tree clean, model-tiers.md covers 29 skills.

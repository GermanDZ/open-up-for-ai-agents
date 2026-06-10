# Agent Run Log — T-008 (Iteration 5)

- **Task**: T-008 — Coordination frontmatter + `/openup-readiness` DAG (Process v2 WS5a + WS5b)
- **Branch**: `feature/T-008-coordination-frontmatter-readiness`
- **Phase**: construction · **Iteration**: 5 · **Track**: standard
- **Date**: 2026-06-11
- **Team**: project-manager (orchestrator) → developer → tester

## Commits

| SHA | Message |
|---|---|
| `68d47f2` | feat(skills): coordination frontmatter + /openup-readiness DAG [T-008] |

## Files changed

- `.claude/skills/openup-workflow/readiness/SKILL.md` (gitignored live copy) + committed mirror `docs-eng-process/.claude-templates/skills/openup-readiness/SKILL.md`
- `docs-eng-process/coordination-frontmatter.md` (new — schema doc)
- `docs-eng-process/model-tiers.md` (added `openup-readiness | haiku | Coordination`)
- `docs/changes/T-008/{plan.md,design.md,test-notes.md}` (new)
- `docs/changes/T-002/plan.md` (frontmatter migrated)
- `docs/changes/README.md` (cross-link)
- `docs/roadmap.md`, `docs/project-status.md` (status sync)

## Decisions

- Hyphenated frontmatter keys (`depends-on`, `claimed-by`, `claimed-at`) over the program-plan's underscore sketch, to match existing change files.
- `/openup-readiness` is read-only and stateless; live `.git/openup/claims/` lease reading deferred to T-009.
- Collision matching uses path-segment-prefix (not substring); collision set = READY ∪ IN-PROGRESS (deferred/archived excluded).
- Tasks without a change folder reported under a non-authoritative "Roadmap-only" section.

## Verification

Tester independently re-derived the DAG by hand against live change folders + roadmap and matched the developer's report with **zero divergence**. Acceptance check (READY/BLOCKED with dependency reasons) PASS. Template sync verified (59 files). One cosmetic example-table value fixed by the PM post-review.

## Residual / follow-ups

- Roadmap uses `completed`/`planned`; change frontmatter uses the `done|verified` enum — reader tolerates both, latent mismatch to watch when T-009/T-010 gain folders.
- `iterations_since_retro` increment + retro trigger is T-011 (not mechanized yet).

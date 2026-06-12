# Agent Run Log — T-018: `docs/project-config.yaml` context/rules injection

**Branch**: claude/zealous-mendel-vrpflr
**Task**: T-018 (docs/plans/2026-06-12-clarity-self-briefing-continue-loop.md, item D — the surviving 2026-05-13 plan item #2)
**Phase**: construction — Iteration 16
**Agent**: claude-opus-4-8[1m] (solo, sequential — analyst→developer→tester hats; no team)
**Track**: standard
**Start**: 2026-06-12 (iteration start)

## What changed
- **New** `docs-eng-process/templates/project-config.example.yaml` — starter config:
  a `context:` block scalar + a `rules:` map keyed by the seven artifact types.
- **New** `docs-eng-process/project-config.md` — single source of the mechanism:
  file location, schema, artifact-type key convention, the
  `<project-context>`/`<project-rules>` injection wrappers, precedence
  (`framework rubric → project rules → task-spec safeguards`), and the consuming-skill list.
- **Modified** the seven artifact create skills (`openup-create-{vision,use-case,
  architecture-notebook,iteration-plan,task-spec,test-plan,risk-list}/SKILL.md`):
  each gained a uniform "Load Project Config" step at the top of `## Process` that
  reads `docs/project-config.yaml`, injects `context:` + its own `rules.<type>` block,
  treats rules as additive, and is absence-safe (skip when the file is missing).
- **Modified** `openup-init/SKILL.md` — emits a starter `docs/project-config.yaml`
  from the example as part of project setup.
- **Modified** `.claude-templates/CLAUDE.md` — Quality section documents the precedence
  and points at `docs-eng-process/project-config.md`.
- **Status**: roadmap T-018 → completed; the Clarity/Self-Briefing/Continue-Loop plan
  marked `completed` (T-015…T-021 all delivered) in the roadmap block + the plan file.

## Decisions
- Single-sourced the mechanism in one doc; skills carry a compact pointer step naming
  only their own artifact-type key (DD1) — avoids nine-way duplication.
- Step inserted unnumbered before `### 1.` ("do this first") rather than renumbering
  every existing step across seven files (DD2).
- `rules:` keyed by the `/openup-create-<type>` suffix (DD3); injection limited to the
  seven *spec* artifacts, not workflow outputs (`create-pr/handoff/documentation`) (DD4).
- Additive precedence, zero rubric edits, no YAML schema — all explicit no-go zones
  from the source plan (DD5). Framework repo ships no live config of its own (DD6).

## Verification
- Example parses as YAML; `rules` keys ⊆ the seven artifact types. ✅
- All seven artifact skills + `openup-init` reference `docs/project-config.yaml`; each
  skill's step names its own `<TYPE>` key. ✅
- Mechanism doc + CLAUDE.md carry the precedence string and both injection wrappers. ✅
- Presence/absence fixture: a temporary `docs/project-config.yaml` with
  `rules.use-case` is the block the use-case step injects; deleting it leaves no tracked
  residue (clean revert). ✅
- `scripts/openup-spec-scenarios.py check docs/changes/T-018/plan.md` → exit 0 (6/6). ✅
- `scripts/check-claude-sync.sh` → exit 0 (no live `.claude/` in this container; only
  `.claude-templates/` is tracked, per the standing convention).

## Surprises / gotchas
- `.claude/` is gitignored/absent in this container, so the live↔templates sync check is
  a no-op here — the templates are the tracked source of truth (same as T-016/T-022).
- The CLAUDE.md precedence string wraps across a line break, so a single-line `grep`
  shows 0; the phrase is present (verified by inspecting the two lines).

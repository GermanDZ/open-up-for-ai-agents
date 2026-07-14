# Traceability Log — T-115

**Task:** T-115  
**Branch:** feat/T-115-archetype-default-accessor  
**Phase:** construction  
**Duration:** 2026-07-14T14:58:49Z → 2026-07-14T15:03:00Z (4m 11s)

## Commits

- 1281fc4e38bd004450bc71d241272c4ec8bc0079
- c803bcc57586acd48d75acf124ddce07f54d95a5
- a90be27c1fe22011cebb6f45f2f46ce429c1b72f

## Files Changed

- `scripts/check-docs.py` — modified: new `--show-archetype-defaults` flag
- `scripts/tests/test_check_docs.py` — modified: new `ArchetypeDefaultsCLITests` class (3 tests)
- `docs-eng-process/project-config.md` — modified: disambiguation sentence
- `docs-eng-process/tracks.md` — modified: disambiguation sentence
- `docs-eng-process/procedures/openup-init.md` — modified: points at new flag
- `docs-eng-process/.claude-templates/skills/openup-init/SKILL.md` — generated mirror
- `docs-eng-process/script-cli-reference.md` — modified: new flag documented
- `docs/changes/T-115/plan.md` — new: spec
- `docs/changes/T-115/design.md` — new: requirement grading

## Decisions

### 1. Accessor location
Chose `check-docs.py` as the accessor's home (where `PROCESS_ARCHETYPE_DEFAULTS` already lives and `resolve_process()` already consumes it) over `openup-doctor.py` or a new `openup-process-map.py` flag. Rationale: avoids duplicating the dict across files. Flagged as vetoable in the spec since the exploration left this genuinely open.

### 2. Reference discipline
The new flag references `PROCESS_ARCHETYPE_DEFAULTS` directly rather than a copy, so a test asserts byte-for-byte equality against the real module dict. Guarantees it can never silently drift from what `resolve_process()` actually uses.

### 3. Behavioral scope
Deliberately did not change what happens when `process:` is absent (confirmed by research: no archetype tailoring applies today). This task only makes that fact queryable and documented, not different.

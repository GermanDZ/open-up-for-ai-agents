# T-076 — Design & Verification

## Key decisions

- **Stdlib-only parser, not PyYAML.** Consuming projects run `scripts/*.py` with
  stdlib only (PyYAML is `convert.py`-only). The shared `parse_frontmatter` is
  flat; the `process:` section is nested (process → phases → phase → inline flow
  map). So a focused nested parser (`parse_process_section` + `_process_*`
  helpers) lives in `check-docs.py`, handling both inline flow maps
  `name: { k: v, k: [a,b] }` and block maps.
- **Archetype defaults as data.** `PROCESS_ARCHETYPE_DEFAULTS` (quick/mvp/product)
  + `resolve_process()` overlay explicit keys onto the archetype default set.
  Exposed so T-077's plan-iteration and tests share one source of truth.
- **R4 corrected mid-flight (fix-spec-first).** The original R4 said doctor
  "still exits 0" on a malformed section — but `openup-doctor`'s aggregate
  already runs `check-docs.py`, which hard-fails on a bad section (R3), so doctor
  *does* exit 1 on that input. R4 was rewritten: doctor's dedicated
  `process-config` check is read-only INFO/WARNING (never ERROR) — the
  human-readable pointer at check-docs.py; the aggregate is the actual escalation
  path. Mirrors `check_section_status_drift`.
- **No manifest/CLI-ref change.** The work extends two already-shipped CLIs
  (`check-docs.py`, `openup-doctor.py`); no new script, so `process-manifest.txt`
  and `script-cli-reference.md` are untouched by design.

## Verification against spec (complete-task step 1a)

Graded against the actual diff (`git diff harness-optional...HEAD`) + green tests.

- **✅ R1 — process: section + archetype defaults + docs.**
  `PROCESS_ARCHETYPE_DEFAULTS` + `resolve_process` in `check-docs.py`; example
  updated (`project-config.example.yaml`); archetype default table in
  `project-config.md`. *Then* (override wins, unmentioned phase keeps default):
  green — `ResolveDefaults.test_override_wins_over_archetype_default`,
  `test_unmentioned_phase_keeps_archetype_default`.
- **✅ R2 — quick degenerates to quick-task ceremony.**
  quick default set = Inception 1/empty, Elaboration `skip`, Construction 1
  no-parallel, `milestone_review: auto-assess`. *Then*: green —
  `QuickDegeneration.test_quick_defaults`.
- **✅ R3 — check-docs.py structural validation, blocking; absent passes.**
  `validate_process_config` wired into `check()`; findings are hard (`is_hard`
  treats non-`coverage-gap` as hard). *Then* (unknown archetype exits non-zero;
  absent exits 0): green — `CheckDocsGate.*` (7 cases, incl. safeguard-waiving
  key). Real-repo `check-docs.py --docs docs` exits 0 (no project-config.yaml →
  no-op).
- **✅ R4 — doctor read-only process-config signal (never ERROR).**
  `check_process_config` reuses the check-docs validator. *Then* (invalid →
  WARNING referencing check-docs.py; valid/absent → INFO): green —
  `DoctorProcessConfig.*` (4 cases).
- **✅ R5 — Development Case mapping + precedence documented; init starter.**
  `project-config.md` gains a "Development Case — the `process:` section" section
  (shape, archetype default table, validation, precedence extension);
  `openup-init.md` appends a commented `process:` starter (re-rendered to
  `.claude/skills/openup-init/SKILL.md`); example carries the commented block.

All requirements ✅. Full suite: 422 tests OK. Fence clean (`--base
harness-optional`, 10 files in-lane). `check-claude-sync` + `render-skills-mirror
--check` green.

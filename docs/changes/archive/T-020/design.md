# T-020 — Design Decisions & Verification

## Decisions

- **Standalone validator, not a board subcommand.** `scripts/openup-spec-scenarios.py`
  is a stdlib-only peer of `openup-board.py`/`openup-claims.py`. It imports
  `openup-claims.py` only for `parse_frontmatter`, so "track" is parsed by one shared
  implementation. Keeping it separate avoids conflating queue derivation (board) with
  spec-structure validation (this).
- **Scenario recognition = three bold markers.** A requirement's block must contain
  `**Given**`, `**When**`, and `**Then**` (case-insensitive). The bold form never appears
  in ordinary requirement prose, giving zero false positives, and is trivially deterministic.
- **Requirement = top-level `N.` line; block = until the next `N.`.** Sub-bullets and
  multi-line scenarios under a requirement count toward it; a scenario cannot leak across a
  requirement boundary (covered by `test_scenario_does_not_leak_across_requirement_boundary`).
- **Track exemption.** `quick` is exempt; `standard`/`full` enforced; default `standard`
  when no track is present (matches the board's "often None until iteration start" note).
- **Exit codes** mirror the toolchain idiom: 0 ok / 1 gap (named on stderr) / 2 usage.

## Implementation-vs-Spec Verification (per `/openup-complete-task` step 1a)

Graded against the staged diff for this change.

- ✅ **R1** template scenario convention — `docs-eng-process/templates/task-spec.md`
  `## Requirements` now states the ≥1 Given/When/Then rule and shows the example marker line.
- ✅ **R2** validator exit 0/1/2 — `scripts/openup-spec-scenarios.py`; demonstrated: T-020/T-021
  specs exit 0, archived T-019 (no scenarios) exits 1 naming all 6 requirements, missing
  file/section exit 2 (tests `test_missing_file_is_usage_error`, `test_no_requirements_section_is_usage_error`).
- ✅ **R3** quick-exempt / standard-default — `resolve_track`; tests
  `test_quick_track_frontmatter_is_skipped`, `test_quick_track_override_is_skipped`,
  `test_default_track_is_enforced_when_no_frontmatter_track`.
- ✅ **R4** rubric criterion 11 + "11 criteria" — `task-spec-rubric.md` §11 Scenario Coverage;
  create-task-spec Success Criteria + Step 5 read "eleven"/"11".
- ✅ **R5** create-task-spec authors+grades, assess runs validator — Round 1 analyst bullet,
  Requirements authoring paragraph, Step 5 grading; assess-completeness "Deterministic
  pre-check for task-spec".
- ✅ **R6** hermetic tests — `scripts/tests/test_openup_spec_scenarios.py`, 11 cases, green
  under `unittest discover -s scripts/tests`.
- ✅ **R7** parity — `scripts/check-claude-sync.sh` exits 0 (61 files).

**Result:** all 7 requirements ✅ against the diff. No ❌. Cleared to complete.

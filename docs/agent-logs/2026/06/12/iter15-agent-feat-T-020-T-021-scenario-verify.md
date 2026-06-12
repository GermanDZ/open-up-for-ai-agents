# Agent Run — Iteration 15 (T-020 + T-021)

- **Branch**: `claude/determined-archimedes-nvjsqh`
- **Phase**: construction
- **Track**: standard (solo, no team)
- **Tasks**: T-020 (scenario-per-requirement + deterministic validation), T-021 (implementation-vs-spec verify step)
- **Date**: 2026-06-12

## What shipped

**T-020 — scenario-per-requirement + deterministic validation**
- `scripts/openup-spec-scenarios.py` (new) — stdlib-only validator; `check <plan>` exits
  0/1/2; imports `openup-claims.py` for shared `parse_frontmatter`/track; `quick`-exempt,
  `standard`/`full` enforced, default `standard`.
- `scripts/tests/test_openup_spec_scenarios.py` (new) — 11 hermetic tests (pass, fail+naming,
  quick-skip via frontmatter and `--track`, full enforce, default enforce, multi-line scenario,
  boundary non-leak, no-Requirements usage error, empty-Requirements gap, missing-file usage).
- `docs-eng-process/templates/task-spec.md` — `## Requirements` now mandates ≥1 Given/When/Then
  scenario with bold markers + example line.
- `task-spec-rubric.md` — criterion 11 (Scenario Coverage); `create-task-spec` "10 criteria" → "11".
- `openup-create-task-spec/SKILL.md` — analyst authors scenarios (Round 1 + Requirements
  paragraph); Step 5 grading runs the validator.
- `openup-assess-completeness/SKILL.md` — task-spec artifact detection + deterministic
  pre-check wiring with track awareness.

**T-021 — implementation-vs-spec verify step**
- `openup-complete-task/SKILL.md` — new BLOCKING `### 1a. Verify Implementation Against Spec`
  (grade each requirement ✅/❌ against `git diff`; grade scenarios when present; any ❌ blocks
  completion and routes to finish-work or fix-spec-first; grade persisted to `design.md`) +
  blocking Success-Criteria item.

## Verification

- `python3 -m unittest scripts.tests.test_openup_spec_scenarios` → 11/11 green.
- Board/claims/state + scenario suites (58 tests) green; the 8 `test_t006_hooks` failures are
  pre-existing/environmental (sandbox git-commit behavior + temp `agent-runs.jsonl`), unrelated.
- `openup-spec-scenarios.py check` → exit 0 on T-020 and T-021 specs (dog-food); exit 1 on the
  scenario-less archived T-019 (negative control).
- `scripts/check-claude-sync.sh` → exit 0 (61 files).
- Step 1a verify grade recorded in each change folder's `design.md` (all requirements ✅).

## Decisions

- Validator is a standalone `scripts/` peer of the board, not a board subcommand — keeps queue
  derivation and spec-structure validation separate.
- Scenario recognition = three bold markers in a requirement's block → zero prose false positives.
- T-021 is skill-only and degrades gracefully without T-020 (scenarios graded only if present);
  no new `openup-state.py` gate.

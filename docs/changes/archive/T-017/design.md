# T-017 — In-flight design decisions

## Decisions

- **DD1 — board.py lives at repo-root `scripts/`, not `.claude/scripts/`.** The plan's
  literal path (`.claude/scripts/openup-board.py`) is inconsistent with every peer:
  `openup-claims.py` / `openup-state.py` are at repo-root `scripts/`, git-tracked, invoked
  as `python3 scripts/openup-…py`. board.py imports `openup-claims.py` from its own
  directory (`Path(__file__).parent`), so co-location is required, not just tidy. (Spec
  Assumption #1, vetoable.)
- **DD2 — agreement-by-construction via import, not duplication.** board.py loads
  `openup-claims.py` through `importlib` (hyphenated filename) and reuses
  `parse_frontmatter`, `dep_satisfied`, `touches_overlap`, `live_claims`, `claims_dir`,
  `repo_root`, `_norm`. A lane the board calls `ready` is therefore one
  `openup-claims.py preflight` also clears — they cannot drift because they are one
  implementation.
- **DD3 — `hat` from an optional `(role)` checkbox prefix, default `developer`.** The
  script never infers a role semantically (that would break determinism). Spec authors tag
  a step `- [ ] (tester) …` only at a hat handoff. Resolves Open Question #5: the lease +
  checkbox state are enough to resume; no extra within-cycle role field added to
  `state.json`.
- **DD4 — board is derived + gitignored, refreshed only in-skill.** `.openup/board.json`
  lives under the already-gitignored `/.openup/`; the script regenerates it on every
  `refresh`/`top`. No Stop/PostToolUse hook (Open Questions #1 + #2 → local-only,
  skill-only). Payload carries no timestamps → byte-identical output for identical inputs.
- **DD5 — `top` exit codes.** `0` = a pickable lane printed; `3` = clean no-op (reason on
  stderr, e.g. "no pickable lane (1 in-progress)"); `2` = usage. `/openup-next` treats `3`
  as a successful stop, not a failure.
- **DD6 — ticking an Operations checkbox is sanctioned progress state.** The one direct
  edit to a persisted `plan.md` that does not require re-running `/openup-create-task-spec`
  — recorded in `CLAUDE.openup.md`. Everything else still follows fix-spec-first.

## Rubric grade (`.claude/rubrics/task-spec-rubric.md`)

1. ✅ Front-matter Completeness · 2. ✅ Story INVEST-fit · 3. ✅ Requirements Testability ·
4. ✅ Entities Accuracy · 5. ✅ Approach Clarity · 6. ✅ Structure Scope-fit ·
7. ✅ Operations Testability · 8. ✅ Norms / Safeguards Inheritance · 9. ✅ Ambiguity
Resolution (6 vetoable Assumptions resolve the 5 plan Open Questions + the script-path
inconsistency; no blocking questions).

**Result:** `satisfied` (all ✅).

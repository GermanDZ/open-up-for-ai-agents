# T-021 — Design Decisions & Verification

## Decisions

- **Skill-only change, no new machine gate.** The verify step is a discipline inside
  `/openup-complete-task`, not a new `openup-state.py` gate. Adding a `spec_verified` gate was
  considered and rejected as out of scope (the existing gate set is unchanged).
- **Position `### 1a.`, before "Commit Remaining Changes".** Verification gates the commit, so
  it must precede it; the `1a`/`7a`/`7b` sub-step convention avoids renumbering the skill.
- **Grade against the diff, not intentions.** The step requires pointing at the line of
  `git diff <trunk>...HEAD` (or a green test) that makes each requirement true — a requirement
  that reads ✅ "because that was the plan" is explicitly called out as not verified.
- **Graceful degradation w.r.t. T-020.** Scenarios sharpen the grade (run each **Then** where
  mechanically checkable) but are optional; a scenario-less requirement is graded on its text.
- **Persist to `design.md`.** Honours the no-conversation-only-state rule — the grade is part
  of the traceability trail.

## Implementation-vs-Spec Verification (per `/openup-complete-task` step 1a — dog-fooded)

Graded against the staged diff for this change.

- ✅ **R1** BLOCKING verify step grading each requirement against the diff, before commit —
  `openup-complete-task/SKILL.md` `### 1a. Verify Implementation Against Spec — BLOCKING`,
  positioned between `### 1.` and `### 2. Commit Remaining Changes`.
- ✅ **R2** any ❌ blocks completion — step point 4: "Any ❌ blocks completion. Do not commit,
  do not update the roadmap, do not archive."
- ✅ **R3** grades scenarios when present, degrades gracefully — step point 3 (grade each
  scenario's **Then**) + Analysis-Context assumption (text-only when no scenario).
- ✅ **R4** grade recorded in `design.md` — step point 5; this very file is the instance.
- ✅ **R5** Success Criteria list the blocking verify first — new first bullet:
  "**BLOCKING**: Every spec requirement is graded ✅ against the actual diff (step 1a)…".

**Result:** all 5 requirements ✅ against the diff. No ❌. Cleared to complete.

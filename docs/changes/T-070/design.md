# T-070 — Design & Verification Notes

## In-flight decisions

- **Kept `TASK_TAG_RE` as an always-accepted alternative** rather than replacing
  it with the lane id. A commit legitimately referencing a related numeric task
  id (e.g. a follow-up touching `[T-042]`) must still pass. The new acceptance is
  the union: literal `[{task_id}]` OR any `[T-NNN]`.
- **Matched the lane id literally via `re.escape`** (case-insensitive), so a
  slug like `quick-remove-approve-plan` — or any future id scheme — is accepted
  without assuming a shape. This is what makes the hook's own printed remedy
  (`Append [{task_id}]`) truthful.
- **In-place branch, not a worktree.** The spec was authored untracked on `main`;
  an in-place `git checkout -b` carries the untracked file onto the branch,
  avoiding the known "spec stranded on main" worktree footgun.
- **Rejected Option B** (mint numeric quick-task ids): heavier, and it wouldn't
  fix a hand-run `openup-state.py init` with a descriptive id.

## Step 1a — Requirement verification (against `git diff main...HEAD` + working tree)

- ✅ **R1** (non-numeric id + literal tag accepted) — `has_tag` includes
  `lane_tag_re.search(subject)` where `lane_tag_re` is the escaped `[{task_id}]`.
  Green: `test_accepts_literal_non_numeric_task_id`.
- ✅ **R2** (any `[T-NNN]` accepted as alternative) — `TASK_TAG_RE.search` retained
  as the first disjunct of `has_tag`. Green: `test_accepts_with_tag_when_state_has_task_id`,
  `test_accepts_numeric_tag_alternative_when_id_non_numeric`.
- ✅ **R3** (no tag still rejected; error names id) — the `if task_id and not
  has_tag:` branch is otherwise unchanged (exit 2, message interpolates
  `{task_id}`). Green: `test_rejects_non_numeric_id_without_tag` asserts
  `quick-remove-approve-plan` in stderr + returncode 2.
- ✅ **R4** (`[openup-skip]` + no-state paths unchanged) — those branches were not
  touched. Green: `test_openup_skip_bypasses`, `test_optional_tag_without_state`.
- ✅ **R5** (live↔template byte-identical) — `diff .claude/scripts/hooks/validate-commit.py
  docs-eng-process/.claude-templates/scripts/hooks/validate-commit.py` → no output
  (BYTE-IDENTICAL) after `sync-templates-to-claude.sh`. (Live copy is gitignored/derived
  per T-056; the template is the tracked canonical source.)

**Result: all requirements ✅ — completion unblocked.**

## Step 1b — Success-measure instrumentation

- ✅ Instrumentation exists in the diff: `test_accepts_literal_non_numeric_task_id`
  in `scripts/tests/test_t006_hooks.py` is the standing check that a non-numeric
  active id commits with its literal tag; `.claude/memory/bypass-log.md` remains
  the counter for numeric-tag-contradiction bypasses (expected: zero going forward).
- **Read-back:** the next `/openup-quick-task` that sets a non-numeric id
  (self-verifying — the test pins the behavior; no future bypass entry should cite
  the numeric-tag contradiction).

## Test results

- `python3 -m unittest scripts.tests.test_t006_hooks` → **43/43 OK**
  (ValidateCommitTests **8/8**, incl. 3 new T-070 cases).
- End-to-end on the live hook: non-numeric active id → no-tag commit blocks (exit 2,
  prints `Append [quick-foo-bar]`); the printed `[quick-foo-bar]` tag → exit 0.

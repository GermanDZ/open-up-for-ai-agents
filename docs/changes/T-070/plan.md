---
id: T-070
title: validate-commit accepts the active task_id as the required tag
status: ready   # proposed → ready → in-progress → done → verified
priority: high   # critical | high | medium | low
estimate: 0.5 session   # rough size
plan: docs/explorations/2026-07-10-validate-commit-numeric-tag-gap.md   # originating exploration
depends-on: []
blocks: []
touches:
  - .claude/scripts/hooks/validate-commit.py
  - docs-eng-process/.claude-templates/scripts/hooks/validate-commit.py
  - scripts/tests/test_t006_hooks.py
last-synced: ""
---

# T-070 — validate-commit accepts the active task_id as the required tag

## Story

> **As an** agent or human committing inside an active OpenUP iteration
> **I want** the mandatory-tag check to accept the exact `[{task_id}]` tag its own error message tells me to append
> **So that** any active lane — numeric `T-NNN` or a descriptive quick-task id — is committable without an `[openup-skip]` bypass.

INVEST check:
✅ Independent · ✅ Negotiable · ✅ Valuable · ✅ Estimable · ✅ Small · ✅ Testable

## Analysis Context

State the *why* the spec needs but the code can't show:
- **Domain.** The `validate-commit.py` PreToolUse hook (fires on every `git commit`). Its mandatory-tag branch requires a task tag on the subject when `.openup/state.json` has a `task_id`.
- **The defect.** `TASK_TAG_RE = r"\[T-\d+\]"` only matches numeric tags, but the failure message (line 191–192) instructs `Append [{task_id}]` using the *actual* active id. When that id is non-numeric (e.g. `quick-remove-approve-plan`, which `/openup-quick-task` mints), the suggested remedy can never satisfy the check — the hook contradicts itself. Observed live this session; forced two audited `[openup-skip]` bypasses on a trivial cleanup.
- **Scope boundaries.** Only the mandatory-tag matching logic changes. No change to: the format check (`PATTERN`), the `[openup-skip]` bypass path, the `Co-Authored-By` short-circuit, message extraction, or the no-state (tag-optional) path. Quick-task's id-generation is **not** changed here (Option B was rejected — it doesn't fix hand-run `state.py init`).
- **Definition of done.** For any active `task_id`, a subject ending `[{task_id}]` passes; a subject with any `[T-NNN]` passes; a subject with no tag still fails (exit 2); `[openup-skip]` still bypasses. Live hook and its template stay byte-identical.

> **Assumption:** a numeric `[T-NNN]` tag remains accepted as an alternative even when the active id differs, so a commit that legitimately references a related task id is not rejected. *(Vetoable at review.)*

## Requirements

1. When state has a non-numeric `task_id`, a well-formed subject carrying the literal `[{task_id}]` tag is accepted.
   - **Given** `.openup/state.json` has `task_id: quick-foo` **When** committing `docs: x [quick-foo]` **Then** the hook exits 0.
2. When state has a `task_id`, a well-formed subject carrying any `[T-NNN]` tag is accepted (numeric alternative preserved).
   - **Given** `task_id: T-006` **When** committing `feat: add thing [T-006]` **Then** the hook exits 0.
3. When state has a `task_id` (numeric or not), a subject with no task tag is still rejected, and the error names the active id.
   - **Given** `task_id: quick-foo` **When** committing `docs: x` (no tag) **Then** the hook exits 2 and stderr contains `quick-foo`.
4. The `[openup-skip]` bypass and the no-state tag-optional path are unchanged.
   - **Given** `task_id: T-006` **When** committing `wip stuff [openup-skip]` **Then** the hook exits 0 and appends to `.claude/memory/bypass-log.md`.
   - **Given** no state file **When** committing `feat: add thing` (no tag) **Then** the hook exits 0.
5. The live hook and its template are byte-identical after the change.
   - **Given** the edit is applied **When** running `diff .claude/scripts/hooks/validate-commit.py docs-eng-process/.claude-templates/scripts/hooks/validate-commit.py` **Then** it reports no differences.

## Behavior Delta

This changes the behavior of an internal process hook, not a Ring-1 product use case (`docs/product/` holds no artifact for the commit-validation hook — it is framework tooling).

**Added** — n/a

**Modified** — mandatory-tag acceptance in `validate-commit.py`: the required tag was a hardcoded `[T-NNN]`; it becomes "the active lane's `[{task_id}]`, OR any `[T-NNN]`". No Ring-1 product artifact documents this hook, so there is no `docs/product/` section to cite or back-propagate to.

**Removed** — n/a

## Entities

- **`validate-commit.py`** (modified) — `.claude/scripts/hooks/validate-commit.py` (live) + `docs-eng-process/.claude-templates/scripts/hooks/validate-commit.py` (template, canonical).
- **`TASK_TAG_RE` / mandatory-tag branch** (modified) — the matching logic at lines ~63 and ~185–197.
- **`ValidateCommitTests`** (modified) — `scripts/tests/test_t006_hooks.py` (the T-006 hook suite already covers this hook).

## Approach

Keep `TASK_TAG_RE` (the generic `[T-NNN]` shape) as an always-accepted alternative. In the mandatory-tag branch, after fetching the active `task_id`, build a per-lane matcher for the literal `[{task_id}]` (via `re.escape`, case-insensitive) and accept the subject when it matches **either** the literal id tag **or** `TASK_TAG_RE`. Only the else (neither present) raises exit 2. The error message already interpolates `{task_id}`, so it becomes truthful with no wording change. Apply the identical edit to the template and re-sync so the pair stays byte-identical.

## Structure

**Add:**
- (none — extend existing tests in place)

**Modify:**
- `docs-eng-process/.claude-templates/scripts/hooks/validate-commit.py` — canonical source: add the literal-id acceptance in the mandatory-tag branch.
- `.claude/scripts/hooks/validate-commit.py` — synced copy (regenerate via `scripts/sync-templates-to-claude.sh`, do not hand-edit divergently).
- `scripts/tests/test_t006_hooks.py` — add non-numeric-id cases to `ValidateCommitTests`.

**Do not touch:**
- `PATTERN` / the conventional-format check — the format contract is unchanged.
- `openup-quick-task/SKILL.md` id generation — Option B (mint numeric ids) was considered and rejected; out of scope.
- `check-iteration.py` — references `T-XXX` only in guidance text, not as an enforced numeric check; no change needed.

## Operations

- [x] Edit the template hook `docs-eng-process/.claude-templates/scripts/hooks/validate-commit.py`: in the mandatory-tag branch, accept the subject when it contains the literal `[{task_id}]` (regex-escaped, case-insensitive) OR matches `TASK_TAG_RE`; only raise exit 2 when neither is present.
- [x] Run `scripts/sync-templates-to-claude.sh` so the live `.claude/` hook matches the template byte-for-byte.
- [x] (tester) Extend `ValidateCommitTests` in `scripts/tests/test_t006_hooks.py`: non-numeric id + `[{id}]` passes; non-numeric id + no tag fails (stderr names the id); numeric id + `[T-NNN]` still passes; `[openup-skip]` still bypasses.
- [x] Run the T-006 hook suite (`python3 -m unittest scripts.tests.test_t006_hooks`) — all green (43/43; ValidateCommit 8/8).
- [x] Verify the falsifiable measure end-to-end: with a non-numeric active `task_id`, the exact tag the hook prints in its error makes a real `git commit` pass.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.)
- `docs-eng-process/model-tiers.md` — model tiering
- The live↔template sync contract: `scripts/sync-templates-to-claude.sh` + `scripts/tests/check-claude-sync.sh` (both hook copies must stay identical).

## Safeguards

- **Token / size budget.** Net change is a few lines in the hook + a handful of test methods; no new files.
- **Reversibility.** Pure logic addition inside one branch; revert is the single hook edit + test removal.
- **No-go zones.** Must not weaken the gate: a subject with **no** tag must still be rejected when an iteration is active; `[openup-skip]` remains the only bypass; the conventional-format check is untouched.
- **Live↔template parity.** `check-claude-sync.sh` must stay green — never hand-edit only one copy.

## Success Measures

We expect the **rate of `[openup-skip]` bypasses attributable to the numeric-tag contradiction** to drop to **zero** within **the first quick-task run after release**. Instrumentation: `.claude/memory/bypass-log.md` (bypass entries) + the T-006 test asserting a non-numeric-id commit passes with its literal tag. Read-back: next `/openup-quick-task` that sets a non-numeric id (self-verifying — the test is the standing check).

## Rollout

**Flagged?** No — this is an internal process hook whose behavior is read at commit time from the repo's own state; there is no user-facing surface and a flag would add no safety (the change is strictly more permissive on a previously-uncommittable case, and the tests pin the no-tag rejection). Kill-switch, if ever needed, is reverting the one hook edit. Not user-facing: `n/a — internal tooling`.

## Verification

- `python3 -m pytest scripts/tests/test_t006_hooks.py` (or the project runner) — all `ValidateCommitTests` green, including the new non-numeric-id cases.
- `diff .claude/scripts/hooks/validate-commit.py docs-eng-process/.claude-templates/scripts/hooks/validate-commit.py` reports no difference; `scripts/tests/check-claude-sync.sh` exits 0.
- Manual: init state with a non-numeric `task_id`, attempt a commit with no tag (blocked, error names the id), then append the printed `[{task_id}]` tag (commit passes).
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅ or a clear gap call-out.

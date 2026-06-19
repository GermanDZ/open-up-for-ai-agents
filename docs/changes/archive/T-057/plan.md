---
id: T-057
title: "Solo UX Friction — Free Exploration, Gate-at-Commit, Auto-Merge"
status: done
priority: high
estimate: 1 session
plan: docs/explorations/2026-06-19-t057-solo-ux-friction.md
depends-on: []
blocks: []
last-synced: ""
touches:
  - .claude/scripts/hooks/on-task-request.py
  - docs-eng-process/.claude-templates/scripts/hooks/on-task-request.py
  - .claude/scripts/hooks/gate-edits.py
  - docs-eng-process/.claude-templates/scripts/hooks/gate-edits.py
  - .claude/skills/openup-complete-task/SKILL.md
  - docs-eng-process/.claude-templates/skills/openup-complete-task/SKILL.md
  - .claude/CLAUDE.openup.md
  - docs-eng-process/.claude-templates/CLAUDE.md
  - scripts/tests/test_t006_hooks.py
  - scripts/tests/test_t010_tracks.py
---

# T-057 — Solo UX Friction — Free Exploration, Gate-at-Commit, Auto-Merge

## Story

> **As a** solo OpenUP practitioner working in a local single-user setup
> **I want** to explore freely without process gates blocking my prompt, have planning
> artifacts writable without a prior iteration, and completed task branches merged to local
> `main` automatically
> **So that** I can iterate without stranded branches causing rebase conflicts and without
> the process itself blocking pre-delivery investigation

INVEST check:
✅ Independent · ✅ Negotiable · ✅ Valuable · ✅ Estimable · ✅ Small · ✅ Testable

## Analysis Context

- **Domain.** OpenUP process hooks (`UserPromptSubmit`, `PreToolUse`) and the
  `openup-complete-task` skill. Changes are to the enforcement posture and
  completion ceremony — not to any application logic.
- **Scope boundaries.** Does not change `check-iteration.py` (already correctly
  advisory at commit), the pre-push write-fence (correctly blocking), or anything
  related to worktree-per-task overhead for multi-user setups.
- **Definition of done.** `on-task-request.py` never exits 2; `gate-edits.py`
  passes writes to `docs/iteration-plans/` and `docs/roadmap.md`; a completed
  task's PR is auto-merged and local `main` pulled; `check-claude-sync.sh` exits 0.

**Assumption:** `gh pr merge --merge` (merge commit, not squash). This preserves atomic
commits on trunk per the project's commit-promotion policy. *(Vetoable at review.)*

**Assumption:** Auto-merge is default-on. A `auto_merge: false` argument disables it.
*(Vetoable at review — solo users almost always want this; a team review gate will
naturally block `gh pr merge` if branch protection is set.)*

**Assumption:** The `on-task-request.py` active-iteration branch (the `else:` path that
fires when an iteration IS in progress) also becomes exit 0. It currently blocks the user
from sending a follow-up message even during a valid iteration, which is unnecessary.
*(Vetoable at review.)*

## Requirements

1. `on-task-request.py` exits 0 on every code path — the `UserPromptSubmit` hook
   never blocks the user's prompt.
   - **Given** no active iteration is present **When** a user sends any prompt
     **Then** `on-task-request.py` exits 0 (the message is processed) and its
     informational stderr message is still emitted

2. `on-task-request.py` continues to emit its informational stderr message (track
   suggestion and iteration reminder) on all paths where it previously did so.
   - **Given** a user sends a prompt that matches task-start language with no
     active iteration **When** `on-task-request.py` runs **Then** its stderr
     output includes the track suggestion and iteration reminder text (exit 0)

3. `gate-edits.py` allows writes to `docs/iteration-plans/` without an active
   iteration.
   - **Given** no active iteration exists **When** a Write/Edit tool targets a
     file under `docs/iteration-plans/` **Then** `gate-edits.py` exits 0 (the
     write is allowed)

4. `gate-edits.py` allows writes to `docs/roadmap.md` without an active iteration.
   - **Given** no active iteration exists **When** a Write/Edit tool targets
     `docs/roadmap.md` **Then** `gate-edits.py` exits 0 (the write is allowed)

5. `/openup-complete-task` auto-merges the PR and pulls to local `main` after the
   PR is created (default behavior).
   - **Given** `/openup-complete-task` has just created a PR **When** `auto_merge`
     is not set to `false` **Then** `gh pr merge --merge --delete-branch` is
     run, followed by `git pull origin main` (from the main repo), and local
     `main` reflects the merged commit

6. Auto-merge is skippable with `auto_merge: false`.
   - **Given** `/openup-complete-task` is invoked with `auto_merge: false`
     **When** the PR-creation step completes **Then** no merge is attempted and
     the PR URL is shown for manual action

7. If auto-merge fails (e.g. branch protection requires review), the user is
   informed with the PR URL and manual merge steps rather than the skill erroring out.
   - **Given** `gh pr merge` exits non-zero **When** `/openup-complete-task` runs
     the merge step **Then** the skill logs the failure and the PR URL, instructs
     the user to merge manually, and continues to the next step (lease release)
     without aborting

8. Both `.claude/` hook and skill files and their
   `docs-eng-process/.claude-templates/` counterparts are updated (parity).
   - **Given** all four files are changed **When** `check-claude-sync.sh` is run
     **Then** it exits 0 (no sync drift between live and template copies)

## Behavior Delta

**Added** — behavior that did not exist before:
- `/openup-complete-task` Step 9: auto-merge PR + pull local main after PR creation
- `gate-edits.py` exemption for `docs/iteration-plans/` and `docs/roadmap.md`

**Modified** — behavior that changes; no Ring-1 product/use-case artifacts exist
for process hooks in this project (`docs/product/` is empty). Source files are the
authoritative behavior reference:
- `on-task-request.py` exit behavior: exit 2 (block) → exit 0 (inform) on both
  the no-active-iteration and the active-iteration paths —
  `.claude/scripts/hooks/on-task-request.py` (lines 179–202 per exploration)
- `CLAUDE.openup.md` Critical Rules: adds a hook-behavior note clarifying that
  `on-task-request.py` is advisory and enforcement gates at commit —
  `.claude/CLAUDE.openup.md §Critical Rules`

**Removed:** none.

## Entities

- **on-task-request.py** (modified) — `.claude/scripts/hooks/on-task-request.py`
  and `docs-eng-process/.claude-templates/scripts/hooks/on-task-request.py`
- **gate-edits.py** (modified) — `.claude/scripts/hooks/gate-edits.py`
  and `docs-eng-process/.claude-templates/scripts/hooks/gate-edits.py`
- **openup-complete-task SKILL.md** (modified) — `.claude/skills/openup-complete-task/SKILL.md`
  and `docs-eng-process/.claude-templates/skills/openup-complete-task/SKILL.md`
- **CLAUDE.openup.md** (modified) — `.claude/CLAUDE.openup.md` (process instructions)
- **check-claude-sync.sh** (read-only) — used as a parity verification tool

## Approach

Four surgical changes targeting hook exit codes, gate exemptions, and skill ceremony — no new
abstractions or cross-cutting infrastructure. The safety invariant is preserved: enforcement
moves entirely to `check-iteration.py` at `git commit` (already exit 0 / advisory), which
is the correct gate placement for a tool-use workflow. The auto-merge step is fail-open: a
branch-protection block surfaces a clear message rather than crashing the skill. Parity between
`.claude/` and `docs-eng-process/.claude-templates/` is maintained and verified by
`check-claude-sync.sh` as the final step.

## Structure

**Modify:**
- `.claude/scripts/hooks/on-task-request.py` — both `sys.exit(2)` → `sys.exit(0)`
- `docs-eng-process/.claude-templates/scripts/hooks/on-task-request.py` — same
- `.claude/scripts/hooks/gate-edits.py` — add `"docs/iteration-plans/"` to EXEMPT_PREFIXES;
  add `"docs/roadmap.md"` to EXEMPT_PREFIXES (exact-match already supported by `is_exempt`)
- `docs-eng-process/.claude-templates/scripts/hooks/gate-edits.py` — same
- `.claude/skills/openup-complete-task/SKILL.md` — add Step 9 after existing Step 8 (PR creation)
- `docs-eng-process/.claude-templates/skills/openup-complete-task/SKILL.md` — same
- `.claude/CLAUDE.openup.md` — add hook-behavior note to Critical Rules

**Do not touch:**
- `.claude/scripts/hooks/check-iteration.py` — already correctly advisory (exit 0 at commit); in scope only as a reader
- `.githooks/pre-push` — write-fence is correctly blocking; out of scope
- `scripts/openup-fence.py` — same

## Operations

- [x] Fix `on-task-request.py`: change both `sys.exit(2)` → `sys.exit(0)` in
  `.claude/scripts/hooks/on-task-request.py` and its template copy; confirm stderr
  messages are still emitted; run `python3 -m pytest tests/ -k on_task_request -v`
  and assert all paths exit 0
- [x] Fix `gate-edits.py`: add `"docs/iteration-plans/"` and `"docs/roadmap.md"` to
  EXEMPT_PREFIXES in `.claude/scripts/hooks/gate-edits.py` and its template copy;
  run `python3 -m pytest tests/ -k gate_edits -v` and assert newly-exempt paths pass
- [x] Add Step 9 to `.claude/skills/openup-complete-task/SKILL.md` and its template
  copy: `gh pr merge --merge --delete-branch` + `git pull origin main` (from main
  repo context, which is where the skill runs after step 7b removed the worktree);
  include fail-open branch (log PR URL + manual instructions on non-zero exit);
  include `auto_merge: false` skip condition
- [x] Update `.claude/CLAUDE.openup.md` Critical Rules: add hook-behavior note
  ("Hooks gate at commit, not at prompt. `on-task-request.py` is advisory…")
- [x] (tester) Run `bash check-claude-sync.sh` and assert exit 0; run full test suite
  `python3 -m pytest tests/ -v` and assert no regressions

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.)

## Safeguards

- **Reversibility.** Revert means restoring the two `sys.exit(2)` calls in
  `on-task-request.py` and removing gate-edits.py's two new EXEMPT_PREFIXES entries
  and the complete-task Step 9. No database or persistent state is altered.
- **Step 9 execution context.** Step 8 (PR push + create) precedes Step 9. The
  developer must verify whether the skill executor is still inside the task worktree
  at that point or already in the main repo (step 7b removed the worktree). Use
  `gh pr merge` with an explicit `--repo` flag or from any directory (gh is
  repo-agnostic); use `git pull origin main` only after confirming we are on the main
  branch. If uncertain, defer the pull to a post-merge note to the user.
- **No-go zones.** `check-iteration.py` exit code must remain 0 (already correct). The
  pre-push write-fence must not be touched. No changes to any script in `scripts/` (CLIs).
- **Parity invariant.** Every change to a `.claude/` hook/skill must land identically in
  its `docs-eng-process/.claude-templates/` counterpart; `check-claude-sync.sh` exit 0
  is a hard gate before completion.

## Success Measures

This is internal process tooling — no user-facing metric moves.
`n/a — observed behavior in next downstream session (bienestarsinfin.com) after merge:
no stranded-branch rebase conflicts, no gate blocks during exploration.
Read-back: first downstream session post-merge.`

## Rollout

Not user-facing. These are changes to Claude Code hook scripts and skill files in a
framework repository — they take effect the next time a downstream project syncs via
`sync-from-framework.sh` and the next time any session starts in this repo.
`n/a — no flag needed; no in-flight user state; revert is a two-line patch.`

## Verification

- `python3 -m pytest tests/ -k on_task_request -v` → all paths exit 0, stderr messages present
- `python3 -m pytest tests/ -k gate_edits -v` → `docs/iteration-plans/x.md` and `docs/roadmap.md` are exempt
- `bash check-claude-sync.sh` exits 0
- Full suite `python3 -m pytest tests/ -v` shows no regressions vs baseline

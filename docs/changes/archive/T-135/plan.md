---
id: T-135
title: "Sharpen on-task-request.py's classifier, then block at prompt time"
status: done
priority: medium
estimate: 1 session
plan: docs/iteration-plans/t-135-sharpen-task-request-classifier-and-block.md
depends-on: []
blocks: []
last-synced: ""
touches:
  - docs-eng-process/.claude-templates/scripts/hooks/on-task-request.py
  - scripts/tests/test_on_task_request_hook.py
  - scripts/tests/test_t010_tracks.py
  - docs/iteration-plans/t-135-sharpen-task-request-classifier-and-block.md
---

# T-135 — Sharpen on-task-request.py's classifier, then block at prompt time

## Story

> **As a** user or agent submitting a prompt in this project
> **I want** the task-request hook to distinguish a genuine delivery
>   directive from a question or discussion, and to actually block when it
>   detects the former with no active iteration
> **So that** "explore freely, gate at commit" stops depending entirely on
>   the model choosing to comply — without the gate itself rejecting
>   legitimate questions

INVEST check:
✅ Independent — one hook file + its new test file; no dependency on other
pending work.
✅ Negotiable — the exact word-count thresholds (`_LEAD_WORDS`,
`_BARE_ID_MAX_WORDS`) are explicitly open (Open Questions), not fixed.
✅ Valuable — closes a real gap this session's own process-introspection
surfaced, using a working precedent (`check-unfinished-tasks.py`'s
`sys.exit(2)`) already in this repo.
✅ Estimable — one hook file, ~30 lines of change, confirmed by reading the
whole file this session; 1 session.
✅ Small — no new subsystem; additive regex refinements + one exit-code
change.
✅ Testable — real transcript quotes from this session are ready-made
fixtures for both true- and false-positive cases.

## Analysis Context

- **Domain.** `docs-eng-process/.claude-templates/scripts/hooks/on-task-request.py`,
  a `UserPromptSubmit` hook. Sibling to `check-unfinished-tasks.py` (same
  hook event, already blocks via `sys.exit(2)`).
- **Scope boundaries.** Does not touch `check-unfinished-tasks.py` (used
  only as precedent). Does not improve classifier **recall** — only
  precision (fewer false positives), so that blocking is safe. Does not
  change the active-iteration reminder branch's advisory behavior. Does not
  attempt to verify Stop-hook re-prompt routing (out of scope, named as an
  open question).
- **Definition of done.** The classifier excludes questions and requires
  imperative-mood positioning; the no-active-iteration branch blocks via
  `sys.exit(2)`; a regression suite built from this session's real
  transcript passes.

> **Assumption:** `_LEAD_WORDS = 8` and `_BARE_ID_MAX_WORDS = 8` are the
> thresholds — chosen to comfortably cover genuine imperative openers while
> excluding longer discussion. *(Vetoable at review.)*
> **Assumption:** the "sharpen, then block" owner directive is one task,
> sequenced internally (Requirements 1-3 sharpen, Requirement 4 blocks) —
> not two separately delivered tasks. *(Vetoable at review.)*
> **Assumption:** the residual risk of a Stop-hook re-prompt reaching
> `UserPromptSubmit` and being misclassified is low and **not** addressed
> here — only background task-**notifications** were confirmed (via
> `claude-code-guide`) to route through a separate `Notification` event
> this session; Stop-hook re-prompt routing specifically was not checked.
> *(Flagged for the next person who touches this hook, not silently
> ignored.)*

## Requirements

1. A prompt ending in `?` (after stripping trailing whitespace) is never
   classified as a task request, regardless of task-id or task-language
   content.
   - **Given** the prompt `"What do you need for T-107?"`, **When** the
     classifier runs, **Then** it returns not-a-request (the hook exits 0
     with no message).
   - **Given** the prompt `"implement T-107"` (no trailing `?`), **When**
     the classifier runs, **Then** it still returns is-a-request (unchanged
     from today).

2. `TASK_LANG_RE` is checked only against the leading 8 words of the
   prompt, not the whole message.
   - **Given** a message whose first 8 words contain no task-language verb
     but a later sentence does (e.g. a long message that mentions "let's
     build" only in its final clause), **When** the classifier runs,
     **Then** it does not classify as a request on that basis alone (it may
     still classify via the bare-task-id path if applicable).
   - **Given** `"Let's implement T-107 now"` (task-language verb in the
     first 4 words), **When** the classifier runs, **Then** it classifies
     as a request (unchanged from today).

3. A bare task-id mention (no task-language verb in the leading 8 words)
   only classifies as a request when the full prompt is 8 words or fewer.
   - **Given** the prompt `"T-107"` (1 word), **When** the classifier runs,
     **Then** it classifies as a request.
   - **Given** a multi-sentence analytical message that mentions "T-107"
     once in passing (this session's actual transcript has several such
     messages), **When** the classifier runs, **Then** it does not
     classify as a request on the bare-id path.

4. The no-active-iteration branch exits 2 (blocks the prompt, feeding its
   existing instructional message back as the reason); the active-iteration
   reminder branch is unchanged (still exits 0).
   - **Given** a classified task request with `docs/project-status.md`
     Status not `in-progress`, **When** the hook runs, **Then** it exits 2
     and the same instructional message text is printed to stderr.
   - **Given** a classified task request with Status `in-progress`, **When**
     the hook runs, **Then** it still exits 0 with the reminder message.

5. A regression suite built from this session's real transcript quotes
   passes: every verified false positive stays unclassified; every verified
   genuine directive stays classified; the one accepted recall gap
   (`"Try nano and run the batch"`) is documented as unchanged, not treated
   as a bug.
   - **Given** the fixture list in the plan's Testing Strategy, **When**
     `python3 -m unittest scripts.tests.test_on_task_request_hook` runs,
     **Then** every fixture's expected classification holds.

## Behavior Delta

`n/a — all Added`. No Ring-1 (`docs/product/`) use-case describes this
hook's classifier behavior — it is process tooling, not product behavior.
Every change is additive (new exclusion, position-bounding, one exit-code
change on one branch), verified not to regress the sibling hook or the
active-iteration branch.

**Added:**
- Question-exclusion (`_QUESTION_RE`)
- Leading-words position bound for `TASK_LANG_RE`
- Short-message requirement for bare task-id classification
- Blocking (`sys.exit(2)`) on the no-active-iteration branch

## Success Measures

We expect zero reports of a legitimate question or discussion prompt being
rejected by this gate in the sessions following this change — the exact
failure mode this task exists to prevent. Instrumentation: the hook's
`[on-task-request]`-prefixed stderr message is distinctive and would appear
immediately in any blocked-prompt report; a false-positive block is
self-evidently disruptive, so no additional logging is needed to notice one.
Read-back: the next time the owner reports (or doesn't report) a
false-positive block — owner-initiated, no fixed date, the same
conditional-trigger convention this repo already uses for spike/hardening
work (e.g. T-080's "the owner's next live batch").

## Rollout

**Flagged?** No. This is a process hook read by the harness on every
prompt — there is no per-environment deployment or user-facing surface to
stage; a flag would add ceremony without adding safety (the change is
already scoped narrowly and tested against real transcript fixtures before
merge, which is the actual safety mechanism here). Reversibility: reverting
the diff restores today's advisory-only behavior exactly.

## Entities

- **`TASK_ID_RE` / `TASK_LANG_RE`** (read-only, unchanged) —
  `docs-eng-process/.claude-templates/scripts/hooks/on-task-request.py:32-48`
- **`_QUESTION_RE`** (new) — question-exclusion pattern
- **`_leading_words()`** (new) — position-bounding helper
- **The no-active-iteration branch's `sys.exit(0)`** (modified) —
  `on-task-request.py:159` → `sys.exit(2)`
- **The active-iteration branch's `sys.exit(0)`** (read-only, confirmed
  unchanged) — `on-task-request.py:176`
- **`check-unfinished-tasks.py`** (read-only, precedent only) —
  `docs-eng-process/.claude-templates/scripts/hooks/check-unfinished-tasks.py:213`

## Approach

Add three narrowly-scoped precision filters ahead of the existing
`TASK_ID_RE`/`TASK_LANG_RE` checks (question exclusion, leading-words
bounding, short-message requirement for bare ids), then flip exactly one
`sys.exit(0)` to `sys.exit(2)` on the branch that actually has a missing
precondition to fix (no active iteration) — mirroring the sibling hook's
already-working blocking convention rather than inventing a new one.

## Structure

**Add:**
- `scripts/tests/test_on_task_request_hook.py`

**Modify:**
- `docs-eng-process/.claude-templates/scripts/hooks/on-task-request.py`

**Do not touch:**
- `.claude/scripts/hooks/on-task-request.py` — the live mirror, regenerated
  by `sync-templates-to-claude.sh` from the template path above; hand-editing
  it would be silently clobbered on the next sync
- `docs-eng-process/.claude-templates/scripts/hooks/check-unfinished-tasks.py`
  — read as precedent only, not modified
- The active-iteration reminder branch's exit code — tempting to also
  "harden" it for consistency, but it has no missing precondition to block
  on; leave it advisory

## Operations

- [x] Add `_QUESTION_RE` and the question-exclusion check to
      `on-task-request.py`; confirm `"What do you need for T-107?"` no
      longer matches
- [x] Add `_leading_words()` and bound `TASK_LANG_RE`'s check to it; add
      `_BARE_ID_MAX_WORDS` and the short-message requirement for bare
      task-id classification
- [x] Flip the no-active-iteration branch's `sys.exit(0)` to `sys.exit(2)`;
      leave the active-iteration branch's `sys.exit(0)` untouched
- [x] Write `scripts/tests/test_on_task_request_hook.py` using the
      `test_t006_hooks.py` subprocess-driven convention, with every fixture
      from the plan's Testing Strategy (real transcript quotes)
- [x] Run `bash scripts/sync-templates-to-claude.sh` and confirm
      `.claude/scripts/hooks/on-task-request.py` picks up the change
      (gitignored — not committed, but must match for this session's own
      live hook to reflect the fix)
- [x] (tester) Run the new test file plus the full existing suite; confirm
      no regression anywhere (739/739 green; one pre-existing intermittent
      flake in test_openup_agent_cycle unrelated to this change, confirmed
      by re-running clean twice)

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format,
  etc.)
- `scripts/tests/test_t006_hooks.py` — the repo's own hook-testing
  convention (subprocess + JSON stdin payload + exit-code/stderr assertions)

## Safeguards

Invariants and limits that must hold:
- **No change to the active-iteration branch's blocking behavior.** Only
  the no-active-iteration branch gains `sys.exit(2)`.
- **No change to `check-unfinished-tasks.py`.** Read as precedent, not
  modified.
- **Reversibility.** A straight revert of the diff restores today's
  advisory-only behavior with no migration to undo.
- **Fixture-grounded, not theoretical.** Every false-positive/true-positive
  test case is a real quote from this session's transcript, not an invented
  example — the actual bar for "does this still work" is empirical.

## Verification

- `python3 -m unittest scripts.tests.test_on_task_request_hook -v` — all
  green
- Manual: `echo '{"hook_event_name":"UserPromptSubmit","prompt":"What do you
  need for T-107?","cwd":"<repo>"}' | python3
  docs-eng-process/.claude-templates/scripts/hooks/on-task-request.py;
  echo $?` → exits 0, no stderr
- Manual: same with `"prompt":"implement T-107"` and a fixture
  `project-status.md` with `Status: pending` → exits 2, stderr message shown
- Full existing test suite green (no regression)
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅
  or a clear gap call-out

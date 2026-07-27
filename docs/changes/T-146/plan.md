---
id: T-146
title: "Quick-task's hardcoded --iteration 0 must not clobber project-status.md's real Iteration header"
status: ready
priority: medium
estimate: 1 session
plan: ""
depends-on: []
blocks: []
last-synced: ""
touches:
  - scripts/sync-status.py
  - scripts/tests/test_sync_status_notes.py
  - docs-eng-process/state-file.md
  - docs/roadmap.md
---

# T-146 — Quick-task's hardcoded `--iteration 0` can clobber `project-status.md`'s real header on sync

## Story

> **As a** reader of `docs/project-status.md` (the file every role's *On Start,
>   Read* block names first)
> **I want** the project-wide `**Iteration**` header to keep describing the
>   project's real iteration counter
> **So that** a quick lane — which has no iteration number at all — cannot
>   silently rewrite it to `0`

INVEST check:
✅ Independent — one guard in one function; no dependency on T-145 (a different
field of the same script) or T-141.
✅ Negotiable — *which* falsy-iteration values are treated as "no real
iteration" is a design choice; the spec fixes only that the field is skipped
rather than zeroed.
✅ Valuable — prevents the shared status header from reporting a lane-local
sentinel as the project's iteration; observed downstream rewriting
`**Iteration**: 64` to `0`.
✅ Estimable — `update_project_status()` is 11 lines and was read in full.
✅ Small — one conditional.
✅ Testable — a `--iteration 0` state and a `--iteration N` state are both
constructible against the existing hermetic sync harness.

## Analysis Context

- **Domain.** `sync-status.py`'s `update_project_status()` — the sole writer of
  `docs/project-status.md`'s header fields.
- **Scope boundaries.** Fixes the `Iteration` field only. The `Status` field has
  the same root cause but needs a real design decision (see the carried open
  question below) and is deliberately **not** changed here. Does not touch
  `/openup-quick-task`'s `--iteration 0` call — `0` is a legitimate sentinel for
  "this lane has no iteration number", and the bug is that the consumer writes a
  sentinel into a shared field, not that the sentinel exists.
- **Definition of done.** A sync run driven by a state whose `iteration` is `0`
  or absent leaves the `**Iteration**` line byte-unchanged, while still writing
  every other header field.

**Confirmed this session, before writing code**: `update_project_status()`
(`scripts/sync-status.py:305-315`) calls
`set_field(text, "Iteration", str(state.get("iteration", "")))` unconditionally,
and `set_field` substitutes whenever the `**Iteration**:` line exists — so a
state carrying `0` writes the literal `**Iteration**: 0`. `/openup-quick-task`
step 2 initializes exactly that (`--iteration 0`), and the schema types
`iteration` as a plain integer with no "unset" representation. This repo's
`/openup-quick-task` steps set the gates directly rather than running
`sync-status.py`, so the bug is **latent here** and triggered downstream; the
guard makes it unreachable either way.

> **Assumption:** "no real iteration" is tested as plain falsiness
> (`0`, absent, `None`, `""`), not as an equality check against `0`. A state
> hand-written without the key, or migrated from an older schema, should behave
> the same as the quick-track sentinel — and no valid iteration number is falsy
> (the counter starts at 1). *(Vetoable at review.)*

## Requirements

1. `update_project_status()` skips the `Iteration` field when the active lane's
   `iteration` is falsy.
   - **Given** a `project-status.md` whose header reads `**Iteration**: 94` and
     an active quick-track state initialized with `--iteration 0`, **When**
     `sync-status.py` runs, **Then** the header still reads `**Iteration**: 94`
     — it is neither zeroed nor blanked.
   - **Given** the same document and a state with no `iteration` key at all,
     **When** `sync-status.py` runs, **Then** the header is likewise unchanged.

2. A lane that *does* carry a real iteration number still writes it — the guard
   is narrow, not a removal of the field.
   - **Given** a `project-status.md` header reading `**Iteration**: 94` and a
     standard-track state initialized with `--iteration 96`, **When**
     `sync-status.py` runs, **Then** the header reads `**Iteration**: 96`.

3. Every other header field is still written on a falsy-iteration lane — the
   guard must not turn into "quick lanes don't sync".
   - **Given** a falsy-iteration state for task `T-200` on the `quick` track,
     **When** `sync-status.py` runs, **Then** `**Current Task**` reads `T-200`,
     `**Phase**`, `**Status**`, `**Last Updated**` and `**Updated By**` are all
     regenerated as usual, and the roadmap Status cell is still stamped.

4. The unresolved `Status`-field question is **carried**, not silently dropped:
   recorded at the guard site in the code, in the change folder's `design.md`,
   and as its own roadmap entry so it survives the archive.
   - **Given** a maintainer reading `update_project_status()` after this change,
     **When** they reach the `Iteration` guard, **Then** an adjacent comment
     states that `Status` has the same root cause, is deliberately unfixed, and
     names the roadmap entry tracking it.

## Behavior Delta

**Modified:**
- `docs/project-status.md`'s `**Iteration**` header — no longer written when the
  active lane has no real iteration number. The governing artifact is
  `docs-eng-process/state-file.md` (the `iteration` field's meaning), updated
  here to state that `0` is the quick-track "no iteration" sentinel and that
  consumers must not write it into shared views. No Ring-1 `docs/product/`
  use case describes the status header.

**Added:** none. **Removed:** none.

## Success Measures

We expect **zero occurrences of `**Iteration**: 0` in `docs/project-status.md`**
across all future syncs — a grep that currently would match after any
`sync-status.py` run made while a quick lane's state is live. Instrumentation:
`git log -S'**Iteration**: 0' -- docs/project-status.md` (an exact, checkable
query over the file's own history). Read-back: the next
`/openup-retrospective`.

## Rollout

**Flagged?** No. A one-line guard in a deterministic, locally-run generator with
no deployed surface; a flag would cost more than the change. Reversible by
revert with no migration — the guard only affects what a *future* sync writes.

## Entities

- **`update_project_status()`** (modified) — `scripts/sync-status.py:305-315`
- **`set_field()`** (read-only, unchanged) — `scripts/sync-status.py:296-302`
- **`iteration`** (read-only, schema unchanged) — `scripts/openup-state.schema.json`

## Approach

Wrap the single `set_field(..., "Iteration", ...)` call in a falsiness check on
`state.get("iteration")`, so a lane with no real iteration number leaves the
shared header alone instead of writing its sentinel into it. Falsiness (rather
than `== 0`) covers the quick-track sentinel, an absent key, and `None`
identically, and no valid iteration number is falsy. The `Status` field shares
the root cause — the header currently means both "status of the last completed
iteration" and "status of the active lane" — but resolving that needs the header
split into two fields or a decision to leave `Status` untouched on `quick`;
that is a design question, carried to its own roadmap entry rather than guessed
at inside this fix.

## Structure

**Add:**
- Tests in `scripts/tests/test_sync_status_notes.py` covering falsy-iteration,
  real-iteration, and "every other field still written"
- A roadmap entry carrying the `Status`-field open question

**Modify:**
- `scripts/sync-status.py` — the `Iteration` line in `update_project_status()`,
  plus a comment naming the carried question
- `docs-eng-process/state-file.md` — document `0` as the quick-track sentinel

**Do not touch:**
- The `Status` field — carried question, not this fix
- `/openup-quick-task`'s `--iteration 0` — the sentinel is fine; writing it into
  a shared view is not
- `scripts/openup-state.schema.json` — `iteration` stays a plain integer; adding
  a nullable "unset" representation would be a schema migration for no gain,
  since falsiness already distinguishes the two cases

## Operations

- [ ] Guard the `Iteration` `set_field` call in `update_project_status()`
      (`scripts/sync-status.py`) on `state.get("iteration")` being truthy
- [ ] Add the comment at the guard site naming the carried `Status` question and
      its roadmap entry
- [ ] Document the `0` sentinel in `docs-eng-process/state-file.md`
- [ ] Add the roadmap entry carrying the `Status`-header open question (reserve
      the id via `openup-claims.py reserve-id`)
- [ ] (tester) Tests: falsy iteration leaves the header untouched; absent key
      likewise; a real iteration number still writes; every other header field
      is still regenerated on a falsy-iteration lane
- [ ] Run the full test suite

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, pre-commit housekeeping
- `scripts/sync-status.py`'s own design rules (deterministic, stdlib-only,
  idempotent, `--state-dir` override for tests)

## Safeguards

Invariants and limits that must hold:
- **Never blank the field.** Skipping means *not writing*; the existing value
  must survive byte-identical. Writing `**Iteration**: ` (empty) would be a
  worse version of the same bug.
- **No other header field changes behavior** in this task — in particular
  `Status` stays exactly as it is, with its problem documented rather than
  half-fixed.
- **Idempotence preserved.** Re-running with unchanged state must still produce
  no further changes.
- **Reversibility.** Revert restores the unconditional write; no state or
  document migration either way.

## Verification

- `python3 -m unittest scripts.tests.test_sync_status_notes
  scripts.tests.test_t006_hooks -v` — green (the latter asserts the header on a
  real-iteration lane, so it is the regression guard for requirement 2)
- Full suite green
- `python3 scripts/check-docs.py` and `python3 scripts/openup-fence.py check`
  exit 0
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅ or a
  clear gap call-out

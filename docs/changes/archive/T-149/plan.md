---
id: T-149
title: "Split project-status.md's Status header — Status keeps the iteration's status, Lane Status carries the active lane's"
status: done
priority: medium
estimate: 1 session
plan: ""
depends-on: []
blocks: []
last-synced: ""
touches:
  - scripts/sync-status.py
  - scripts/tests/test_t149_status_split.py
  - scripts/tests/test_on_task_request_hook.py
  - scripts/tests/test_sync_status_notes.py
  - docs-eng-process/templates/project-status.md
  - docs-eng-process/.claude-templates/scripts/hooks/on-task-request.py
  - docs-eng-process/.claude-templates/skills/openup-retrospective/SKILL.md
  - docs-eng-process/state-file.md
  - docs-eng-process/QUICKSTART.md
  - docs-eng-process/procedures/openup-retrospective.md
  - docs/roadmap.md
---

# T-149 — `project-status.md`'s `Status` header conflates last-completed-iteration with active-lane status

## Story

> **As a** reader of `docs/project-status.md` — human, `/openup-retrospective`,
>   and the `on-task-request` hook alike
> **I want** each header field to answer exactly one question
> **So that** a live lane can no longer rewrite the recorded status of a
>   *completed* iteration, and the two consumers that read the field in
>   opposite senses both keep working.

INVEST check:
✅ Independent — T-146 (its prerequisite half) is merged and archived ·
✅ Negotiable — the (a)/(b) tie-break was explicitly delegated to this lane ·
✅ Valuable — removes the last known clobber in the project-wide derived view ·
✅ Estimable — one script function, one hook read, three doc surfaces ·
✅ Small — single role, ~40 lines of behavior change ·
✅ Testable — every requirement is a header string a test can assert on.

## Analysis Context

- **Domain.** The derived shared view `docs/project-status.md` and its single
  writer `scripts/sync-status.py::update_project_status()`; plus its two
  programmatic readers, which disagree about what `**Status**` means.
- **The conflation, precisely.** `update_project_status()` writes `**Status**`
  from `derive_status(state)` — the *active lane's* status — unconditionally.
  Two consumers read it in opposite senses:
  - `on-task-request.py` (`.claude/scripts/hooks/`) treats `Status ==
    "in-progress"` as *"a lane is active"* — **lane** semantics; it is what
    decides between blocking a task-request (`sys.exit(2)`) and the advisory
    reminder branch.
  - `/openup-retrospective` steps 1–2 read the header for *"iteration goal,
    dates, overall status"* — **iteration** semantics, describing the iteration
    named by the adjacent `**Iteration**` field.
  T-146 guarded `**Iteration**` against the quick track's `--iteration 0`
  sentinel but left `**Status**` unguarded, so the pair can now split: this
  repo's header can read `Iteration: 104` (a completed iteration) beside
  `Status: in-progress` (an unrelated live quick lane).
- **Decision — (a) split the field, not (b) skip-on-quick.** Recorded here
  because the roadmap entry delegates the tie-break to this lane.
  (b) would make the header self-consistent by skipping `**Status**` on the same
  falsy-iteration condition as `**Iteration**`, but it destroys the hook's only
  signal that a lane is live: during a quick lane the hook would read a stale
  `completed` and block a legitimate task-request. (a) keeps both consumers
  answerable: `**Status**` is pinned to the iteration named beside it (written
  under the *same* guard as `**Iteration**`, so the pair always moves together),
  and a new `**Lane Status**` carries the active lane's derived status
  unconditionally. (b)'s cheapness is real but it trades a visible bug for an
  invisible one.
- **Which field keeps the name.** `**Status**` retains **iteration** semantics.
  At rest, every existing `project-status.md` already reads that way
  (`Iteration: 104` / `Status: completed`), so no downstream file's current
  value becomes a lie on upgrade; `**Lane Status**` is purely additive.
- **Scope boundaries.** Not covered: `**Current Task**` (lane-scoped in the same
  way, but naming the live lane is its whole job — no clobber to fix);
  `/openup-quick-task`'s `--iteration 0` sentinel (T-146 DD3 stands); rewriting
  the hook to read `.openup/state.json` instead of a derived doc (a bigger,
  separate question); the `merge=union` question (T-155).
- **Definition of done.** A `sync-status.py` run under a live quick lane leaves
  `**Status**` byte-identical, writes `**Lane Status**`, and the hook's
  block/advisory decision is unchanged from today for both migrated and
  un-migrated documents.

> **Assumption:** `**Lane Status**` is inserted immediately **after**
> `**Status**` in documents that lack it, rather than requiring every downstream
> repo to hand-edit its header. *(Vetoable at review.)*

> **Assumption:** insertion is a **new** `upsert_field()` helper; `set_field()`
> keeps its replace-only semantics, so no other missing field (`Iteration
> Goal`, `Retrospective`, …) starts silently appearing in un-migrated
> documents. *(Vetoable at review.)*

> **Assumption:** if the `after` anchor (`**Status**`) is itself absent —
> a hand-rolled or heavily edited document — `upsert_field()` is a no-op rather
> than appending to the end of the file, matching `set_field()`'s conservative
> "never restructure a document you don't recognize" contract. The hook's
> fallback keeps such a document working. *(Vetoable at review.)*

## Requirements

1. On a lane whose `iteration` is falsy, `update_project_status()` leaves
   `**Status**` untouched — the same treatment `**Iteration**` received in T-146.
   - **Given** a `docs/project-status.md` reading `**Iteration**: 104` and
     `**Status**: completed`, and a state file with `iteration: 0`, `track:
     quick`, `task_id: T-999` and incomplete gates
     **When** `sync-status.py` runs against it
     **Then** the file still reads `**Iteration**: 104` and `**Status**:
     completed`, and contains no `**Status**: in-progress` line.

2. On a lane with a real iteration number, `**Status**` is still written from
   `derive_status(state)`, so it continues to describe the iteration named
   beside it.
   - **Given** a state file with `iteration: 105` and gates not all satisfied
     **When** `sync-status.py` runs
     **Then** the header reads `**Iteration**: 105` and `**Status**:
     in-progress`.

3. `**Lane Status**` is written from `derive_status(state)` on **every** sync,
   regardless of whether `iteration` is truthy.
   - **Given** the quick-lane state of requirement 1 (`iteration: 0`, gates
     incomplete)
     **When** `sync-status.py` runs
     **Then** the header reads `**Lane Status**: in-progress` while `**Status**`
     remains `completed`.

4. `**Lane Status**` is inserted directly after the `**Status**` line when the
   document lacks it, replaced in place when it is present, and no *other*
   absent header field is inserted by this change.
   - **Given** a header containing `**Status**` but neither `**Lane Status**`
     nor `**Iteration Goal**`
     **When** `sync-status.py` runs with a goal available
     **Then** the line immediately following `**Status**` is `**Lane Status**:
     …`, and no `**Iteration Goal**` line has been added.

5. `on-task-request.py` decides block-vs-advisory from `**Lane Status**` when
   that field is present.
   - **Given** a header with `**Status**: completed` and `**Lane Status**:
     in-progress`
     **When** the hook receives a task-request prompt
     **Then** it takes the active-iteration advisory branch and exits 0 (it does
     not exit 2).

6. The hook falls back to `**Status**` when `**Lane Status**` is absent, so an
   un-migrated document behaves exactly as it does today.
   - **Given** a header with only `**Status**: pending` and no `**Lane Status**`
     **When** the hook receives the same task-request prompt
     **Then** it blocks with `sys.exit(2)`; and with `**Status**: in-progress`
     instead, it exits 0.

## Behavior Delta

This repo has no Ring-1 use case covering the derived views — the contract for
these header fields lives in `docs-eng-process/`, which the citations name.

**Added**
- `**Lane Status**` header field in `docs/project-status.md`, written on every
  `sync-status.py` run and seeded by the bootstrap template.
- `upsert_field()` in `scripts/sync-status.py` — replace-or-insert-after-anchor,
  used only for `**Lane Status**`.

**Modified**
- `**Status**` is now skipped, not written, when the active lane's `iteration`
  is falsy — `docs-eng-process/state-file.md §Schema (v1)` (the `iteration` row
  already records T-146's identical treatment of `**Iteration**`; it gains the
  `Status`/`Lane Status` split).
- The bootstrap header shape gains a field —
  `docs-eng-process/templates/project-status.md` (whole file, copied verbatim by
  `/openup-init`) and the sample header in `docs-eng-process/QUICKSTART.md`.
- `on-task-request.py`'s active-lane probe reads `Lane Status` first —
  `docs-eng-process/.claude-templates/scripts/hooks/on-task-request.py`.
- `/openup-retrospective` steps 1–2 name `**Status**` as the *iteration's*
  status — `docs-eng-process/procedures/openup-retrospective.md §1–§2`.

**Removed**
- Nothing.

## Entities

- **`update_project_status()`** (modified) — `scripts/sync-status.py:320`
- **`set_field()`** (read-only — semantics must not change) — `scripts/sync-status.py:311`
- **`upsert_field()`** (new) — `scripts/sync-status.py`
- **`derive_status()`** (read-only) — `scripts/sync-status.py:114`
- **`parse_project_status()` / `main()`** (modified) —
  `docs-eng-process/.claude-templates/scripts/hooks/on-task-request.py:145,197`
- **Project-status bootstrap template** (modified) —
  `docs-eng-process/templates/project-status.md`

## Approach

Give each meaning its own field instead of guarding one field twice. `**Status**`
is bound to the `**Iteration**` beside it by writing both under the *same*
truthy-`iteration` condition, so the pair can never disagree. The active-lane
value moves to a new, always-written `**Lane Status**`, added to documents that
predate it by a small replace-or-insert helper — leaving `set_field()`'s
replace-only contract intact so nothing else materializes in un-migrated files.
The hook, the only programmatic consumer of the lane sense, reads the new field
and falls back to the old one, which makes the migration a no-op for consumers
that have not re-synced yet.

## Structure

**Add:**
- `scripts/tests/test_t149_status_split.py` — requirements 1–4 (writer side).

**Modify:**
- `scripts/sync-status.py` — add `upsert_field()`; move the `Status` write
  inside the existing truthy-`iteration` guard; write `Lane Status`
  unconditionally; replace the T-146 comment's "deliberately left alone …
  carried as T-149" paragraph with the resolution.
- `docs-eng-process/.claude-templates/scripts/hooks/on-task-request.py` —
  `fields.get("Lane Status") or fields.get("Status")`.
- `docs-eng-process/templates/project-status.md` — add `**Lane Status**:
  initialized` after `**Status**`.
- `docs-eng-process/QUICKSTART.md` — the sample bootstrap header, kept identical
  to the template.
- `docs-eng-process/state-file.md` — extend the `iteration` row / header-contract
  note with the `Status` vs `Lane Status` split.
- `docs-eng-process/procedures/openup-retrospective.md` — steps 1–2 name the
  field they mean.
- `scripts/tests/test_on_task_request_hook.py` — requirements 5–6.
- `scripts/tests/test_sync_status_notes.py` — T-146's
  `test_falsy_iteration_still_syncs_every_other_field` asserts `**Status**:
  in-progress` on a falsy-iteration quick lane, which is precisely the behavior
  requirement 1 changes. Re-point that assertion at `**Lane Status**` and add
  the `**Status**`-is-preserved assertion; the test's actual subject (a quick
  lane still syncs everything else) is unchanged.
- `docs/roadmap.md` — status cell (via `sync-status.py`, never by hand).

**Do not touch:**
- `.claude/scripts/hooks/on-task-request.py`, `.claude-templates/skills/`,
  `.claude/skills/` — regenerated mirrors; edit the pack/template source and run
  `scripts/sync-templates-to-claude.sh`.
- `set_field()` — tempting to make it insert-when-missing, but that would add
  every absent field to every un-migrated document.
- `/openup-quick-task`'s `--iteration 0` — T-146 DD3: the sentinel is fine, the
  consumer was the bug.
- `**Current Task**` — same lane-scoped shape, no clobber to fix.
- `docs/project-status.md` — derived view; it picks up `**Lane Status**` from the
  generator at completion, never by hand.
- `scripts/process-manifest.txt` — no new CLI ships; `sync-status.py` is already
  listed.

## Operations

- [x] Add `upsert_field(text, field, value, after=…)` to `scripts/sync-status.py`
      — replace in place when the field exists, insert on the line after the
      `after` anchor when it does not, leave `set_field()` untouched.
- [x] Move the `**Status**` write inside the existing truthy-`iteration` guard
      and add the unconditional `**Lane Status**` write, replacing the T-146
      comment's carried-question paragraph with the resolution and its rationale.
- [x] Add `**Lane Status**` to `docs-eng-process/templates/project-status.md`
      and mirror it in the `docs-eng-process/QUICKSTART.md` sample header.
- [x] Point the hook at `Lane Status` with a `Status` fallback in
      `docs-eng-process/.claude-templates/scripts/hooks/on-task-request.py`, then
      run `scripts/sync-templates-to-claude.sh` to regenerate `.claude/`.
- [x] Record the two-field contract in `docs-eng-process/state-file.md` and fix
      `/openup-retrospective` steps 1–2 to name `**Status**` as the iteration's.
- [x] (tester) Write `scripts/tests/test_t149_status_split.py` (requirements
      1–4) and extend `scripts/tests/test_on_task_request_hook.py`
      (requirements 5–6); run both modules plus `test_sync_status_notes.py`,
      `test_sync_status_sections.py` and `test_t006_hooks.py` green.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, script conventions.
- `.claude/CLAUDE.openup.md` — derived views are never hand-edited; edit the
  pack/template, not the `.claude/` mirror.
- `docs-eng-process/parallel-lanes.md` — write-fence surface rules.
- `docs-eng-process/state-file.md` — `.openup/state.json` field contract.

## Safeguards

- **Token / size budget.** `scripts/sync-status.py` net delta ≤ ~40 lines; no
  new module, no new CLI.
- **`set_field()` is invariant.** Replace-only. Insertion lives in a separate
  function used by exactly one caller.
- **Backward compatibility.** A `project-status.md` with no `**Lane Status**`
  must keep producing today's hook decision on every path; the fallback is not
  optional.
- **Reversibility.** Revert the commit. `**Lane Status**` lines already written
  into downstream documents become inert — the reverted hook reads `**Status**`
  again and the reverted writer ignores the extra line.
- **No-go zones.** `derive_status()`'s gate logic; the `--iteration 0` sentinel;
  `**Current Task**`; the hook's classifier (`QUESTION_RE`, `TASK_LANG_RE`,
  `BARE_ID_MAX_WORDS` — T-135 precision tuning is not in scope).
- **Never hand-edit** `docs/project-status.md`, `docs/roadmap.md`, or
  `docs/INDEX.md`; regenerate them.

## Verification

- `python3 -m pytest scripts/tests/test_t149_status_split.py scripts/tests/test_on_task_request_hook.py scripts/tests/test_sync_status_notes.py scripts/tests/test_sync_status_sections.py scripts/tests/test_t006_hooks.py` — all green.
- `python3 scripts/check-docs.py` exits 0.
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-149/plan.md` exits 0.
- `scripts/sync-templates-to-claude.sh` reports the hook synced, and
  `.claude/scripts/hooks/on-task-request.py` matches its template source.
- `python3 scripts/openup-fence.py check` clean at `/openup-complete-task`.
- Grade the final artifact against `.claude/rubrics/task-spec-rubric.md`.

## Success Measures

We expect **the number of commits to `docs/project-status.md` whose
`**Iteration**` line is unchanged from the previous commit while `**Status**`
moves from `completed` to `in-progress`** — the exact clobber signature, a live
lane rewriting a finished iteration's recorded status — to be **0** over the
**next ~10 iterations** (through the next retrospective). Today the guard that
would prevent it does not exist; on a standard/full lane `**Iteration**` and
`**Status**` always move together, so any hit is the bug and not normal traffic.
Instrumentation: `git log -p --follow -- docs/project-status.md`, reading the
adjacent `**Iteration**`/`**Status**` pair per commit (the same
history-as-instrument approach T-146 used, needing nothing in the diff).
Read-back environment: **this repo**. Read-back: the next `/openup-retrospective`.

Secondary, checkable at the same read-back: `**Lane Status**` is present in
`docs/project-status.md` — if it is absent, the upsert never fired and the
primary measure's `0` would be meaningless.

## Rollout

**Flagged? No.** Internal process tooling with no user-facing surface: the
change is a header-schema addition plus two script behaviors read at run time,
and a flag would need its own header field to be read from — more machinery than
the change it guards. Backout is a revert (see Safeguards → Reversibility), and
the additive field is inert to any un-upgraded reader, so the blast radius is
already bounded. No flag, therefore no flag-removal follow-up.

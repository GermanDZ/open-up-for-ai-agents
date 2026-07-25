---
id: T-131
title: "Lane-hygiene fixes: id-allocator audit-tree scan (F2) + fence base_sha (F3)"
status: ready
priority: high
estimate: 1 session
plan: docs/iteration-plans/t-131-lane-hygiene-id-scan-fence-base-sha.md
depends-on: []
blocks: []
last-synced: ""
---

# T-131 — Lane-hygiene fixes: id-allocator audit-tree scan (F2) + fence base_sha (F3)

## Story

> **As a** solo or autonomous OpenUP session
> **I want** the task-id allocator to see every lane-owned audit trail (not just
>   change folders and roadmap rows) and the write-fence to know where the
>   current lane actually started
> **So that** a quick-track task's id is never silently re-issued, and a second
>   lane landing on a shared branch right after a first lane merged is never
>   falsely blocked for files it never touched

INVEST check:
✅ Independent — both fixes are additive, scoped to `openup-claims.py` /
`openup-fence.py` / `openup-session.py` / `openup-state.py`, no dependency on
other pending work.
✅ Negotiable — the scan-source list and precedence order are implementation
detail, open to review.
✅ Valuable — closes a data-loss-class bug (id reuse) and a false-positive
gate failure with no discoverable recovery path.
✅ Estimable — two additive, well-understood functions; 1 session.
✅ Small — no new subsystem, no schema migration.
✅ Testable — both are unit-testable against hermetic fixture repos; both have
live reproductions already captured in the exploration and this session's own
run.

## Analysis Context

- **Domain.** Two process-integrity scripts: the task-id allocator
  (`used_seqs_in_repo` in `openup-claims.py`) and the write-fence's base-ref
  resolution (`resolve_base` in `openup-fence.py`), plus the acquisition path
  that will stamp new data for the fence to consume (`openup-session.py
  cmd_begin`, `openup-state.py cmd_init`, `openup-claims.py cmd_claim`).
- **Scope boundaries.** This task does NOT touch `reserved_seqs()` or the
  live-reservation locking protocol (F2 only widens the *used* scan). It does
  NOT retrofit `base_sha` onto already-completed/archived lanes (forward-looking
  only). It does NOT add an `openup-doctor` validator for "id used in a run log
  but never promoted to a roadmap row" — that is a detection/reporting concern
  layered on top, tracked as an open question in the source exploration, not
  required to close this correctness gap.
- **Definition of done.** `next-id`/`reserve-id` skip an id that exists only as
  a run-log shard `task_id` field or a status-note filename; `openup-fence.py
  check` run with no `--base` flag on a branch carrying a second lane's commits
  on top of a first lane's already-merged commits reports zero false `OUT OF
  LANE` violations for the first lane's files.

> **Assumption:** an explicit `--base` flag on `openup-fence.py check` always
> outranks the lane's stamped `base_sha` (manual override / existing tests that
> pass `--base` keep their exact behavior). *(Vetoable at review.)*
> **Assumption:** `git rev-parse HEAD` at the moment `openup-session.py begin`
> runs is always the lane's true base commit, because every current call site
> (`openup-start-iteration`, `openup-next`) creates the branch/worktree first
> and calls `begin` before any commit lands on it — verified against
> `openup-start-iteration`'s skill body for this session. *(Vetoable if a call
> site is found that commits before calling `begin`.)*

## Requirements

1. `used_seqs_in_repo()` treats a task id found only in a
   `docs/agent-logs/runs/*.jsonl` shard's `task_id` field as used.
   - **Given** a repo with no `docs/changes/T-005` folder and no `T-005`
     mention in `docs/roadmap.md`, but a committed run-log shard containing
     `{"task_id": "T-005", ...}` **When** `next-id` (or `reserve-id` with no
     `--task-id`) is run with prefix `T-` **Then** the returned id is `T-006`,
     never `T-005`.
2. `used_seqs_in_repo()` treats a task id found only as a
   `docs/status-notes/YYYY-MM-DD-<id>.md` filename as used.
   - **Given** a repo with a file `docs/status-notes/2026-07-25-T-005.md` and
     no other mention of `T-005` anywhere else **When** `next-id` is run
     **Then** `T-005` is excluded from the allocatable range.
3. A malformed run-log line or a non-matching status-note filename degrades
   silently (never raises).
   - **Given** a run-log shard containing one line of invalid JSON alongside
     valid lines, and a `docs/status-notes/` file whose name doesn't match the
     `YYYY-MM-DD-<prefix><digits>.md` pattern **When** `used_seqs_in_repo()` is
     called **Then** it returns the seqs from every valid source with no
     exception raised.
4. `openup-session.py begin` stamps `base_sha` (`git rev-parse HEAD` at call
   time) into both the claim file and `.openup/state.json`.
   - **Given** a fresh branch checked out from `main` at commit `abc123`, with
     no commits made on it yet **When** `openup-session.py begin` is run
     **Then** both the claim JSON (`<claims-dir>/<task>.json`) and
     `.openup/state.json` contain `"base_sha": "abc123..."` (the full resolved
     sha).
5. `openup-fence.py`'s `resolve_base` prefers the lane's stamped `base_sha`
   over `origin/main`/`main` when no explicit `--base` is given, and an
   explicit `--base` still wins over the stamped value.
   - **Given** a branch with lane-1's commit A (already merged into `main`)
     followed by lane-2's commit B, and `.openup/state.json` stamped with
     `base_sha` = A's sha **When** `openup-fence.py check` is run with no
     `--base` flag **Then** it reports zero `OUT OF LANE` violations for files
     lane-1's commit A touched (they are not in lane-2's diff against A).
   - **Given** the same setup **When** `openup-fence.py check --base main` is
     run explicitly **Then** it uses `main`, not the stamped `base_sha`
     (explicit override preserved).
6. A pre-existing claim/state file with no `base_sha` key degrades to today's
   `origin/main`/`main` resolution chain, not an error.
   - **Given** a `.openup/state.json` written before this change (no
     `base_sha` key) **When** `openup-fence.py check` reads it **Then**
     `resolve_base` falls through to `origin/main`, then `main`, exactly as
     before this task.

## Behavior Delta

**Added**:
- `used_seqs_in_repo()` gains two additional scan sources (run-log shards,
  status-note filenames) — strictly widens what counts as "used", never
  narrows it.
- `openup-claims.py claim` and `openup-state.py init` gain an optional
  `--base-sha` flag; `openup-session.py cmd_begin` computes and passes it
  automatically.
- `openup-fence.py resolve_base` gains a `stamped` parameter sourced from
  `.openup/state.json`'s `base_sha`, tried after an explicit `--base` and
  before `origin/main`/`main`.

**Modified**: none — no existing documented behavior in `docs/product/`
changes; these are internal process-tooling correctness fixes with no
user-facing product behavior. `n/a` for Modified/Removed.

**Removed**: none.

## Success Measures

`n/a — internal process-tooling correctness fix, not user-facing product
behavior`. The falsifiable expectation instead: **zero** manual id-collision
workarounds (grep git log / pick-by-hand) and **zero** false `OUT OF LANE`
fence failures for a sequential same-branch lane, observed across future
sessions. No dashboard metric — both are rare, session-level correctness
failures; read-back is "did it recur" at the next retrospective covering this
window (already recorded as this task's Success Measure in
`docs/iteration-plans/t-131-lane-hygiene-id-scan-fence-base-sha.md`).

## Rollout

`n/a — not user-facing`. Both fixes run inside internal maintainer tooling
(`openup-claims.py`, `openup-fence.py`, `openup-session.py`, `openup-state.py`)
invoked by OpenUP skills/scripts, not by end users of any product this
framework builds. No flag: the fixes are pure-function/config-read changes
with documented backward-compatible fallbacks (Requirement 6) — a flag would
add ceremony without adding safety.

## Entities

- **`used_seqs_in_repo`** (modified) — `scripts/openup-claims.py:476`
- **`resolve_base`** (modified) — `scripts/openup-fence.py:98`
- **`cmd_begin`** (modified) — `scripts/openup-session.py:90`
- **`cmd_init`** (modified) — `scripts/openup-state.py:321`
- **`cmd_claim`** (modified) — `scripts/openup-claims.py:886`
- **`base_sha`** (new field) — claim JSON payload, `.openup/state.json`

## Approach

Both fixes are additive scans/fields layered on existing, working machinery —
no new subsystem. F2 adds two more read-only scan sources to a function that
already unions multiple sources by design. F3 stamps one extra piece of data
(`git rev-parse HEAD`) at the exact moment it is cheapest and most accurate to
capture — session acquisition — and teaches the fence's existing
first-match-wins resolution chain to consult it. Neither fix touches the
locking/claiming protocol itself or the fence's allowlist-matching logic.

## Structure

**Add:**
- (none — all changes are to existing files)

**Modify:**
- `scripts/openup-claims.py` — `used_seqs_in_repo()` gains the two scan
  sources; `cmd_claim` + its argparse subparser gain `--base-sha`
- `scripts/openup-state.py` — `cmd_init` + its argparse subparser gain
  `--base-sha`
- `scripts/openup-session.py` — `cmd_begin` computes `base_sha` and threads it
  into the `claim` and `init` calls
- `scripts/openup-fence.py` — `resolve_base` gains the `stamped` parameter;
  `cmd_check` reads `.openup/state.json`'s `base_sha` and passes it
- `scripts/tests/test_openup_claims.py` — new scan-source tests + live-shape
  regression
- `scripts/tests/test_openup_fence.py` — `resolve_base` precedence tests +
  live-shape regression
- `scripts/tests/test_openup_session.py` — `base_sha` stamping test
- `docs-eng-process/script-cli-reference.md` — document the new `--base-sha`
  flags

**Do not touch:**
- `reserved_seqs()` (`openup-claims.py:512`) — live-reservation locking is a
  separate mechanism (in-progress reservations), not part of the "used ids"
  scan this task widens
- `openup-board.py` — consumes `openup-fence.py`/`openup-claims.py` but its own
  resolve/collision logic is unrelated to either fix
- worktree-per-lane defaults/recommendation — F3 accommodates the sequential
  same-branch case without changing what's recommended

## Operations

- [ ] Add `used_seqs_in_repo()` scan sources — `docs/agent-logs/runs/*.jsonl`
      `task_id` fields and `docs/status-notes/YYYY-MM-DD-<id>.md` filenames,
      degrading silently on malformed input — with hermetic tests for both new
      sources, the malformed-input degrade case, and the live-shape
      T-129-replay regression (Requirements 1–3)
- [ ] Add optional `--base-sha` to `openup-claims.py claim` (stored in the
      claim payload) and to `openup-state.py init` (stored in `state.json`);
      wire `openup-session.py cmd_begin` to compute `base_sha = git rev-parse
      HEAD` and pass it to both calls, with a test asserting it lands in both
      files after `begin` (Requirement 4)
- [ ] Add the `stamped` parameter to `openup-fence.py`'s `resolve_base`
      (precedence: explicit `--base` > stamped > `origin/main` > `main`), wire
      `cmd_check` to read `.openup/state.json`'s `base_sha`, and add tests for
      the precedence order, the no-`base_sha` fallback (Requirement 6), and the
      live-shape T-128-vs-T-127 sequential-lane regression (Requirement 5)
- [ ] Document the new `--base-sha` flags in
      `docs-eng-process/script-cli-reference.md`
- [ ] Run the full test suite + `check-docs.py --changed-only` +
      `openup-fence.py check` and confirm all green

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, etc.)
- `docs-eng-process/parallel-lanes.md` — write-fence / claim mechanics this
  task modifies

## Safeguards

- **Token / size budget.** Both changed functions stay under ~30 added lines
  each; no new file.
- **Reversibility.** Both fixes are purely additive (new optional scan
  sources, new optional field with a documented fallback) — reverting the
  commit restores exactly today's behavior with no migration needed.
- **No-go zones.** Do not change `reserved_seqs()` or the claim/reservation
  race-safety guarantees (atomic hard-link create in
  `create_reservation_exclusive`). Do not change the fence's allowlist/segment-
  prefix matching (`is_allowed`/`seg_prefix_collide`) — only which *base ref*
  the diff is computed against.
- **Back-compat.** A claim/state file written before this change (no
  `base_sha` key) must continue to work exactly as today — read as absent, not
  an error.

## Verification

- `python3 -m unittest discover -s scripts/tests -p "test_*.py"` — full suite
  green, including the new F2/F3 tests.
- `python3 scripts/check-docs.py --changed-only` clean.
- `python3 scripts/openup-fence.py check --task-id T-131` clean at completion.
- Grade against `.claude/rubrics/task-spec-rubric.md` before marking `ready`
  (done as part of this authoring pass).

---

<!--
Worked example: see docs/changes/archive/T-001/plan.md for a real
spec produced from this template.
-->

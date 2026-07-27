---
id: T-142
title: "Every completed lane must advance the retro-cadence counter, regardless of track"
status: ready
priority: high
estimate: 1 session
plan: ""
depends-on: []
blocks: []
last-synced: ""
touches:
  - scripts/openup-state.py
  - scripts/tests/test_t011_retro.py
  - scripts/tests/test_openup_state.py
  - docs-eng-process/procedures/openup-quick-task.md
  - docs-eng-process/procedures/openup-complete-task.md
  - docs-eng-process/state-file.md
  - docs-eng-process/.claude-templates/skills/openup-quick-task/SKILL.md
  - docs-eng-process/.claude-templates/skills/openup-complete-task/SKILL.md
  - docs/roadmap.md
  - docs/changes/T-143/plan.md
  - docs/changes/T-143/design.md
  - docs-eng-process/procedures/openup-start-iteration.md
  - docs-eng-process/procedures/openup-retrospective.md
  - docs-eng-process/.claude-templates/skills/openup-start-iteration/SKILL.md
  - docs-eng-process/.claude-templates/skills/openup-retrospective/SKILL.md
  - .claude/skills/openup-start-iteration/SKILL.md
---

# T-142 — Quick-track completion never increments the retro-cadence counter

> **This lane owns two tasks.** T-143 ships in the same PR by explicit roadmap
> instruction ("neither is independently valuable" — see T-143's Dependencies
> line), so `touches` above covers both change folders and both tasks' surfaces.
> T-143 keeps its own change folder, spec, and roadmap status.

## Story

> **As a** process owner relying on the retro-cadence gate to force a
> retrospective every 5 completed lanes
> **I want** the counter to advance on *every* completed lane, not only the ones
> that exit through `/openup-complete-task`
> **So that** the gate that refuses a `full`-track start actually fires when it
> is due, instead of silently never reaching its threshold.

INVEST check:
✅ Independent (no DAG dep; ships with T-143 for value, not for correctness) ·
✅ Negotiable (increment site is a design choice, see Assumption) ·
✅ Valuable (restores a broken enforcement gate) ·
✅ Estimable (one function + two procedure edits + tests) ·
✅ Small (single session) ·
✅ Testable (the counter is an integer a test can read)

## Analysis Context

- **Domain.** The retro-cadence counter (T-011): a durable integer read by
  `/openup-start-iteration` step 3b, incremented on completion, reset by
  `/openup-retrospective`. Implemented in `scripts/openup-state.py`
  (`cmd_retro`, `read_retro_count`, `write_retro_count`).
- **The defect.** The increment is a *prose instruction* that exists in exactly
  one skill: `docs-eng-process/procedures/openup-complete-task.md` step 7a.
  `/openup-quick-task` has no reference to `retro` at all, so every quick-track
  lane completes without advancing the cadence. Self-confirmed this session:
  T-133 and T-137 both completed quick and never called `retro increment`.
  Because the gate degrades by *undercounting*, it fails silently — there is no
  error, just a threshold that arrives later than it should, or never.
- **Scope boundaries.** This task fixes *when* the counter advances. It does NOT
  fix *where the counter is stored* — the gitignored/per-worktree durability
  hole is T-143, and the two ship in one PR because neither is independently
  valuable. It does not change the threshold (5), the `full`-track refusal
  behavior, or `/openup-retrospective`'s reset.
- **Definition of done.** Archiving a lane's state advances the durable counter
  on every track, enforced by code rather than by prose; `/openup-complete-task`
  no longer double-counts; a test proves a quick-track teardown advances it.

> **Assumption:** the increment moves into `openup-state.py archive` — the
> shared teardown both completion paths already run — rather than being copied
> as a second prose step into `/openup-quick-task`. The roadmap description
> sanctions either ("or a shared teardown step with `/openup-complete-task`");
> the structural option is chosen because the observed failure mode *is* prose
> not being followed, and a third completion path added later would reintroduce
> the same gap. *(Vetoable at review.)*

> **Assumption:** over-counting is treated as strictly safer than under-counting
> for a cadence gate — an extra increment makes a retrospective due sooner,
> whereas a missed one disables the gate. `archive` therefore increments
> unconditionally rather than trying to detect "was this a real completion".
> *(Vetoable at review.)*

No blocking questions: the roadmap entry names both the mechanism and the
acceptance check, and the only genuine choice (increment site) is recorded above
as a non-blocking default.

## Requirements

1. `openup-state.py archive` advances the durable retro counter by exactly one
   as part of the archive operation.
   - **Given** a live `.openup/state.json` and a retro count of `2`
     **When** `openup-state.py archive <dest>` runs and exits 0
     **Then** `openup-state.py retro get` prints `3`.
2. A failed archive does not advance the counter.
   - **Given** no state file present (archive exits `3`)
     **When** `openup-state.py archive <dest>` runs
     **Then** `openup-state.py retro get` prints the same value it printed
     before the call.
3. `archive` accepts a `--no-retro` escape hatch that suppresses the increment,
   for callers archiving a state that is not a lane completion.
   - **Given** a live state file and a retro count of `1`
     **When** `openup-state.py archive <dest> --no-retro` runs and exits 0
     **Then** `openup-state.py retro get` prints `1`.
4. `/openup-complete-task` no longer issues its own `retro increment`, so a
   single completion advances the counter exactly once.
   - **Given** the procedure `docs-eng-process/procedures/openup-complete-task.md`
     **When** step 7a is read after this change
     **Then** it contains no `openup-state.py retro increment` command, and
     instead states that the `end`/`archive` teardown advances the cadence.
5. `/openup-quick-task` documents that its archive step advances the cadence, so
   the behavior is discoverable from the skill a quick lane actually reads.
   - **Given** the rendered mirror
     `docs-eng-process/.claude-templates/skills/openup-quick-task/SKILL.md`
     **When** `grep -c retro` is run against it
     **Then** the result is non-zero.
6. The archive-increment behavior is documented in
   `docs-eng-process/state-file.md` alongside the counter's existing description.
   - **Given** `docs-eng-process/state-file.md`
     **When** the retro-counter section is read
     **Then** it states that `archive` performs the increment and names
     `--no-retro`.

## Behavior Delta

**Modified:**
- `openup-state.py archive` — now advances the durable retro counter as a side
  effect of a successful archive. The governing artifact is
  `docs-eng-process/state-file.md` (the retro-counter section and the `archive`
  subcommand's description), updated here. No Ring-1 `docs/product/` use case
  describes the state CLI's teardown.
- `/openup-complete-task` step 7a — stops issuing its own `retro increment`
  (the teardown now does it), so the counter advances once, not twice, per
  completion. Governing artifact:
  `docs-eng-process/procedures/openup-complete-task.md §7a`.
- `/openup-quick-task` step 7 — its archive call now advances the cadence.
  Governing artifact:
  `docs-eng-process/procedures/openup-quick-task.md §7 Archive State`.

**Added:** `--no-retro` flag on `archive`. **Removed:** none.

## Success Measures

We expect the **ratio of retro-counter increments to completed lanes** to move
from its current **≈0.6** (this session: 5 of 8 completions were non-quick) to
**1.0** for every lane completed after this change, within the **next 5
completed lanes**. Instrumentation: compare `python3 scripts/openup-state.py
retro get` against the number of archived state files written under
`docs/agent-logs/<Y>/<M>/<D>/state-*.json` since the last `retro reset` — both
are exact counts already produced by the process, needing no new telemetry.
Read-back: the next `/openup-retrospective` (which is also what resets the
counter, so the check must be made before the reset).

## Rollout

**Flagged?** No. A deterministic, locally-run CLI with no deployed surface and
no in-flight users; the change affects only what a *future* archive writes.
Reversible by revert with no migration — the counter is a scalar, and reverting
simply stops the increment. `--no-retro` is the built-in kill switch for a
single call site that needs the old behavior, so a feature flag would be a
second, redundant mechanism.

## Entities

- **`cmd_archive()`** (modified) — `scripts/openup-state.py`
- **`read_retro_count()` / `write_retro_count()`** (read-only, reused) —
  `scripts/openup-state.py`
- **`_sync_state_count()`** (read-only) — `scripts/openup-state.py`; a no-op
  after archive, since archive removes the state file
- **retro-counter docs** (modified) — `docs-eng-process/state-file.md`
- **completion procedures** (modified) —
  `docs-eng-process/procedures/openup-complete-task.md` §7a,
  `docs-eng-process/procedures/openup-quick-task.md` §7

## Approach

Move the cadence increment from skill prose into the one code path every
completed lane already runs: `openup-state.py archive`. Archiving *is* the
"this lane is over" event — it validates, copies, and deletes the live state —
so incrementing there makes the cadence advance by construction rather than by a
model remembering a step. The increment happens only after the archive has
succeeded, so a failed teardown leaves the count untouched. `--no-retro` keeps
an explicit opt-out for any caller archiving state that is not a completion.
`/openup-complete-task`'s step 7a is then reduced from a command to a note,
which is what prevents the double count.

## Structure

**Add:**
- `--no-retro` argument on the `archive` subparser — `scripts/openup-state.py`
- Retro-cadence tests in `scripts/tests/test_t011_retro.py` — the existing home
  for counter behavior (archive increments; failed archive does not;
  `--no-retro` suppresses but still archives)

**Modify:**
- `scripts/openup-state.py` — `cmd_archive()` increments after a successful
  archive; module docstring's `archive` line notes the cadence side effect
- `scripts/tests/test_t011_retro.py` — `test_counter_survives_archive` asserted
  the *old* contract ("archive leaves the counter untouched"); it now asserts
  survives-and-increments
- `scripts/tests/test_openup_state.py` — pointer comment to the cadence tests'
  home; no behavioural test changes
- `docs-eng-process/procedures/openup-complete-task.md` — §7a becomes a note,
  the `retro increment` command is removed
- `docs-eng-process/procedures/openup-quick-task.md` — §7 states that archiving
  advances the cadence and links `state-file.md`
- `docs-eng-process/state-file.md` — document the archive-increment and
  `--no-retro`
- The rendered skill mirrors under
  `docs-eng-process/.claude-templates/skills/` (regenerated, not hand-edited)

**Do not touch:**
- `retro_path()` / storage location — that is T-143, shipping in the same PR but
  as its own change folder; conflating them makes the revert unit wrong
- The threshold `5` and the `full`-track refusal in
  `/openup-start-iteration` §3b — the gate's *policy* is out of scope; this task
  only restores its *input*
- `/openup-retrospective`'s `retro reset` — unchanged; reset stays explicit
- `openup-session.py end` — it already delegates to `archive`, so it inherits
  the fix without an edit

## Operations

- [x] Add `--no-retro` to the `archive` subparser and increment the durable
      counter in `cmd_archive()` after the archive succeeds
      (`scripts/openup-state.py`); update the module docstring's `archive` line
- [x] Reduce `/openup-complete-task` §7a to a note (remove the
      `retro increment` command) in
      `docs-eng-process/procedures/openup-complete-task.md`
- [x] State the cadence side effect in `/openup-quick-task` §7
      (`docs-eng-process/procedures/openup-quick-task.md`)
- [x] Document archive-increment + `--no-retro` in
      `docs-eng-process/state-file.md`
- [x] (tester) Tests in `scripts/tests/test_t011_retro.py`: archive advances the
      count by one; archive with no state file (exit 3) leaves it unchanged;
      `--no-retro` suppresses the increment but still archives; and update
      `test_counter_survives_archive`, which asserted the old
      "archive-never-touches-it" contract
- [x] Regenerate the skill mirrors (`python3 scripts/render-skills-mirror.py
      --write`, `bash scripts/sync-templates-to-claude.sh`) and confirm
      `grep -c retro
      docs-eng-process/.claude-templates/skills/openup-quick-task/SKILL.md` is
      non-zero
- [x] Run the full test suite

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, pre-commit housekeeping
- `scripts/openup-state.py`'s own design rules (deterministic, stdlib-only,
  skills write through the CLI, `--state-dir` override for tests)
- `.claude/CLAUDE.openup.md` — edit the pack (`docs-eng-process/procedures/`),
  never the rendered `.claude/skills/` mirror

## Safeguards

- **Reversibility.** Revert of a single commit; no on-disk migration. A count
  that was over-advanced self-corrects at the next `retro reset`.
- **No-go zones.** The counter must never *decrease* on this path; `reset` stays
  the only way to zero it. `archive`'s existing exit codes and destination
  semantics must not change.
- **Idempotence.** A second `archive` for the same lane exits `3` (state already
  removed) and must not increment — that is Requirement 2, not an accident.
- **Token / size budget.** ≤ 20 net lines in `scripts/openup-state.py`; no new
  dependencies.

## Verification

- `python3 -m pytest scripts/tests/test_openup_state.py -q` passes, including
  the four new cadence tests
- Full suite: `python3 -m pytest scripts/tests tests -q`
- `grep -c 'retro increment' docs-eng-process/procedures/openup-complete-task.md`
  returns `0`
- `grep -c retro docs-eng-process/.claude-templates/skills/openup-quick-task/SKILL.md`
  returns non-zero
- `python3 scripts/check-docs.py` passes
- Grade against `.claude/rubrics/task-spec-rubric.md` — all criteria ✅

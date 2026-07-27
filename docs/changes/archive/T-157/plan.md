---
id: T-157
title: "`sync-status.py --views-only` — regenerate the shared views without a live lane"
status: done
priority: high
estimate: 1 session
plan: ""
depends-on: []
blocks: []
last-synced: ""
touches:
  - scripts/sync-status.py
  - scripts/tests/test_sync_status_notes.py
  - scripts/tests/test_sync_status_sections.py
  - docs-eng-process/parallel-lanes.md
  - docs-eng-process/script-cli-reference.md
  - docs-eng-process/.claude-templates/CLAUDE.md
---

# T-157 — `sync-status.py --views-only` — regenerate the shared views without a live lane

## Story

> **As a** framework maintainer recovering a PR that conflicts in the shared views
> **I want** `sync-status.py` to regenerate the state-free parts of those views without an active `.openup/state.json`
> **So that** the documented conflict-recovery recipe works at the moment it is actually needed — after the lane has completed — instead of requiring a hand-repair

INVEST check:
✅ Independent — touches one script + its two existing test files · ✅ Negotiable — the exact flag surface is open · ✅ Valuable — removes the only known state a human must hand-repair · ✅ Estimable — one flag, one state-free branch · ✅ Small — mirrors an existing branch in the same file · ✅ Testable — the flag either runs without state or it doesn't

## Analysis Context

- **Domain.** The derived shared views (`docs/roadmap.md`, `docs/project-status.md`) and their sole generator, `scripts/sync-status.py`. Specifically the recovery path used when two lanes' PRs collide in those files.
- **Scope boundaries.** This does NOT regenerate the lane-derived header fields, does NOT touch roadmap *table-row* Status cells, does NOT change any existing invocation's behavior, and does NOT attempt to prevent view conflicts (only to make recovery possible). It is a recovery path, not a merge strategy.
- **Definition of done.** `python3 scripts/sync-status.py --views-only` exits 0 and correctly rewrites `## Notes` in a checkout with **no** `.openup/state.json`, and `docs-eng-process/parallel-lanes.md`'s recovery recipe names that command.

**Root cause (verified before drafting, per action item B2).** `main()` calls `read_state()` and returns `EXIT_NO_STATE` (3) at `scripts/sync-status.py:501-504` when `.openup/state.json` is absent. `/openup-complete-task` runs `openup-session.py end --archive-to docs/changes/{task_id}/state.json`, which moves that file out of `.openup/`. So the recipe at `docs-eng-process/parallel-lanes.md:206-219` — rebase onto trunk, re-run `sync-status.py`, force-push — is impossible in exactly the situation it is written for, since a PR conflict surfaces *after* push, which is after completion. This is the same failure shape as T-150: **the recovery tool needs a precondition the situation has already destroyed.**

**Evidence it is not hypothetical.** `docs/iteration-retrospectives/iteration-103-retrospective.md:67-79` records a four-PR merge wave that left `## Notes` assembled from whichever copy won, with three notes on disk absent from the block and two PRs going `CONFLICTING`. The recovery performed was calling the module's own `assemble_notes` / `update_notes_section` functions directly — which is precisely the capability this task promotes to a supported flag.

> **Assumption:** B1's phrase *"reconciles Status cells"* is implemented as the **existing state-free section reconcile** (`reconcile_sections`, which stamps free-form `## T-NNN:` sections from archived change folders). Roadmap **table-row** Status cells are deliberately excluded: they are written only by `update_roadmap(text, task_id, status, today)`, which needs a specific lane's id and derived status, so there is no state-free truth for them. The iteration-103 recovery never needed table cells repaired. *(Vetoable at review.)*

> **Assumption:** An absent or empty `docs/status-notes/` (where `assemble_notes()` returns `None`) is a clean no-op returning `EXIT_OK`, not an error — a repo with no note shards is legitimate. *(Vetoable at review.)*

> **Assumption:** `--views-only` is a superset of `--reconcile` (it runs that pass), so passing both is redundant rather than an error; `--views-only` is checked first and wins. *(Vetoable at review.)*

> **Assumption:** `Last Updated` and `Updated By` are treated as **lane-derived and left untouched**, alongside the other header fields — even though they arguably describe the *document* rather than the lane, and a `--views-only` run does modify the document. Chosen because it keeps requirement 4's assertion strong and unambiguous (*nothing* above `## Notes` changes), and a slightly stale `Last Updated` is a smaller harm than a no-go zone with exceptions in it. The counter-argument is real: after a recovery run the file will claim it was last updated at the completing lane's date while its `## Notes` body has changed. *(Vetoable at review.)*

**Acknowledged trade-off — the recovered PR's header never reflects its own lane.** Because requirement 4 leaves the header untouched, a lane that recovers a conflict with `--views-only` carries trunk's header values (from whichever lane last completed) rather than its own, and on merge those trunk values persist — so the recovering lane's iteration is never reflected in the `Iteration` / `Iteration Goal` / `Current Task` fields. This is accepted, not overlooked: the alternative is reconstructing a header from an archived state file, which is the fragile path this task explicitly rejects, and the header is a *current-state* view whose trunk value is already the one that survives a merge. Named here so a later reader recognises it as a decision rather than a bug.

**Write-fence interaction (no change required).** `docs/roadmap.md` and `docs/project-status.md` are `VIEW_PATHS` in `scripts/openup-fence.py`. `--views-only` writes exactly the files the existing generator already writes, so fence behavior is unchanged: regenerating on a freshly-rebased base passes, and on a stale base it reports `STALE VIEW` rather than `OUT OF LANE`, exactly as today. The recovery recipe rebases first, so the supported path stays green.

## Requirements

1. `--views-only` runs to completion with no `.openup/state.json` present, returning `EXIT_OK` (0) rather than `EXIT_NO_STATE` (3).
   - **Given** a checkout with `docs/project-status.md`, `docs/roadmap.md` and `docs/status-notes/` present but **no** `.openup/state.json`, **When** `python3 scripts/sync-status.py --views-only` runs, **Then** it exits `0` and does not emit the `No state file at …` message.

2. `--views-only` reassembles the `## Notes` section of `docs/project-status.md` from every `docs/status-notes/*.md` shard, newest-first, via the existing `assemble_notes()` / `update_notes_section()`.
   - **Given** three shards on disk (`2026-01-03-T-003.md`, `2026-01-02-T-002.md`, `2026-01-01-T-001.md`) and a `docs/project-status.md` whose `## Notes` body contains only the T-001 note, **When** `--views-only` runs, **Then** the `## Notes` body contains all three notes in descending filename order and the sections after `## Notes` are byte-identical.

3. `--views-only` runs the existing state-free roadmap section reconcile, so one command restores both views.
   - **Given** `docs/changes/archive/T-042/` exists and `docs/roadmap.md` carries a `## T-042:` section whose `**Status**:` line reads `in-progress`, **When** `--views-only` runs, **Then** that line reads `completed (<archival-date>)`.

4. `--views-only` does not write any lane-derived header field of `docs/project-status.md` — `Phase`, `Iteration`, `Status`, `Current Task`, `Lane Status`, `Iteration Goal`, `Last Updated`, `Updated By`.
   - **Given** a `docs/project-status.md` whose header reads `**Iteration**: 107` and `**Current Task**: T-139`, **When** `--views-only` runs with no state file, **Then** every line above the `## Notes` heading is byte-identical to before the run.

5. `--views-only` does not set `gates.roadmap_synced`, since there is no lane to gate.
   - **Given** a `.openup/state.json` that **is** present with `gates.roadmap_synced` absent, **When** `--views-only` runs, **Then** the state file is unmodified and `gates.roadmap_synced` is still absent.

6. `--views-only --dry-run` reports what would change and writes nothing, consistent with `--reconcile --dry-run`.
   - **Given** a `docs/project-status.md` whose `## Notes` body is stale relative to the shards, **When** `--views-only --dry-run` runs, **Then** it exits `0`, reports the pending change on stdout, and `docs/project-status.md` is byte-identical on disk.

7. Every existing invocation of `sync-status.py` (no flag, `--reconcile`, `--no-gate`, `--state-dir`) behaves exactly as before.
   - **Given** the existing `test_sync_status_notes.py` and `test_sync_status_sections.py` suites, **When** they run against the modified script, **Then** all previously-passing tests still pass with no assertion changes.

8. `docs-eng-process/parallel-lanes.md`'s "Conflict recovery recipe" names the command that actually works after completion.
   - **Given** the recipe block at `docs-eng-process/parallel-lanes.md:206-219`, **When** a maintainer follows it verbatim in a post-completion checkout with no state file, **Then** every command in it succeeds.

9. Every *live* instruction that states the recovery recipe names the working command; historical records are left as written.
   - **Given** `docs-eng-process/.claude-templates/CLAUDE.md`'s "If a PR conflicts in the views" rule — the copy loaded into every agent session — **When** the recipe changes, **Then** that rule names `--views-only` too, **and** the recipe text in `docs/status-notes/`, `docs/explorations/`, `docs/iteration-retrospectives/` and `docs/changes/archive/` is unchanged, because those are audit records of what was true when written.

## Behavior Delta

Ring 1 (`docs/product/`) contains only `milestones/` and carries no artifact describing `sync-status.py`; the authoritative document for this behavior is the process doc cited below, so that is what the Modified entry cites.

**Added** — behavior that did not exist before:
- A state-free `--views-only` recovery path on `sync-status.py` that regenerates the `## Notes` assembly and the roadmap section reconcile without `.openup/state.json`.
- `--views-only --dry-run`, a read-only report of what that path would change.

**Modified** — behavior that changes; cited artifact + section:
- The documented conflict-recovery procedure changes from `python3 scripts/sync-status.py` to the `--views-only` form — `docs-eng-process/parallel-lanes.md §Conflict recovery recipe`.
- The CLI's documented flag set gains `--views-only` — `docs-eng-process/script-cli-reference.md §sync-status.py`.

**Removed** — none. No existing invocation, flag, or exit code changes; this is purely additive.

## Entities

- **`sync-status.py`** (modified) — `scripts/sync-status.py`; gains the flag, the early state-free branch in `main()`, and a `run_views_only()` entrypoint.
- **`run_reconcile()`** (read-only) — `scripts/sync-status.py:435`; the existing state-free branch whose shape `run_views_only()` mirrors.
- **`assemble_notes()` / `update_notes_section()`** (read-only) — `scripts/sync-status.py:390,405`; reused unchanged, called directly by the new path.
- **`reconcile_sections()`** (read-only) — `scripts/sync-status.py:456`; reused unchanged by the new path.
- **Conflict recovery recipe** (modified) — `docs-eng-process/parallel-lanes.md:206-219`.
- **Notes tests** (modified) — `scripts/tests/test_sync_status_notes.py`.
- **Section-reconcile tests** (modified) — `scripts/tests/test_sync_status_sections.py`.

## Approach

Mirror the branch that already exists: `--reconcile` returns from `main()` at lines 498-499 *before* `read_state()`, proving a state-free path in this file is a solved shape. Add `--views-only` with the same early-return, delegating to a new `run_views_only()` that composes three functions already written and already tested — `assemble_notes`, `update_notes_section`, `reconcile_sections` — rather than introducing new derivation logic. The design intent is that `--views-only` regenerates exactly what is derivable from **committed, lane-independent inputs** (the note shards and the archived change folders) and touches nothing derived from a live lane; the header fields stay untouched because after a rebase they correctly carry the trunk value, and inventing one from an archived state would be a guess. Deliberately deferred: any attempt to reconcile roadmap table-row cells, which have no state-free truth source.

## Structure

**Add:**
- `run_views_only(args) -> int` in `scripts/sync-status.py` — the state-free entrypoint.

**Modify:**
- `scripts/sync-status.py` — register `--views-only`; early-return from `main()` before `read_state()`; extend `--dry-run`'s help to cover both state-free paths.
- `scripts/tests/test_sync_status_notes.py` — one `ViewsOnlyTests` class covering **all** of requirements 1–6. *(Corrected mid-lane: the original Structure split these across the two test files by which module they exercised. Splitting one feature's tests across two files to mirror the implementation's internals makes the feature's coverage unreadable — every test here shares the same "no state file present" fixture, which is the actual subject. `test_sync_status_sections.py` is consequently unmodified; it stays in `touches` as a harmless superset.)*
- `docs-eng-process/parallel-lanes.md` — the recovery recipe (req. 8) and a one-line note that the header fields are not regenerated.
- `docs-eng-process/script-cli-reference.md` — the `sync-status.py` signature.
- `docs-eng-process/.claude-templates/CLAUDE.md` — the "If a PR conflicts in the views" rule (req. 9). Added mid-lane: this is the copy loaded into every agent session, so leaving it naming the broken command is precisely the rot the iteration-103 retrospective warned about. Its untracked, gitignored mirror `.claude/CLAUDE.md` needs no edit.

**Do not touch:**
- `update_project_status()` — tempting, since it owns the header, but requirement 4 is that the header is *not* written; the new path simply never calls it.
- `update_roadmap()` — owns table-row Status cells; excluded by the first Assumption (no state-free truth for them).
- `set_gate_roadmap_synced()` — requirement 5 is that it is not called; it needs no change.
- `scripts/openup-session.py` — archiving state at completion is correct; the fix belongs in the recovery tool, not by keeping state alive longer.
- `scripts/tests/test_t149_status_split.py` — asserts header-field behavior this task must leave unchanged; if a test here fails, that is a real regression, not a test to update.
- `docs/status-notes/`, `docs/explorations/`, `docs/iteration-retrospectives/`, `docs/changes/archive/` — several state the old recipe verbatim and a sweep is tempting, but they are **audit records of what was true when written**. Rewriting history to match current behavior destroys the evidence trail this task was built from (req. 9).
- `.claude/CLAUDE.md` — the local mirror of the template above; gitignored (`.gitignore:38`) and untracked, so editing it would put an uncommittable file in the lane's diff.

## Operations

- [x] Confirm the current failure mode first: in a fixture with no `.openup/state.json`, plain `sync-status.py` exits `3` with `No state file at …` — verified before any edit (this is requirement 2's precondition, checked against the pristine script rather than after the flag existed).
- [x] Add the `--views-only` argparse flag and the `run_views_only()` skeleton; confirm `python3 scripts/sync-status.py --views-only --help` lists the flag and the script still imports clean.
- [x] Write the `ViewsOnlyTests` cases for requirements 1–6; confirm they fail against the current implementation for the stated reason, not an import error. **9 of 11 failed** against `HEAD`'s script; the 2 that passed are `test_plain_sync_still_fails_without_state` (a deliberate no-regression guard, expected to pass both ways) and `test_table_row_status_untouched` (which passes vacuously on the old script, since the command errors out before touching anything).
- [x] Implement `run_views_only()` — early-return in `main()` before `read_state()`, composing `assemble_notes` / `update_notes_section` / `reconcile_sections`, honoring `--dry-run`; confirm the new tests pass (11/11).
- [x] Verify the change is a pure widening: full `scripts/tests/` suite **884 passed, 1 skipped, 20 subtests** — exactly the 873 baseline + 11 new, with no assertion edits to any pre-existing test (requirement 7).
- [x] Verify the fix bites end-to-end: on a copy of the **real** repo docs with `.openup/state.json` absent and `## Notes` truncated to one stale line, plain `sync-status.py` exits `3` and `--views-only` exits `0`, restoring all **113 of 113** shards (0 missing) — the exact iteration-103 failure mode ("three notes on disk but absent from the block").
- [x] Update `docs-eng-process/parallel-lanes.md`'s recovery recipe and `docs-eng-process/script-cli-reference.md`; the recipe now branches on lane-live vs completed, and the completed branch's `--views-only` command was the one run in the live check above.
- [x] Update the "If a PR conflicts in the views" rule in `docs-eng-process/.claude-templates/CLAUDE.md` (requirement 9, added mid-lane); `check-claude-sync` green, and the historical records were deliberately left unrewritten.
- [x] (tester) Confirm the header-preservation claim independently — `diff` of `docs/project-status.md` above `## Notes` before/after a live `--views-only` run is **empty**, including `Last Updated` and `Updated By`, which a normal sync run would have rewritten.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format, script layout).
- `docs-eng-process/parallel-lanes.md` — the derived-views model this task serves.
- `.claude/rubrics/task-spec-rubric.md` — grading for this spec.

## Safeguards

- **Purely additive.** No existing flag, exit code, or default invocation may change behavior. Requirement 7 is the check; a failure in `test_t149_status_split.py` is a stop-and-revert signal, not a test to edit.
- **No new derivation logic.** The new path composes existing, already-tested functions. If it needs a new way to derive a value, that is a scope breach — stop and re-spec.
- **No-go zone: the header fields.** `--views-only` must never write `Phase`, `Iteration`, `Status`, `Current Task`, `Lane Status`, `Iteration Goal`, `Last Updated`, or `Updated By`. Guessing one from an archived state is exactly the fragility this task rejects.
- **No writes to archived artifacts.** The rejected `--state-dir docs/changes/T-NNN` workaround would write `gates.roadmap_synced` into an archived state file; the new path writes only the two view files.
- **Reversibility.** Revert the single commit — the flag is opt-in and unreferenced by any other script, so nothing depends on it.
- **Size budget.** ≤ ~60 LOC of implementation in `sync-status.py`; more means the composition assumption was wrong.

## Success Measures

We expect the number of view-conflict recoveries requiring a **hand-repair** — a direct edit to `docs/roadmap.md` / `docs/project-status.md`, or a `python -c` call into `sync-status.py`'s internal functions — to fall from **2 of 2** (the iteration-103 four-PR merge wave, where both `CONFLICTING` PRs needed one) to **0 of the next 3** view-conflicting PRs. Instrumentation: the **Measure Read-Back table of this repo's iteration retrospectives**, which already recorded the iteration-103 incident in exactly this form, cross-checked against `git log -- docs/project-status.md docs/roadmap.md` for commits that change a view without a corresponding generator run. Read-back environment: **this repo** — the framework repo is where the shared-view merge waves occur and where the recovery is performed. Read-back: **the second retrospective after landing** (absolute backstop 2026-09-30).

If at read-back fewer than 3 view-conflicting PRs have occurred, report the count honestly as *insufficient data* rather than declaring the measure met — zero conflicts is not evidence the recovery path works.

## Rollout

`n/a — not user-facing.` This is an additive CLI flag on an internal maintenance script. No feature flag: the new code path is reachable **only** by explicitly passing `--views-only`, so every existing invocation is byte-identical and the opt-in flag already provides what a feature flag would (nothing to toggle off — not passing it is the off state). There is consequently no flag-removal follow-up to enqueue. The change reaches users through the normal PR merge, and downstream consumers pick it up via their existing `sync-from-framework.sh` run.

## Verification

- `python3 -m pytest scripts/tests/test_sync_status_notes.py scripts/tests/test_sync_status_sections.py -q` — all green, including the new cases.
- `python3 -m pytest scripts/tests/ -q` — full suite; pre-existing count still passes (requirement 7).
- Live check: in a throwaway copy with `.openup/state.json` removed, `python3 scripts/sync-status.py` exits 3 and `python3 scripts/sync-status.py --views-only` exits 0 and repairs a stale `## Notes`.
- Header preservation: `diff <(sed -n '1,/## Notes/p' before.md) <(sed -n '1,/## Notes/p' after.md)` is empty.
- `python3 scripts/check-docs.py` clean.
- Grade the final artifact against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅ or a clear gap call-out.

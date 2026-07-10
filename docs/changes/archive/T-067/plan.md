---
id: T-067
title: sync-status.py stamps free-form `## T-NNN:` section Status lines (+ reconcile sweep, doctor drift check)
status: done
priority: high   # critical | high | medium | low
estimate: 1 session
plan: ""
depends-on: []
blocks: []
touches:
  - scripts/
  - docs/changes/
  - docs/roadmap.md
  - docs-eng-process/
last-synced: ""
---

# T-067 — sync-status.py stamps section-style roadmap Status lines

## Story

> **As a** maintainer driving the OpenUP continue-loop
> **I want** `sync-status.py` to update the `**Status**:` line of free-form
> `## T-NNN:` roadmap sections, not only markdown-table rows
> **So that** every completed task's roadmap status reflects reality without a
> hand-edit — closing the silent status-rot that left T-063/T-064/T-066 stale.

INVEST — ✅ Independent · ✅ Negotiable · ✅ Valuable · ✅ Estimable · ✅ Small · ✅ Testable

## Analysis Context

- **Domain.** The derived-view generator `scripts/sync-status.py` and the
  read-only diagnostic `scripts/openup-doctor.py`. `docs/roadmap.md` is a
  write-fenced derived view (T-024).
- **Root cause.** `update_roadmap()` matches only table rows
  (`row_re = re.compile(r"^\s*\|")`). Roadmap entries authored by
  `/openup-plan-feature` are free-form `## T-NNN:` sections whose status lives
  in a `**Status**:` line — never a table cell. So those sections are updated
  only when a human hand-edits them (git blame confirms: T-065's `completed`
  came from manual commit `7ae9b716`, "…+ section status"). Three delivered
  tasks were never hand-fixed and rotted: T-063 & T-064 (`pending`), T-066
  (`ready`).
- **Scope boundaries.** Does NOT change the table-row path (still authoritative
  for table entries), does NOT alter `/openup-plan-feature`'s output format,
  does NOT make `openup-doctor` write anything (it stays read-only — it only
  *detects* the drift and names the fix). Does NOT touch `project-status.md`
  regeneration or the `## Notes` assembly.
- **Definition of done.** (a) `sync-status.py` stamps a matching section's
  `**Status**:` line when no table row matches the current task; (b) a
  `--reconcile` sweep derives `completed (<archival-date>)` for every `## T-NNN:`
  section whose change folder is archived; (c) `openup-doctor` emits a
  `warning`-severity finding for any such drift, pointing at the reconcile fix;
  (d) the three rotted entries are backfilled by running reconcile; (e) a test
  covers the section fallback and reconcile.

> **Assumption:** the completion date for a reconciled/section-stamped entry is
> the date of the last git commit touching `docs/changes/archive/<id>/` (the
> archival commit), falling back to `today` when git is unavailable. This keeps
> backfilled dates accurate (T-063 → 2026-07-06, not "today"). *(Vetoable at review.)*

> **Assumption:** section matching keys on the header `## <task-id>:` (colon
> after the id) — the exact shape `/openup-plan-feature` emits. A section header
> without the id is not a target. *(Vetoable at review.)*

## Requirements

1. When `update_roadmap(text, task_id, status, today)` finds no matching table
   row for `task_id`, it stamps the `**Status**:` line of the `## <task_id>:`
   section instead, using the same idempotent `completed (YYYY-MM-DD)` convention
   (preserve an already-present date; only add a date when flipping to completed).
   - **Given** a roadmap with a `## T-066:` section reading `**Status**: ready`
     and no table row for T-066, **When** `update_roadmap` runs with
     `status="completed"`, **Then** that line becomes `**Status**: completed (<today>)`
     and no table row is altered.
2. Table-row entries keep their existing behavior unchanged — the section path
   is a fallback taken only when no row matched.
   - **Given** a roadmap where T-062 exists as a table row, **When**
     `update_roadmap` runs for T-062, **Then** the table cell is flipped exactly
     as before and no `## T-062:` section edit is attempted.
3. A `--reconcile` mode stamps `completed (<archival-date>)` on the `**Status**:`
   line of every `## T-NNN:` section whose change folder exists under
   `docs/changes/archive/<id>/` and is not already `completed`. It is idempotent
   and writes the roadmap only when something changed.
   - **Given** sections T-063 (`pending`), T-064 (`pending`), T-066 (`ready`)
     each with an archived change folder, **When** `sync-status.py --reconcile`
     runs, **Then** each line becomes `completed (<archival-date>)` and a second
     run makes no further change (exit reports 0 updated).
4. `openup-doctor` emits a `warning`-severity finding for each `## T-NNN:`
   section whose change folder is archived but whose `**Status**:` is not
   `completed`, naming `sync-status.py --reconcile` as the fix. Doctor writes
   nothing.
   - **Given** a roadmap with one rotted archived section, **When**
     `python3 scripts/openup-doctor.py` runs, **Then** output contains a
     `warning` finding referencing that task id and `--reconcile`, and exit code
     stays 0 (warning, not error).
5. Running `--reconcile` on the live repo backfills T-063, T-064, T-066 to
   `completed` with their real archival dates.
   - **Given** the current `docs/roadmap.md`, **When** reconcile runs, **Then**
     T-063→`completed (2026-07-06)`, T-064→`completed (2026-07-10)`,
     T-066→`completed (2026-07-10)`.

## Behavior Delta

Internal process-tooling change; no Ring-1 (`docs/product/`) product behavior is
touched.

**Added**
- `sync-status.py --reconcile` sweep (new mode).
- `openup-doctor` section-status-drift check (new read-only finding).

**Modified**
- `sync-status.py update_roadmap()` — adds a section-line fallback when no table
  row matches. Internal function; not a Ring-1 artifact.

**Removed** — n/a.

## Entities

- **`update_roadmap`** (modified) — `scripts/sync-status.py`
- **reconcile entrypoint** (new) — `scripts/sync-status.py` (arg + sweep fn)
- **section-drift check** (new) — `scripts/openup-doctor.py`
- **roadmap** (read-only input / write target) — `docs/roadmap.md`
- **archive dir** (read-only ground truth) — `docs/changes/archive/`
- **test** (new) — `scripts/tests/test_sync_status_sections.py`

## Approach

Add one helper that stamps a section `**Status**:` line by task id (mirroring the
table-cell idempotent date logic), and call it from `update_roadmap` as the
no-table-row fallback. Add a `reconcile_sections()` sweep that lists archived
change-folder ids, resolves each archival date from git (`git log -1 --format=%cs
-- docs/changes/archive/<id>`, fallback today), and stamps any non-completed
matching section; wire it to a `--reconcile` flag that writes the file and prints
a count. In `openup-doctor`, add a read-only check that reports the same drift set
as `warning` findings pointing at the reconcile command. Reuse the existing date
and matching conventions — no second source of truth.

## Structure

**Add:**
- `scripts/tests/test_sync_status_sections.py`

**Modify:**
- `scripts/sync-status.py` — section-line helper + `update_roadmap` fallback +
  `--reconcile` sweep/arg.
- `scripts/openup-doctor.py` — section-status-drift `warning` check.
- `docs/roadmap.md` — backfilled by running reconcile (via the generator, not by
  hand).
- `docs-eng-process/script-cli-reference.md` — document the `--reconcile` flag.

**Do not touch:**
- `update_roadmap`'s table-row branch — behavior must stay identical.
- `/openup-plan-feature` output format — out of scope; the fix is on the
  consumer side.
- `project-status.md` regeneration / `## Notes` assembly.

## Operations

- [x] Add a `stamp_section_status(text, task_id, status, today)` helper in
      `sync-status.py` and call it from `update_roadmap` as the fallback when no
      table row matched; keep the idempotent `completed (date)` convention.
- [x] Add `reconcile_sections()` + `--reconcile` arg: sweep archived ids, resolve
      archival date via git (fallback today), stamp non-completed sections, write
      once, print count.
- [x] Add the read-only section-status-drift `warning` check to
      `openup-doctor.py` (points at `sync-status.py --reconcile`; exit stays 0).
- [x] (tester) Write `scripts/tests/test_sync_status_sections.py` covering: table
      row unchanged (req 2), section fallback stamp (req 1), reconcile
      idempotence (req 3), doctor drift finding (req 4). Run the full
      `scripts/tests/` suite green.
- [x] Run `python3 scripts/sync-status.py --reconcile` to backfill T-063/T-064/
      T-066; verify the three lines and idempotence (req 5).
- [x] Document `--reconcile` in `docs-eng-process/script-cli-reference.md`.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, process conventions.
- `docs-eng-process/script-cli-reference.md` — CLI signature conventions.
- Existing `scripts/sync-status.py` idioms (Finding/severity model in
  `openup-doctor.py`).

## Safeguards

- **Token / size budget.** Net additions small (~2 helpers + 1 check + 1 test);
  no refactor of the table path.
- **Reversibility.** Pure additive code paths; `--reconcile` is opt-in and
  idempotent. Roadmap backfill is a normal reviewable diff.
- **No-go zones.** The table-row branch of `update_roadmap` must produce
  byte-identical output for table entries. `openup-doctor` must remain read-only
  (no writes). The write-fence rule for `docs/roadmap.md` stands — it is only
  ever changed by running the generator, never hand-edited.
- **Idempotence.** Re-running section stamping / reconcile preserves existing
  `completed (date)` values.

## Success Measures

`n/a — internal process tooling with no runtime user metric.` Correctness is
falsifiable and verified deterministically instead: `openup-doctor` reports **0**
`roadmap-status-drift` findings after reconcile (was 3: T-063/T-064/T-066), the
new unit suite passes, and `--reconcile` is idempotent (a second run reports
`0 section(s)`). Read-back: at the next `/openup-plan-feature` completion — its
section should reach `completed` with no hand-edit.

## Rollout

`n/a — not user-facing.` Pure internal tooling: `sync-status.py` runs at
`/openup-complete-task` and on demand; `--reconcile` is opt-in and idempotent;
`openup-doctor` stays read-only. No flag — the new code path is additive and a
no-op on repos with no section-style entries, so a flag would add no safety.
Backout: revert the commit; the derived views regenerate.

## Verification

- `python3 scripts/tests/test_sync_status_sections.py` (and the full
  `scripts/tests/` suite) pass.
- `python3 scripts/sync-status.py --reconcile` flips T-063/T-064/T-066 to
  `completed (<archival-date>)`; a second run reports 0 changes.
- `python3 scripts/openup-doctor.py` shows no section-status-drift warning after
  reconcile (and did show one before).
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-067/plan.md`
  exits 0.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

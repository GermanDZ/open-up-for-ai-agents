---
id: T-132
title: "openup-entropy.py --include allowlist + --snapshots + --by-era coupling + manifest registration (F1 + F6)"
status: ready
priority: high
estimate: 1-2 sessions
plan: docs/iteration-plans/t-132-entropy-include-snapshots-era-manifest.md
depends-on: []
blocks: []
last-synced: ""
touches:
  - scripts/openup-entropy.py
  - scripts/tests/test_openup_entropy.py
  - scripts/process-manifest.txt
  - docs-eng-process/script-cli-reference.md
  - docs/iteration-plans/t-132-entropy-include-snapshots-era-manifest.md
---

# T-132 — `openup-entropy.py` allowlist scoping, structural snapshots, era-sliced coupling + manifest registration (F1 + F6)

## Story

> **As a** maintainer measuring codebase entropy on a repo that vendors this
>   framework (or any repo needing scoped, tree-shaped, or era-sliced signal)
> **I want** `openup-entropy.py` to support an allowlist, a month-end
>   structural series, and era-sliced coupling — and to actually reach
>   projects that vendor `scripts/`
> **So that** the next codebase-decay measurement doesn't need hundreds of
>   lines of throwaway one-off analysis, and doesn't silently reach the wrong
>   conclusion because vendored framework code was counted as application code

INVEST check:
✅ Independent — additive changes scoped to `openup-entropy.py` + its test
file + one manifest line; no dependency on other pending work.
✅ Negotiable — flag names/shapes for `--by-era` and where `--snapshots`
lives are explicitly open (see Assumptions below), open to review.
✅ Valuable — reverses a demonstrated wrong conclusion (Project A) and closes
the gap that forced 836 lines of throwaway analysis in the sibling
exploration.
✅ Estimable — three additive features ported from working reference
implementations (`docs/explorations/2026-07-25-agent-built-repo-decay/method/`),
plus one manifest line; 1-2 sessions.
✅ Small — no new subsystem, no schema migration, additive-only CLI surface.
✅ Testable — each feature has a working reference implementation to test
against, plus the exploration's recorded Project B numbers as a falsifiable
external check.

## Analysis Context

- **Domain.** `scripts/openup-entropy.py` (T-127/T-128) — the report-only,
  stdlib-only codebase-entropy analyzer. This task extends its scope (what
  files are measured, what shape of report it produces) without touching its
  design rules (deterministic, no writes, no network, degrade-independently).
- **Scope boundaries.** Does not touch `--unit {task,commit,pr}` (T-128,
  already shipped). Does not productize line survival (F1's fourth measure —
  explicitly rejected by the exploration's PM pass as not identifiable). Does
  not delete or migrate the `method/` throwaway scripts — they stay as the
  historical reference. Does not perform a live re-run against Project A or
  Project B — neither is reachable from this environment.
- **Definition of done.** `--include`, `--snapshots`, and `--by-era` are real
  flags with tests; `openup-entropy.py` is registered in
  `scripts/process-manifest.txt`; the CLI reference documents all three;
  omitting all three flags produces byte-identical output to pre-T-132
  (T-128's own backward-compatibility bar).

> **Assumption:** `--by-era N` slices coupling into N equal-commit-count eras
> (matching the reference implementation `method/coupling_trend.py`'s
> `--eras N`), not explicit `FROM:TO` date ranges (which the exploration's
> prose also mentions but never implements). *(Vetoable at review.)*

> **Assumption:** `--snapshots` lives inside `openup-entropy.py` itself,
> gated behind the flag, rather than as a sibling script — per the
> exploration disposition's literal instruction to "fold three of the four
> measures into the analyzer." *(Vetoable at review.)*

> **Assumption:** the F1 acceptance criterion (reproduce the Project B p90
> trend 382 → 315) is verified as a **manual numeric comparison** against the
> numbers already recorded in
> `docs/explorations/2026-07-25-agent-built-repo-decay.md`, not a live re-run
> — Project A/Project B are not reachable from this sandbox. Recorded in this
> change folder's `design.md` at review time. *(Vetoable at review.)*

## Requirements

1. `--include GLOB` (repeatable) scopes every metric to an allowlist, applied
   **before** `--exclude`/default excludes; omitting it preserves current
   (blocklist-only) behavior exactly.
   - **Given** a repo where `scripts/` is 100% vendored framework code and
     `--include 'app/*'` is passed, **When** `openup-entropy.py` runs,
     **Then** no `scripts/*` path appears in `declared_touches`,
     `actual_files`, or either coupling graph, and
     `report["sources"]["includes"]` lists the pattern used.
   - **Given** no `--include` flag, **When** `openup-entropy.py` runs on the
     same inputs as before this task, **Then** the JSON payload is
     byte-identical to the pre-T-132 output (same contract T-128 held for
     `--unit`).

2. `--snapshots` emits one row per calendar month with structural metrics
   (file/line counts, median/p90/max file length, share of files over 400
   lines, module spread, test/src line ratio), computed from the tree as it
   stood at each month's last commit.
   - **Given** a git fixture with commits spanning 3+ calendar months and a
     mix of in-scope/excluded files, **When** `openup-entropy.py --snapshots`
     runs, **Then** the output contains one row per month with a non-`None`
     `p90_file_lines` for any month with >10 in-scope files, and excluded
     files never contribute to any month's counts.
   - **Given** `--snapshots` is omitted, **When** `openup-entropy.py` runs,
     **Then** `report` has no `"snapshots"` key (no cost paid for the
     unused feature).

3. `--by-era N` slices the actual-graph coupling computation into N
   equal-commit-count chronological eras and reports each era's pair count,
   cross-module share, and median Jaccard alongside the existing pooled
   (whole-history) coupling.
   - **Given** a fixture with 40 commits and `--by-era 4`, **When**
     `openup-entropy.py` runs, **Then** `report["coupling"]["by_era"]`
     contains 4 entries (the last absorbing any remainder), each with its own
     `top` pairs list, and `report["coupling"]["actual"]` (pooled) is
     unchanged from the `--by-era`-absent case.

4. `openup-entropy.py` is registered in `scripts/process-manifest.txt`, so
   every install/update path (`bootstrap-project.sh`, `sync-from-framework.sh`,
   etc.) ships it.
   - **Given** a fresh `scripts/lib/install-process-clis.sh` run against the
     manifest, **When** the install completes, **Then** the target project's
     `scripts/openup-entropy.py` exists and matches this repo's copy.

5. The falsifiable F1 acceptance test: `--include` + `--snapshots` on a repo
   vendoring this framework, when compared against the numbers recorded in
   `docs/explorations/2026-07-25-agent-built-repo-decay.md`, reproduces the
   published Project B p90 trend (382 → 315) to the line.
   - **Given** the `build_snapshots()` computation applied to the same
     month-end tree states the sibling exploration measured, **When** the
     resulting p90 series is compared to the recorded table, **Then** the
     values match exactly (this is a numeric-parity check against recorded
     output, not a live rerun — see Assumption above).

## Behavior Delta

`n/a — all Added`. `openup-entropy.py` is a report-only diagnostic tool with
no Ring-1 (`docs/product/`) use-case describing its current output — every
change here is a new, opt-in, default-off flag. Omitting all three new flags
preserves byte-identical output (Requirement 1's second scenario), so no
existing invocation's behavior changes.

**Added:**
- `--include GLOB` (repeatable allowlist, applied before excludes)
- `--snapshots` (month-end structural series report section)
- `--by-era N` (era-sliced coupling report section)
- `openup-entropy.py` line in `scripts/process-manifest.txt`

## Success Measures

We expect the next codebase-measurement exploration (repo-decay-style, like
`docs/explorations/2026-07-25-agent-built-repo-decay.md`) to need **zero**
new throwaway one-off analysis scripts for allowlist scoping, structural
snapshots, or era-sliced coupling — the three measures this task folds into
the shipped analyzer. Instrumentation: at that next exploration, check
whether a new `method/`-style throwaway script (or equivalent ad hoc code)
duplicates `--include`/`--snapshots`/`--by-era` functionality instead of
using the shipped flags. Read-back: at the next such exploration (an
infrequent, owner-initiated activity with no fixed calendar date — read back
whenever the next one runs, the same conditional-trigger convention T-080
uses for its owner-live-batch read-back).

## Rollout

**Flagged?** No. `openup-entropy.py` is a read-only maintainer CLI diagnostic
tool with no deployed user-facing surface — there is nothing to roll out to
users. The three new capabilities are themselves opt-in via explicit CLI
flags (`--include`/`--snapshots`/`--by-era`, all default-off), which already
gives the same safety a feature flag would: a maintainer who never passes the
new flags sees byte-identical behavior to pre-T-132 (Requirement 1's second
scenario).

## Entities

- **`excluded()`** (modified) — `scripts/openup-entropy.py:124-125` — gains an
  `includes=()` parameter, allowlist-before-blocklist precedence (ported from
  `docs/explorations/2026-07-25-agent-built-repo-decay/method/decay.py:49-58`)
- **`build_snapshots()` / `tree_sizes()` / `month_ends()`** (new) —
  `scripts/openup-entropy.py` — ported from
  `docs/explorations/2026-07-25-agent-built-repo-decay/method/snapshots.py`
- **`bucket_commits_by_era()`** (new) — `scripts/openup-entropy.py` — ported
  from `docs/explorations/2026-07-25-agent-built-repo-decay/method/coupling_trend.py`'s
  equal-commit-chunk logic, adapted to feed `compute_coupling()`
- **`compute_coupling()`** (read-only) — `scripts/openup-entropy.py:507-550` —
  reused unchanged, called once per era plus once pooled
- **`build_report()`** (modified) — `scripts/openup-entropy.py:556-598` —
  wires `--include` through existing calls, adds `snapshots` and
  `coupling.by_era` keys behind their flags
- **`render_text()`** (modified) — `scripts/openup-entropy.py:605-683` — new
  text sections for snapshots and by-era coupling

## Approach

Port the three reference implementations from
`docs/explorations/2026-07-25-agent-built-repo-decay/method/` into
`scripts/openup-entropy.py`, adapted to its existing `_git()` helper,
`excluded()` signature, and report/render structure rather than copied
verbatim. `--include` is a small signature change threaded through existing
call sites. `--snapshots` and `--by-era` are new, flag-gated report sections
so their cost (extra `git` subprocess calls) is paid only when requested.
`--by-era` reuses `compute_coupling()` as-is, only the graph it's called on
changes. Register the script in the manifest as a one-line addition.

## Structure

**Add:**
- (nothing — all changes land in existing files)

**Modify:**
- `scripts/openup-entropy.py` — `excluded()` gains `includes`; new
  `month_ends()`, `tree_sizes()`, `build_snapshots()`,
  `bucket_commits_by_era()`; `build_report()` wires all three flags;
  `render_text()` gains two new sections; `main()` gains `--include`,
  `--snapshots`, `--by-era` argparse entries
- `scripts/tests/test_openup_entropy.py` — new test classes for allowlist
  precedence, snapshot computation, and era bucketing
- `scripts/process-manifest.txt` — add `openup-entropy.py` line (with a
  comment naming F6, matching the existing comment convention for
  `openup-doctor.py`/`openup-version-check.py`)
- `docs-eng-process/script-cli-reference.md` — document the three new flags
  in the existing `openup-entropy.py` section

**Do not touch:**
- `docs/explorations/2026-07-25-agent-built-repo-decay/method/*.py` — stays
  as the historical reference implementation, not deleted or migrated
- `scripts/openup-entropy.py`'s `--unit {task,commit,pr}` logic (T-128,
  already shipped) — tempting to touch since era-slicing interacts with
  units, but out of scope; `--by-era` must work under all three units
  unchanged
- Any live network call to Project A / Project B — not reachable from this
  environment; verification is against recorded numbers only

## Operations

- [x] Port `excluded()`'s allowlist parameter + thread `args.include` through
      every existing `excluded(p, excludes)` call site in `build_tasks()` and
      the coupling-graph construction in `build_report()`; add
      `report["sources"]["includes"]`
- [x] Add `month_ends()`, `tree_sizes()`, `build_snapshots()` (ported from
      `method/snapshots.py`, adapted to `_git()`/`excluded()`); wire behind
      `--snapshots` in `build_report()`; add the "Structural snapshots"
      section to `render_text()`
- [x] Add `bucket_commits_by_era()` (ported from `method/coupling_trend.py`'s
      equal-commit-chunk logic) + wire `report["coupling"]["by_era"]` behind
      `--by-era N` in `build_report()`; add the by-era section to
      `render_text()`
- [x] Add `--include`, `--snapshots`, `--by-era` argparse entries to `main()`
      with help text matching the existing flag style
- [x] Add `openup-entropy.py` to `scripts/process-manifest.txt` with an F6
      comment; document all three new flags in
      `docs-eng-process/script-cli-reference.md`
- [x] (tester) Unit tests: allowlist precedence (include+no-match excludes
      even with empty blocklist; include-absent unchanged), `build_snapshots()`
      against a multi-month git fixture (month boundaries, p90 guard,
      share-over-threshold math), `bucket_commits_by_era()` against a
      non-multiple-of-N commit fixture (remainder in the last chunk);
      confirm full `scripts/tests/test_openup_entropy.py` stays green and
      flag-absent output is byte-identical to pre-T-132
- [x] Record the F1 acceptance check (numeric comparison of computed p90
      series shape against the recorded Project B table in
      `docs/explorations/2026-07-25-agent-built-repo-decay.md`) in this
      folder's `design.md`

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process conventions (commit format,
  etc.)
- `scripts/openup-entropy.py`'s own module docstring (lines 1-39) — design
  rules (deterministic, no writes, no network, degrade independently)

## Safeguards

Invariants and limits that must hold:
- **Backward compatibility.** Omitting `--include`/`--snapshots`/`--by-era`
  must produce byte-identical JSON to pre-T-132 output — the same contract
  T-128 held for `--unit`.
- **No network, no writes.** `openup-entropy.py`'s design rules (module
  docstring) are unchanged by this task: stdlib-only, report-only, no state
  written to the analyzed repo.
- **Reversibility.** Every change is additive (new flags, new optional report
  keys); reverting is a straight revert of this task's diff with no
  migration to undo.
- **No-go zones.** Do not change `--unit {task,commit,pr}` semantics (T-128).
  Do not touch the `DEFAULT_EXCLUDES` tuple's existing entries (only the new
  allowlist parameter is added alongside it).

## Verification

- `python3 -m pytest scripts/tests/test_openup_entropy.py -q` (or
  `unittest`, matching the existing suite's runner) — full green including
  new test classes
- `python3 scripts/openup-entropy.py --repo . --include 'scripts/*' --json`
  runs clean and `sources.includes == ["scripts/*"]`
- `python3 scripts/openup-entropy.py --repo . --snapshots --json` runs clean
  and `report["snapshots"]` has one row per month with git history in this
  repo
- `grep -c openup-entropy.py scripts/process-manifest.txt` → 1
- Grade the final artifact against `.claude/rubrics/task-spec-rubric.md` —
  every criterion ✅ or a clear gap call-out
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-132/plan.md`
  exits 0

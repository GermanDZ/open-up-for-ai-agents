# T-127 — in-flight decisions & completion grade

## Completion grade (step 1a — requirements vs the actual diff)

Graded against `git diff origin/main...HEAD` and the green test run, not against
intent. Test names refer to `scripts/tests/test_openup_entropy.py`.

- ✅ **R1 — per-task cost series.** `build_tasks()` joins the three loaders into one
  ordered row per task id. Absent sources yield `null`, not `0`
  (`test_cost_series_joins_three_sources`, `test_absent_metric_is_null_not_zero`).
- ✅ **R2 — index + month bucketing.** `bucket_by_index()` / `bucket_by_month()`,
  medians over present values only with a per-metric `_n` count
  (`test_buckets_by_index_and_month`).
- ✅ **R3 — drift with segment-prefix matching.** `drift_for()` reports coverage,
  precision, Jaccard, undeclared files; matching imports `seg_prefix_collide` from
  `openup-claims.py`. Both spec scenarios are direct tests
  (`test_partial_overlap_scenario` asserts the exact 0.333/0.5/0.5 the spec names;
  `test_directory_declaration_covers_children`), plus the negative case
  (`test_sibling_directory_does_not_match`).
- ✅ **R3a — drift bucketed with cost.** `coverage` / `drift_jaccard` are per-row
  fields in `METRIC_KEYS`, so every cost bucket carries their medians
  (`test_drift_is_bucketed_alongside_cost`).
- ✅ **R4 — co-change coupling.** `compute_coupling()` over both graphs, with the
  cross-module flag and reported (never silent) oversized-task skips
  (`test_pair_metrics_and_cross_module_flag` asserts the spec's exact
  support 5 / Jaccard 1.0 / lift 2.0; `test_min_support_filters_noise`,
  `test_oversized_task_is_skipped_and_reported`).
- ✅ **R5 — independent degradation.** Each loader returns empty on absence
  (`test_degrades_to_git_only`, `test_degrades_to_declared_only`), and only a repo
  with no telemetry at all exits 3 (`test_empty_repo_exits_no_data`).
- ✅ **R6 — determinism.** `test_json_output_is_byte_identical_across_runs`, plus a
  live check on this repo: two `--json` runs diffed clean.
- ✅ **R7 — no enforcement.** No write path exists in the script; verified
  mechanically by `test_report_writes_nothing_to_the_analyzed_repo` (porcelain
  status unchanged, no `.openup/` created).

**Result: satisfied** — 8/8 requirements ✅, full suite 702 pass.

## Success-Measure instrumentation (step 1b)

- ✅ **Instrumentation exists** — `drift.median_coverage` is emitted by
  `compute_drift()` and present in the `--json` payload (the field the spec names).
- **Read-back: done now** (the spec's read-back is "immediately, in this task's
  baseline note"). Measured **1.0**, against an expectation of **≥ 0.5** →
  **expectation met**. Recorded in
  `docs/explorations/2026-07-25-maintainability-baselines.md` §2.

## Decisions taken in flight

**DD1 — Import the fence's matcher, don't reimplement it.** The first cut compared
declared `touches` to actual paths by set equality and reported median Jaccard
**0.06**, which reads as catastrophic drift. Two causes, both in the data's real
shape: `touches:` entries are often **directory prefixes**
(`docs-eng-process/templates/`) and often carry **inline YAML comments**
(`scripts/    # claims + tests`). Correcting both — importing
`claims.seg_prefix_collide` via importlib (the pattern `openup-board.py` already
uses) and stripping ` #` comments — moved the number to **0.81**. A 13× error, in
the direction that would have falsely confirmed the decay thesis. Agreement-by-
construction with the fence is not a style preference here; it is the difference
between a right and a wrong headline.

**DD2 — Report coverage and precision, not Jaccard alone.** Under prefix matching
a plain set Jaccard is ill-defined (one declaration can cover many files). The
generalization used — `covered / (|actual| + |unused declarations|)` — reduces to
the plain form when every entry is an exact file path, so the spec's original
scenario still holds numerically. Coverage and precision are reported alongside it
because they are separately actionable: coverage answers "did the lane declare what
it changed", precision answers "did it over-declare".

**DD3 — Default exclusion list, printed not hidden.** Every lane touches
`docs/roadmap.md`, the audit trees, and its own change folder, so leaving them in
makes all file pairs look coupled. They are excluded by default, the active list is
printed in the report header, and `--no-default-excludes` restores them.

**DD4 — Report both graphs rather than picking one.** Declared and actual coupling
are computed independently. Their disagreement is the open question the brief
raises, so collapsing them to one number would discard the finding.

**DD5 — Left out of `scripts/process-manifest.txt`.** The manifest's stated
criterion is "runtime scripts the workflow skills invoke"; nothing invokes the
analyzer — it is a maintainer tool. `openup-doctor.py` confirms no manifest drift
without it. Revisit if a skill ever calls it.

## Gotchas for whoever runs this next

**G1 — Shallow clones silently corrupt the result.** This session's checkout was
shallow: git matched 34 of 126 tasks and attributed the entire tree (2560 files) to
the boundary task T-056. `git fetch --unshallow` fixed both. A CI entropy job on a
default depth-1 checkout would emit confident garbage. Check `.git/shallow` first.

**G2 — `openup-claims.py next-id` under-reports.** It returned `T-125` while
T-126 already existed (the scan misses prose-roadmap / archive ids), so the id was
reserved explicitly with `--task-id T-127`. Not fixed here — out of lane, and worth
its own task since it can hand two lanes the same id.

**G3 — `docs/INDEX.md` carries pre-existing drift.** `docs-index.py --check` fails
on trunk: T-071's iteration plan is missing from the index. It is unrelated to this
lane and outside its surface, so the regeneration was reverted rather than smuggled
into this diff. Needs its own lane (or a `--fix` pass by whoever owns the view).

## Blocked scope (carried, not dropped)

The Project A baseline — the interesting half of §5 — did not run.
`list_repos` sees Project A, but `add_repo` refuses it: this session's
sources belong to owner `germandz` and cross-owner adds are unsupported. The
Operations box is deliberately left **unticked**. Project D is not reachable at
all. The analyzer's foreign-repo paths are covered hermetically
(`test_degrades_to_git_only`, `test_conventional_scope_fallback_when_no_bracket_tag`)
but have never met either repo's real history, and the baseline note says so rather
than implying the tool is proven there.

# T-128 — in-flight decisions & completion grade

## Completion grade (step 1a — requirements vs the actual diff)

- ✅ **R1 — default unchanged.** `--unit` defaults to `task`; `load_git` only varies
  the graph's *key*, and the metric functions were not touched.
  `test_default_unit_matches_explicit_task` asserts default == `--unit task`.
  The stronger second scenario was checked directly: the pre-change analyzer
  (`git show`) and the new one were run on this repo and their payloads compared
  with `sources.unit` removed — **equal object-for-object**.
- ✅ **R2 — commit unit.** `collect(lambda sha, subj: sha[:12])`.
  `test_commit_unit_measures_a_repo_with_no_task_ids` asserts the task unit exits
  `3` on the same fixture while the commit unit exits 0 with the expected pair
  (`src/a.py` ↔ `src/b.py`, support 4).
- ✅ **R3 — PR unit.** `pr_key` returns `None` for untagged commits so they are
  dropped rather than each becoming a unit
  (`test_pr_unit_groups_by_number_and_drops_untagged`: one unit `#7`, 2 files).
- ✅ **R4 — unit is always stated.** Header line + `sources.unit`
  (`test_unit_is_named_in_header_and_payload`).
- ✅ **R5 — drift stays task-only.** `load_declared` is skipped for non-task units
  (`test_drift_is_task_only`).

**Result: satisfied** — 5/5 ✅.

## Success-Measure read-back

- ✅ **Instrumentation** — `sources.git_tasks` and `coupling.actual.top` in the
  `--json` payload.
- **Read-back: done.** Against the Project C clone, which previously
  exited `3 — no telemetry`: `--unit commit` now reports **672 units, 1262 coupled
  pairs at support ≥3**. The expectation was binary and is **met**.

## Decisions taken in flight

**DD1 — No `--unit auto`.** Inferring the unit would silently produce reports whose
rows count different things (a task spans many commits), and the whole point of the
baseline programme is cross-repo comparison. The unit is explicit, defaults to
`task`, and is printed in the header *and* the payload precisely so a reader cannot
compare two incomparable reports by accident.

**DD2 — PR unit drops untagged commits.** The alternative (each untagged commit
becomes its own unit) would mix PR-sized and commit-sized rows in one series and
corrupt every median. Dropping is the honest choice; the count of retained units is
visible as `sources.git_tasks`.

**DD3 — Ordinal is computed for the task unit only.** Found by running the fixed
build against Project C: a commit sha that happens to be all digits (e.g.
`073790706116`) parses as a task ordinal — an enormous one — and
`bucket_by_index`'s `index is not None` filter then kept only those few commits,
collapsing 672 units into 3 buckets of 1. `index_of()` now returns `None` unless the
unit is `task`, and non-task series order by date.
`test_all_digit_sha_does_not_parse_as_a_task_ordinal` locks it.

## Finding: the commit unit is the wrong unit *for this repo*

Running this repo with `--unit commit` reports a median of **0 files** per commit in
three of four windows. Not a bug: after process-noise exclusions, a large share of
this repo's commits are housekeeping (`chore(process): sweep run-log shard`) that
touch only excluded paths. The task unit is correct here; the commit unit is correct
for a repo with no task ids. Consequence recorded in the baseline note: the
cross-repo comparison is a **trend-shape** comparison, never a level comparison.

## What the second baseline is, and is not

Project C is a **fork** — 601 of 672 commits are by the upstream gem's
maintainer. It measures the upstream open-source project, **not** Project B's own
engineering, and the note says so plainly. The other reachable Project B repo,
`usage-guides`, is an empty repository. Project A remains unreachable
by all three access paths (re-verified: `add_repo` cross-owner refusal, GitHub MCP
"not configured for this session", and a private-repo clone auth failure).

---
id: T-127
title: "Maintainability entropy measurement (M1) + first baselines (M3)"
status: done
priority: medium
estimate: 1 session
plan: docs/roadmap.md
depends-on: []
blocks: []
last-synced: ""
touches:
  - scripts/openup-entropy.py
  - scripts/tests/test_openup_entropy.py
  - docs-eng-process/script-cli-reference.md
---

# T-127 — Maintainability entropy measurement + first baselines

## Story

> **As** the maintainer deciding whether to add anti-decay gates to this framework
> **I want** the codebase-entropy signal computed from telemetry the process
> already emits — declared `touches`, run-log JSONL, and git history
> **So that** the decision to add (or not add) gates rests on this project's own
> numbers instead of on a thesis whose published evidence is one correlational
> report plus anecdotes

INVEST — ✅ Independent (no dependency on other lanes) · ✅ Negotiable (metric set
is arguable, the graph is not) · ✅ Valuable (decides items 7–10 of the design
queue) · ✅ Estimable (one script + tests + a report) · ✅ Small (single script,
stdlib) · ✅ Testable (pure functions over fixtures + a hermetic git fixture)

## Analysis Context

- **Domain.** Measurement over the framework's own audit trail. Three
  independent inputs already exist and are never written by a model: change-folder
  frontmatter (`docs/changes/**/plan.md` → `touches:`), lane-owned run-log shards
  (`docs/agent-logs/runs/*.jsonl` → `session_begin` / `session_end` / `commit`),
  and git history (commit subjects carry a `[T-NNN]` tag — verified across the
  last 40 commits on this repo).
- **Why now.** The decay claim under test ("agent-built codebases start to
  struggle at 3–6 months") has no benchmark behind it, and a first pass over this
  repo's 126 tasks showed *flat* median touches and duration across four months.
  A flat result on a docs-and-scripts repo is weak evidence either way; the
  measurement has to exist and be re-runnable before any gate is justified.
- **Scope boundaries.** **Report-only.** This task adds no gate, no threshold, no
  `GATES` entry, no hook, and no CI. It does not modify the fence, the board, or
  `check-docs.py`. It does not implement the fence-violation ledger (M2), the
  architecture-constraint checker (P1), the touches budget (P2), the verify gate
  (P3), mutation testing (V1), refactor emission (R1), or the regression gate
  (D1) — every one of those is explicitly gated on evidence this task produces.
- **Definition of done.** `python3 scripts/openup-entropy.py --repo <path>` prints
  a cost/drift/coupling report, this repo's baseline is captured in a dated
  exploration note, and the tests are green. The Project A baseline is carried
  as an explicitly-blocked Operations step (see below) rather than counted as done
  — the analyzer's foreign-repo paths are covered by hermetic tests but have not
  been exercised against that repo's real history.

> **Assumption:** Project A may not carry OpenUP change folders or `[T-NNN]`
> commit tags. Rather than guess its layout, every input degrades independently —
> a repo with only git history still yields actual-diff cost and coupling; the
> declared-`touches` sections render as "no data". *(Vetoable at review.)*

> **Assumption:** coupling is computed over **both** the declared-`touches` graph
> and the actual-git-diff graph whenever both exist, rather than picking one. The
> agreement between them is itself the open question ("do declared touches track
> actual diffs closely enough to use as a coupling proxy?"). *(Vetoable at review.)*

> **Assumption:** process-noise paths are excluded from the coupling graph by
> default (derived views `docs/roadmap.md` / `docs/project-status.md` /
> `docs/INDEX.md`, the lane-owned audit trees, and each task's own
> `docs/changes/T-NNN/` folder). Every task touches these, so including them makes
> every file pair look coupled. The default list is printed in the report and is
> overridable. *(Vetoable at review.)*

> **Assumption:** Project D is **out of scope** — it is not reachable from
> this session (`list_repos` returns no match). The brief's third baseline is
> deferred, not silently dropped. *(Vetoable at review.)*

> **Discovered mid-lane (2026-07-25):** Project A is likewise not
> attachable from this session — `list_repos` sees it, but `add_repo` refuses
> cross-owner adds against this session's `germandz` sources. Both application
> baselines are therefore deferred to a session scoped to those repos. The
> analyzer is repo-agnostic by construction and its degrade paths are tested, but
> "tested hermetically" is not "run against that history" and the note says so.

## Requirements

1. `scripts/openup-entropy.py` computes a **per-task cost series** — declared
   `touches` count, actual files-changed count, session duration in minutes, and
   commit count — keyed by task id and ordered by task index.
   - **Given** a repo with change folders, run-log shards, and `[T-NNN]` commits
     **When** `openup-entropy.py --repo <path> --json` runs
     **Then** the payload's `tasks` array holds one record per discovered task id
     carrying `declared_touches`, `actual_files`, `duration_minutes`, and
     `commits`, with `null` (not 0) for any field whose source is absent.

2. The cost series is **bucketed** both by task-index window and by calendar
   month, reporting the median of each metric per bucket, so a trend over the
   3–6-month window is readable.
   - **Given** 12 tasks spanning three calendar months
     **When** the report runs with `--buckets 4`
     **Then** the output contains 4 index buckets and 3 month buckets, each with a
     median for every metric computed over only the tasks having that metric.

3. The tool reports **declared-vs-actual drift** per task: coverage (fraction of
   actually-changed files the lane declared), precision (fraction of declarations
   that matched a real change), Jaccard, and the files changed but never declared.
   A declared entry matches an actual path by **segment-prefix**, not string
   equality — `touches:` legitimately carries directory entries
   (`docs-eng-process/templates/`), and the matching semantics must be the fence's,
   not a re-implementation.
   - **Given** a task declaring `[a.py, b.py]` whose commits actually touch
     `[a.py, c.py]`
     **When** the drift section renders
     **Then** that task shows `jaccard 0.333`, `coverage 0.5`, `precision 0.5`,
     and `undeclared 1` naming `c.py`.
   - **Given** a task declaring the directory `src/` whose commits touch
     `src/a.py` and `src/b.py`
     **When** the drift section renders
     **Then** coverage is `1.0` and `undeclared` is `0` — the directory entry
     covers both files rather than matching neither.

3a. Drift is **bucketed on the same windows as cost**, so a rise in
   declared-vs-actual divergence is readable as a trend rather than a single
   pooled number.
   - **Given** tasks spanning four index buckets **When** the report runs
     **Then** each cost bucket also carries a median coverage and median Jaccard
     computed over the tasks in that bucket that have both signals.

4. The tool computes **co-change coupling** over file pairs — support, Jaccard,
   and lift — from the declared graph and the actual graph independently, listing
   the top N pairs and flagging pairs whose modules differ.
   - **Given** files `scripts/a.py` and `docs/b.md` co-occurring in 5 of 10 tasks
     and each appearing in exactly those 5 **When** coupling renders with
     `--min-support 3` **Then** the pair appears with `support 5`, `jaccard 1.0`,
     `lift 2.0`, and is flagged cross-module.

5. Each input source **degrades independently**: absence of change folders, of
   run logs, or of parseable git history yields a report with those sections
   marked as having no data, and a non-zero-exit only for a wholly unreadable repo.
   - **Given** a git repo with commits but no `docs/changes/` tree
     **When** the tool runs against it
     **Then** it exits 0, the actual-diff cost and coupling sections are populated,
     and the declared sections read `no data (0 tasks declared touches)`.

6. The tool is **deterministic and model-free**: stdlib only, no network, no
   timestamps or randomness in the `--json` payload, so identical inputs produce
   byte-identical output.
   - **Given** the same repo at the same commit
     **When** `--json` runs twice
     **Then** the two payloads are byte-identical.

7. The tool **adds no enforcement**: it registers no gate, writes no state, and
   modifies no file in the analyzed repo.
   - **Given** a clean working tree **When** the tool runs with any flag
     combination **Then** `git status --porcelain` on the analyzed repo is
     unchanged and no `.openup/` file is created.

## Behavior Delta

`n/a — all Added.` This task introduces a new read-only analysis script. It
changes no existing product behavior; there is no Ring-1 `docs/product/` artifact
describing measurement, and no existing script, gate, hook, or skill is modified.

**Added**
- A maintainability/entropy report derivable from existing telemetry.
- A dated baseline record for this repo and for Project A.

## Entities

- **Entropy analyzer** (new) — `scripts/openup-entropy.py`
- **Analyzer tests** (new) — `scripts/tests/test_openup_entropy.py`
- **Change-folder frontmatter** (read-only) — `docs/changes/**/plan.md` `touches:`
- **Run-log shards** (read-only) — `docs/agent-logs/runs/*.jsonl`
- **Git history** (read-only) — `git log --numstat`, joined on `[T-NNN]` subjects
- **CLI reference** (modified) — `docs-eng-process/script-cli-reference.md`
- **Baseline record** (new) — `docs/explorations/2026-07-25-maintainability-baselines.md`

## Approach

Mirror the deterministic-script pattern the repo already uses (`openup-board.py`,
`openup-claims.py`): stdlib only, never invokes a model, subcommand-free single
report with flags, `--json` for machine use and a text table for humans. Model the
data as one **task × file** bipartite graph built twice — once from declared
`touches`, once from actual git diffs — so every downstream metric (cost, drift,
coupling, module spread) is a projection of the same structure rather than four
independent pipelines. Each of the three inputs is loaded by its own function
returning an empty result on absence, which is what makes the tool run against a
foreign repo without special-casing. Report-only is a design constraint, not a
phase: the script has no write path at all.

## Structure

**Add:**
- `scripts/openup-entropy.py` — the analyzer.
- `scripts/tests/test_openup_entropy.py` — unit tests over pure functions plus one
  hermetic git-fixture integration test.
- `docs/explorations/2026-07-25-maintainability-baselines.md` — the M3 baseline
  record (lane-owned audit tree; no frontmatter, matching sibling notes).

**Modify:**
- `docs-eng-process/script-cli-reference.md` — add the `openup-entropy.py`
  signature block, matching the existing per-script format.

**Do not touch:**
- `scripts/openup_agent/loop.py` — adding a `GATES` entry is P3/D1, explicitly
  gated on the evidence this task produces. Tempting because the analyzer output
  is gate-shaped; premature because no threshold is defensible yet.
- `scripts/openup-fence.py` — the fence-violation ledger (M2) is a separate lane.
- `docs/roadmap.md`, `docs/project-status.md` — derived views, regenerated by
  `sync-status.py` at complete-task, never hand-edited here.
- `.github/` — CI (G2) is a separate lane with its own risk surface.

## Operations

- [x] Write `scripts/openup-entropy.py`: the three loaders (change-folder
      `touches`, run-log JSONL, git `--numstat` joined on `[T-NNN]`), each
      returning empty on absence.
- [x] Add the metric layer — cost series, index/month bucketing with medians,
      declared-vs-actual drift, and co-change coupling (support/Jaccard/lift) over
      both graphs, with the default exclusion list applied and printed.
- [x] Add the text and `--json` renderers; verify byte-identical output across two
      consecutive `--json` runs on this repo.
- [x] Write `scripts/tests/test_openup_entropy.py` covering each requirement's
      scenario, including the hermetic git fixture and the degrade-to-empty path.
- [x] Run the full suite (`python3 -m pytest scripts/tests/ -q`) and confirm no
      pre-existing test regressed.
- [x] Run the analyzer against this repo; record the report, the interpretation,
      and the Project A blocker in
      `docs/explorations/2026-07-25-maintainability-baselines.md`.
- [ ] **BLOCKED** — run the analyzer against Project A and append its
      baseline. Blocked on session repo scope, not on the tooling: this session's
      sources belong to owner `germandz`, and `add_repo` refuses cross-owner adds
      (`cross-tier adds are not supported in v1`). Unblock by starting a session
      with Project A as an initial source; the command is recorded in
      the baseline note §7.
- [x] Add the CLI signature block to `docs-eng-process/script-cli-reference.md`.
- [x] (tester) Verify the report-only invariant: analyzed repos show no working-tree
      change and no `.openup/` write after a full run.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, pre-commit housekeeping.
- `docs-eng-process/parallel-lanes.md` — lane surface + derived-view rules.
- `docs-eng-process/script-cli-reference.md` — deterministic-script CLI conventions.
- `scripts/openup-board.py` (module docstring) — the determinism rules this script
  mirrors (stdlib only, no model, identical inputs → byte-identical output).

## Safeguards

- **Report-only invariant.** No write path in the analyzer: no file creation, no
  state mutation, no gate registration. This is the load-bearing constraint of the
  whole task — a threshold added here would be a gate justified by no evidence.
- **Token / size budget.** Analyzer ≤ ~600 lines; the baseline note ≤ ~200 lines.
- **Reversibility.** Two new files plus one doc block; reverting is deleting them.
  Nothing else in the repo depends on the analyzer.
- **No-go zones.** No change to fence, board, `check-docs.py`, `loop.py` `GATES`,
  hooks, or any skill. No network calls. No model invocation.
- **Foreign-repo safety.** Only read-only git commands (`git log`) run against an
  analyzed repo; Project A is analyzed in a throwaway clone outside this repo.

## Success Measures

We expect **median declared-vs-actual coverage across tasks with both signals** to
be **≥ 0.5** on this repo — i.e. a lane declares at least half of what it actually
changes. Instrumentation: the `drift.median_coverage` field of
`openup-entropy.py --json`. Read-back: **immediately, in this task's baseline
note.** This is the falsifiable premise of the whole measurement programme — the
declared `touches` graph is only usable as a coupling proxy (M1's claim, and the
input to P2/D1) if it tracks what actually changed. Below 0.5, the finding is that
declared touches are a planning artifact rather than a coupling signal, and the
downstream queue items that depend on them are not justified.

## Rollout

`n/a — not user-facing.` A manually-invoked, read-only analysis script with no
runtime callers: it is not wired into the driver, any hook, any skill, or CI, so
there is no rollout surface to flag and nothing to kill-switch. The gating question
this feature exists to answer is itself the release decision for anything built on
it.

## Verification

- `python3 -m pytest scripts/tests/test_openup_entropy.py -q` passes; full suite
  shows no regression against the pre-change baseline (785 passing).
- `python3 scripts/openup-entropy.py --json > /tmp/a && python3 scripts/openup-entropy.py --json > /tmp/b && diff /tmp/a /tmp/b` produces no output.
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-127/plan.md` exits 0.
- `python3 scripts/check-docs.py` and `python3 scripts/openup-fence.py check` are clean.
- `docs/explorations/2026-07-25-maintainability-baselines.md` reports both repos,
  states the read-back of the Success Measure, and names what the data does and
  does not license building next.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

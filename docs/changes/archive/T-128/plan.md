---
id: T-128
title: "Entropy analyzer: unit-of-work fallback (task | commit | pr) for repos without task ids"
status: done
priority: medium
estimate: 0.5 session
plan: docs/roadmap.md
depends-on: []
blocks: []
last-synced: ""
touches:
  - scripts/openup-entropy.py
  - scripts/tests/test_openup_entropy.py
  - docs-eng-process/script-cli-reference.md
---

# T-128 — Unit-of-work fallback for the entropy analyzer

## Story

> **As** the maintainer running the M3 baseline programme across several codebases
> **I want** the entropy analyzer to work on repos that carry no task ids in their
> commit subjects
> **So that** the comparison the decay thesis actually needs — agent-driven vs
> human-driven codebases — is computable, instead of only OpenUP repos being
> measurable

INVEST — ✅ Independent · ✅ Negotiable (unit set is arguable) · ✅ Valuable
(unblocks every non-OpenUP baseline) · ✅ Estimable · ✅ Small (one flag, one
grouping function) · ✅ Testable

## Analysis Context

- **Domain.** `scripts/openup-entropy.py` (T-127) keys every metric on a task id
  parsed from the commit subject (`[T-NNN]`, falling back to a conventional-commit
  scope). Cost, drift, and coupling are all projections of a **unit-of-work × file**
  graph; "task" is simply one choice of unit.
- **Why now — a measured blocker.** Running T-127's analyzer against
  `TallyFoxAI/ruby_llm` (672 commits, Jan–Sep 2025) exits `3 — no telemetry`:
  its subjects are plain prose (`Bump to 1.8.2`, `Display tool calls in message
  template (#416)`). The tool cannot measure any repo that does not adopt OpenUP's
  commit convention, which is most repos, including the two the brief actually
  wants compared.
- **Why it matters beyond convenience.** The brief's own strongest criticism of the
  decay thesis is the **missing baseline**: human-only teams also degrade
  codebases, and the claim needing support is a *rate comparison*. Every repo
  available for that comparison is human-authored and none of them tag commits
  with task ids. Without this, the framework can only ever measure itself.
- **Scope boundaries.** Grouping only. No new metric, no gate, no threshold, no
  change to how cost/drift/coupling are computed once the graph is built. Drift
  stays task-only by construction (a commit has no declared surface). Still
  report-only.
- **Definition of done.** `openup-entropy.py --repo <any-git-repo> --unit commit`
  produces a cost + coupling report on a repo with no task ids, and `--unit pr`
  groups by the `(#N)` merge convention.

> **Assumption:** `--unit auto` is **not** added. Silently switching units would
> make two reports look comparable when their rows mean different things (a task
> spans many commits). The unit is explicit, printed in the report header, and
> defaults to `task` — preserving T-127's behavior exactly. *(Vetoable at review.)*

> **Assumption:** under `--unit commit`, per-unit "commits" is trivially 1 and
> duration is unavailable, so those columns render `-` rather than being faked
> from commit timestamps. *(Vetoable at review.)*

## Requirements

1. A `--unit {task,commit,pr}` flag selects the unit of work; `task` is the
   default and leaves **every computed metric** identical to T-127. The payload
   gains exactly one field (`sources.unit`, required by R4) and nothing else —
   generalizing the graph's *key* must not perturb the math.
   - **Given** a repo with `[T-NNN]` commits **When** the report runs with no
     `--unit` flag and again with `--unit task` **Then** both `--json` payloads are
     byte-identical.
   - **Given** the pre-change (T-127) analyzer **When** both versions run on this
     repo and `sources.unit` is removed from the new payload **Then** the two
     payloads are equal object-for-object.

2. Under `--unit commit`, every non-merge commit is its own unit, so cost and
   coupling are computed on repos with no task ids at all.
   - **Given** a repo whose subjects carry no task id **When** the report runs with
     `--unit commit` **Then** it exits 0 and the coupling section is populated from
     the commits' file sets.

3. Under `--unit pr`, commits are grouped by a trailing `(#N)` pull-request number,
   and commits without one are excluded from the graph rather than each becoming a
   unit.
   - **Given** three commits, two tagged `(#7)` and one untagged **When** the report
     runs with `--unit pr` **Then** exactly one unit `#7` exists, holding the union
     of the two tagged commits' files.

4. The active unit is stated in the report header and in the `--json` payload, so
   two reports can never be silently compared across different units.
   - **Given** any run **When** the report renders **Then** the header names the
     unit and `sources.unit` carries it in JSON.

5. Drift remains task-only: under a non-task unit the drift section reports no
   data rather than inventing a declared surface.
   - **Given** a repo with change folders **When** the report runs with
     `--unit commit` **Then** `drift.tasks_with_both` is 0 and the text section
     reads as having no data.

## Behavior Delta

**Added**
- `--unit {task,commit,pr}` and the `sources.unit` payload field.

**Modified**
- `docs/changes/archive/T-127/plan.md` §Requirements 1–4 describe metrics keyed on
  "task"; they remain true under the default unit. No Ring-1 `docs/product/`
  artifact exists for the analyzer, so there is no product-behavior citation to
  make — the T-127 spec is archived and is not retro-edited.

**Removed** — none.

## Entities

- **Entropy analyzer** (modified) — `scripts/openup-entropy.py`: `load_git`,
  `build_tasks`, `build_report`, `render_text`, `main`
- **Analyzer tests** (modified) — `scripts/tests/test_openup_entropy.py`
- **CLI reference** (modified) — `docs-eng-process/script-cli-reference.md`

## Approach

Keep one graph builder and change only what supplies its keys. `load_git` already
walks commits and buckets them by a subject-derived id; generalize that id to a
`unit_key(subject, sha)` selected by the flag — task id, short sha, or `#N`. Every
downstream metric is untouched, which is what keeps the default byte-identical.
Drift short-circuits when the unit is not `task`, because a declared surface only
exists per task.

## Structure

**Modify:**
- `scripts/openup-entropy.py` — add the flag, the unit-key selection in `load_git`,
  the header/payload field, and the drift short-circuit.
- `scripts/tests/test_openup_entropy.py` — one test per requirement.
- `docs-eng-process/script-cli-reference.md` — document `--unit` in the existing block.

**Do not touch:**
- The metric functions (`compute_coupling`, `drift_for`, bucketing) — generalizing
  the *key* must not change the math, and leaving them untouched is the evidence.
- `docs/changes/archive/T-127/` — an archived, completed lane; superseding specs
  are new specs, not retro-edits.

## Operations

- [x] Add `--unit {task,commit,pr}` and thread a `unit_key` selector through
      `load_git`, keeping `task` the default.
- [x] Short-circuit drift for non-task units; surface the unit in the text header
      and in `sources.unit`.
- [x] Add tests for each requirement, including the byte-identical default.
- [x] Run the full suite and confirm no pre-existing test regressed.
- [x] Run `--unit commit` against the `TallyFoxAI/ruby_llm` clone and record the
      human-authored comparison baseline in the T-127 exploration note.
- [x] Update the `openup-entropy.py` block in `script-cli-reference.md`.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, pre-commit housekeeping.
- `docs-eng-process/script-cli-reference.md` — deterministic-script CLI conventions.
- `scripts/openup-entropy.py` (module docstring) — the report-only + determinism
  rules this change must preserve.

## Safeguards

- **Default is byte-identical.** `--unit task` must reproduce T-127's payload
  exactly; a test asserts it.
- **Report-only preserved.** No write path, no gate, no threshold — unchanged.
- **No silent unit switching.** No `auto` mode; the unit is always explicit and
  always printed, so cross-repo comparisons can't be accidentally invalid.
- **Token / size budget.** Net addition ≤ ~60 lines of analyzer code.
- **Reversibility.** Removing the flag restores T-127 behavior; nothing else
  depends on it.

## Success Measures

We expect the analyzer to **produce a populated cost + coupling report on a repo
with zero task ids**, where it currently exits `3`. Instrumentation: running
`openup-entropy.py --repo <ruby_llm clone> --unit commit --json` and reading
`sources.git_tasks > 0` plus a non-empty `coupling.actual.top`. Read-back:
**immediately, in this task's Operations step 5.** This is binary and falsifiable:
either the human-authored baseline becomes computable or the change failed.

## Rollout

`n/a — not user-facing.` An added flag on a manually-invoked, read-only analysis
script with no runtime callers and a byte-identical default. Nothing to flag,
nothing to kill-switch.

## Verification

- `python3 -m unittest scripts.tests.test_openup_entropy` passes; full suite shows
  no regression against the 702 baseline.
- Default equivalence: `--json` and `--unit task --json` diff clean on this repo.
- `openup-entropy.py --repo <ruby_llm> --unit commit` exits 0 with a populated
  coupling section.
- `python3 scripts/openup-spec-scenarios.py check docs/changes/T-128/plan.md` exits 0.
- `check-docs.py` and `openup-fence.py check` clean.

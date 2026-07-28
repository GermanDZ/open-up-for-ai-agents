---
id: T-160
title: "Make \"full suite\" mean the whole suite, and make a downstream measure name its reader"
status: ready
priority: medium
estimate: 1 session
plan: ""
depends-on: []
blocks: []
last-synced: ""
touches:
  - scripts/run-tests.sh
  - scripts/tests/test_full_suite_runner.py
  - docs-eng-process/conventions.md
  - docs-eng-process/procedures/openup-complete-task.md
  - docs-eng-process/procedures/openup-create-task-spec.md
  - docs-eng-process/.claude-templates/skills/openup-complete-task/SKILL.md
  - docs-eng-process/.claude-templates/skills/openup-create-task-spec/SKILL.md
  - .claude/rubrics/task-spec-rubric.md
  - docs-eng-process/.claude-templates/rubrics/task-spec-rubric.md
  - docs/roadmap.md
---

# T-160 — Make "full suite" mean the whole suite, and make a downstream measure name its reader

## Story

> **As a** reader of a lane's completion notes or a retrospective's read-back table
> **I want** "full suite" to mean every test, and a downstream measure to say who will read it
> **So that** a verification claim means what it says, and a measure whose environment I cannot reach becomes an assignable follow-up instead of a permanent `can't tell`

INVEST check:
✅ Independent — one new script, one new test, four process docs · ✅ Negotiable — the runner's shape is open · ✅ Valuable — closes iteration-109's C2 and C4 · ✅ Estimable — a wrapper plus rubric prose · ✅ Small · ✅ Testable — C2 is mechanically checkable; C4 is graded prose with a discrimination check

## Analysis Context

- **Domain.** The honesty of verification claims: what a lane means when it says it ran the tests (C2), and what a success measure promises when its number lives somewhere this repo cannot reach (C4).
- **Scope boundaries.** This does NOT change any test, does NOT add CI, does NOT make measures readable that are not (only assignable), and does NOT relax criterion 12's existing read-back-environment requirement — it adds to it.
- **Definition of done.** One command runs every project test directory and fails if a new one appears uncovered; and criterion 12 requires a named reader and cadence whenever the read-back environment is not this repo.

**C2 premise (verified).** `pytest scripts/tests/` → **884 passed**; `pytest tests/` → **114 passed**; full collection → **999**. T-155, T-157 and T-158 each reported the 884-family figure as "full suite" — as did T-159 until it was corrected to state both. **No pack, skill, or convention names a test command at all** (`grep` over `openup-complete-task.md` and `conventions.md` finds none), so "full suite" has been free prose with nothing to anchor it. `tests/test_claims_heartbeat_reap.py` — the coverage most relevant to T-159's C1 — sat in the directory nobody was running.

**C4 premise (verified).** Criterion 12 already requires a read-back environment (T-152), and it works: every post-T-152 measure names one. But naming is not access. `kaze-webapp`, `cqecho-app` and `tallyfox-app` are **not present on this machine**, so T-147's and T-155's measures came back `can't tell` in the iteration-109 read-back — the second consecutive cycle a downstream measure went unread. **Owner decision (2026-07-28): require the measure to name a reader**, rather than requiring reachable checkouts (which is not the framework's to arrange) or banning downstream measures (which would blind the framework to R1, the risk it most needs evidence on).

> **Assumption:** the runner is a thin shell script (`scripts/run-tests.sh`) that invokes `pytest` once per project test directory and aggregates exit codes — not a `pytest.ini`/`pyproject` rootdir change. A config change would silently alter every existing bare `pytest` invocation in this repo and downstream, which is a wider blast radius than the problem warrants. *(Vetoable at review.)*

> **Assumption:** the covered directories are **enumerated** in the script, with a test that fails when a *new* top-level test directory appears uncovered — rather than discovered at runtime. Discovery would sweep `venv/` and `.claude/worktrees/` (both contain `test_*.py`), and excluding them is a denylist that rots. An explicit list plus a bite-checked guard fails loudly instead. *(Vetoable at review.)*

> **Assumption:** C4's new requirement fires **only** when the read-back environment is not this repo. A measure read here already names the reader implicitly — whoever runs the next retrospective — and demanding a name for every measure would add ceremony to the common case to fix the rare one. *(Vetoable at review.)*

## Requirements

1. A single command runs every project test directory and reports one aggregate result.
   - **Given** `scripts/run-tests.sh`, **When** it runs, **Then** it invokes the suite for **both** `scripts/tests/` and `tests/`, prints a per-directory count, and exits non-zero if any directory fails.
2. The runner excludes non-project test directories.
   - **Given** `venv/` and `.claude/worktrees/` both contain `test_*.py` files, **When** the runner runs, **Then** neither is collected.
3. A new top-level project test directory cannot be silently omitted.
   - **Given** a test asserting the runner's directory list covers every top-level dir containing `test_*.py` outside the known exclusions, **When** a third project test directory is added without updating the runner, **Then** that test fails and names the uncovered directory.
4. The completion procedure points at the runner instead of leaving the command to prose.
   - **Given** `docs-eng-process/procedures/openup-complete-task.md`, **When** a lane reaches its verification step, **Then** the text names `scripts/run-tests.sh` as what "full suite" means, and says that quoting a single-directory number as "full suite" is the defect this closes.
5. Criterion 12 requires a named reader and cadence when the read-back environment is not this repo.
   - **Given** a spec whose measure names `kaze-webapp` as its read-back environment but no reader, **When** it is graded against criterion 12, **Then** that is a gap; **and Given** a measure read back in this repo with no named reader, **Then** criterion 12 is satisfied without one.
6. Criterion 12 requires stating what a blocked read-back means.
   - **Given** a measure whose environment may be unreachable at read-back time, **When** it is graded, **Then** it must say what an unreadable number means (explicitly *not* "the change failed"), because T-155's own note showed a `0` can mean "not delivered".
7. The authoring template prompts for the new elements, so the rubric is not the first place an author learns of them.
   - **Given** `docs-eng-process/procedures/openup-create-task-spec.md`'s measure template, **When** an author drafts a measure, **Then** the template shows a `Reader:` element and the blocked-read-back clause, marked as required only for non-local environments.
8. Both rubric copies stay byte-identical, and the rendered skill mirrors match their packs.
   - **Given** `.claude/rubrics/task-spec-rubric.md` and `docs-eng-process/.claude-templates/rubrics/task-spec-rubric.md`, **When** the edit lands, **Then** `diff` reports no difference and `check-claude-sync` exits 0.
9. The new criterion-12 elements discriminate rather than pass by construction.
   - **Given** every archived spec carrying a non-local read-back environment, **When** each is checked for a named reader, **Then** the count lacking one is reported — establishing that the criterion distinguishes, and that this is forward-looking rather than retroactive debt.

## Behavior Delta

**Added:**
- `scripts/run-tests.sh` and its coverage guard test.
- Two required elements on criterion 12 (reader + blocked-read-back meaning) for non-local environments.
- A `Reader:` element in the authoring template.

**Modified** — cited artifact + section:
- What "full suite" denotes at completion — `docs-eng-process/procedures/openup-complete-task.md` §Verify Task Completion, and `docs-eng-process/conventions.md` (test-running convention).
- Criterion 12 — `.claude/rubrics/task-spec-rubric.md §12. Success Measure Falsifiability` and its `.claude-templates/` twin.
- The measure template — `docs-eng-process/procedures/openup-create-task-spec.md` §Round 1.
- Step 1b's grading — `docs-eng-process/procedures/openup-complete-task.md` §1b.

**Removed** — none. No existing criterion is relaxed and no test changes.

## Entities

- **Suite runner** (new) — `scripts/run-tests.sh`.
- **Coverage guard** (new) — `scripts/tests/test_full_suite_runner.py`.
- **Criterion 12** (modified, two copies) — `.claude/rubrics/task-spec-rubric.md`, `docs-eng-process/.claude-templates/rubrics/task-spec-rubric.md`.
- **Measure template** (modified) — `docs-eng-process/procedures/openup-create-task-spec.md`.
- **Completion procedure** (modified) — `docs-eng-process/procedures/openup-complete-task.md` (§Verify + §1b).
- **Conventions** (modified) — `docs-eng-process/conventions.md`.
- **Rendered mirrors** (modified, generated) — the two `.claude-templates/skills/` SKILL.md files.

## Approach

C2 replaces prose with a command: one thin wrapper that enumerates the project's test directories, so "full suite" has a referent that cannot drift, plus a guard test that fails when a new directory appears uncovered — the same "no silent omission" shape T-150 used for hook guards. C4 extends criterion 12 rather than adding a criterion: T-152 established that a measure must name where its number is read, and the gap iteration-109 found is one step further out — *who* reads it and *when*, and what an unreadable number means. Both are graded prose with no validator, for the reason T-152 recorded: a name-matcher would pass any phrasing while answering nothing. Deliberately deferred: CI, pytest rootdir configuration, and any attempt to make unreachable environments reachable.

## Structure

**Add:**
- `scripts/run-tests.sh` — enumerate `scripts/tests` + `tests`, run each, aggregate exit codes, print per-directory counts.
- `scripts/tests/test_full_suite_runner.py` — reqs 1–3, including the uncovered-directory guard.

**Modify:**
- `docs-eng-process/procedures/openup-complete-task.md` — §Verify names the runner (req 4); §1b grades the reader element (reqs 5–6).
- `docs-eng-process/procedures/openup-create-task-spec.md` — the measure template gains `Reader:` (req 7).
- `.claude/rubrics/task-spec-rubric.md` + `docs-eng-process/.claude-templates/rubrics/task-spec-rubric.md` — criterion 12 (reqs 5, 6, 8).
- `docs-eng-process/conventions.md` — the test-running convention.
- The two rendered `.claude-templates/skills/` mirrors — regenerated, never hand-edited.
- `docs/roadmap.md` — this task's own entry. *Listed up front deliberately: T-158 and T-159 both omitted it and were caught only at completion (T-159 by its own C3 fix).*

**Do not touch:**
- Any test file other than the new one — C2 is about which tests get run, not what they assert.
- `pytest.ini` / `pyproject.toml` rootdir or `testpaths` — a config change would silently alter every bare `pytest` invocation here and downstream; the wrapper's blast radius is one new file.
- Criterion 12's existing read-back-environment requirement — extended, never relaxed.
- `docs-eng-process/templates/task-spec.md` — the read-only KB-derived template carries no Success Measures section; that section is an authored addition owned by the create-task-spec pack.

## Operations

- [ ] Write `scripts/run-tests.sh` — enumerate the two project test dirs, run each, aggregate exit codes, print per-directory counts; confirm it reports 884 + 114 and exits 0 today.
- [ ] Write `scripts/tests/test_full_suite_runner.py` for reqs 1–3; bite-check req 3 by pointing the guard at a synthetic third test directory and confirming it fails and names it.
- [ ] Update `openup-complete-task.md` §Verify (req 4) and `conventions.md` so "full suite" means the runner, citing the T-155/T-157/T-158 drift as the reason.
- [ ] Extend criterion 12 in **both** rubric copies with the reader + blocked-read-back elements and their gap lines (reqs 5, 6); `diff` the copies to confirm byte-identical (req 8).
- [ ] Add the `Reader:` element to the measure template in `openup-create-task-spec.md` and grade it in `openup-complete-task.md` §1b (reqs 6, 7).
- [ ] Re-render the skill mirrors and sync; confirm `check-claude-sync` exits 0 and both new texts are present in `.claude/skills/` (req 8).
- [ ] (analyst) Run the discrimination check (req 9): across archived specs, count how many name a non-local read-back environment and how many of those name a reader; report both numbers.
- [ ] (tester) Run `scripts/run-tests.sh` and confirm it reports both directories, then confirm the pre-existing counts are unchanged by this lane.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — process + script conventions.
- `docs-eng-process/procedure-frontmatter.md` — edit-the-pack-not-the-mirror.
- `.claude/rubrics/task-spec-rubric.md` — the criterion being extended.

## Safeguards

- **Edit the pack, not the mirror.** `.claude-templates/skills/` and `.claude/skills/` are generated.
- **Both rubric copies or neither.** A one-sided edit is how the two silently diverge; req 8 diffs them.
- **No test may change.** If this lane finds itself editing an assertion, the scope was misread — C2 changes which tests run, not what they check.
- **No relaxation.** Criterion 12's read-back-environment requirement is extended; removing or softening it would undo T-152.
- **No validator for C4.** "Is this reader real?" is not parseable; a matcher would pass any phrasing.
- **Reversibility.** One new script, one new test, prose edits; revert the commit.
- **Size budget.** Runner ≤ ~40 lines of shell. More means it is growing into a CI config, which is out of scope.

## Success Measures

We expect **the number of completion notes or retrospective entries that quote a single-directory test count as "full suite"** to fall from **4 of 4** (T-155, T-157, T-158, and T-159's first draft) to **0 across the next 5 lanes**; and **the number of `can't tell` read-back verdicts that name no follow-up owner** to fall from **3 of 3** (T-147, T-153, T-155 in iteration-109) to **0 for measures authored after this change**. Instrumentation, both already produced by existing process: for C2, the completion notes assembled into `docs/project-status.md` `## Notes` — grep them for a suite figure and compare against `scripts/run-tests.sh`'s aggregate; for C4, the **Measure Read-Back table** of each retrospective, where a `can't tell` row must now carry the reader the spec named. Read-back environment: **this repo** — both instruments are committed here. Reader: **whoever runs the next retrospective** (`/openup-retrospective` step 4b already walks these tables, so no new duty is created). Read-back: **the second retrospective after landing** (absolute backstop **2026-11-30**).

If fewer than 5 lanes complete before read-back, report the lane count with the number — a `0` over an empty window is not evidence.

## Rollout

`n/a — not user-facing.` A developer-facing script plus process documentation; no runtime path and nothing to flag. The runner is additive — existing `pytest <dir>` invocations keep working, so nothing breaks if a lane ignores it. Reaches agents through the rendered mirrors on merge, and downstream consumers via `sync-from-framework.sh`. No flag-removal follow-up is owed.

## Verification

- `bash scripts/run-tests.sh` — exits 0, reports both directories with their counts.
- `asdf exec python3 -m pytest scripts/tests/test_full_suite_runner.py -q` — green, and req 3 bite-checked against a synthetic third directory.
- `diff .claude/rubrics/task-spec-rubric.md docs-eng-process/.claude-templates/rubrics/task-spec-rubric.md` — empty.
- `bash scripts/check-claude-sync.sh` — exits 0; both new texts present in `.claude/skills/`.
- Discrimination count for req 9 reported in `design.md`.
- `python3 scripts/check-docs.py` and `python3 scripts/openup-fence.py check` clean.
- Grade against `.claude/rubrics/task-spec-rubric.md` — including, reflexively, the criterion this task extends.

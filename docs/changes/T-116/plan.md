---
id: T-116
title: Hook-sweep parity — fold hook-appended docs/agent-logs/ shards into the same commit instead of a manual follow-up
status: ready
priority: medium
estimate: 1 session
plan: docs/iteration-plans/2026-07-14-bootstrap-overhead-fixes.md
depends-on: []
blocks: []
touches:
  - docs-eng-process/conventions.md
  - docs-eng-process/procedures/openup-complete-task.md
  - docs-eng-process/procedures/openup-cycle.md
  - docs-eng-process/.claude-templates/skills/openup-complete-task/SKILL.md
  - docs-eng-process/.claude-templates/skills/openup-cycle/SKILL.md
last-synced: ""
---

# T-116 — Hook-sweep parity — fold hook-appended docs/agent-logs/ shards into the same commit instead of a manual follow-up

## Story

> **As an** agent driving a delivery lane through any Claude-Code OpenUP skill
> **I want** the log line `auto-log-commit.py` appends after each of my commits
> to be swept into my *next* commit automatically, instead of discovering it
> via `git status` and improvising a second commit
> **So that** a lane's commit history stops accumulating avoidable follow-up
> commits and round-trip tool calls — observed 6 times in one live bootstrap
> lane

INVEST check:
✅ Independent (doc/procedure wording only, no dependency) · ✅ Negotiable
(exact wording, which skills get the explicit pointer vs. rely on the
canonical convention) · ✅ Valuable (evidenced live: 6 redundant round trips
in one lane) · ✅ Estimable (3 files, all prose) · ✅ Small (no code, no new
mechanism — porting a pattern that already exists and works) · ✅ Testable
(re-running the same class of lane should show no "check for further
hook-triggered changes" round trip)

## Analysis Context

- **Domain.** Process documentation: `docs-eng-process/conventions.md` (the
  acknowledged single source of truth for commit conventions — every skill's
  Norms section inherits from it) and the two procedure files whose commit
  steps are the natural "final sweep" points for a lane:
  `openup-complete-task.md` (step 2, "Commit Remaining Changes" — already
  described as sweeping "any leftover uncommitted work") and `openup-cycle.md`
  (its box-loop gate-before-tick step, which already commits/gates per box).
- **Scope boundaries.** Does not touch `.claude/scripts/hooks/auto-log-commit.py`
  itself (its `PostToolUse`-can't-block-before-a-commit constraint is
  mechanical and correct — this task works *with* that constraint, not around
  it). Does not touch `docs-eng-process/procedures/openup-next.md` (no-go
  zone carried over from T-112/T-113 unless proven necessary — it is not:
  `/openup-next` delegates its commit-issuing work to
  `/openup-start-iteration` and `/openup-complete-task`, so fixing those two
  covers `/openup-next`'s lanes too without editing `/openup-next` itself).
  Does not attempt a repo-wide sweep of every skill that ever issues a
  `git commit` (e.g. `/openup-quick-task`, `/openup-init`,
  `/openup-create-vision`'s internal commit step) — those inherit the fix via
  the canonical convention doc but are not individually edited in this task
  (see Assumption below).
- **Definition of done.** `conventions.md` states the sweep rule once,
  authoritatively, next to the existing commit-format rule it's already the
  source of truth for. `openup-complete-task.md` step 2 and `openup-cycle.md`'s
  gate/tick step each carry an explicit one-line pointer to it (mirroring how
  "canonical format" is both centrally defined and locally restated today).
  check-docs/mirror/guide gates stay green; `openup-next.md` stays
  byte-unchanged.

**Assumption:** only `openup-complete-task.md` and `openup-cycle.md` get an
explicit inline pointer — every other commit-issuing skill (`/openup-quick-task`,
`/openup-init`, `/openup-create-vision`, `/openup-start-iteration`'s step 6c)
relies on the canonical `conventions.md` rule alone, not a per-skill edit.
Rationale: those two are the highest-leverage "final sweep" points a lane
always passes through before it's considered done, and editing every
commit-issuing skill in the framework is a much larger, cross-cutting change
the exploration's product-manager pass explicitly scoped this task away from.
*(Vetoable at review — if a follow-up dry run still shows ping-pong inside
`/openup-init` or `/openup-create-vision` specifically, those get their own
narrow follow-up rather than retroactively expanding this task.)*

## Requirements

1. `docs-eng-process/conventions.md` states the hook-sweep rule once,
   authoritatively, referencing the proven pattern it mirrors.
   - **Given** an agent about to make any commit has read `conventions.md`'s
     commit-format section, **When** it checks for a prior hook-appended
     `docs/agent-logs/` delta, **Then** the doc instructs folding it into the
     current commit's `git add` rather than leaving it for a follow-up commit,
     and names `scripts/openup_agent/cycle.py`'s `_sweep_run_logs` as the
     pattern this mirrors.

2. `openup-complete-task.md` step 2 explicitly sweeps hook-appended
   `docs/agent-logs/` deltas, not just the task's own leftover changes.
   - **Given** a lane has made one or more commits earlier in its life, each
     of which triggered `auto-log-commit.py` to append a line after the fact,
     **When** `/openup-complete-task` reaches step 2 ("Commit Remaining
     Changes"), **Then** its instructions explicitly stage and fold any
     `docs/agent-logs/` delta into that step's commit alongside other leftover
     changes, rather than only mentioning "leftover uncommitted work" in the
     abstract.

3. `openup-cycle.md`'s box-loop gate/tick step folds hook-appended deltas into
   the commit it's already making for that box, when that box's execution
   included a commit.
   - **Given** a script or judgment box's execution included a `git commit`
     (e.g. a script-step box that is itself a commit, or a judgment box whose
     work ends in one), **When** `/openup-cycle` reaches its gate-before-tick
     step, **Then** the instructions direct folding any
     `docs/agent-logs/`-shard delta left by that commit's hook into the
     box-loop's own next action rather than leaving it to accumulate silently
     until completion.

4. `openup-next.md` is preserved exactly as-is.
   - **Given** T-116 is complete, **When**
     `git diff <base> -- docs-eng-process/procedures/openup-next.md` is run,
     **Then** it produces no output.

## Behavior Delta

`n/a — all Added`. This adds an explicit instruction where prior wording was
silent (`openup-complete-task.md`'s step 2 already existed and already swept
"leftover uncommitted work" in the abstract; this task makes the
`docs/agent-logs/` case concrete, not a change to what the step *does*). No
existing documented product behavior is removed or contradicted.

## Entities

- **Commit conventions** (modified) — `docs-eng-process/conventions.md`
- **`openup-complete-task` procedure** (modified) — `docs-eng-process/procedures/openup-complete-task.md`
- **`openup-cycle` procedure** (modified) — `docs-eng-process/procedures/openup-cycle.md`
- **`auto-log-commit.py` hook** (read-only reference, unmodified) — `.claude/scripts/hooks/auto-log-commit.py`
- **`_sweep_run_logs` reference pattern** (read-only reference, unmodified) — `scripts/openup_agent/cycle.py:1060-1084`

## Approach

Port the *effect* of `cycle.py`'s `_sweep_run_logs` (fold hook-appended
`docs/agent-logs/` deltas into the lane's own commit stream, zero manual
noticing) into the Claude-Code substrate as prose, the same restatement
pattern `/openup-cycle` already uses for `classify_box`. State the rule once
in `conventions.md` (the acknowledged single source of truth every skill's
Norms section already inherits from), then add a short explicit pointer at
the two highest-leverage commit-issuing points a lane always passes through:
`/openup-complete-task`'s final sweep and `/openup-cycle`'s per-box
gate/commit step. No new script, no hook change — the fix is that agents stop
needing to *notice* the hook's append and instead fold it in as a matter of
habit, documented once and pointed to twice.

## Structure

**Modify:**
- `docs-eng-process/conventions.md` — add the sweep rule to (or immediately
  after) the existing "Commit Message Format" section
- `docs-eng-process/procedures/openup-complete-task.md` — step 2 gains an
  explicit `docs/agent-logs/` sweep instruction
- `docs-eng-process/procedures/openup-cycle.md` — the gate-before-tick step
  gains the same pointer
- `docs-eng-process/.claude-templates/skills/openup-complete-task/SKILL.md` —
  regenerated mirror
- `docs-eng-process/.claude-templates/skills/openup-cycle/SKILL.md` —
  regenerated mirror

**Do not touch:**
- `.claude/scripts/hooks/auto-log-commit.py` — its post-commit-only timing is
  a correct mechanical constraint, not a bug to fix
- `docs-eng-process/procedures/openup-next.md` — no-go zone; its lanes inherit
  the fix via the two skills it delegates commits to
- `docs-eng-process/procedures/openup-init.md`, `openup-quick-task.md`,
  `openup-create-vision.md`, `openup-start-iteration.md` — out of scope per
  the Analysis Context assumption; they inherit the canonical
  `conventions.md` rule but are not individually edited here

## Operations

- [x] (developer) Add the hook-sweep rule to `docs-eng-process/conventions.md`, naming `_sweep_run_logs` (`scripts/openup_agent/cycle.py:1060-1084`) as the pattern it mirrors.
- [x] (developer) Add the explicit `docs/agent-logs/` sweep pointer to `openup-complete-task.md` step 2 ("Commit Remaining Changes").
- [x] (developer) Add the same pointer to `openup-cycle.md`'s gate-before-tick step.
- [x] `python3 scripts/render-skills-mirror.py --write && scripts/sync-templates-to-claude.sh && python3 scripts/check-skills-guide.py --write && python3 scripts/check-model-tiers.py --write`
- [x] `git diff harness-optional -- docs-eng-process/procedures/openup-next.md`
- [x] `python3 scripts/render-skills-mirror.py --check && python3 scripts/check-skills-guide.py --check && python3 scripts/check-model-tiers.py --check && python3 scripts/check-docs.py`

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — this task's own subject and the
  existing commit-format source of truth it extends
- `docs-eng-process/procedure-frontmatter.md` — the neutral procedure
  frontmatter contract the two edited procedures already satisfy

## Safeguards

- **Token / size budget.** Each edit is a short, localized addition (a few
  lines) — not a rewrite of either procedure's existing structure.
- **Reversibility.** Revert the three prose edits and regenerate the mirrors;
  no other repo state depends on this wording.
- **No-go zones.** Never edit `docs-eng-process/procedures/openup-next.md`.
  Never hand-edit the generated mirrors (only via their generators). Never
  touch `.claude/scripts/hooks/auto-log-commit.py`'s timing — the fix works
  with the `PostToolUse` constraint, not around it.

## Verification

- `python3 scripts/render-skills-mirror.py --check`
- `python3 scripts/check-skills-guide.py --check`
- `python3 scripts/check-model-tiers.py --check`
- `python3 scripts/check-docs.py`
- `git diff harness-optional -- docs-eng-process/procedures/openup-next.md` — must be empty
- Manual re-read: does the new wording, applied to the observed live
  transcript's commit points, eliminate the "check for further hook-triggered
  changes" round trip? (Reasoned check against the transcript, not a live
  re-run — see Success Measures.)

## Success Measures

We expect the next real lane completed through `/openup-complete-task` (or a
`/openup-cycle` box-loop with an in-box commit) to show **zero** separate
"notice the hook appended something, make a follow-up commit" round trips —
a magnitude of exactly 0, vs. the 6 observed in the live T-002 bootstrap lane
this task is fixing. Instrumentation: the commit history of that lane itself
(`git log --oneline`) — a clean sweep looks like one commit per real step, not
two. Read-back: after the next real lane's completion, whenever that occurs
(this repo's own delivery loop is the only consumer).

## Rollout

**Flagged?** No — this is a procedure-wording change with no runtime toggle;
the only "rollout" is the next agent that reads the updated instructions.
Not applicable in the feature-flag sense.

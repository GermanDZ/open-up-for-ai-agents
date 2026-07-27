---
id: T-148
title: "`begin` never seeds the plan gate from the task's own spec, forcing a manual `set-gate plan_persisted` every session"
status: ready
priority: medium
estimate: 0.5 session
plan: ""
depends-on: []
blocks: []
last-synced: ""
touches:
  - scripts/openup-session.py
  - scripts/tests/test_openup_session.py
  - docs-eng-process/procedures/openup-start-iteration.md
  - docs-eng-process/.claude-templates/skills/openup-start-iteration/SKILL.md
  - docs-eng-process/script-cli-reference.md
  - docs-eng-process/state-file.md
  - docs/roadmap.md
---

# T-148 — `begin` never seeds the plan gate from the task's own spec

## Story

> **As** an agent starting a standard-track lane
> **I want** `openup-session.py begin` to seed `gates.plan_persisted` from the task's own
> already-persisted spec without being told the path
> **So that** the first source-code edit is not blocked by `gate-edits.py`, and nobody has
> to run a manual `set-gate plan_persisted` recovery step every single session.

INVEST check:
✅ Independent (no other lane touches `begin`'s init plumbing) ·
✅ Negotiable (auto-resolve vs. prose-only fix was the live choice; both are in scope below) ·
✅ Valuable (the workaround was applied on five consecutive tasks this session, and observed
   live in a downstream project) ·
✅ Estimable (one resolution helper + one pack step + one test) ·
✅ Small (< 60 LOC of script change) ·
✅ Testable (a `begin` with no `--plan` either seeds the gate or it does not — a single
   `state.json` read decides it).

## Analysis Context

- **Domain.** The session-acquire path: `openup-session.py begin` → `openup-state.py init
  --plan` → `gates.plan_persisted`, consumed by the `gate-edits.py` hook, which blocks
  `Write`/`Edit` on `standard`/`full` tracks while the gate is `false`.
- **Why the current shape fails.** `begin` forwards `--plan` only when the caller supplies
  it, and the only place that tells a caller to supply it —
  `docs-eng-process/procedures/openup-start-iteration.md` step 6, line 365 — renders it as
  an **optional** flag pointing at the **wrong convention**:
  `[--plan docs/plans/{plan}.md]`. `docs/plans/` holds *phase-level* plans; a task's spec
  lives at `docs/changes/{task_id}/plan.md`. So the flag is both easy to skip and, if
  copied verbatim, wrong. The information needed to resolve it correctly is already a
  hard precondition of step 6 ("the claim's `touches` and `depends-on` are read from
  `docs/changes/{task_id}/plan.md` … persist the plan **before** `begin`"), so the spec
  file is guaranteed present on disk at the moment `begin` runs.
- **Scope boundaries.** Does **not** change what the plan gate *means*, the `quick`-track
  relaxation, `gate-edits.py` itself, the `--plan` flag's explicit form, or
  `openup-doctor --fix`'s existing auto-heal of an unset gate (T-117) — that band-aid stays
  as a recovery path for lanes started before this fix.
- **Definition of done.** `openup-session.py begin --track standard` (no `--plan`) run for a
  task whose `docs/changes/<id>/plan.md` exists writes `gates.plan_persisted` =
  `"docs/changes/<id>/plan.md"`, logs a `plan_gate_autoresolved` event, and needs no
  follow-up `set-gate` call; the pack's step 6 no longer prints the `docs/plans/` path.

> **Assumption:** auto-resolution applies on `standard`/`full` only — the `quick` track has
> no plan gate, so seeding it there would be noise. *(Vetoable at review.)*

> **Assumption:** an explicit `--plan` always wins over auto-resolution, with no warning
> even when it disagrees with the conventional path — legacy lanes legitimately point at
> `docs/plans/` and `docs/iteration-plans/` files. *(Vetoable at review.)*

> **Assumption:** resolution is **fail-open** — a missing `docs/changes/<id>/plan.md` leaves
> the gate `false` exactly as today rather than refusing the `begin`. Refusing would turn a
> paper cut into a hard stop for any lane that keeps its plan elsewhere. *(Vetoable at review.)*

## Requirements

1. `begin` with `--track standard` (or `full`), **no** `--plan`, and an existing
   `docs/changes/<task_id>/plan.md` under the resolved worktree seeds
   `gates.plan_persisted` with the repo-relative path `docs/changes/<task_id>/plan.md`.
   - **Given** a worktree containing `docs/changes/T-900/plan.md` and no `--plan` flag
     **When** `openup-session.py begin --task-id T-900 --track standard --worktree <wt>` runs
     **Then** `state.json`'s `gates.plan_persisted` equals `"docs/changes/T-900/plan.md"`
     (a string, not `false`).

2. An explicitly supplied `--plan` is used verbatim and auto-resolution does not override it.
   - **Given** a worktree containing `docs/changes/T-900/plan.md`
     **When** `begin … --plan docs/plans/legacy.md` runs
     **Then** `gates.plan_persisted` equals `"docs/plans/legacy.md"`.

3. Resolution is fail-open: a missing spec file leaves the gate `false` and `begin` still
   exits 0.
   - **Given** a worktree with **no** `docs/changes/T-901/plan.md` and no `--plan` flag
     **When** `begin --task-id T-901 --track standard` runs
     **Then** `begin` exits 0 and `gates.plan_persisted` is `false`.

4. The `quick` track does not auto-resolve.
   - **Given** a worktree containing `docs/changes/T-902/plan.md` and no `--plan` flag
     **When** `begin --task-id T-902 --track quick` runs
     **Then** `gates.plan_persisted` is `false`.

5. Auto-resolution is observable in the durable run log, so the fix's effect can be read
   back later without a transcript.
   - **Given** a `begin` that auto-resolved the plan path
     **When** the lane's run shard under `docs/agent-logs/runs/` is read
     **Then** it contains a record whose `event` is `plan_gate_autoresolved` for that task id.

6. The pack's step 6 no longer advertises the wrong path or the flag as optional-by-default.
   - **Given** `docs-eng-process/procedures/openup-start-iteration.md`
     **When** step 6's `begin` block is read
     **Then** it contains no `--plan docs/plans/{plan}.md` occurrence, and states that on
     `standard`/`full` the gate is auto-resolved from `docs/changes/{task_id}/plan.md`.

7. The rendered skill mirror matches the pack (no drift).
   - **Given** the pack edit has landed **When** `python3 scripts/render-skills-mirror.py --check`
     runs **Then** it exits 0.

## Behavior Delta

The affected artifacts are process/tooling (Ring 2 + `docs-eng-process/`), not Ring-1
product behavior under `docs/product/` — **verified**: `docs/product/` contains only
`milestones/`, and no file under it mentions `plan_persisted`, `openup-session`, or the
session-acquire path. So the Modified entries below cite their `docs-eng-process/` sources,
which is where `/openup-sync-spec` must go for this task.

**Added**
- `begin` auto-resolves the plan gate from the task's own spec on `standard`/`full`.
- A `plan_gate_autoresolved` run-log event.

**Modified**
- `docs-eng-process/procedures/openup-start-iteration.md` §6 — the `--plan` line changes from
  optional `docs/plans/{plan}.md` to auto-resolved-from-`docs/changes/{task_id}/plan.md`.
- `docs-eng-process/script-cli-reference.md` §`openup-session.py` — the `begin` signature
  block gains the auto-resolution note.
- `docs-eng-process/state-file.md` §gate-source table — the `plan_persisted` row's source
  changes from "`openup-start-iteration` (`init --plan`)" to "`begin` (auto-resolved) or
  explicit `--plan`".

**Removed**
- Nothing. The manual `set-gate plan_persisted` path remains valid and is still what
  `openup-doctor --fix` invokes for pre-existing lanes.

## Entities

- **`begin` command** (modified) — `scripts/openup-session.py` `cmd_begin`, the `init_argv`
  assembly around the existing `if args.plan:` branch.
- **`plan_gate` seed** (read-only) — `scripts/openup-state.py:407`
  (`plan_gate = args.plan if args.plan else False`); unchanged, the fix feeds it.
- **`gate-edits.py`** (read-only) — the consumer that blocks on `plan_persisted == false`.
- **Pack step 6** (modified) — `docs-eng-process/procedures/openup-start-iteration.md`.
- **Skill mirror** (regenerated) —
  `docs-eng-process/.claude-templates/skills/openup-start-iteration/SKILL.md`.

## Approach

Move the resolution from prose (which every agent must remember to follow) into `begin`
(which cannot forget). A small pure helper takes `(plan_arg, track, worktree, task_id)` and
returns the path to forward plus whether it was auto-resolved; `cmd_begin` calls it just
before building `init_argv` and, on an auto-resolution, emits one extra `log-event` so the
behavior is auditable. The pack edit then becomes documentation of what the tool already
does rather than an instruction the tool depends on — belt *and* braces, with the braces
load-bearing.

## Structure

**Add:**
- `_resolve_plan_path(...)` helper in `scripts/openup-session.py` (module-level, pure,
  unit-testable without a claim).
- Four tests in `scripts/tests/test_openup_session.py` covering requirements 1–5.

**Modify:**
- `scripts/openup-session.py` — call the helper in `cmd_begin`; log
  `plan_gate_autoresolved` when it fires.
- `docs-eng-process/procedures/openup-start-iteration.md` — step 6 `--plan` line + a
  sentence stating the auto-resolution and its `standard`/`full` scope.
- `docs-eng-process/script-cli-reference.md` — `begin` block note.
- `docs-eng-process/state-file.md` — `plan_persisted` gate-source row.
- `docs-eng-process/.claude-templates/skills/openup-start-iteration/SKILL.md` — regenerated,
  never hand-edited.
- `docs/roadmap.md` — status row for T-148.

**Do not touch:**
- `scripts/openup-state.py` — its `--plan` → `plan_gate` seeding is already correct; the bug
  is entirely upstream of it.
- `.claude/scripts/hooks/gate-edits.py` and its template — the gate's *semantics* are
  correct; only its input was missing.
- `scripts/openup-doctor.py` (T-117 auto-heal) — still the right recovery for lanes started
  before this fix.
- `.claude/skills/openup-start-iteration/` — a sync target, not a source (see the
  edit-the-pack rule).

## Operations

- [ ] Add `_resolve_plan_path()` to `scripts/openup-session.py` and wire it into `cmd_begin`'s
      `init_argv` assembly (explicit `--plan` wins; `standard`/`full` only; fail-open).
- [ ] Emit a `plan_gate_autoresolved` `log-event` from `cmd_begin` when the helper resolved
      the path, so the effect is readable from the run shard.
- [ ] (tester) Add the four regression tests to `scripts/tests/test_openup_session.py`
      (auto-resolve, explicit wins, missing-file fail-open, quick-track no-op) and run
      `python3 -m unittest scripts.tests.test_openup_session`.
- [ ] Fix `docs-eng-process/procedures/openup-start-iteration.md` step 6: drop
      `--plan docs/plans/{plan}.md`, state the auto-resolution from
      `docs/changes/{task_id}/plan.md` on `standard`/`full`.
- [ ] Update `docs-eng-process/script-cli-reference.md` (`begin` block) and
      `docs-eng-process/state-file.md` (`plan_persisted` gate-source row) to match.
- [ ] Regenerate the mirror — `python3 scripts/render-skills-mirror.py --write` then
      `bash scripts/sync-templates-to-claude.sh` — and confirm `--check` exits 0.
- [ ] Run the full suite (`python3 scripts/check-docs.py`, `bash tests/test-scripts.sh`)
      and confirm no regression.

## Norms

Inherits from:
- `docs-eng-process/conventions.md` — commit format, process conventions.
- `.claude/CLAUDE.openup.md` — edit-the-pack-not-the-mirror; fix-spec-first; write-fence.
- `docs-eng-process/state-file.md` — the gate contract this task feeds.
- `docs-eng-process/tracks.md` — the `quick` relaxation this task must preserve.

## Safeguards

- **Token / size budget.** ≤ 60 LOC net in `scripts/openup-session.py`; ≤ 6 changed lines in
  each of the three `docs-eng-process/` prose files.
- **Reversibility.** The helper is additive and returns the caller's `--plan` untouched when
  supplied; reverting the single call site restores today's behavior exactly.
- **No-go zones.** `begin`'s exit codes must not change (3/4/9 keep their meanings, and a
  missing spec must never produce a nonzero exit). The rollback boundary must stay where it
  is — resolution happens **before** the claim-dependent init, and must not introduce a new
  failure path between claim and state-init.
- **Mirror integrity.** The `.claude-templates/skills/` and `.claude/skills/` copies are
  generated; hand-editing either is a defect even if the content is right.
- **No event enum.** `openup-state.py log-event --event` is deliberately free-form
  (verified: no `choices=` on the argument). Do not add an allow-list while wiring
  `plan_gate_autoresolved` — other callers pass arbitrary event names.

## Verification

- `python3 -m unittest scripts.tests.test_openup_session` — all four new tests pass.
- `python3 scripts/render-skills-mirror.py --check` exits 0 (mirror matches the pack).
- `grep -c 'docs/plans/{plan}.md' docs-eng-process/procedures/openup-start-iteration.md`
  returns 0.
- `bash tests/test-scripts.sh` and `python3 scripts/check-docs.py` pass.
- End-to-end: this lane's own `.openup/state.json` shows
  `gates.plan_persisted == "docs/changes/T-148/plan.md"` — but note it was seeded by the
  pre-fix manual path, so the real end-to-end proof is the next lane started after merge.
- Grade against `.claude/rubrics/task-spec-rubric.md` — every criterion ✅.

## Success Measures

We expect the count of lanes needing a manual `openup-state.py set-gate plan_persisted`
recovery step to move **from 5-of-5 (T-132, T-134, T-135, T-136, T-138) to 0** within the
**next 5 `standard`/`full` lanes started after this merges**. Instrumentation: the
`plan_gate_autoresolved` event this task adds, appended to the lane's run shard under
`docs/agent-logs/runs/<date>-<task>.jsonl`; a lane that auto-resolved has the event, a lane
that needed the manual workaround does not. Read-back environment: **this repo** —
`docs/agent-logs/runs/` is git-tracked here (verified: 2026-07-27 shards for T-146, T-150,
T-151, T-152, T-153 are all present and tracked). Read-back: at the next retrospective, or
2026-08-10, whichever comes first.

Deliberately *not* measured via archived `state.json` gate values: every archived lane already
shows the gate set, because the manual workaround set it — that instrument cannot tell
"automatic" from "repaired by hand", which is precisely the difference this task creates.

## Rollout

**Flagged? No.** The change is an internal tooling default with no user-facing surface and no
data migration: `begin` either forwards a path it derived or forwards nothing, exactly as
today. A flag would add a branch to a code path whose entire risk is "does the gate get a
string or `false`", which the four regression tests already pin. Backout is
`git revert` of one call site — cheaper than a toggle. Consumers on an older checkout are
unaffected: the pack change reaches them only via `sync-templates-to-claude.sh`, and the
script change is backward compatible with every existing `--plan` caller.

No flag ⇒ no flag-removal follow-up.
